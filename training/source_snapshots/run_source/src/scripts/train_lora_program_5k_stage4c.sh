#!/usr/bin/env bash
set -euo pipefail

python train_program_lora.py \
  --model-name Qwen/Qwen2.5-Coder-1.5B \
  --train-jsonl data/smoke5k/train_stage4c_facefeature_oversample.jsonl \
  --val-jsonl data/smoke5k/val.jsonl \
  --output-dir outputs/qwen25_coder_1_5b_program_5k_stage4c \
  --init-adapter-dir outputs/qwen25_coder_1_5b_program_5k_stage4b \
  --target program \
  --modality step \
  --max-length 1536 \
  --epochs 3 \
  --per-device-train-batch-size 1 \
  --per-device-eval-batch-size 1 \
  --gradient-accumulation-steps 8 \
  --learning-rate 3e-5 \
  --eval-steps 40 \
  --save-steps 40 \
  --logging-steps 5 \
  --save-total-limit 2 \
  --lora-r 16 \
  --lora-alpha 32 \
  --bf16
