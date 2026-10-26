#!/bin/bash
source __USER_HOME__/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src
export PYTHONPATH=.

echo "=== starting point 100-sample $(date) ==="
python scratch/gen_nbest_candidates.py \
  --modality point \
  --ir-jsonl outputs/lora_ir_5k/predicted_ir_point500_p1a.jsonl \
  --output-jsonl scratch/nbest_100_point.jsonl \
  --limit 100 \
  --num-candidates 10 \
  > outputs/gen_nbest_100_point.log 2>&1
echo "=== finished point 100-sample $(date) exit=$? ==="
echo "ALL_DONE"
