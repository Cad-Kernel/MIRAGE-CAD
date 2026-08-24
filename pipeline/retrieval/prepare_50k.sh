#!/usr/bin/env bash
set -euo pipefail

python prepare_manifest.py \
  --dataset-dir /mnt/c/Workspace/Project/FllumaOne/FllumaOne-100K \
  --output-dir data/50k \
  --scale 50k \
  --prompt-mode mixed \
  --sampling stratified-level
