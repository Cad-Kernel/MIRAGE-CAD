#!/usr/bin/env bash
# Run V2-Lite prior_rag pipeline on step modality, 500-sample test.
set -euo pipefail
python -m lite_scripts.generate \
  --pipeline prior_rag \
  --modality step \
  --adapter-dir outputs/lora_program_500 \
  --alignment-checkpoint outputs/alignment_500/best.pt \
  --prior-checkpoint outputs/prior_step_500/best.pt \
  --retrieval-index outputs/index_step_500/index.npz \
  --input-jsonl data/test_500.jsonl \
  --output-jsonl outputs/lite_step_500/prior_rag.jsonl \
  --retrieval-mode prior \
  --retrieval-top-k 3 \
  --bf16
