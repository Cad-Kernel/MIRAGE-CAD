#!/usr/bin/env bash
set -euo pipefail

python generate_latent_prior.py \
  --model-name Qwen/Qwen2.5-Coder-1.5B \
  --adapter-dir outputs/qwen25_coder_1_5b_program_smoke500 \
  --alignment-checkpoint outputs/align_smoke500/best.pt \
  --prior-checkpoint outputs/prior_step_smoke500/best.pt \
  --retrieval-index outputs/align_smoke500/train_ir_index.npz \
  --input-jsonl data/smoke500/step_features_test.jsonl \
  --output-jsonl outputs/predictions_prior_step_smoke500.jsonl \
  --modality step \
  --retrieval-mode prior \
  --retrieval-top-k 3 \
  --candidate-pool 128 \
  --include-nearest-ir \
  --hide-target-text \
  --limit 100 \
  --bf16
