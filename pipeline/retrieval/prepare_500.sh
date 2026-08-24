#!/usr/bin/env bash
set -euo pipefail

python prepare_manifest.py \
  --dataset-dir /mnt/c/Workspace/Project/FllumaOne/FllumaOne-100K \
  --output-dir data/smoke500 \
  --scale smoke500 \
  --prompt-mode mixed \
  --sampling stratified-level
