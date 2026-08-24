#!/bin/bash
# Phase 2 / Stage 1 follow-up: build the train (retrieval) and test (retrieval-
# quality self-eval) IR indices from the trained alignment checkpoint.
# Asymmetric on purpose (train index off train.jsonl, test index off
# step_features_test.jsonl) -- matches the existing 500/50K precedent exactly;
# step_features_test.jsonl is what actually carries the joined
# step_feature_path for the test split's extracted STEP features.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

python build_index.py \
  --checkpoint outputs/align_25k/best.pt --jsonl data/25k/train.jsonl \
  --output outputs/align_25k/train_ir_index.npz --index-modality ir \
  --batch-size 32 --point-count 1024

python build_index.py \
  --checkpoint outputs/align_25k/best.pt --jsonl data/25k/step_features_test.jsonl \
  --output outputs/align_25k/test_ir_index.npz --index-modality ir \
  --batch-size 32 --point-count 1024

echo "=== Wrote outputs/align_25k/{train,test}_ir_index.npz (+ .json sidecars) ==="
