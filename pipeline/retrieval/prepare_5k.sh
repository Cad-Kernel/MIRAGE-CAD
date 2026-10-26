#!/usr/bin/env bash
set -euo pipefail

python prepare_manifest.py \
  --dataset-dir __LOCAL_WORKSPACE__/Project/FllumaOne/FllumaOne-100K \
  --output-dir data/smoke5k \
  --scale 10k \
  --train-samples 5000 \
  --val-samples 500 \
  --test-samples 500 \
  --prompt-mode mixed \
  --sampling stratified-level
