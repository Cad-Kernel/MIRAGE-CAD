#!/usr/bin/env bash
set -euo pipefail

python evaluate_latent_retrieval.py \
  --alignment-checkpoint outputs/align_smoke500/best.pt \
  --prior-checkpoint outputs/prior_point_smoke500/best.pt \
  --retrieval-index outputs/smoke500_test_ir_index.npz \
  --test-jsonl data/smoke500/step_features_test.jsonl \
  --output-json outputs/eval_retrieval_prior_point_smoke500.json \
  --modality point \
  --candidate-pools 10 64 128
