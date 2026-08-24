#!/bin/bash
# Compositional-split pipeline / Stage 2: four modality-specific latent
# priors, trained on data/25k_comp against outputs/align_25k_comp. Same
# hyperparameters as 05_train_prior_{step,point,text,image}.sh. Run
# sequentially (not backgrounded per-modality) to avoid four processes
# fighting over the single GPU's 16GB VRAM.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

python train_latent_prior.py \
  --alignment-checkpoint outputs/align_25k_comp/best.pt \
  --train-jsonl data/25k_comp/train.jsonl --val-jsonl data/25k_comp/val.jsonl \
  --output-dir outputs/prior_step_25k_comp --modality step \
  --epochs 8 --batch-size 48 --learning-rate 1e-4 \
  --temperature 0.07 --lambda-cos 1.0 --lambda-nce 1.0
echo "=== Checkpoint: outputs/prior_step_25k_comp/best.pt ==="

python train_latent_prior.py \
  --alignment-checkpoint outputs/align_25k_comp/best.pt \
  --train-jsonl data/25k_comp/train.jsonl --val-jsonl data/25k_comp/val.jsonl \
  --output-dir outputs/prior_point_25k_comp --modality point \
  --epochs 8 --batch-size 48 --learning-rate 1e-4 \
  --temperature 0.07 --lambda-cos 1.0 --lambda-nce 1.0 \
  --train-point-sampling hybrid --eval-point-sampling fps
echo "=== Checkpoint: outputs/prior_point_25k_comp/best.pt ==="

python train_latent_prior.py \
  --alignment-checkpoint outputs/align_25k_comp/best.pt \
  --train-jsonl data/25k_comp/train.jsonl --val-jsonl data/25k_comp/val.jsonl \
  --output-dir outputs/prior_text_25k_comp --modality text \
  --epochs 8 --batch-size 48 --learning-rate 1e-4 \
  --temperature 0.07 --lambda-cos 1.0 --lambda-nce 1.0
echo "=== Checkpoint: outputs/prior_text_25k_comp/best.pt ==="

python train_latent_prior.py \
  --alignment-checkpoint outputs/align_25k_comp/best.pt \
  --train-jsonl data/25k_comp/train.jsonl --val-jsonl data/25k_comp/val.jsonl \
  --output-dir outputs/prior_image_25k_comp --modality image \
  --epochs 8 --batch-size 48 --learning-rate 1e-4 \
  --temperature 0.07 --lambda-cos 1.0 --lambda-nce 1.0
echo "=== Checkpoint: outputs/prior_image_25k_comp/best.pt ==="
