#!/usr/bin/env bash
# Stage 4b: generate predicted_ir for train split ONLY.
# Do NOT run on val or test — this would cause data leakage.
set -euo pipefail
python -m gen_scripts.generate_predicted_ir \
  --model-name Qwen/Qwen2.5-Coder-1.5B \
  --lora-ir-dir outputs/lora_ir_500 \
  --alignment-checkpoint outputs/align_smoke500/best.pt \
  --prior-checkpoint outputs/prior_step_smoke500/best.pt \
  --modality step \
  --input-jsonl data/smoke500/train.jsonl \
  --output-jsonl outputs/predicted_ir_train_500.jsonl \
  --max-new-tokens 512 \
  --bf16
