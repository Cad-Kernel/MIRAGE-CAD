#!/usr/bin/env bash
set -euo pipefail

python train_program_lora.py \
  --model-name Qwen/Qwen2.5-Coder-1.5B \
  --train-jsonl data/50k/train.jsonl \
  --val-jsonl data/50k/val.jsonl \
  --output-dir outputs/qwen25_coder_1_5b_program_50k \
  --target program \
  --max-length 1536 \
  --epochs 1 \
  --per-device-train-batch-size 1 \
  --per-device-eval-batch-size 1 \
  --gradient-accumulation-steps 16 \
  --learning-rate 2e-4 \
  --eval-steps 1000 \
  --save-steps 1000 \
  --logging-steps 20 \
  --save-total-limit 2 \
  --lora-r 16 \
  --lora-alpha 32 \
  --bf16
