#!/bin/bash
source __USER_HOME__/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src
export PYTHONPATH=.

for MOD in step point; do
  if [ "$MOD" = "step" ]; then
    IR_JSONL=outputs/lora_ir_5k/predicted_ir_test500_full_p1a.jsonl
  else
    IR_JSONL=outputs/lora_ir_5k/predicted_ir_point500_p1a.jsonl
  fi
  echo "=== starting $MOD $(date) ==="
  python scratch/gen_nbest_candidates.py \
    --modality $MOD \
    --ir-jsonl $IR_JSONL \
    --output-jsonl scratch/nbest_smoke10_${MOD}.jsonl \
    --limit 10 \
    --num-candidates 10 \
    > outputs/gen_nbest_smoke10_${MOD}.log 2>&1
  echo "=== finished $MOD $(date) exit=$? ==="
done
echo "ALL_DONE"
