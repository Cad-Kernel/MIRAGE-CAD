"""MIRAGE-CAD Phase 2a â€” LoRA fine-tuning of the Flluma program generator.

Fine-tunes Qwen2.5-Coder-1.5B-Instruct with LoRA adapters (r=16, Î±=32) on
construction IR â†’ Flluma Python program pairs.  Loss is masked over prompt tokens
so only the target program tokens contribute to the gradient.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
from torch.utils.data import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, Trainer, TrainingArguments

from miragecad.data import load_program_example, read_jsonl, read_text
from miragecad.gen_prompts import build_program_prompt


class ProgramDataset(Dataset):
    def __init__(self, rows, tokenizer, target: str, max_length: int, modality: str | None = None,
                 include_plan: bool = True):
        self.rows = rows
        self.tokenizer = tokenizer
        self.target = target
        self.max_length = max_length
        self.modality = modality
        self.include_plan = include_plan

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx):
        row = self.rows[idx]
        if self.target == "program":
            # Match the inference-time prompt used by run_miragecad.py's gen_ir /
            # gen_ir_retrieval / full pipelines (build_program_prompt with a
            # "Construction IR plan" block), so LoRA-Code isn't trained on a
            # different prompt shape than it sees at generation time.
            #
            # `ir_text_for_program`, when present, overrides the ground-truth
            # IR with a precomputed string (e.g. a Stage 3 predicted_ir) —
            # used for Stage 4b robustness mixed fine-tuning, where a subset
            # of rows condition on predicted_ir instead of ground truth while
            # still targeting the same reference program.
            ir_text = row.get("ir_text_for_program") or read_text(row["ir_path"])
            prompt = build_program_prompt(row, self.modality, ir_text,
                                          include_plan=self.include_plan)
            target_text = read_text(row["program_path"]).strip()
        else:
            ex = load_program_example(row, target=self.target)
            prompt = ex.prompt
            target_text = ex.target
        target = target_text + self.tokenizer.eos_token
        prompt_ids = self.tokenizer(prompt, add_special_tokens=True)["input_ids"]
        target_ids = self.tokenizer(target, add_special_tokens=False)["input_ids"]
        input_ids = (prompt_ids + target_ids)[: self.max_length]
        labels = [-100] * min(len(prompt_ids), len(input_ids))
        remaining = len(input_ids) - len(labels)
        labels += target_ids[:remaining]
        labels = labels[: len(input_ids)]
        attention_mask = [1] * len(input_ids)
        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
        }


class DataCollator:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def __call__(self, features):
        max_len = max(len(x["input_ids"]) for x in features)
        pad_id = self.tokenizer.pad_token_id
        batch = {"input_ids": [], "attention_mask": [], "labels": []}
        for item in features:
            n = len(item["input_ids"])
            pad = max_len - n
            batch["input_ids"].append(torch.cat([item["input_ids"], torch.full((pad,), pad_id, dtype=torch.long)]))
            batch["attention_mask"].append(torch.cat([item["attention_mask"], torch.zeros(pad, dtype=torch.long)]))
            batch["labels"].append(torch.cat([item["labels"], torch.full((pad,), -100, dtype=torch.long)]))
        return {k: torch.stack(v) for k, v in batch.items()}


def parse_args():
    p = argparse.ArgumentParser(description="Train a LoRA text/prompt-to-Flluma-program baseline.")
    p.add_argument("--model-name", default="Qwen/Qwen2.5-Coder-1.5B")
    p.add_argument("--train-jsonl", type=Path, required=True)
    p.add_argument("--val-jsonl", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--target", choices=["program", "ir"], default="program")
    p.add_argument("--modality", choices=["text", "image", "point", "step"], default="step",
                   help="Query modality used to build the evidence block in the IR-conditioned program prompt.")
    # --- no-plan ablation ---------------------------------------------------
    # Trains the code model with the construction plan removed from the prompt,
    # so it must work from the observation block alone. This is the fair form of
    # the question "why insert a plan at all?" -- feeding an empty plan to a
    # checkpoint trained WITH plans tests only that the model expects one.
    # Note it removes the plan and, transitively, the query encoder: the pathway
    # as a whole, not the plan text in isolation.
    # Default True reproduces every published checkpoint byte-for-byte.
    p.add_argument("--no-plan", action="store_true",
                   help="omit the Construction IR plan block from the prompt")
    p.add_argument("--max-length", type=int, default=2048)
    p.add_argument("--epochs", type=float, default=1)
    # Default 42 is TrainingArguments' own default, so leaving this alone reproduces every run
    # made before the flag existed, bit for bit. It exists because the exposure-matched arm's
    # coverage margin over the direct-latent arm is 4.2 pp at p = 0.03 on ONE run, and a single
    # seed cannot tell that apart from run-to-run variation. The soft-prefix trainer already
    # had --seed; this one did not, so the two arms could not be seeded as a pair.
    p.add_argument("--seed", type=int, default=42)
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
    p.add_argument("--lora-r", type=int, default=16)
    p.add_argument("--lora-alpha", type=int, default=32)
    p.add_argument("--lora-dropout", type=float, default=0.05)
    p.add_argument("--load-in-4bit", action="store_true")
    p.add_argument("--bf16", action="store_true")
    p.add_argument("--fp16", action="store_true")
    p.add_argument("--no-tf32", action="store_true")
    p.add_argument("--init-adapter-dir", type=Path, default=None,
                   help="Continue training from an existing LoRA adapter checkpoint instead of a fresh one "
                        "(e.g. Stage 4b robustness fine-tuning on top of a Stage 4 GT-IR checkpoint).")
    p.add_argument("--resume-from-checkpoint", type=Path, default=None,
                   help="Resume an interrupted run (model/optimizer/scheduler/rng/step count) from a "
                        "Trainer checkpoint-N directory, e.g. after a crash. Distinct from --init-adapter-dir: "
                        "that starts a new run's step count from an adapter's weights; this continues the same run.")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if torch.cuda.is_available() and not args.no_tf32:
        torch.backends.cuda.matmul.allow_tf32 = True

    tokenizer = AutoTokenizer.from_pretrained(args.model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model_kwargs = {"trust_remote_code": True}
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

    model = AutoModelForCausalLM.from_pretrained(args.model_name, **model_kwargs)
    if args.load_in_4bit:
        model = prepare_model_for_kbit_training(model)

    if args.init_adapter_dir is not None:
        model = PeftModel.from_pretrained(model, str(args.init_adapter_dir), is_trainable=True)
    else:
        # Apply LoRA to all attention and FFN projection matrices as described in Section 4.3.
        lora_config = LoraConfig(
            r=args.lora_r,
            lora_alpha=args.lora_alpha,
            lora_dropout=args.lora_dropout,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        )
        model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    train_rows = read_jsonl(args.train_jsonl)
    val_rows = read_jsonl(args.val_jsonl)
    if args.no_plan:
        print("[NO-PLAN] training with the Construction IR plan removed from the prompt. "
              "This checkpoint is an ablation baseline and must not be used as a system "
              "result.")
    train_ds = ProgramDataset(train_rows, tokenizer, args.target, args.max_length,
                              modality=args.modality, include_plan=not args.no_plan)
    val_ds = ProgramDataset(val_rows, tokenizer, args.target, args.max_length,
                            modality=args.modality, include_plan=not args.no_plan)
    collator = DataCollator(tokenizer)

    torch.manual_seed(args.seed)
    training_args = TrainingArguments(
        output_dir=str(args.output_dir),
        seed=args.seed,
        data_seed=args.seed,
        num_train_epochs=args.epochs,
        learning_rate=args.learning_rate,
        warmup_ratio=args.warmup_ratio,
        weight_decay=args.weight_decay,
        per_device_train_batch_size=args.per_device_train_batch_size,
        per_device_eval_batch_size=args.per_device_eval_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        eval_strategy="steps",
        eval_steps=args.eval_steps,
        save_steps=args.save_steps,
        logging_steps=args.logging_steps,
        save_total_limit=args.save_total_limit,
        bf16=args.bf16,
        fp16=args.fp16,
        report_to=[],
        remove_unused_columns=False,
    )

    trainer_kwargs = dict(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        data_collator=collator,
    )
    try:
        trainer = Trainer(**trainer_kwargs, processing_class=tokenizer)
    except TypeError:
        try:
            trainer = Trainer(**trainer_kwargs, tokenizer=tokenizer)
        except TypeError:
            trainer = Trainer(**trainer_kwargs)

    trainer.train(resume_from_checkpoint=str(args.resume_from_checkpoint) if args.resume_from_checkpoint else None)
    trainer.save_model(str(args.output_dir))
    tokenizer.save_pretrained(str(args.output_dir))

    report = {
        "model_name": args.model_name,
        "target": args.target,
        "seed": args.seed,
        "train_rows": len(train_rows),
        "val_rows": len(val_rows),
        "max_length": args.max_length,
        "output_dir": str(args.output_dir),
    }
    with open(args.output_dir / "training_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Training report: {args.output_dir / 'training_report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


