#!/usr/bin/env bash
set -euo pipefail

python evaluate_programs.py \
  --predictions outputs/predictions_50k_image_query.jsonl \
  --output-dir outputs/eval_50k_image_query
