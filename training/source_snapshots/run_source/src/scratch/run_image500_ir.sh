#!/bin/bash
source __USER_HOME__/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src
export PYTHONPATH=.
python scratch/gen_predicted_ir_500.py --modality image --prior-checkpoint outputs/prior_image_5k/best.pt --output-jsonl outputs/lora_ir_5k/predicted_ir_image500.jsonl > outputs/gen_predicted_ir_image500.log 2>&1
