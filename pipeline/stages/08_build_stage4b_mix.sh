#!/bin/bash
# Phase 5 / Stage 4b prep, part 2: filter to grammar-valid predicted_ir rows
# and build the 70%-GT/30%-predicted mixed training set.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

python training_25k/scripts/build_stage4b_mix.py \
  --predicted-ir-jsonl outputs/lora_ir_25k/predicted_ir_train_subset.jsonl \
  --full-train-jsonl data/25k/train.jsonl \
  --output-jsonl data/25k/train_stage4b_mix.jsonl \
  --predicted-ratio 0.30

echo "=== Wrote data/25k/train_stage4b_mix.jsonl ==="
