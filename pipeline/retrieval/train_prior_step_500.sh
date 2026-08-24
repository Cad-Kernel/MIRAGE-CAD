#!/usr/bin/env bash
set -euo pipefail

python train_latent_prior.py \
  --alignment-checkpoint outputs/align_smoke500/best.pt \
  --train-jsonl data/smoke500/train.jsonl \
  --val-jsonl data/smoke500/val.jsonl \
  --output-dir outputs/prior_step_smoke500 \
  --modality step \
  --epochs 10 \
  --batch-size 32 \
  --learning-rate 1e-4 \
  --temperature 0.07 \
  --lambda-cos 1.0 \
  --lambda-nce 1.0
