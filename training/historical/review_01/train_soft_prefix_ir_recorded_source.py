"""Train LoRA-IR with soft-prefix conditioning from z_ir_hat.

This replaces the old hints-probe IR path. The Qwen text prompt carries only
task instructions, optional query-derived evidence, and optional retrieved IR
examples. The predicted latent enters LoRA-IR through inputs_embeds:

    inputs_embeds = concat(SoftPrefixAdapter(z_ir_hat), token_embeddings(prompt+target))

--target selects what the prefix conditions. `ir` is the deployed plan decoder.
`program` is B1: the same latent through the same adapter into the CODE decoder, with
no plan text in the prompt, so that the paper can separate conditioning on a
construction representation from writing the construction down as text.
"""
from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
from torch import nn
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, Trainer, TrainerCallback, TrainingArguments

from miragecad.data import (
    load_image,
    load_step_brep_tensors,
    read_jsonl,
    read_text,
)
from miragecad.gen_prompts import build_ir_prompt, build_program_prompt
from miragecad.latent_prior import LatentPrior, LatentPriorConfig
from miragecad.models import load_alignment_checkpoint
from miragecad.point_sampling import load_point_cloud_sampled
from miragecad.soft_prefix import (
    SoftPrefixAdapter,
    SoftPrefixConfig,
    load_soft_prefix_adapter,
    resolve_soft_prefix_path,
    save_soft_prefix_adapter,
)


