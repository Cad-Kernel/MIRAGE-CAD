#!/bin/bash
# Phase 1: build the 25K/2.5K/2.5K manifest split.
# Run in WSL, from ~/workspace/MIRAGE/src.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

python prepare_manifest.py \
  --dataset-dir /mnt/c/Workspace/Project/FllumaOne/FllumaOne-100K \
  --output-dir data/25k \
  --scale 50k \
  --train-samples 25000 --val-samples 2500 --test-samples 2500 \
  --prompt-mode mixed --sampling stratified-level

echo "=== Output: data/25k/{train,val,test}.jsonl + data/25k/manifest.json ==="
wc -l data/25k/train.jsonl data/25k/val.jsonl data/25k/test.jsonl
