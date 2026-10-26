#!/usr/bin/env bash
set -euo pipefail

python train_alignment.py \
  --train-jsonl data/50k/train.jsonl \
  --val-jsonl data/50k/val.jsonl \
  --output-dir outputs/align_50k \
  --modalities text image point step ir \
  --image-mode iso \
  --epochs 3 \
  --batch-size 8 \
  --grad-accum 4 \
  --max-text-length 128 \
  --max-ir-length 256 \
  --point-count 1024 \
  --bf16
