#!/usr/bin/env bash
set -euo pipefail

python build_index.py \
  --checkpoint outputs/align_50k/best.pt \
  --jsonl data/50k/train.jsonl \
  --output outputs/align_50k/train_ir_index.npz \
  --index-modality ir \
  --batch-size 32 \
  --point-count 1024
