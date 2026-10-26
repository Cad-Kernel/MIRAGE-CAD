#!/usr/bin/env bash
set -euo pipefail

python train_program_lora.py \
  --model-name Qwen/Qwen2.5-Coder-1.5B \
  --train-jsonl data/smoke5k/train.jsonl \
  --val-jsonl data/smoke5k/val.jsonl \
  --output-dir outputs/qwen25_coder_1_5b_program_5k \
  --target program \
  --modality step \
  --max-length 1536 \
  --epochs 1 \
  --per-device-train-batch-size 1 \
  --per-device-eval-batch-size 1 \
  --gradient-accumulation-steps 8 \
  --learning-rate 2e-4 \
  --eval-steps 100 \
  --save-steps 100 \
  --logging-steps 10 \
  --save-total-limit 2 \
  --lora-r 16 \
  --lora-alpha 32 \
  --bf16
