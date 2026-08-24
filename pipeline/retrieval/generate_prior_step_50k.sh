#!/usr/bin/env bash
set -euo pipefail

python generate_latent_prior.py \
  --model-name Qwen/Qwen2.5-Coder-1.5B \
  --adapter-dir outputs/qwen25_coder_1_5b_program_50k \
  --alignment-checkpoint outputs/align_50k/best.pt \
  --prior-checkpoint outputs/prior_step_50k/best.pt \
  --retrieval-index outputs/align_50k/train_ir_index.npz \
  --input-jsonl data/50k/step_features_test.jsonl \
  --output-jsonl outputs/predictions_prior_step_50k.jsonl \
  --modality step \
  --retrieval-mode prior \
  --retrieval-top-k 3 \
  --candidate-pool 128 \
  --include-nearest-ir \
  --hide-target-text \
  --bf16
