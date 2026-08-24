#!/bin/bash
# Phase 6 repair step 1 (P1a): face-extrude alias normalization, applied to
# predicted_ir BEFORE Stage 4b code generation. Operates on the 'predicted_ir'
# field (not 'prediction' -- do not confuse with the P0/extrude_on_face
# repairs in step 14, which operate on generated code instead).
#
# NOTE: scratch/repair_face_extrude_alias.py defaults to DRY-RUN (only writes
# the log, not --output) unless --apply is passed -- this script always
# passes --apply. Fast, pure-Python, no GPU needed.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

for m in step point text image; do
  echo "=== P1a repair: $m ==="
  python scratch/repair_face_extrude_alias.py \
    --input outputs/lora_ir_25k/predicted_ir_test_${m}.jsonl \
    --output outputs/lora_ir_25k/predicted_ir_test_${m}_p1a.jsonl \
    --log outputs/lora_ir_25k/repair_face_extrude_alias_log_${m}.json \
    --apply
done

echo "=== Wrote outputs/lora_ir_25k/predicted_ir_test_{step,point,text,image}_p1a.jsonl ==="
