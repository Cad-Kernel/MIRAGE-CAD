"""Stage 4b: generate program.py for 500 test samples from (P1a-repaired)
predicted_ir, any modality. 500-sample formal-eval version of
gen_code_{point,text,image}100_from_predicted_ir.py. Fixed config: same
Stage4b checkpoint, N=1 greedy, max_new_tokens=1536.
"""
import argparse
import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, ".")
from miragecad.data import read_jsonl, read_text
from miragecad.gen_prompts import build_program_prompt
from miragecad.point_sampling import load_point_cloud_sampled
from gen_scripts.run_miragecad import load_lm, load_tokenizer, generate_text


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--modality", choices=["text", "image", "point"], required=True)
    p.add_argument("--ir-jsonl", type=Path, required=True, help="P1a-repaired predicted_ir jsonl")
    p.add_argument("--output-jsonl", type=Path, required=True)
    p.add_argument("--limit", type=int, default=500)
    p.add_argument("--lora-code-dir", type=Path, default=Path("outputs/qwen25_coder_1_5b_program_5k_stage4b"))
    p.add_argument("--input-jsonl", type=Path, default=Path("data/smoke5k/test.jsonl"))
    p.add_argument("--point-count", type=int, default=1024)
    p.add_argument("--max-length", type=int, default=1536)
    p.add_argument("--max-new-tokens", type=int, default=1536)
    return p.parse_args()


def main():
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    lora_code = load_lm("Qwen/Qwen2.5-Coder-1.5B", args.lora_code_dir, torch.bfloat16, device)
    lora_code_tok = load_tokenizer(args.lora_code_dir)

    ir_rows = read_jsonl(args.ir_jsonl)
    test_rows = {r["sample_id"]: r for r in read_jsonl(args.input_jsonl)[: args.limit]}

    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_jsonl, "w", encoding="utf-8", newline="\n") as f:
        for i, ir_row in enumerate(ir_rows):
            sid = ir_row["sample_id"]
            row = test_rows.get(sid)
            if row is None:
                continue
            predicted_ir = ir_row["predicted_ir"]
            point_xyz = None
            if args.modality == "point":
                point_xyz = load_point_cloud_sampled(row["point_path"], point_count=args.point_count, sampling="fps", seed=42)
            prompt = build_program_prompt(row, args.modality, predicted_ir, point_xyz=point_xyz)
            prediction = generate_text(lora_code, lora_code_tok, prompt, args.max_length, args.max_new_tokens, 0.0, 1.0, device)
            out = {
                "sample_id": sid,
                "modality": args.modality,
                "predicted_ir": predicted_ir,
                "reference_ir": ir_row.get("reference_ir", ""),
                "prediction": prediction,
                "reference": read_text(row.get("program_path", "")),
            }
            f.write(json.dumps(out, ensure_ascii=False) + "\n")
            if (i + 1) % 50 == 0:
                print(f"{i+1}/{len(ir_rows)} done", flush=True)
    print("Wrote", args.output_jsonl)


if __name__ == "__main__":
    main()