@dataclass
class IRExample:
    sample_id: str
    prompt: str
    target: str
    z_ir_hat: np.ndarray


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train soft-prefix LoRA-IR.")
    p.add_argument("--model-name", default="Qwen/Qwen2.5-Coder-1.5B")
    p.add_argument("--alignment-checkpoint", type=Path, required=True)
    p.add_argument("--prior-checkpoint", type=Path, default=None,
                   help="Required for single-modality training (paired with --modality); unused in "
                        "--modality-prior multi-modality mode.")
    p.add_argument("--modality", choices=["text", "image", "point", "step"], default=None,
                   help="Single-modality training (the original, validated recipe). Mutually exclusive "
                        "with --modality-prior; exactly one of the two must be given.")
    p.add_argument("--modality-prior", action="append", default=None, metavar="MODALITY:PATH",
                   help="Stage 3b multi-modality mixed training: repeat this flag once per modality to mix "
                        "(e.g. --modality-prior step:outputs/prior_step_25k/best.pt --modality-prior "
                        "point:outputs/prior_point_25k/best.pt ...). Every listed modality's rows are built "
                        "from the SAME --train-jsonl/--val-jsonl rows (same target reference IR each time), "
                        "using that modality's own prior checkpoint to produce z_ir_hat, then concatenated "
                        "into one combined training set. Mutually exclusive with --modality/--prior-checkpoint.")
    p.add_argument("--init-lora-ir-dir", type=Path, default=None,
                   help="Continue training from an existing LoRA-IR + soft_prefix.pt checkpoint (e.g. "
                        "outputs/lora_ir_25k) instead of initializing fresh -- for Stage 3b continuation "
                        "fine-tuning on top of the validated Stage 3 checkpoint.")
    p.add_argument("--train-jsonl", type=Path, required=True)
    p.add_argument("--val-jsonl", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--retrieval-index", type=Path, default=None)
    p.add_argument("--use-retrieval", action="store_true")
    p.add_argument("--retrieval-top-k", type=int, default=3)
    # B1, the direct-latent arm. `ir` is the deployed configuration: the latent conditions
    # the PLAN decoder and the plan text is what reaches the code decoder. `program` removes
    # the plan entirely and conditions the CODE decoder on the same latent through the same
    # adapter, which is the arm the paper needs in order to separate "conditioning on a
    # construction representation" from "writing the construction down as text".
    #
    # The observation block is UNCHANGED in both: build_program_prompt appends it exactly as
    # the deployed code decoder receives it. B1 differs from A3 in one respect only, the
    # absence of the plan, which is what makes the contrast interpretable.
    #
    # Default `ir` so every published path reproduces byte for byte.
    p.add_argument("--target", choices=["ir", "program"], default="ir",
                   help="ir: train the plan decoder (deployed). "
                        "program: B1 -- train the code decoder on the latent directly, with "
                        "no plan text in the prompt.")
    p.add_argument("--prefix-len", type=int, default=4)
    p.add_argument("--prefix-dropout", type=float, default=0.0)
    p.add_argument("--max-length", type=int, default=1536)
    p.add_argument("--epochs", type=float, default=3)
    p.add_argument("--learning-rate", type=float, default=2e-4)
    p.add_argument("--warmup-ratio", type=float, default=0.03)
    p.add_argument("--weight-decay", type=float, default=0.0)
    p.add_argument("--per-device-train-batch-size", type=int, default=1)
    p.add_argument("--per-device-eval-batch-size", type=int, default=1)
    p.add_argument("--gradient-accumulation-steps", type=int, default=16)
    p.add_argument("--eval-steps", type=int, default=250)
    p.add_argument("--save-steps", type=int, default=250)
    p.add_argument("--logging-steps", type=int, default=10)
    p.add_argument("--save-total-limit", type=int, default=2)
    p.add_argument("--lora-r", type=int, default=8)
    p.add_argument("--lora-alpha", type=int, default=16)
    p.add_argument("--lora-dropout", type=float, default=0.05)
    p.add_argument("--load-in-4bit", action="store_true")
    p.add_argument("--bf16", action="store_true")
    p.add_argument("--fp16", action="store_true")
    p.add_argument("--no-tf32", action="store_true")
    p.add_argument("--point-count", type=int, default=1024)
    p.add_argument("--train-point-sampling", choices=["random", "fps", "hybrid"], default="hybrid",
                   help="Point sampling for training rows (architecture §8: 50%% random + 50%% FPS).")
    p.add_argument("--eval-point-sampling", choices=["random", "fps", "hybrid"], default="fps",
                   help="Point sampling for val/test rows (deterministic FPS).")
    p.add_argument("--limit-train", type=int, default=None)
    p.add_argument("--limit-val", type=int, default=None)
    p.add_argument("--seed", type=int, default=42)
    # NO CRASH RESUME HERE, and the reason is worth recording so it is not attempted again.
    #
    # A --crash-resume flag briefly existed, switching on the HF Trainer's own checkpointing so
    # that a CUDA fault would cost --save-steps steps rather than the whole run. Trainer._save
    # serialises through safetensors, which refuses tied tensors, and this base model ties
    # lm_head.weight to embed_tokens.weight. The first native save is at step --save-steps, so
    # the run died at step 500 -- at precisely the moment the feature existed to protect. The
    # one-line escape, save_safetensors=False, was removed in transformers 5.5.1.
    #
    # A correct version needs overrides of both Trainer._save and Trainer._load_from_checkpoint
    # so the checkpoint holds only the trainable tensors; the 4-bit base is frozen and not worth
    # saving. That is real surgery on a trainer whose published runs must reproduce, and it is
    # not worth doing speculatively.
    #
    # train_program_lora.py is unaffected and resumes fine: it hands Trainer a PeftModel, so HF
    # saves the adapter alone and never meets the tied pair. This trainer hands it a plain module
    # wrapper, so HF tries the full state dict. That difference is the entire story.
    return p.parse_args()


def load_prior(path: Path, device: torch.device) -> LatentPrior:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    cfg = payload["config"]
    if "modality" not in cfg:
        raise ValueError(f"Prior checkpoint {path} missing 'modality' in config. Re-save with updated train_latent_prior.py.")
    config = LatentPriorConfig(**cfg)
    prior = LatentPrior(config)
    prior.load_state_dict(payload["state_dict"], strict=True)
    return prior.to(device).eval()


@torch.no_grad()
def encode_query(
    row: dict,
    modality: str,
    aligner,
    prior: LatentPrior,
    args: argparse.Namespace,
    device: torch.device,
    point_sampling: str = "fps",
) -> tuple[np.ndarray, np.ndarray | None]:
    point_xyz = None
    if modality == "text":
        z_m = aligner.encode_text([row.get("text", "")], device)
    elif modality == "image":
        img = load_image(row["iso_image_path"])
        z_m = aligner.encode_image([img], device)
    elif modality == "step":
        tensors = load_step_brep_tensors(row["step_feature_path"], strict=True)
        batch = {k: torch.tensor(v[None], dtype=torch.float32).to(device) for k, v in tensors.items()}
        z_m = aligner.encode_step(batch)
    elif modality == "point":
        point_xyz = load_point_cloud_sampled(
            row["point_path"],
            point_count=args.point_count,
            sampling=point_sampling,
            seed=args.seed,
        )
        z_m = aligner.encode_point(torch.tensor(point_xyz[None], dtype=torch.float32).to(device))
    else:
        raise ValueError(modality)
    z_ir_hat = prior(z_m)
    return z_ir_hat.cpu().numpy()[0], point_xyz


def retrieve_ir_examples(index, z_ir_hat: np.ndarray, top_k: int, row: dict) -> list[dict[str, str]]:
    embeddings = index["embeddings"]
    scores = embeddings @ z_ir_hat
    order = np.argsort(-scores)[:top_k]
    dataset_root = Path(row.get("dataset_root", "."))
    examples: list[dict[str, str]] = []
    for i in order:
        sample_dir = dataset_root / str(index["relpaths"][i])
        examples.append({"ir": read_text(sample_dir / "training_ir.txt")})
    return examples


def build_examples(
    rows: list[dict[str, Any]],
    modality: str,
    aligner,
    prior: LatentPrior,
    args: argparse.Namespace,
    device: torch.device,
    retrieval_index=None,
    desc: str = "build-examples",
    point_sampling: str = "fps",
) -> list[IRExample]:
    examples: list[IRExample] = []
    for row in tqdm(rows, desc=desc):
        try:
            z_ir_hat, point_xyz = encode_query(row, modality, aligner, prior, args, device, point_sampling=point_sampling)
        except Exception as exc:
            print(f"WARNING: encode failed for {row.get('sample_id', '?')}: {exc}")
            continue
        retrieved_ir = None
        if retrieval_index is not None and args.use_retrieval:
            retrieved_ir = retrieve_ir_examples(retrieval_index, z_ir_hat, args.retrieval_top_k, row)
        if args.target == "program":
            # No plan block and no plan instruction line: include_plan=False drops both, so
            # the prompt cannot refer to something that is not there. The observation block
            # is appended exactly as the deployed code decoder sees it.
            prompt = build_program_prompt(row, modality, "", point_xyz=point_xyz,
                                          include_plan=False)
            target = read_text(row.get("program_path", "")).strip()
        else:
            prompt = build_ir_prompt(row, modality, retrieved_ir=retrieved_ir,
                                     point_xyz=point_xyz)
            target = read_text(row["ir_path"]).strip()
        if not target:
            continue
        examples.append(IRExample(str(row.get("sample_id", "")), prompt, target, z_ir_hat.astype(np.float32)))
    return examples


class SoftPrefixIRDataset(Dataset):
    def __init__(self, examples: list[IRExample], tokenizer, max_length: int):
        self.examples = examples
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        ex = self.examples[idx]
        prompt_ids = self.tokenizer(ex.prompt, add_special_tokens=True)["input_ids"]
        target_ids = self.tokenizer(ex.target + self.tokenizer.eos_token, add_special_tokens=False)["input_ids"]
        input_ids = (prompt_ids + target_ids)[: self.max_length]
        labels = [-100] * min(len(prompt_ids), len(input_ids))
        remaining = len(input_ids) - len(labels)
        labels += target_ids[:remaining]
        labels = labels[: len(input_ids)]
        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.ones(len(input_ids), dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
            "z_ir_hat": torch.tensor(ex.z_ir_hat, dtype=torch.float32),
        }


class SoftPrefixCollator:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def __call__(self, features):
        max_len = max(len(x["input_ids"]) for x in features)
        pad_id = self.tokenizer.pad_token_id
        batch = {"input_ids": [], "attention_mask": [], "labels": [], "z_ir_hat": []}
        for item in features:
            pad = max_len - len(item["input_ids"])
            batch["input_ids"].append(torch.cat([item["input_ids"], torch.full((pad,), pad_id, dtype=torch.long)]))
            batch["attention_mask"].append(torch.cat([item["attention_mask"], torch.zeros(pad, dtype=torch.long)]))
            batch["labels"].append(torch.cat([item["labels"], torch.full((pad,), -100, dtype=torch.long)]))
            batch["z_ir_hat"].append(item["z_ir_hat"])
        return {k: torch.stack(v) for k, v in batch.items()}


class SoftPrefixCausalLM(nn.Module):
    def __init__(self, lm: nn.Module, prefix_adapter: SoftPrefixAdapter):
        super().__init__()
        self.lm = lm
        self.prefix_adapter = prefix_adapter
        self.config = getattr(lm, "config", None)

    def forward(self, input_ids, attention_mask, labels, z_ir_hat):
        embed = self.lm.get_input_embeddings()
        text_embeds = embed(input_ids)
        self.prefix_adapter.to(text_embeds.device)
        prefix = self.prefix_adapter(z_ir_hat.to(text_embeds.device))
        prefix = prefix.to(device=text_embeds.device, dtype=text_embeds.dtype)
        inputs_embeds = torch.cat([prefix, text_embeds], dim=1)
        prefix_mask = torch.ones(
            attention_mask.shape[0],
            prefix.shape[1],
            dtype=attention_mask.dtype,
            device=attention_mask.device,
        )
        full_attention_mask = torch.cat([prefix_mask, attention_mask], dim=1)
        prefix_labels = torch.full(
            (labels.shape[0], prefix.shape[1]),
            -100,
            dtype=labels.dtype,
            device=labels.device,
        )
        full_labels = torch.cat([prefix_labels, labels], dim=1)
        return self.lm(inputs_embeds=inputs_embeds, attention_mask=full_attention_mask, labels=full_labels)


@torch.no_grad()
def eval_prefix_losses(model: SoftPrefixCausalLM, collator: SoftPrefixCollator, dataset: Dataset, device: torch.device, batch_size: int = 1) -> dict[str, float]:
    batch_size = min(batch_size, max(len(dataset), 1))
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, collate_fn=collator)
    out: dict[str, float] = {}
    model.eval()
    # The permutation below is WITHIN a batch, so it is the identity at batch size 1 and
    # touches only a few adjacent rows at small batch sizes. Whether it ran at all is
    # recorded, because otherwise shuffled_loss comes out exactly equal to normal_loss and
    # reads as "the decoder ignores its prefix" when it means "nothing was shuffled".
    permuted_any = False
    for mode in ["normal", "zero", "shuffled"]:
        losses: list[float] = []
        for batch in loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            if mode == "zero":
                batch["z_ir_hat"] = torch.zeros_like(batch["z_ir_hat"])
            elif mode == "shuffled" and batch["z_ir_hat"].shape[0] > 1:
                batch["z_ir_hat"] = batch["z_ir_hat"][torch.randperm(batch["z_ir_hat"].shape[0], device=device)]
                permuted_any = True
            outputs = model(**batch)
            losses.append(float(outputs.loss.item()))
        out[f"{mode}_loss"] = float(np.mean(losses)) if losses else 0.0
    # A bool, not a number, so no existing field changes value.
    out["shuffled_actually_permuted"] = permuted_any
    if not permuted_any:
        out["shuffled_loss_note"] = (
            "VACUOUS: the in-batch permutation never ran (eval batch size 1), so "
            "shuffled_loss is normal_loss by construction and says nothing about whether "
            "the prefix is read. The generation-level prefix ablation is the evidence for "
            "that."
        )
    return out


