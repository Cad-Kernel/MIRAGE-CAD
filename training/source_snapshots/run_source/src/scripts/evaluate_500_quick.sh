#!/usr/bin/env bash
set -euo pipefail

python evaluate_programs.py \
  --predictions outputs/predictions_smoke500_quick.jsonl \
  --output-dir outputs/eval_smoke500_quick
