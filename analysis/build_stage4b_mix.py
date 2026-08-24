"""Build the Stage 4b mixed training set: 70% ground-truth IR rows + 30%
grammar-valid predicted_ir rows (train split only, no val/test leakage).
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, ".")
from miragecad.data import read_jsonl
from miragecad.gen_prompts import validate_ir_grammar

RATIO_PREDICTED = 0.30
SEED = 42

pred_rows = read_jsonl(Path("outputs/qwen25_coder_1_5b_program_5k/predicted_ir_train_subset.jsonl"))
pred_by_id = {r["sample_id"]: r["predicted_ir"] for r in pred_rows}

valid_pred_ids = [sid for sid, ir in pred_by_id.items() if validate_ir_grammar(ir)["valid"]]
print(f"predicted_ir generated: {len(pred_by_id)}, grammar-valid: {len(valid_pred_ids)}")

# GT-IR rows are drawn from the FULL train split (not just the 200-row slice
# used to generate predicted_ir) so there's enough pool to hit the target
# 70/30 ratio regardless of how many predicted_ir samples turned out valid.
train_rows_full = read_jsonl(Path("data/smoke5k/train.jsonl"))
train_by_id = {r["sample_id"]: r for r in train_rows_full}

n_pred = len(valid_pred_ids)
n_gt = int(round(n_pred * (1 - RATIO_PREDICTED) / RATIO_PREDICTED))
rng = random.Random(SEED)
gt_candidate_ids = [sid for sid in train_by_id if sid not in valid_pred_ids]
gt_ids = rng.sample(gt_candidate_ids, min(n_gt, len(gt_candidate_ids)))

out_rows = []
for sid in gt_ids:
    out_rows.append(train_by_id[sid])
for sid in valid_pred_ids:
    row = dict(train_by_id[sid])
    row["ir_text_for_program"] = pred_by_id[sid]
    out_rows.append(row)
rng.shuffle(out_rows)

out_path = Path("data/smoke5k/train_stage4b_mix.jsonl")
with open(out_path, "w", encoding="utf-8", newline="\n") as f:
    for row in out_rows:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

print(f"GT-IR rows: {len(gt_ids)}, predicted_ir rows: {len(valid_pred_ids)}, total: {len(out_rows)}")
print(f"actual predicted_ir ratio: {len(valid_pred_ids)/len(out_rows):.1%}")
print("wrote", out_path)