class _PrefixCheckpointCallback(TrainerCallback):
    """Saves LoRA adapter + soft_prefix.pt at every evaluation step.

    Trainer's built-in load_best_model_at_end is unstable with the custom
    SoftPrefixCausalLM wrapper because Trainer tries to reload the model
    from disk using from_pretrained, which doesn't know about the prefix
    adapter. This callback handles both components together.

    Policy:
      - Save checkpoint at every on_evaluate call (tied to --eval-steps).
      - Track the checkpoint with the lowest eval_loss as "best".
      - Prune: keep best + most recent up to save_total_limit total.
      - Call restore_best() after trainer.train() to reload best weights.
    """

    def __init__(
        self,
        wrapped: SoftPrefixCausalLM,
        tokenizer,
        output_dir: Path,
        save_total_limit: int = 2,
    ) -> None:
        self.wrapped = wrapped
        self.tokenizer = tokenizer
        self.output_dir = output_dir
        self.save_total_limit = max(save_total_limit, 1)
        self.best_loss: float = float("inf")
        self.best_ckpt_dir: Path | None = None
        self._saved: list[Path] = []

    def _save_one(self, step: int, eval_loss: float) -> Path:
        ckpt_dir = self.output_dir / f"checkpoint-{step}"
        ckpt_dir.mkdir(parents=True, exist_ok=True)
        self.wrapped.lm.save_pretrained(str(ckpt_dir))
        self.tokenizer.save_pretrained(str(ckpt_dir))
        save_soft_prefix_adapter(ckpt_dir / "soft_prefix.pt", self.wrapped.prefix_adapter)
        with open(ckpt_dir / "trainer_state.json", "w", encoding="utf-8") as f:
            json.dump({"step": step, "eval_loss": eval_loss}, f)
        return ckpt_dir

    def _prune(self) -> None:
        while len(self._saved) > self.save_total_limit:
            # Remove oldest checkpoint that is NOT the current best.
            for i, ckpt in enumerate(self._saved):
                if ckpt != self.best_ckpt_dir:
                    self._saved.pop(i)
                    shutil.rmtree(ckpt, ignore_errors=True)
                    break
            else:
                # All saved checkpoints are the best entry; remove oldest.
                shutil.rmtree(self._saved.pop(0), ignore_errors=True)

    def on_evaluate(self, hf_args, state, control, metrics=None, **kwargs):
        if not metrics:
            return
        eval_loss = metrics.get("eval_loss", float("inf"))
        step = state.global_step
        ckpt_dir = self._save_one(step, eval_loss)
        self._saved.append(ckpt_dir)
        if eval_loss < self.best_loss:
            self.best_loss = eval_loss
            self.best_ckpt_dir = ckpt_dir
            print(f"\n[PrefixCheckpoint] New best at step {step}: eval_loss={eval_loss:.4f}")
        self._prune()

    def restore_best(self) -> None:
        """Reload best LoRA + soft_prefix weights into the wrapped model.

        Must be called after trainer.train(). Restores both components
        atomically so the final save always contains the best-checkpoint weights.
        """
        if self.best_ckpt_dir is None or not self.best_ckpt_dir.exists():
            print("[PrefixCheckpoint] No periodic checkpoint found; keeping last-step weights.")
            return
        device = next(self.wrapped.parameters()).device

        # Restore LoRA adapter weights (PEFT saves as safetensors or bin).
        sf_path = self.best_ckpt_dir / "adapter_model.safetensors"
        bin_path = self.best_ckpt_dir / "adapter_model.bin"
        if sf_path.exists():
            from safetensors.torch import load_file
            lora_state = load_file(str(sf_path), device=str(device))
        elif bin_path.exists():
            lora_state = torch.load(str(bin_path), map_location=device, weights_only=True)
        else:
            print(f"[PrefixCheckpoint] WARNING: no adapter weights in {self.best_ckpt_dir}; skipping.")
            return
        self.wrapped.lm.load_state_dict(lora_state, strict=False)

        # Restore soft prefix weights.
        sp_path = self.best_ckpt_dir / "soft_prefix.pt"
        if sp_path.exists():
            best_prefix = load_soft_prefix_adapter(sp_path, device=device)
            self.wrapped.prefix_adapter.load_state_dict(best_prefix.state_dict())

        print(
            f"[PrefixCheckpoint] Restored best checkpoint from {self.best_ckpt_dir} "
            f"(eval_loss={self.best_loss:.4f})"
        )


