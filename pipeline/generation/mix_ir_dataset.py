"""Mix ground-truth IR rows and predicted IR rows for Stage 4b training.

Creates a 70/30 (default) mixed JSONL dataset.

NOTE for train_program_lora.py integration:
  Rows with ir_source == "predicted" carry their IR text in row["predicted_ir"]
  instead of on disk at row["ir_path"].  To support these rows, add the following
  patch to load_program_example in miragecad/data.py (in the ir branch):

      if target == "ir":
          if row.get("ir_source") == "predicted":
              target_text = row.get("predicted_ir", "")
          else:
              target_text = read_text(row["ir_path"])

  Do not implement this patch here; it belongs in miragecad/data.py or the
  training script that calls load_program_example.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from miragecad.data import read_jsonl, write_jsonl


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Create 70/30 mixed GT+predicted IR dataset for Stage 4b.")
    p.add_argument("--train-jsonl", type=Path, required=True, help="Original train JSONL with ir_path/program_path.")
    p.add_argument("--predicted-ir-jsonl", type=Path, required=True, help="Output of generate_predicted_ir.py.")
    p.add_argument("--output-jsonl", type=Path, required=True)
    p.add_argument("--gt-ratio", type=float, default=0.7, help="Fraction of rows using ground-truth IR.")
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    rng = random.Random(args.seed)

    train_rows = read_jsonl(args.train_jsonl)
    predicted_rows = read_jsonl(args.predicted_ir_jsonl)

    # Index predicted IR by sample_id for fast lookup
    predicted_by_id: dict[str, dict] = {}
    for pred_row in predicted_rows:
        sid = pred_row.get("sample_id", "")
        if sid:
            predicted_by_id[sid] = pred_row

    gt_pool: list[dict] = []
    predicted_pool: list[dict] = []

    for row in train_rows:
        sid = row.get("sample_id", "")
        pred = predicted_by_id.get(sid)

        gt_row = dict(row)
        gt_row["ir_source"] = "ground_truth"
        gt_pool.append(gt_row)

        if pred and pred.get("predicted_ir"):
            pred_row = dict(row)
            pred_row["ir_source"] = "predicted"
            pred_row["predicted_ir"] = pred["predicted_ir"]
            predicted_pool.append(pred_row)

    if not gt_pool:
        print("No rows found, nothing to write.")
        return 1

    # Use all GT rows; compute how many predicted rows achieve the target ratio.
    # gt_ratio = n_gt / (n_gt + n_pred)  =>  n_pred = n_gt * (1 - gt_ratio) / gt_ratio
    n_gt = len(gt_pool)
    if args.gt_ratio >= 1.0 or not predicted_pool:
        n_pred = 0
    else:
        n_pred_target = round(n_gt * (1 - args.gt_ratio) / args.gt_ratio)
        n_pred = min(n_pred_target, len(predicted_pool))

    sampled_gt = rng.sample(gt_pool, n_gt)
    sampled_pred = rng.sample(predicted_pool, n_pred) if n_pred > 0 else []

    actual_gt_ratio = n_gt / max(n_gt + n_pred, 1)
    if abs(actual_gt_ratio - args.gt_ratio) > 0.05:
        print(
            f"WARNING: Target GT ratio {args.gt_ratio:.0%} but actual {actual_gt_ratio:.0%}. "
            f"Predicted pool too small ({len(predicted_pool)} available, {n_pred} sampled)."
        )

    mixed = sampled_gt + sampled_pred
    rng.shuffle(mixed)

    write_jsonl(args.output_jsonl, mixed)
    print(
        f"Wrote {len(mixed)} rows to {args.output_jsonl} "
        f"(GT={len(sampled_gt)}, predicted={len(sampled_pred)}, actual_gt_ratio={actual_gt_ratio:.0%})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
