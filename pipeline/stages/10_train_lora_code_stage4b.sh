#!/bin/bash
# Phase 5 / Stage 4b: continue-train Stage 4's LoRA-Code adapter on the
# 70%-GT/30%-predicted mix, to close the train/inference distribution gap
# (LoRA-Code sees real, imperfect predicted_ir at inference, never at Stage 4
# training time). Lower LR than Stage 4 (5e-5 vs 2e-4) since this is a small-
# delta continuation fine-tune, not a from-scratch run -- do not raise this,
# the 5K precedent (docs/Todo.md) found this exact LR necessary to avoid
# catastrophic forgetting of the Stage-4 GT-IR capability (Stage 4c's
# cautionary tale used higher LR/longer training and regressed 110/500
# previously-working samples).
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

python train_program_lora.py \
  --model-name Qwen/Qwen2.5-Coder-1.5B \
  --train-jsonl data/25k/train_stage4b_mix.jsonl --val-jsonl data/25k/val.jsonl \
  --output-dir outputs/qwen25_coder_1_5b_program_25k_stage4b \
  --init-adapter-dir outputs/qwen25_coder_1_5b_program_25k \
  --target program --modality step --max-length 1536 \
  --epochs 3 --per-device-train-batch-size 1 --per-device-eval-batch-size 1 \
  --gradient-accumulation-steps 8 --learning-rate 5e-5 \
  --eval-steps 100 --save-steps 100 --logging-steps 10 --save-total-limit 2 \
  --lora-r 16 --lora-alpha 32 --load-in-4bit --bf16

echo "=== Checkpoint: outputs/qwen25_coder_1_5b_program_25k_stage4b/ (THE recommended inference checkpoint) ==="
