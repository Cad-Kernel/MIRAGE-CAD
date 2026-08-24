#!/bin/bash
# Wrapper for audit_5k_vs_25k_zirhat_gap.py (docs/MIRAGE-CAD_experiment_results.md
# SS8, follow-up to SS8.2's confirmed point/text regression). No training, no
# LoRA-IR/LoRA-Code involved -- Stage 1/2 forward passes only, should finish
# in a few minutes (500 samples x 3 modalities x 2 scales of small-encoder
# forward passes, no LLM decoding).
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

python training_25k/scripts/audit_5k_vs_25k_zirhat_gap.py
