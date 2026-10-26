#!/usr/bin/env bash
set -euo pipefail

python evaluate_programs.py \
  --predictions outputs/predictions_50k_point_query.jsonl \
  --output-dir outputs/eval_50k_point_query
