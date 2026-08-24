#!/bin/bash
# Compositional-split pipeline / Stage 4b prep: generate predicted_ir for a
# comp-train subset using the Stage 3b checkpoint, then build the 70%-GT/
# 30%-predicted mix, matching 07_gen_predicted_ir_train_subset.sh +
# 08_build_stage4b_mix.sh exactly (same ~4% subset fraction: 1000/23577).
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

python training_25k/scripts/gen_predicted_ir.py \
  --modality step \
  --alignment-checkpoint outputs/align_25k_comp/best.pt \
  --prior-checkpoint outputs/prior_step_25k_comp/best.pt \
  --lora-ir-dir outputs/lora_ir_25k_comp_stage3b \
  --input-jsonl data/25k_comp/train.jsonl \
  --output-jsonl outputs/lora_ir_25k_comp_stage3b/predicted_ir_train_subset.jsonl \
  --limit 1000 \
  --max-length 1536 --max-new-tokens 1536

echo "=== Wrote outputs/lora_ir_25k_comp_stage3b/predicted_ir_train_subset.jsonl ==="

python training_25k/scripts/build_stage4b_mix.py \
  --predicted-ir-jsonl outputs/lora_ir_25k_comp_stage3b/predicted_ir_train_subset.jsonl \
  --full-train-jsonl data/25k_comp/train.jsonl \
  --output-jsonl data/25k_comp/train_stage4b_mix.jsonl \
  --predicted-ratio 0.30

echo "=== Wrote data/25k_comp/train_stage4b_mix.jsonl ==="
