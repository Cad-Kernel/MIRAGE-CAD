#!/bin/bash
# Phase 6 / Stage 3 formal eval: generate predicted_ir for the full 2.5K test set, image query.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

python training_25k/scripts/gen_predicted_ir.py \
  --modality image \
  --alignment-checkpoint outputs/align_25k/best.pt \
  --prior-checkpoint outputs/prior_image_25k/best.pt \
  --lora-ir-dir outputs/lora_ir_25k \
  --input-jsonl data/25k/test.jsonl \
  --output-jsonl outputs/lora_ir_25k/predicted_ir_test_image.jsonl \
  --max-length 1536 --max-new-tokens 1536

echo "=== Wrote outputs/lora_ir_25k/predicted_ir_test_image.jsonl ==="
