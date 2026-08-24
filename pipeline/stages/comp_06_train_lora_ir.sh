#!/bin/bash
# Compositional-split pipeline / Stage 3 + Stage 3b, back-to-back: since the
# mixed multimodal-prefix recipe (Stage 3b) is already the established,
# validated recommended method (docs/MIRAGE-CAD_experiment_results.md S8.13),
# there is no need to replay the original discovery arc (STEP-only first,
# observe regression, then fix) on this new split -- we already know the
# answer. Stage 3 (STEP-only, full comp-train set, matches 06_train_lora_ir.sh's
# hyperparameters exactly) is still run first because Stage 3b is defined as a
# continuation of it, not a substitute training recipe.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# --- Stage 3: STEP-only, full new training set (23,577 rows) ---
# Skip if already complete (crash recovery) -- this stage alone can take
# several hours, so re-running it unnecessarily after a Stage-3b-only crash
# would waste that entire time.
if [ -f outputs/lora_ir_25k_comp/soft_prefix_training_report.json ]; then
  echo "[$(date)] Stage 3 (STEP-only) already complete -- skipping."
else
  python -m gen_scripts.train_soft_prefix_ir \
    --model-name Qwen/Qwen2.5-Coder-1.5B \
    --alignment-checkpoint outputs/align_25k_comp/best.pt \
    --prior-checkpoint outputs/prior_step_25k_comp/best.pt \
    --modality step \
    --train-jsonl data/25k_comp/train.jsonl --val-jsonl data/25k_comp/val.jsonl \
    --output-dir outputs/lora_ir_25k_comp \
    --prefix-len 4 --load-in-4bit --bf16 \
    --per-device-train-batch-size 1 --gradient-accumulation-steps 16 \
    --epochs 3 --learning-rate 2e-4 --max-length 1536 --lora-r 8

  echo "=== Checkpoint: outputs/lora_ir_25k_comp/ (Stage 3, STEP-only) ==="
fi

# --- Stage 3b: mixed 4-modality continuation, same recipe as
#     06b_train_lora_ir_stage3b.sh (2000 rows/modality, 1 epoch, lr=1e-5) ---
if [ -f outputs/lora_ir_25k_comp_stage3b/soft_prefix_training_report.json ]; then
  echo "[$(date)] Stage 3b (mixed continuation) already complete -- skipping."
else
  python -m gen_scripts.train_soft_prefix_ir \
    --model-name Qwen/Qwen2.5-Coder-1.5B \
    --alignment-checkpoint outputs/align_25k_comp/best.pt \
    --modality-prior step:outputs/prior_step_25k_comp/best.pt \
    --modality-prior point:outputs/prior_point_25k_comp/best.pt \
    --modality-prior text:outputs/prior_text_25k_comp/best.pt \
    --modality-prior image:outputs/prior_image_25k_comp/best.pt \
    --init-lora-ir-dir outputs/lora_ir_25k_comp \
    --train-jsonl data/25k_comp/train.jsonl --val-jsonl data/25k_comp/val.jsonl \
    --limit-train 2000 --limit-val 200 \
    --output-dir outputs/lora_ir_25k_comp_stage3b \
    --prefix-len 4 --load-in-4bit --bf16 \
    --per-device-train-batch-size 1 --gradient-accumulation-steps 16 \
    --epochs 1 --learning-rate 1e-5 --max-length 1536 \
    --eval-steps 50 --save-steps 50 --logging-steps 10 --save-total-limit 2

  echo "=== Checkpoint: outputs/lora_ir_25k_comp_stage3b/ (Stage 3b, the compositional-split model to evaluate) ==="
fi
