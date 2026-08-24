#!/bin/bash
# Phase 5 / Stage 4b prep, part 1: generate predicted_ir for a TRAIN subset
# (step modality, matching the 5K precedent's train-time recipe exactly), to
# build the 70% GT-IR / 30% predicted_ir Stage 4b mix.
#
# N=1000 out of 25000 train rows (~4%, same fraction as the 5K run's N=200/
# 5000) -- scale this up if you want a larger absolute predicted_ir pool, but
# keep the ~4% fraction as the default unless you have a specific reason to
# change it (a bigger N here means more Stage-4b generation time now, in
# exchange for a larger predicted_ir pool later).
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

python training_25k/scripts/gen_predicted_ir.py \
  --modality step \
  --alignment-checkpoint outputs/align_25k/best.pt \
  --prior-checkpoint outputs/prior_step_25k/best.pt \
  --lora-ir-dir outputs/lora_ir_25k \
  --input-jsonl data/25k/train.jsonl \
  --output-jsonl outputs/lora_ir_25k/predicted_ir_train_subset.jsonl \
  --limit 1000 \
  --max-length 1536 --max-new-tokens 1536

echo "=== Wrote outputs/lora_ir_25k/predicted_ir_train_subset.jsonl ==="
