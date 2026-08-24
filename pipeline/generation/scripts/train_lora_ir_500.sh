#!/usr/bin/env bash
set -euo pipefail
python -m gen_scripts.train_soft_prefix_ir \
  --model-name Qwen/Qwen2.5-Coder-1.5B \
  --alignment-checkpoint outputs/align_smoke500/best.pt \
  --prior-checkpoint outputs/prior_step_smoke500/best.pt \
  --modality step \
  --train-jsonl data/smoke500/train.jsonl \
  --val-jsonl data/smoke500/val.jsonl \
  --output-dir outputs/lora_ir_500 \
  --prefix-len 4 \
  --load-in-4bit \
  --bf16 \
  --per-device-train-batch-size 1 \
  --gradient-accumulation-steps 16 \
  --epochs 3 \
  --learning-rate 2e-4 \
  --max-length 1536
