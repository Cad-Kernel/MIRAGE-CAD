"""Build the Stage 4c continued-training set: oversample GT-IR training rows
that exercise the low-frequency face-feature op family
(OP_SKETCH_ON_FACE / OP_FACE_EXTRUDE_ADD / OP_FACE_EXTRUDE_CUT, 7.14% of
train rows, 357/5000), mixed with an equal-sized random sample of the
remaining general rows so the continued fine-tune doesn't forget everything
else. Pure GT-IR only (no predicted_ir mixing this round) to isolate the
"more training exposure to this op family" variable cleanly -- Stage 4b
already handles the predicted_ir distribution shift.
"""
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, ".")
from miragecad.data import read_jsonl, read_text
from miragecad.gen_prompts import OP_TOKEN_PATTERN

TARGET_OPS = {"OP_SKETCH_ON_FACE", "OP_FACE_EXTRUDE_ADD", "OP_FACE_EXTRUDE_CUT"}
OVERSAMPLE_FACTOR = 3
SEED = 42

rows = list(read_jsonl(Path("data/smoke5k/train.jsonl")))
target_rows = []
general_rows = []
for row in rows:
    ir = read_text(Path(row["ir_path"]))
    ops = set(OP_TOKEN_PATTERN.findall(ir.upper()))
    (target_rows if ops & TARGET_OPS else general_rows).append(row)

print(f"total train rows: {len(rows)}, target (face-feature) rows: {len(target_rows)}, general rows: {len(general_rows)}")

rng = random.Random(SEED)
oversampled_target = target_rows * OVERSAMPLE_FACTOR
general_sample = rng.sample(general_rows, min(len(oversampled_target), len(general_rows)))

out_rows = oversampled_target + general_sample
rng.shuffle(out_rows)

out_path = Path("data/smoke5k/train_stage4c_facefeature_oversample.jsonl")
with open(out_path, "w", encoding="utf-8", newline="\n") as f:
    for row in out_rows:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

print(f"oversampled target rows: {len(oversampled_target)} ({OVERSAMPLE_FACTOR}x of {len(target_rows)})")
print(f"general rows sampled: {len(general_sample)}")
print(f"total: {len(out_rows)}")
print("wrote", out_path)
