#!/usr/bin/env bash
set -euo pipefail

python train_latent_prior.py \
  --alignment-checkpoint outputs/align_smoke5k_ep10/best.pt \
  --train-jsonl data/smoke5k/train.jsonl \
  --val-jsonl data/smoke5k/val.jsonl \
  --output-dir outputs/prior_text_5k \
  --modality text \
  --epochs 10 \
  --batch-size 32 \
  --learning-rate 1e-4 \
  --temperature 0.07 \
  --lambda-cos 1.0 \
  --lambda-nce 1.0
