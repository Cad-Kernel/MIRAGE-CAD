#!/usr/bin/env bash
set -euo pipefail

python generate_programs.py \
  --model-name Qwen/Qwen2.5-Coder-1.5B \
  --adapter-dir outputs/qwen25_coder_1_5b_program_smoke500 \
  --input-jsonl data/smoke500/test.jsonl \
  --output-jsonl outputs/predictions_smoke500_quick.jsonl \
  --target program \
  --limit 50 \
  --max-new-tokens 1024 \
  --retrieval-checkpoint outputs/align_smoke500/best.pt \
  --retrieval-index outputs/align_smoke500/train_ir_index.npz \
  --retrieval-top-k 3 \
  --bf16
