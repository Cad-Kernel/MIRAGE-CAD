#!/bin/bash
# Phase 7 / Table 1: retrieval quality (direct vs prior R@1/R@5/R@10/MRR@10),
# all four modalities, self-retrieval against the test index built in step 04.
#
# WARNING (a documented past mistake, docs/Todo.md): --retrieval-index MUST be
# built on the SAME split as --test-jsonl (self-retrieval) -- using the TRAIN
# index here would make R@k collapse to ~0, since the true match for each
# query would never be in the candidate pool. This script correctly uses
# outputs/align_25k/test_ir_index.npz (built from step_features_test.jsonl in
# step 04), not train_ir_index.npz. Do not "fix" this to use the train index.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

for m in step point text image; do
  echo "=== retrieval eval: $m ==="
  python evaluate_latent_retrieval.py \
    --alignment-checkpoint outputs/align_25k/best.pt \
    --prior-checkpoint outputs/prior_${m}_25k/best.pt \
    --retrieval-index outputs/align_25k/test_ir_index.npz \
    --test-jsonl data/25k/test.jsonl \
    --output-json outputs/eval_retrieval_prior_${m}_25k.json \
    --modality $m \
    --corpus-jsonl data/25k/train.jsonl
done

echo "=== Wrote outputs/eval_retrieval_prior_{step,point,text,image}_25k.json ==="
