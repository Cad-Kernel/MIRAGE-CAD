#!/bin/bash
source __USER_HOME__/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src
export PYTHONPATH=.

echo "=== starting step 100-sample $(date) ==="
python scratch/gen_nbest_candidates.py \
  --modality step \
  --ir-jsonl outputs/lora_ir_5k/predicted_ir_test500_full_p1a.jsonl \
  --output-jsonl scratch/nbest_100_step.jsonl \
  --limit 100 \
  --num-candidates 10 \
  > outputs/gen_nbest_100_step.log 2>&1
echo "=== finished step 100-sample $(date) exit=$? ==="
echo "ALL_DONE"
