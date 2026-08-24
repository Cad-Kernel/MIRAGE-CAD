"""Stage 4b: generate program.py for 100 point-cloud test samples from
(P1a-repaired) predicted_ir. Mirrors scratch/gen_code_from_predicted_ir.py's
pattern, parameterized for point modality + the 100-sample quick-eval run.
"""
import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, ".")
from miragecad.data import read_jsonl, read_text
from miragecad.point_sampling import load_point_cloud_sampled
from miragecad.gen_prompts import build_program_prompt
from gen_scripts.run_miragecad import load_lm, load_tokenizer, generate_text

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
lora_code = load_lm("Qwen/Qwen2.5-Coder-1.5B", Path("outputs/qwen25_coder_1_5b_program_5k_stage4b"), torch.bfloat16, device)
lora_code_tok = load_tokenizer(Path("outputs/qwen25_coder_1_5b_program_5k_stage4b"))

ir_rows = read_jsonl(Path("outputs/lora_ir_5k/predicted_ir_point100_p1a.jsonl"))
test_rows = {r["sample_id"]: r for r in read_jsonl(Path("data/smoke5k/test.jsonl"))[:100]}

out_path = Path("outputs/qwen25_coder_1_5b_program_5k_stage4b/gen_point100_from_predicted_ir.jsonl")
with open(out_path, "w", encoding="utf-8", newline="\n") as f:
    for i, ir_row in enumerate(ir_rows):
        sid = ir_row["sample_id"]
        row = test_rows.get(sid)
        if row is None:
            continue
        predicted_ir = ir_row["predicted_ir"]
        point_xyz = load_point_cloud_sampled(row["point_path"], point_count=1024, sampling="fps", seed=42)
        prompt = build_program_prompt(row, "point", predicted_ir, point_xyz=point_xyz)
        prediction = generate_text(lora_code, lora_code_tok, prompt, 1536, 1536, 0.0, 1.0, device)
        out = {
            "sample_id": sid,
            "modality": "point",
            "predicted_ir": predicted_ir,
            "reference_ir": ir_row.get("reference_ir", ""),
            "prediction": prediction,
            "reference": read_text(row.get("program_path", "")),
        }
        f.write(json.dumps(out, ensure_ascii=False) + "\n")
        if (i + 1) % 10 == 0:
            print(f"{i+1}/{len(ir_rows)} done", flush=True)
print("Wrote", out_path)
