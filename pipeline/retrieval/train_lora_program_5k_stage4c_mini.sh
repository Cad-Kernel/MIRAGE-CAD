#!/usr/bin/env bash
set -euo pipefail

# Stage 4c-mini: a much gentler retry of the failed Stage 4c experiment.
# First attempt: epochs=0.5 (most conservative). If the quick-eval screen
# (scratch/eval_quick_stage4c.py against data/smoke5k/quick_eval_rareop_set.jsonl)
# looks healthy, a second run with epochs=1.0 can be tried; if 0.5 already
# regresses badly, do not continue this line at all.
#
# Frequent save/eval steps (every 25 steps, ~223 steps total at epochs=0.5)
# so multiple intermediate checkpoints are available for quick-eval
# screening, not just the final one.

python train_program_lora.py \
  --model-name Qwen/Qwen2.5-Coder-1.5B \
  --train-jsonl data/smoke5k/train_stage4c_mini.jsonl \
  --val-jsonl data/smoke5k/val.jsonl \
  --output-dir outputs/qwen25_coder_1_5b_program_5k_stage4c_mini \
  --init-adapter-dir outputs/qwen25_coder_1_5b_program_5k_stage4b \
  --target program \
  --modality step \
  --max-length 1536 \
  --epochs 0.5 \
  --per-device-train-batch-size 1 \
  --per-device-eval-batch-size 1 \
  --gradient-accumulation-steps 8 \
  --learning-rate 1e-5 \
  --eval-steps 25 \
  --save-steps 25 \
  --logging-steps 5 \
  --save-total-limit 6 \
  --lora-r 16 \
  --lora-alpha 32 \
  --bf16
