#!/bin/bash
# Phase 3 / Stage 2: point-cloud-modality latent prior.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

python train_latent_prior.py \
  --alignment-checkpoint outputs/align_25k/best.pt \
  --train-jsonl data/25k/train.jsonl --val-jsonl data/25k/val.jsonl \
  --output-dir outputs/prior_point_25k --modality point \
  --epochs 8 --batch-size 48 --learning-rate 1e-4 \
  --temperature 0.07 --lambda-cos 1.0 --lambda-nce 1.0 \
  --train-point-sampling hybrid --eval-point-sampling fps

echo "=== Checkpoint: outputs/prior_point_25k/best.pt ==="
