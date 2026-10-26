"""Generate program.py ONLY for the ~135 samples in the fixed quick-eval set
(data/smoke5k/quick_eval_rareop_set.jsonl), using a given LoRA-Code
checkpoint. This is the fast screening step for continued-fine-tune
experiments (e.g. Stage 4c-mini) -- ~135 samples instead of 500 means this
finishes in a few minutes instead of ~90.

Usage:
  python scratch/gen_code_quick_eval.py --checkpoint-dir outputs/qwen25_coder_1_5b_program_5k_stage4c_mini/checkpoint-100 --out outputs/qwen25_coder_1_5b_program_5k_stage4c_mini/quick_eval_ckpt100.jsonl
"""
import argparse
import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, ".")
from miragecad.data import read_jsonl, read_text
from miragecad.gen_prompts import build_program_prompt
from gen_scripts.run_miragecad import load_lm, load_tokenizer, generate_text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint-dir", type=Path, required=True)
    ap.add_argument("--predicted-ir", type=Path, default=Path("outputs/lora_ir_5k/predicted_ir_test500_full_p1a.jsonl"))
    ap.add_argument("--quick-eval-set", type=Path, default=Path("data/smoke5k/quick_eval_rareop_set.jsonl"))
    ap.add_argument("--test-jsonl", type=Path, default=Path("data/smoke5k/test.jsonl"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--max-new-tokens", type=int, default=1536)
    args = ap.parse_args()

    quick_ids = {json.loads(l)["sample_id"] for l in open(args.quick_eval_set, encoding="utf-8") if l.strip()}
    print(f"quick-eval set: {len(quick_ids)} samples")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    lora_code = load_lm("Qwen/Qwen2.5-Coder-1.5B", args.checkpoint_dir, torch.bfloat16, device)
    lora_code_tok = load_tokenizer(args.checkpoint_dir)

    test_rows = {r["sample_id"]: r for r in read_jsonl(args.test_jsonl)}
    predicted_rows = {r["sample_id"]: r for r in read_jsonl(args.predicted_ir)}

    args.out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        for sid in quick_ids:
            pr = predicted_rows[sid]
            row = test_rows[sid]
            predicted_ir = pr["predicted_ir"]
            prompt = build_program_prompt(row, "step", predicted_ir)
            prediction = generate_text(lora_code, lora_code_tok, prompt, args.max_new_tokens, args.max_new_tokens, 0.0, 1.0, device)
            f.write(json.dumps({
                "sample_id": sid,
                "target": "program",
                "predicted_ir": predicted_ir,
                "prediction": prediction,
                "reference": read_text(row.get("program_path", "")),
            }, ensure_ascii=False) + "\n")
            n += 1
            if n % 25 == 0:
                print(f"{n}/{len(quick_ids)} done", flush=True)
    print("Wrote", args.out)


if __name__ == "__main__":
    main()
