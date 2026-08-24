#!/bin/bash
# Phase 5 / Stage 4: LoRA-Code trained on ground-truth IR only.
#
# Same modality-reuse note as Stage 3 (see 06_train_lora_ir.sh): trained ONCE
# with --modality step, then reused for all four modalities at inference.
# This mirrors the validated 5K/production recipe (qwen25_coder_1_5b_program_5k
# -> qwen25_coder_1_5b_program_5k_stage4b was likewise step-only-trained and
# reused across all four modalities).
#
# eval/save-steps scaled up from the 5K wrapper's 100 (against ~625 steps/epoch
# at 5K's batch=1/grad-accum=8) to 500, since 25K has ~5x the steps/epoch.
#
# --load-in-4bit added (the 5K run did NOT use this): docs/Todo.md's own
# lesson from the 5K Stage-4 run was that full-precision LoRA at this length/
# scale ran into a VRAM boundary (100% GPU utilization but only 30-40W power
# draw -- classic memory-bound thrashing, not compute-bound) and took ~5 hours
# for 625 steps on 5K rows. At 5x the data, the same full-precision setup
# would likely take a full day or more; 4-bit avoids that risk. If VRAM is
# not actually the bottleneck on your machine, you can drop --load-in-4bit,
# but the project's own prior experience argues for defaulting to it here.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

python train_program_lora.py \
  --model-name Qwen/Qwen2.5-Coder-1.5B \
  --train-jsonl data/25k/train.jsonl --val-jsonl data/25k/val.jsonl \
  --output-dir outputs/qwen25_coder_1_5b_program_25k \
  --target program --modality step --max-length 1536 \
  --epochs 1 --per-device-train-batch-size 1 --per-device-eval-batch-size 1 \
  --gradient-accumulation-steps 8 --learning-rate 2e-4 \
  --eval-steps 500 --save-steps 500 --logging-steps 20 --save-total-limit 2 \
  --lora-r 16 --lora-alpha 32 --load-in-4bit --bf16

echo "=== Checkpoint: outputs/qwen25_coder_1_5b_program_25k/ ==="
