#!/bin/bash
# Phase 7 / Table 2: predicted_ir quality (IR cosine, Op-Set F1, Op-Seq LCS),
# all four modalities, against ground-truth IR.
#
# WARNING (a documented past bug, docs/Todo.md): gen_scripts.evaluate_ir_quality
# silently falls back to comparing against an empty/wrong field if the input
# JSONL lacks 'reference_ir' (producing a bogus near-zero score, not an error)
# -- our training_25k/scripts/gen_predicted_ir.py always writes reference_ir,
# so the *_p1a.jsonl files from step 12 are safe to use directly. If you ever
# substitute a different predicted_ir file here, verify it has a genuine
# reference_ir field first (spot-check with: head -1 file.jsonl | python3 -m
# json.tool | grep reference_ir).
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

for m in step point text image; do
  echo "=== IR quality eval: $m ==="
  python -m gen_scripts.evaluate_ir_quality \
    --predicted-jsonl outputs/lora_ir_25k/predicted_ir_test_${m}_p1a.jsonl \
    --alignment-checkpoint outputs/align_25k/best.pt \
    --output-json outputs/lora_ir_25k/ir_quality_${m}_25k.json
done

echo "=== Wrote outputs/lora_ir_25k/ir_quality_{step,point,text,image}_25k.json ==="
