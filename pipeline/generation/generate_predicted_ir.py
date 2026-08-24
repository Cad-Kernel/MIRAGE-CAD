"""Stage 4b: generate predicted_ir for train split using trained LoRA-IR adapter.

WARNING: This script must ONLY be run on the TRAIN split.
Running on val/test would cause data leakage into the Stage 4b mixed dataset.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from peft import PeftModel
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer

from miragecad.data import (
    load_image,
    load_step_brep_tensors,
    read_jsonl,
    read_text,
)
from miragecad.gen_prompts import build_ir_prompt, get_geometry_summary
from miragecad.soft_prefix import load_soft_prefix_adapter, resolve_soft_prefix_path
from miragecad.latent_prior import LatentPrior, LatentPriorConfig
from miragecad.models import load_alignment_checkpoint
from miragecad.point_sampling import load_point_cloud_sampled


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate predicted_ir for train split (Stage 4b).")
    p.add_argument("--model-name", default="Qwen/Qwen2.5-Coder-1.5B")
    p.add_argument("--lora-ir-dir", type=Path, required=True, help="Trained LoRA-IR adapter directory.")
    p.add_argument("--alignment-checkpoint", type=Path, required=True)
    p.add_argument("--prior-checkpoint", type=Path, required=True)
    p.add_argument("--soft-prefix-checkpoint", type=Path, default=None)
    p.add_argument("--retrieval-index", type=Path, default=None)
    p.add_argument("--modality", choices=["text", "image", "point", "step"], default="step")
    p.add_argument("--input-jsonl", type=Path, required=True, help="TRAIN SPLIT ONLY.")
    p.add_argument("--output-jsonl", type=Path, required=True)
    p.add_argument("--retrieval-top-k", type=int, default=3)
    p.add_argument("--use-retrieval", action="store_true", help="Retrieve IR examples for prompt context.")
    p.add_argument("--max-new-tokens", type=int, default=512)
    p.add_argument("--max-length", type=int, default=2048)
    p.add_argument("--bf16", action="store_true")
    p.add_argument("--point-count", type=int, default=1024)
    p.add_argument("--eval-point-sampling", choices=["random", "fps", "hybrid"], default="fps")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def load_prior(path: Path, device: torch.device) -> LatentPrior:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    cfg = payload["config"]
    if "modality" not in cfg:
        raise ValueError(f"Prior checkpoint {path} missing 'modality' in config.")
    config = LatentPriorConfig(**cfg)
    prior = LatentPrior(config)
    prior.load_state_dict(payload["state_dict"], strict=True)
    return prior.to(device).eval()


@torch.no_grad()
def encode_query(row: dict, modality: str, aligner, prior: LatentPrior, args: argparse.Namespace, device: torch.device) -> tuple[np.ndarray, np.ndarray]:
    if modality == "text":
        z_m = aligner.encode_text([row.get("text", "")], device)
    elif modality == "image":
        img = load_image(row["iso_image_path"])
        z_m = aligner.encode_image([img], device)
    elif modality == "step":
        tensors = load_step_brep_tensors(row["step_feature_path"])
        batch = {k: torch.tensor(v[None], dtype=torch.float32).to(device) for k, v in tensors.items()}
        z_m = aligner.encode_step(batch)
    elif modality == "point":
        pts = load_point_cloud_sampled(
            row["point_path"],
            point_count=args.point_count,
            sampling=args.eval_point_sampling,
            seed=args.seed,
        )
        z_m = aligner.encode_point(torch.tensor(pts[None], dtype=torch.float32).to(device))
    else:
        raise ValueError(modality)
    z_ir_hat = prior(z_m)
    return z_m.cpu().numpy()[0], z_ir_hat.cpu().numpy()[0]


def retrieve_ir_examples(index, z_ir_hat: np.ndarray, top_k: int, row: dict) -> list[dict]:
    embeddings = index["embeddings"]
    scores = embeddings @ z_ir_hat
    order = np.argsort(-scores)[:top_k]
    dataset_root = Path(row.get("dataset_root", "."))
    out: list[dict] = []
    for i in order:
        relpath = str(index["relpaths"][i])
        sample_dir = dataset_root / relpath
        out.append({
            "sample_id": str(index["sample_ids"][i]),
            "ir": read_text(sample_dir / "training_ir.txt"),
        })
    return out


def load_point_xyz(row: dict, args: argparse.Namespace) -> np.ndarray | None:
    if args.modality != "point":
        return None
    try:
        pts = load_point_cloud_sampled(
            row["point_path"],
            point_count=args.point_count,
            sampling=args.eval_point_sampling,
            seed=args.seed,
        )
        return pts
    except Exception:
        return None


def main() -> int:
    args = parse_args()
    torch.manual_seed(args.seed)

    rows = read_jsonl(args.input_jsonl)
    # Hard fail if any row is from val/test — running on those splits causes Stage 4b data leakage.
    non_train = [r for r in rows if r.get("split", "train") not in ("train", "")]
    if non_train:
        raise RuntimeError(
            f"generate_predicted_ir must only run on the TRAIN split. "
            f"Found {len(non_train)} row(s) with split != 'train' in {args.input_jsonl}. "
            "Running on val/test would cause data leakage into Stage 4b."
        )

    if args.limit:
        rows = rows[: args.limit]

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    aligner, _, _, _ = load_alignment_checkpoint(args.alignment_checkpoint, map_location="cpu")
    aligner.to(device).eval()
    prior = load_prior(args.prior_checkpoint, device)

    index = None
    if args.use_retrieval and args.retrieval_index:
        index = np.load(args.retrieval_index, allow_pickle=True)

    dtype = torch.bfloat16 if args.bf16 else None
    model_kwargs: dict = {"trust_remote_code": True}
    if dtype is not None:
        model_kwargs["torch_dtype"] = dtype
    base = AutoModelForCausalLM.from_pretrained(args.model_name, **model_kwargs)
    lora_model = PeftModel.from_pretrained(base, args.lora_ir_dir)
    lora_model.to(device).eval()
    prefix_path = resolve_soft_prefix_path(args.lora_ir_dir, args.soft_prefix_checkpoint)
    prefix_adapter = load_soft_prefix_adapter(prefix_path, device=device, dtype=dtype)
    tokenizer = AutoTokenizer.from_pretrained(args.lora_ir_dir, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)

    with open(args.output_jsonl, "w", encoding="utf-8", newline="\n") as f_out:
        for row in tqdm(rows, desc="generate-predicted-ir"):
            z_direct, z_ir_hat = encode_query(row, args.modality, aligner, prior, args, device)

            retrieved_ir: list[dict] = []
            if index is not None and args.use_retrieval:
                retrieved_ir = retrieve_ir_examples(index, z_ir_hat, args.retrieval_top_k, row)

            point_xyz = load_point_xyz(row, args)
            prompt = build_ir_prompt(
                row,
                args.modality,
                retrieved_ir=retrieved_ir if retrieved_ir else None,
                point_xyz=point_xyz,
            )

            inputs = tokenizer(prompt, truncation=True, max_length=args.max_length, return_tensors="pt").to(device)
            text_embeds = lora_model.get_input_embeddings()(inputs["input_ids"])
            z_tensor = torch.tensor(z_ir_hat[None], dtype=torch.float32, device=device)
            soft_prefix = prefix_adapter(z_tensor).to(device=text_embeds.device, dtype=text_embeds.dtype)
            inputs_embeds = torch.cat([soft_prefix, text_embeds], dim=1)
            prefix_mask = torch.ones(
                inputs["attention_mask"].shape[0],
                soft_prefix.shape[1],
                dtype=inputs["attention_mask"].dtype,
                device=device,
            )
            attention_mask = torch.cat([prefix_mask, inputs["attention_mask"]], dim=1)
            with torch.no_grad():
                gen = lora_model.generate(
                    inputs_embeds=inputs_embeds,
                    attention_mask=attention_mask,
                    max_new_tokens=args.max_new_tokens,
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id,
                )
            predicted_ir = tokenizer.decode(gen[0], skip_special_tokens=True).strip()

            out = {
                "sample_id": row.get("sample_id", ""),
                "predicted_ir": predicted_ir,
                "reference_ir": read_text(row.get("ir_path", "")),
                "relpath": row.get("relpath", ""),
            }
            f_out.write(json.dumps(out, ensure_ascii=False) + "\n")

    print(f"Wrote predicted IR: {args.output_jsonl}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
