#!/bin/bash
# Phase 7 / Table 3 (text-level half): syntax validity, defines-part rate,
# Op-F1/LCS/count-error, source similarity -- from the repaired generated
# code, no kernel execution (that's step 15's job; this is the cheap,
# torch-only companion metric set for the same Table 3 columns).
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

for m in step point text image; do
  echo "=== program-level eval: $m ==="
  python evaluate_programs.py \
    --predictions outputs/qwen25_coder_1_5b_program_25k_stage4b/gen_test_${m}_repaired_p0.jsonl \
    --output-dir outputs/qwen25_coder_1_5b_program_25k_stage4b/eval_${m}_25k
done

echo "=== Wrote outputs/qwen25_coder_1_5b_program_25k_stage4b/eval_{step,point,text,image}_25k/{evaluation_rows.jsonl,evaluation_summary.json} ==="
