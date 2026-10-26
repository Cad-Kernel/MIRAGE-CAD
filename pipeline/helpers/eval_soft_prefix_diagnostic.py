"""Standalone re-run of train_soft_prefix_ir.py's post-training soft-prefix
diagnostic (normal vs. zero vs. shuffled prefix loss), against an ALREADY
SAVED checkpoint -- no retraining. Written after the 25K Stage 3 run's own
in-process call to this diagnostic OOM'd (batch_size=8 bug, since fixed in
train_soft_prefix_ir.py) right after the real checkpoint had already been
saved successfully. Loads the saved adapter + soft_prefix.pt instead of
training from scratch, and evaluates at batch_size=1 (matching what the
actual training run used throughout, and what the now-fixed default is).
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

sys.path.insert(0, ".")
from miragecad.data import read_jsonl
from miragecad.models import load_alignment_checkpoint
from miragecad.soft_prefix import load_soft_prefix_adapter
from gen_scripts.train_soft_prefix_ir import (
    build_examples,
    load_prior,
    SoftPrefixIRDataset,
    SoftPrefixCollator,
    SoftPrefixCausalLM,
    eval_prefix_losses,
)


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model-name", default="Qwen/Qwen2.5-Coder-1.5B")
    p.add_argument("--lora-ir-dir", type=Path, required=True)
    p.add_argument("--alignment-checkpoint", type=Path, required=True)
    p.add_argument("--prior-checkpoint", type=Path, required=True)
    p.add_argument("--modality", choices=["text", "image", "point", "step"], default="step")
    p.add_argument("--val-jsonl", type=Path, required=True)
    p.add_argument("--limit-val", type=int, default=200,
                    help="Subset size for a quick read; pass the full val split size for the rigorous number.")
    p.add_argument("--max-length", type=int, default=1536)
    p.add_argument("--point-count", type=int, default=1024)
    p.add_argument("--eval-point-sampling", choices=["random", "fps", "hybrid"], default="fps")
    p.add_argument("--eval-batch-size", type=int, default=1)
    p.add_argument("--output-json", type=Path, default=None)
    p.add_argument("--bf16", action="store_true")
    p.add_argument("--load-in-4bit", action="store_true")
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def main():
    args = parse_args()
    torch.manual_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    aligner, _, _, _ = load_alignment_checkpoint(args.alignment_checkpoint, map_location="cpu")
    aligner.to(device).eval()
    prior = load_prior(args.prior_checkpoint, device)

    val_rows = read_jsonl(args.val_jsonl)[: args.limit_val]
    val_examples = build_examples(
        val_rows, args.modality, aligner, prior, args, device,
        retrieval_index=None, desc="val-examples", point_sampling=args.eval_point_sampling,
    )
    del aligner, prior
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    tokenizer = AutoTokenizer.from_pretrained(args.lora_ir_dir, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model_kwargs = {"trust_remote_code": True}
    if args.bf16:
        model_kwargs["torch_dtype"] = torch.bfloat16
    if args.load_in_4bit:
        model_kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16 if args.bf16 else torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
        )
        model_kwargs["device_map"] = "auto"

    base = AutoModelForCausalLM.from_pretrained(args.model_name, **model_kwargs)
    lm = PeftModel.from_pretrained(base, args.lora_ir_dir)
    if not args.load_in_4bit:
        lm = lm.to(device)
    lm.eval()

    prefix_adapter = load_soft_prefix_adapter(args.lora_ir_dir / "soft_prefix.pt", device=device)
    wrapped = SoftPrefixCausalLM(lm, prefix_adapter)

    val_ds = SoftPrefixIRDataset(val_examples, tokenizer, args.max_length)
    collator = SoftPrefixCollator(tokenizer)

    report = eval_prefix_losses(wrapped, collator, val_ds, device, batch_size=args.eval_batch_size)
    report["n_val_examples"] = len(val_examples)
    print(json.dumps(report, indent=2))

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print("Wrote", args.output_json)


if __name__ == "__main__":
    main()
