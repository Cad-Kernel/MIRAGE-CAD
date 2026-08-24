#!/bin/bash
# Phase 6 / Stage 4b formal eval: generate program.py from P1a-repaired
# predicted_ir, STEP query, using the recommended Stage 4b checkpoint.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

python training_25k/scripts/gen_code_from_predicted_ir.py \
  --modality step \
  --lora-code-dir outputs/qwen25_coder_1_5b_program_25k_stage4b \
  --ir-jsonl outputs/lora_ir_25k/predicted_ir_test_step_p1a.jsonl \
  --input-jsonl data/25k/test.jsonl \
  --output-jsonl outputs/qwen25_coder_1_5b_program_25k_stage4b/gen_test_step.jsonl \
  --max-length 1536 --max-new-tokens 1536

echo "=== Wrote outputs/qwen25_coder_1_5b_program_25k_stage4b/gen_test_step.jsonl ==="
