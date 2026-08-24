"""Generate N candidate programs per sample (predicted_ir input, Stage 4b
checkpoint), matching run_miragecad.py's "full" pipeline candidate policy:
candidate 0 is always greedy, the rest are sampled at temperature=0.8.
"""
import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, ".")
from miragecad.data import read_jsonl, read_text
from miragecad.gen_prompts import build_program_prompt
from gen_scripts.run_miragecad import load_lm, load_tokenizer, generate_text

N_CANDIDATES = 3
N_SAMPLES = int(sys.argv[1]) if len(sys.argv) > 1 else 10
OUT_NAME = sys.argv[2] if len(sys.argv) > 2 else f"gen_ncand_predicted_ir_{N_SAMPLES}.jsonl"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
lora_code = load_lm("Qwen/Qwen2.5-Coder-1.5B", Path("outputs/qwen25_coder_1_5b_program_5k_stage4b"), torch.bfloat16, device)
lora_code_tok = load_tokenizer(Path("outputs/qwen25_coder_1_5b_program_5k_stage4b"))

test_rows = read_jsonl(Path("data/smoke5k/test.jsonl"))[:100]
stage3_rows = {r["sample_id"]: r for r in read_jsonl(Path("outputs/lora_ir_5k/gen_test100_mnt1536.jsonl"))}

out_path = Path("outputs/qwen25_coder_1_5b_program_5k_stage4b") / OUT_NAME
with open(out_path, "w", encoding="utf-8", newline="\n") as f:
    for i, row in enumerate(test_rows[:N_SAMPLES]):
        s3 = stage3_rows[row["sample_id"]]
        predicted_ir = s3["predicted_ir"]
        prompt = build_program_prompt(row, "step", predicted_ir)
        candidates = [generate_text(lora_code, lora_code_tok, prompt, 1536, 1536, 0.0, 1.0, device)]
        for _ in range(N_CANDIDATES - 1):
            candidates.append(generate_text(lora_code, lora_code_tok, prompt, 1536, 1536, 0.8, 0.95, device))
        f.write(json.dumps({
            "sample_id": row["sample_id"],
            "predicted_ir": predicted_ir,
            "all_candidates": candidates,
            "reference": read_text(row.get("program_path", "")),
        }, ensure_ascii=False) + "\n")
        print(f"{i+1}/{N_SAMPLES} done", flush=True)
print("Wrote", out_path)
