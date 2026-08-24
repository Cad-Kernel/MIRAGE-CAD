#!/usr/bin/env bash
set -euo pipefail

python train_latent_prior.py \
  --alignment-checkpoint outputs/align_50k/best.pt \
  --train-jsonl data/50k/train.jsonl \
  --val-jsonl data/50k/val.jsonl \
  --output-dir outputs/prior_point_50k \
  --modality point \
  --epochs 5 \
  --batch-size 64 \
  --learning-rate 1e-4 \
  --train-point-sampling hybrid \
  --eval-point-sampling fps \
  --temperature 0.07 \
  --lambda-cos 1.0 \
  --lambda-nce 1.0
