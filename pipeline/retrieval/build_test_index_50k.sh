#!/usr/bin/env bash
set -euo pipefail

python build_index.py \
  --checkpoint outputs/align_50k/best.pt \
  --jsonl data/50k/step_features_test.jsonl \
  --output outputs/50k_test_ir_index.npz \
  --index-modality ir \
  --batch-size 32
