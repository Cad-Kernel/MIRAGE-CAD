#!/usr/bin/env bash
set -euo pipefail

python build_index.py \
  --checkpoint outputs/align_smoke500/best.pt \
  --jsonl data/smoke500/step_features_test.jsonl \
  --output outputs/smoke500_test_ir_index.npz \
  --index-modality ir \
  --batch-size 32
