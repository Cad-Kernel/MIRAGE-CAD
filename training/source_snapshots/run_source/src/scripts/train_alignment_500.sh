#!/usr/bin/env bash
set -euo pipefail

python train_alignment.py \
  --train-jsonl data/smoke500/train.jsonl \
  --val-jsonl data/smoke500/val.jsonl \
  --output-dir outputs/align_smoke500 \
  --modalities text image point step ir \
  --image-mode iso \
  --epochs 1 \
  --batch-size 8 \
  --grad-accum 2 \
  --max-text-length 128 \
  --max-ir-length 256 \
  --point-count 1024 \
  --bf16
