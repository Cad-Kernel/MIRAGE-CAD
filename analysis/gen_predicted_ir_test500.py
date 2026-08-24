"""Generate predicted_ir for a slice of the TEST split (Stage 3 pass1 only,
no LoRA-Code) — used to extend the 100-sample held-out result to 500 samples
for stability verification.
"""
import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, ".")
from miragecad.data import read_jsonl, read_text
from miragecad.gen_prompts import build_ir_prompt
from miragecad.models import load_alignment_checkpoint
from miragecad.soft_prefix import load_soft_prefix_adapter, resolve_soft_prefix_path
from gen_scripts.run_miragecad import encode_query, generate_text_with_soft_prefix, load_lm, load_prior, load_tokenizer

START = int(sys.argv[1]) if len(sys.argv) > 1 else 100
END = int(sys.argv[2]) if len(sys.argv) > 2 else 500
OUT_NAME = sys.argv[3] if len(sys.argv) > 3 else f"predicted_ir_test_{START}_{END}.jsonl"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
dtype = torch.bfloat16

aligner, _, _, _ = load_alignment_checkpoint(Path("outputs/align_smoke5k_ep10/best.pt"), map_location="cpu")
aligner.to(device).eval()
prior = load_prior(Path("outputs/prior_step_5k/best.pt"), device)

lora_ir = load_lm("Qwen/Qwen2.5-Coder-1.5B", Path("outputs/lora_ir_5k"), dtype, device)
lora_ir_tok = load_tokenizer(Path("outputs/lora_ir_5k"))
prefix_path = resolve_soft_prefix_path(Path("outputs/lora_ir_5k"))
prefix_adapter = load_soft_prefix_adapter(prefix_path, device=device, dtype=dtype)


class Args:
    modality = "step"
    point_count = 1024
    eval_point_sampling = "fps"
    seed = 42
    max_length = 1536


args = Args()
rows = read_jsonl(Path("data/smoke5k/test.jsonl"))[START:END]
out_path = Path("outputs/lora_ir_5k") / OUT_NAME
with open(out_path, "w", encoding="utf-8", newline="\n") as f:
    for i, row in enumerate(rows):
        z_m, z_ir_hat = encode_query(row, "step", aligner, prior, args, device)
        ir_prompt = build_ir_prompt(row, "step", retrieved_ir=None, point_xyz=None)
        predicted_ir = generate_text_with_soft_prefix(
            lora_ir, lora_ir_tok, prefix_adapter, z_ir_hat, ir_prompt, args.max_length, 1536, device
        )
        f.write(json.dumps({
            "sample_id": row["sample_id"],
            "predicted_ir": predicted_ir,
            "reference_ir": read_text(row["ir_path"]),
        }, ensure_ascii=False) + "\n")
        if (i + 1) % 20 == 0:
            print(f"{i+1}/{len(rows)} done", flush=True)
print("Wrote", out_path)
