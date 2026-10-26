#!/usr/bin/env bash
set -euo pipefail
python -m gen_scripts.train_soft_prefix_ir \
  --model-name Qwen/Qwen2.5-Coder-1.5B \
  --alignment-checkpoint outputs/align_smoke5k_ep10/best.pt \
  --prior-checkpoint outputs/prior_step_5k/best.pt \
  --modality step \
  --train-jsonl data/smoke5k/train.jsonl \
  --val-jsonl data/smoke5k/val.jsonl \
  --output-dir outputs/lora_ir_5k \
  --prefix-len 4 \
  --load-in-4bit \
  --bf16 \
  --per-device-train-batch-size 1 \
  --gradient-accumulation-steps 16 \
  --epochs 3 \
  --learning-rate 2e-4 \
  --max-length 1536