def main() -> int:
    args = parse_args()
    torch.manual_seed(args.seed)
    if torch.cuda.is_available() and not args.no_tf32:
        torch.backends.cuda.matmul.allow_tf32 = True

    if bool(args.modality_prior) == bool(args.modality):
        raise SystemExit(
            "Exactly one of --modality (single-modality, original recipe) or --modality-prior "
            "(Stage 3b multi-modality mix, repeatable) must be given, not both/neither."
        )
    if args.modality and args.prior_checkpoint is None:
        raise SystemExit("--modality requires --prior-checkpoint.")

    if args.modality_prior:
        modality_priors: dict[str, Path] = {}
        for kv in args.modality_prior:
            m, _, p = kv.partition(":")
            if m not in ("text", "image", "point", "step") or not p:
                raise SystemExit(f"--modality-prior expects MODALITY:PATH, got {kv!r}")
            modality_priors[m] = Path(p)
    else:
        modality_priors = {args.modality: args.prior_checkpoint}
    modality_list = sorted(modality_priors)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    aligner, _, _, _ = load_alignment_checkpoint(args.alignment_checkpoint, map_location="cpu")
    aligner.to(device).eval()
    priors = {m: load_prior(p, device) for m, p in modality_priors.items()}

    train_rows = read_jsonl(args.train_jsonl)
    val_rows = read_jsonl(args.val_jsonl)
    if args.limit_train:
        train_rows = train_rows[: args.limit_train]
    if args.limit_val:
        val_rows = val_rows[: args.limit_val]

    retrieval_index = None
    if args.use_retrieval and args.retrieval_index:
        retrieval_index = np.load(args.retrieval_index, allow_pickle=True)

    train_examples = []
    val_examples = []
    for m, prior in priors.items():
        train_examples += build_examples(train_rows, m, aligner, prior, args, device, retrieval_index, f"train-examples-{m}", point_sampling=args.train_point_sampling)
        val_examples += build_examples(val_rows, m, aligner, prior, args, device, retrieval_index, f"val-examples-{m}", point_sampling=args.eval_point_sampling)
    print(f"Built {len(train_examples)} train / {len(val_examples)} val examples across modalities: {modality_list}")

    del aligner, priors
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    tokenizer = AutoTokenizer.from_pretrained(args.model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model_kwargs: dict[str, Any] = {"trust_remote_code": True}
    if args.bf16:
        model_kwargs["torch_dtype"] = torch.bfloat16
    elif args.fp16:
        model_kwargs["torch_dtype"] = torch.float16
    if args.load_in_4bit:
        model_kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16 if args.bf16 else torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
        )
        model_kwargs["device_map"] = "auto"

    base = AutoModelForCausalLM.from_pretrained(args.model_name, **model_kwargs)
    if args.load_in_4bit:
        base = prepare_model_for_kbit_training(base)

    if args.init_lora_ir_dir is not None:
        lm = PeftModel.from_pretrained(base, str(args.init_lora_ir_dir), is_trainable=True)
        prefix_adapter = load_soft_prefix_adapter(
            resolve_soft_prefix_path(args.init_lora_ir_dir, None), device=device, dtype=None
        ).train()
        print(f"Continuing Stage 3b training from {args.init_lora_ir_dir} (LoRA-IR adapter + soft_prefix.pt).")
    else:
        lora_config = LoraConfig(
            r=args.lora_r,
            lora_alpha=args.lora_alpha,
            lora_dropout=args.lora_dropout,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        )
        lm = get_peft_model(base, lora_config)
        hidden_size = int(getattr(lm.config, "hidden_size", 1536))
        prefix_config = SoftPrefixConfig(
            latent_dim=512,
            hidden_size=hidden_size,
            prefix_len=args.prefix_len,
            dropout=args.prefix_dropout,
        )
        prefix_adapter = SoftPrefixAdapter(prefix_config)
    lm.print_trainable_parameters()
    wrapped = SoftPrefixCausalLM(lm, prefix_adapter)

    train_ds = SoftPrefixIRDataset(train_examples, tokenizer, args.max_length)
    val_ds = SoftPrefixIRDataset(val_examples, tokenizer, args.max_length)
    collator = SoftPrefixCollator(tokenizer)

    ckpt_callback = _PrefixCheckpointCallback(
        wrapped=wrapped,
        tokenizer=tokenizer,
        output_dir=args.output_dir,
        save_total_limit=args.save_total_limit,
    )

    training_args = TrainingArguments(
        output_dir=str(args.output_dir),
        num_train_epochs=args.epochs,
        learning_rate=args.learning_rate,
        warmup_ratio=args.warmup_ratio,
        weight_decay=args.weight_decay,
        per_device_train_batch_size=args.per_device_train_batch_size,
        per_device_eval_batch_size=args.per_device_eval_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        eval_strategy="steps",
        eval_steps=args.eval_steps,
        save_strategy="no",        # _PrefixCheckpointCallback handles all saves
        logging_steps=args.logging_steps,
        bf16=args.bf16,
        fp16=args.fp16,
        report_to=[],
        remove_unused_columns=False,
    )
    trainer_kwargs = dict(
        model=wrapped,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        data_collator=collator,
        callbacks=[ckpt_callback],
    )
    try:
        trainer = Trainer(**trainer_kwargs, processing_class=tokenizer)
    except TypeError:
        try:
            trainer = Trainer(**trainer_kwargs, tokenizer=tokenizer)
        except TypeError:
            trainer = Trainer(**trainer_kwargs)

    trainer.train()

    # Reload best-checkpoint weights before the final save.
    # This ensures args.output_dir always contains the lowest-eval-loss weights,
    # not the last-step weights (which may be worse due to overfitting).
    ckpt_callback.restore_best()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    wrapped.lm.save_pretrained(str(args.output_dir))
    tokenizer.save_pretrained(str(args.output_dir))
    save_soft_prefix_adapter(args.output_dir / "soft_prefix.pt", wrapped.prefix_adapter)

    eval_report = eval_prefix_losses(wrapped, collator, val_ds, device)
    report = {
        "model_name": args.model_name,
        "modalities": modality_list,
        "init_lora_ir_dir": str(args.init_lora_ir_dir) if args.init_lora_ir_dir else None,
        "train_rows": len(train_examples),
        "val_rows": len(val_examples),
        "prefix_len": args.prefix_len,
        "max_length": args.max_length,
        "soft_prefix_eval": eval_report,
        "output_dir": str(args.output_dir),
    }
    with open(args.output_dir / "soft_prefix_training_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Saved LoRA-IR + soft prefix to {args.output_dir}")
    print(f"Soft-prefix eval: {eval_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
