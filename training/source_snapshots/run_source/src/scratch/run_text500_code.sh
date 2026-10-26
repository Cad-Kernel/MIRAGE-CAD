#!/bin/bash
source __USER_HOME__/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src
export PYTHONPATH=.
python scratch/gen_code_500_from_predicted_ir.py --modality text --ir-jsonl outputs/lora_ir_5k/predicted_ir_text500_p1a.jsonl --output-jsonl outputs/qwen25_coder_1_5b_program_5k_stage4b/gen_text500_from_predicted_ir.jsonl > outputs/gen_code_text500.log 2>&1
