#!/usr/bin/env bash
# Evaluate IR quality for gen_ir pipeline on 500-sample test.
set -euo pipefail
python -m gen_scripts.evaluate_ir_quality \
  --predicted-jsonl outputs/gen_step_500/gen_ir.jsonl \
  --alignment-checkpoint outputs/align_smoke500/best.pt \
  --output-json outputs/gen_step_500/ir_quality_500.json
