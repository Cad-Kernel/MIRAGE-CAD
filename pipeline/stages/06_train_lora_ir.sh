#!/bin/bash
# Phase 4 / Stage 3: LoRA-IR (soft-prefix construction-plan generation).
#
# IMPORTANT: trained ONCE using the step-modality prior, then reused directly
# for ALL FOUR modalities at inference (text/image/point/step). This exactly
# matches the validated 5K precedent (outputs/lora_ir_5k was trained with
# --modality step only, yet used unmodified for all four modalities' 500-
# sample formal results, docs/STATUS.md). This works because z_ir_hat lives
# in the SAME shared, modality-agnostic latent space for every modality by
# construction (the whole point of Stage 1's star-topology alignment) --
# LoRA-IR only ever sees z_ir_hat + a soft prefix, never the raw modality
# signal, so which modality's prior produced it during training is not a
# correctness requirement, only a convention already validated at 5K scale.
# Do not train four separate LoRA-IR checkpoints; that would be new,
# unvalidated territory for this project.
#
# PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True added after a real OOM crash
# at step 2872/4689 (~61%, ~6h in) on the first 25K attempt -- loss was healthy
# (~0.10-0.11, steadily decreasing) right up to the crash, so this was a VRAM
# allocator issue, not a training problem: most likely fragmentation built up
# over thousands of variable-length (--per-device-train-batch-size 1, so
# per-step memory depends on that step's specific sample length) forward
# passes over ~6 hours, possibly compounded by hitting a longer-than-usual
# sequence for the first time at that step. This flag lets PyTorch's CUDA
# allocator use expandable memory segments instead of fixed-size blocks,
# which is the standard mitigation for exactly this "trains fine for hours,
# then suddenly OOMs" pattern. If it recurs even with this flag, the next
# thing to try is lowering --max-length (currently 1536) for more headroom,
# not just rerunning again.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

python -m gen_scripts.train_soft_prefix_ir \
  --model-name Qwen/Qwen2.5-Coder-1.5B \
  --alignment-checkpoint outputs/align_25k/best.pt \
  --prior-checkpoint outputs/prior_step_25k/best.pt \
  --modality step \
  --train-jsonl data/25k/train.jsonl --val-jsonl data/25k/val.jsonl \
  --output-dir outputs/lora_ir_25k \
  --prefix-len 4 --load-in-4bit --bf16 \
  --per-device-train-batch-size 1 --gradient-accumulation-steps 16 \
  --epochs 3 --learning-rate 2e-4 --max-length 1536 --lora-r 8

echo "=== Checkpoint: outputs/lora_ir_25k/ (adapter + soft_prefix.pt + tokenizer + soft_prefix_training_report.json) ==="
