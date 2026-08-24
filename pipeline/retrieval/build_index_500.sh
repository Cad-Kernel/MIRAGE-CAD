#!/usr/bin/env bash
set -euo pipefail

python build_index.py \
  --checkpoint outputs/align_smoke500/best.pt \
  --jsonl data/smoke500/train.jsonl \
  --output outputs/align_smoke500/train_ir_index.npz \
  --index-modality ir \
  --batch-size 32 \
  --point-count 1024
