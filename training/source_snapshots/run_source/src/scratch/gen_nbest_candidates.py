"""Generate a pool of N candidate programs per sample (candidate 0 greedy,
candidates 1..N-1 temperature-sampled) from already-generated predicted_ir,
for Table 4 (geometry-conditioned N-best selection). Reuses the same
predicted_ir + Stage4b checkpoint as the main "Ours" pipeline -- only the
LoRA-Code decoding varies (greedy vs. sampled), matching variant E's design
(fixed construction plan, multiple code realizations, execution-guided pick).
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
    p.add_argument("--modality", choices=["point", "step"], required=True)
    p.add_argument("--ir-jsonl", type=Path, required=True)
    p.add_argument("--output-jsonl", type=Path, required=True)
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--num-candidates", type=int, default=10)
    p.add_argument("--lora-code-dir", type=Path, default=Path("outputs/qwen25_coder_1_5b_program_5k_stage4b"))
    p.add_argument("--input-jsonl", type=Path, default=Path("data/smoke5k/test.jsonl"))
    p.add_argument("--point-count", type=int, default=1024)
    p.add_argument("--max-length", type=int, default=1536)
    p.add_argument("--max-new-tokens", type=int, default=1536)
    p.add_argument("--temperature", type=float, default=0.8)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def main():
    args = parse_args()
    torch.manual_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    lora_code = load_lm("Qwen/Qwen2.5-Coder-1.5B", args.lora_code_dir, torch.bfloat16, device)
    lora_code_tok = load_tokenizer(args.lora_code_dir)

    ir_rows = read_jsonl(args.ir_jsonl)[: args.limit]
    test_rows = {r["sample_id"]: r for r in read_jsonl(args.input_jsonl)}

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
                point_xyz = load_point_cloud_sampled(row["point_path"], point_count=args.point_count, sampling="fps", seed=args.seed)
            prompt = build_program_prompt(row, args.modality, predicted_ir, point_xyz=point_xyz)

            candidates = [generate_text(lora_code, lora_code_tok, prompt, args.max_length, args.max_new_tokens, 0.0, 1.0, device)]
            for _ in range(args.num_candidates - 1):
                candidates.append(generate_text(lora_code, lora_code_tok, prompt, args.max_length, args.max_new_tokens, args.temperature, 1.0, device))

            out = {
                "sample_id": sid,
                "modality": args.modality,
                "predicted_ir": predicted_ir,
                "reference_ir": ir_row.get("reference_ir", ""),
                "all_candidates": candidates,
                "reference": read_text(row.get("program_path", "")),
                "point_path": row.get("point_path", ""),
                "step_path": row.get("step_path", ""),
            }
            f.write(json.dumps(out, ensure_ascii=False) + "\n")
            print(f"{i+1}/{len(ir_rows)} done", flush=True)
    print("Wrote", args.output_jsonl)


if __name__ == "__main__":
    main()
