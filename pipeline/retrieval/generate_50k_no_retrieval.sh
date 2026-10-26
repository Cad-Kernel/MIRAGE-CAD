#!/usr/bin/env bash
set -euo pipefail

python generate_programs.py \
  --model-name Qwen/Qwen2.5-Coder-1.5B \
  --adapter-dir outputs/qwen25_coder_1_5b_program_50k \
  --input-jsonl data/50k/test.jsonl \
  --output-jsonl outputs/predictions_50k_no_retrieval.jsonl \
  --target program \
  --max-new-tokens 1024 \
  --bf16
