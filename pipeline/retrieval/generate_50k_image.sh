#!/usr/bin/env bash
set -euo pipefail

python generate_programs.py \
  --model-name Qwen/Qwen2.5-Coder-1.5B \
  --adapter-dir outputs/qwen25_coder_1_5b_program_50k \
  --input-jsonl data/50k/test.jsonl \
  --output-jsonl outputs/predictions_50k_image_query.jsonl \
  --target program \
  --max-new-tokens 1024 \
  --retrieval-checkpoint outputs/align_50k/best.pt \
  --retrieval-index outputs/align_50k/train_ir_index.npz \
  --retrieval-top-k 3 \
  --retrieval-query-modality image \
  --hide-target-text \
  --bf16
