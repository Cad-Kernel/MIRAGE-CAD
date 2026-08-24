#!/usr/bin/env bash
set -euo pipefail

python train_program_lora.py \
  --model-name Qwen/Qwen2.5-Coder-1.5B \
  --train-jsonl data/smoke5k/train_stage4b_mix.jsonl \
  --val-jsonl data/smoke5k/val.jsonl \
  --output-dir outputs/qwen25_coder_1_5b_program_5k_stage4b \
  --init-adapter-dir outputs/qwen25_coder_1_5b_program_5k \
  --target program \
  --modality step \
  --max-length 1536 \
  --epochs 3 \
  --per-device-train-batch-size 1 \
  --per-device-eval-batch-size 1 \
  --gradient-accumulation-steps 8 \
  --learning-rate 5e-5 \
  --eval-steps 20 \
  --save-steps 20 \
  --logging-steps 5 \
  --save-total-limit 2 \
  --lora-r 16 \
  --lora-alpha 32 \
  --bf16
