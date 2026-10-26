#!/usr/bin/env bash
set -euo pipefail

python prepare_manifest.py \
  --dataset-dir __LOCAL_WORKSPACE__/Project/FllumaOne/FllumaOne-100K \
  --output-dir data/50k \
  --scale 50k \
  --prompt-mode mixed \
  --sampling stratified-level
