#!/usr/bin/env bash
set -euo pipefail

python train_latent_prior.py \
  --alignment-checkpoint outputs/align_50k/best.pt \
  --train-jsonl data/50k/train.jsonl \
  --val-jsonl data/50k/val.jsonl \
  --output-dir outputs/prior_step_50k \
  --modality step \
  --epochs 5 \
  --batch-size 64 \
  --learning-rate 1e-4 \
  --temperature 0.07 \
  --lambda-cos 1.0 \
  --lambda-nce 1.0
