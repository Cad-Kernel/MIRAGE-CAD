#!/bin/bash
# Phase 4 / Stage 3b: continue-train the Stage 3 LoRA-IR (+ soft prefix) on a
# MIX of all four modalities' z_ir_hat (same target reference IR each time),
# instead of STEP-only. Motivated by docs/MIRAGE-CAD_experiment_results.md
# SS8.10: two checks (z_ir_hat-vs-STEP direction, z_ir_hat-vs-true-IR-embedding
# accuracy) both REJECTED an upstream (Stage 1/2) latent-drift explanation for
# the confirmed 25K point/text execution regression (SS8.2) -- both got
# BETTER, not worse, at 25K. But predicted_ir TEXT quality (ir_cosine, SS8.4)
# dropped for point/text/image while staying flat for STEP, which points at
# the shared LoRA-IR DECODER (trained on STEP's z_ir_hat only, both at 5K and
# 25K by design) having sharpened specifically around STEP's characteristics
# at 25K scale, at the other modalities' expense. This run exposes LoRA-IR to
# all four modalities' z_ir_hat during training to test whether that fixes it.
#
# LOW-RISK BY DESIGN, same philosophy as Stage 4b:
#   - Continues from the existing outputs/lora_ir_25k checkpoint via
#     --init-lora-ir-dir (does NOT discard it -- if this run doesn't clear
#     the validation gate below, outputs/lora_ir_25k remains the recommended
#     checkpoint, nothing is lost).
#   - Short (1 epoch, --limit-train/--limit-val subsample per modality --
#     NOT the full 25K train set x 4 modalities, which would be an expensive,
#     unvalidated-scale experiment) and low learning rate (1e-5, vs Stage 3's
#     original 2e-4) to avoid the Stage 4c-style catastrophic-forgetting
#     failure mode this project has already hit once (docs/Todo.md).
#
# DO NOT adopt this checkpoint as "the" LoRA-IR without first passing the
# validation gate in quick_eval_stage3b_all4_100.sh: point/text must show a
# real improvement AND STEP/image must not regress. If it fails the gate,
# outputs/lora_ir_25k (STEP-only) remains the recommended checkpoint.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

python -m gen_scripts.train_soft_prefix_ir \
  --model-name Qwen/Qwen2.5-Coder-1.5B \
  --alignment-checkpoint outputs/align_25k/best.pt \
  --modality-prior step:outputs/prior_step_25k/best.pt \
  --modality-prior point:outputs/prior_point_25k/best.pt \
  --modality-prior text:outputs/prior_text_25k/best.pt \
  --modality-prior image:outputs/prior_image_25k/best.pt \
  --init-lora-ir-dir outputs/lora_ir_25k \
  --train-jsonl data/25k/train.jsonl --val-jsonl data/25k/val.jsonl \
  --limit-train 2000 --limit-val 200 \
  --output-dir outputs/lora_ir_25k_stage3b \
  --prefix-len 4 --load-in-4bit --bf16 \
  --per-device-train-batch-size 1 --gradient-accumulation-steps 16 \
  --epochs 1 --learning-rate 1e-5 --max-length 1536 \
  --eval-steps 50 --save-steps 50 --logging-steps 10 --save-total-limit 2

echo "=== Checkpoint: outputs/lora_ir_25k_stage3b/ (DO NOT use downstream until it clears the validation gate -- see quick_eval_stage3b_all4_100.sh) ==="
