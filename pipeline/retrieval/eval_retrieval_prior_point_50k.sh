#!/usr/bin/env bash
set -euo pipefail

python evaluate_latent_retrieval.py \
  --alignment-checkpoint outputs/align_50k/best.pt \
  --prior-checkpoint outputs/prior_point_50k/best.pt \
  --retrieval-index outputs/50k_test_ir_index.npz \
  --test-jsonl data/50k/step_features_test.jsonl \
  --output-json outputs/eval_retrieval_prior_point_50k.json \
  --modality point \
  --candidate-pools 10 64 128 1024
