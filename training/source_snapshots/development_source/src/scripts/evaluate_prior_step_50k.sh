#!/usr/bin/env bash
set -euo pipefail

python evaluate_programs.py \
  --predictions outputs/predictions_prior_step_50k.jsonl \
  --output-dir outputs/eval_prior_step_50k
