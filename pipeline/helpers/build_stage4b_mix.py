"""Stage 4b: build the 70% ground-truth-IR / 30% predicted_ir mixed training
set for LoRA-Code robustness fine-tuning. CLI-parameterized generalization of
scratch/build_stage4b_mix.py (which had every path/ratio/seed hardcoded to 5K
literals) -- same logic: keep only grammar-valid predicted_ir rows, then
sample enough additional ground-truth rows (excluding the predicted_ir
sample_ids) to hit the target ratio, and mark the predicted_ir rows with
ir_text_for_program so train_program_lora.py picks them up.
"""
import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, ".")
from miragecad.gen_prompts import validate_ir_grammar


def read_jsonl(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--predicted-ir-jsonl", type=Path, required=True,
                    help="Output of gen_predicted_ir.py run on a TRAIN subset.")
    p.add_argument("--full-train-jsonl", type=Path, required=True)
    p.add_argument("--output-jsonl", type=Path, required=True)
    p.add_argument("--predicted-ratio", type=float, default=0.30)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def main():
    args = parse_args()
    pred_rows = read_jsonl(args.predicted_ir_jsonl)
    train_rows_full = read_jsonl(args.full_train_jsonl)

    valid_pred_rows = []
    n_invalid = 0
    for r in pred_rows:
        check = validate_ir_grammar(r["predicted_ir"])
        if check["valid"]:
            valid_pred_rows.append(r)
        else:
            n_invalid += 1
    print(f"predicted_ir grammar valid: {len(valid_pred_rows)}/{len(pred_rows)} "
          f"({n_invalid} invalid, dropped)")

    n_pred = len(valid_pred_rows)
    n_gt = round(n_pred * (1 - args.predicted_ratio) / args.predicted_ratio)
    pred_ids = {r["sample_id"] for r in valid_pred_rows}
    gt_pool = [r for r in train_rows_full if r["sample_id"] not in pred_ids]
    if n_gt > len(gt_pool):
        raise SystemExit(
            f"Need {n_gt} ground-truth rows for a {1 - args.predicted_ratio:.0%}/"
            f"{args.predicted_ratio:.0%} mix but only {len(gt_pool)} are available "
            f"(train set too small relative to predicted_ir subset size)."
        )
    rng = random.Random(args.seed)
    gt_rows = rng.sample(gt_pool, n_gt)

    pred_by_id = {r["sample_id"]: r for r in valid_pred_rows}
    full_by_id = {r["sample_id"]: r for r in train_rows_full}
    mixed = []
    for r in valid_pred_rows:
        row = dict(full_by_id[r["sample_id"]])
        row["ir_text_for_program"] = r["predicted_ir"]
        mixed.append(row)
    mixed.extend(gt_rows)
    rng.shuffle(mixed)

    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_jsonl, "w", encoding="utf-8", newline="\n") as f:
        for row in mixed:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Mix: {len(valid_pred_rows)} predicted_ir rows + {len(gt_rows)} ground-truth rows "
          f"= {len(mixed)} total ({args.predicted_ratio:.0%}/{1 - args.predicted_ratio:.0%} target)")
    print("Wrote", args.output_jsonl)


if __name__ == "__main__":
    main()
