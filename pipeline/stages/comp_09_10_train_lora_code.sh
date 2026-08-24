#!/bin/bash
# Compositional-split pipeline / Stage 4 + Stage 4b, back-to-back. Same
# hyperparameters as 09_train_lora_code_stage4.sh + 10_train_lora_code_stage4b.sh,
# only data/output paths changed to the _comp variants.
#
# CRASH RECOVERY: unlike the other stages in this pipeline, train_program_lora.py
# writes periodic checkpoint-N folders (save_steps=500 for Stage 4, 100 for
# Stage 4b) and genuinely supports --resume-from-checkpoint, so this script
# auto-detects the latest checkpoint-N in each output dir and resumes from it
# if the stage's final training_report.json is missing but a checkpoint exists.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

latest_checkpoint() {
  # Prints the highest-numbered checkpoint-N dir under $1, or nothing if none.
  # Uses bash's own globbing (nullglob) instead of `ls`, so a no-match doesn't
  # produce a nonzero exit status that `set -e` would treat as a script
  # failure -- ls -d nonexistent-glob/* exits nonzero even with stderr
  # silenced, which previously killed this whole script the moment it was
  # asked to check for a checkpoint before Stage 4 had ever run once.
  shopt -s nullglob
  local matches=("$1"/checkpoint-*)
  shopt -u nullglob
  if [ "${#matches[@]}" -eq 0 ]; then
    return 0
  fi
  printf '%s\n' "${matches[@]}" | sed -E 's/.*checkpoint-([0-9]+)$/\1 &/' | sort -n | tail -n1 | cut -d' ' -f2-
}

# --- Stage 4: LoRA-Code on ground-truth IR only ---
if [ -f outputs/qwen25_coder_1_5b_program_25k_comp/training_report.json ]; then
  echo "[$(date)] Stage 4 (GT-IR LoRA-Code) already complete -- skipping."
else
  RESUME_ARG=()
  CKPT=$(latest_checkpoint outputs/qwen25_coder_1_5b_program_25k_comp)
  if [ -n "$CKPT" ]; then
    echo "[$(date)] Found Stage 4 checkpoint $CKPT -- resuming from it."
    RESUME_ARG=(--resume-from-checkpoint "$CKPT")
  fi
  python train_program_lora.py \
    --model-name Qwen/Qwen2.5-Coder-1.5B \
    --train-jsonl data/25k_comp/train.jsonl --val-jsonl data/25k_comp/val.jsonl \
    --output-dir outputs/qwen25_coder_1_5b_program_25k_comp \
    --target program --modality step --max-length 1536 \
    --epochs 1 --per-device-train-batch-size 1 --per-device-eval-batch-size 1 \
    --gradient-accumulation-steps 8 --learning-rate 2e-4 \
    --eval-steps 500 --save-steps 500 --logging-steps 20 --save-total-limit 2 \
    --lora-r 16 --lora-alpha 32 --load-in-4bit --bf16 \
    "${RESUME_ARG[@]}"

  echo "=== Checkpoint: outputs/qwen25_coder_1_5b_program_25k_comp/ ==="
fi

# --- Stage 4b: continue-train on the 70/30 GT/predicted mix ---
if [ -f outputs/qwen25_coder_1_5b_program_25k_comp_stage4b/training_report.json ]; then
  echo "[$(date)] Stage 4b (mixed continuation) already complete -- skipping."
else
  RESUME_ARG=()
  CKPT=$(latest_checkpoint outputs/qwen25_coder_1_5b_program_25k_comp_stage4b)
  if [ -n "$CKPT" ]; then
    echo "[$(date)] Found Stage 4b checkpoint $CKPT -- resuming from it."
    RESUME_ARG=(--resume-from-checkpoint "$CKPT")
  fi
  python train_program_lora.py \
    --model-name Qwen/Qwen2.5-Coder-1.5B \
    --train-jsonl data/25k_comp/train_stage4b_mix.jsonl --val-jsonl data/25k_comp/val.jsonl \
    --output-dir outputs/qwen25_coder_1_5b_program_25k_comp_stage4b \
    --init-adapter-dir outputs/qwen25_coder_1_5b_program_25k_comp \
    --target program --modality step --max-length 1536 \
    --epochs 3 --per-device-train-batch-size 1 --per-device-eval-batch-size 1 \
    --gradient-accumulation-steps 8 --learning-rate 5e-5 \
    --eval-steps 100 --save-steps 100 --logging-steps 10 --save-total-limit 2 \
    --lora-r 16 --lora-alpha 32 --load-in-4bit --bf16 \
    "${RESUME_ARG[@]}"

  echo "=== Checkpoint: outputs/qwen25_coder_1_5b_program_25k_comp_stage4b/ (THE compositional-split inference checkpoint) ==="
fi
