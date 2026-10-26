#!/usr/bin/env bash
# Run all 5 pipeline modes on step modality, 500-sample test.
set -euo pipefail

ALIGNMENT=outputs/align_smoke500/best.pt
PRIOR=outputs/prior_step_smoke500/best.pt
INDEX=outputs/align_smoke500/train_ir_index.npz
LORA_IR=outputs/lora_ir_500
LORA_CODE=outputs/qwen25_coder_1_5b_program_smoke500
TEST_JSONL=data/smoke500/test.jsonl
OUT=outputs/gen_step_500

# Pipeline A: direct_rag
python -m gen_scripts.run_miragecad \
  --pipeline direct_rag \
  --modality step \
  --alignment-checkpoint "$ALIGNMENT" \
  --prior-checkpoint "$PRIOR" \
  --retrieval-index "$INDEX" \
  --lora-code-dir "$LORA_CODE" \
  --input-jsonl "$TEST_JSONL" \
  --output-jsonl "$OUT/direct_rag.jsonl" \
  --retrieval-mode direct \
  --bf16

# Pipeline B: prior_rag
python -m gen_scripts.run_miragecad \
  --pipeline prior_rag \
  --modality step \
  --alignment-checkpoint "$ALIGNMENT" \
  --prior-checkpoint "$PRIOR" \
  --retrieval-index "$INDEX" \
  --lora-code-dir "$LORA_CODE" \
  --input-jsonl "$TEST_JSONL" \
  --output-jsonl "$OUT/prior_rag.jsonl" \
  --retrieval-mode prior \
  --bf16

# Pipeline C: gen_ir (no retrieval)
python -m gen_scripts.run_miragecad \
  --pipeline gen_ir \
  --modality step \
  --alignment-checkpoint "$ALIGNMENT" \
  --prior-checkpoint "$PRIOR" \
  --lora-ir-dir "$LORA_IR" \
  --lora-code-dir "$LORA_CODE" \
  --input-jsonl "$TEST_JSONL" \
  --output-jsonl "$OUT/gen_ir.jsonl" \
  --bf16

# Pipeline D: gen_ir_retrieval
python -m gen_scripts.run_miragecad \
  --pipeline gen_ir_retrieval \
  --modality step \
  --alignment-checkpoint "$ALIGNMENT" \
  --prior-checkpoint "$PRIOR" \
  --retrieval-index "$INDEX" \
  --lora-ir-dir "$LORA_IR" \
  --lora-code-dir "$LORA_CODE" \
  --input-jsonl "$TEST_JSONL" \
  --output-jsonl "$OUT/gen_ir_retrieval.jsonl" \
  --retrieval-mode prior \
  --bf16

# Pipeline E: full (N=5 candidates, execution selection — main paper table setting)
python -m gen_scripts.run_miragecad \
  --pipeline full \
  --modality step \
  --alignment-checkpoint "$ALIGNMENT" \
  --prior-checkpoint "$PRIOR" \
  --retrieval-index "$INDEX" \
  --lora-ir-dir "$LORA_IR" \
  --lora-code-dir "$LORA_CODE" \
  --input-jsonl "$TEST_JSONL" \
  --output-jsonl "$OUT/full.jsonl" \
  --retrieval-mode prior \
  --num-candidates 5 \
  --execution-selection \
  --temperature 0.8 \
  --bf16
