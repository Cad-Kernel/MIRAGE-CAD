#!/bin/bash
# Frozen CAG runner for the A1E/B2P exact-match multi-seed comparison.
#
# This wrapper is deliberately independent of the historical
# 44_seeds_a1e_b2p.sh orchestration. It may KEEP an arm that is already
# complete and verified, TRAIN an absent arm, and REFUSE a partial arm.
# It never silently resumes or skips partial output.
set -euo pipefail

source __USER_HOME__/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

source training_25k/_guard_fresh.sh \
  training_25k/cag_run_frozen_a1e_b2p_seed.sh \
  scratch/cag_a1e_b2p_actuals.py \
  gen_scripts/train_soft_prefix_ir.py \
  training_25k/scripts/gen_b1_direct_latent.py \
  training_25k/scripts/gen_code_from_predicted_ir.py \
  train_program_lora.py

SEED=${SEED:?set SEED, e.g. SEED=1 or SEED=2. Seed 42 is the existing reference and is refused.}
MODALITY=${MODALITY:-step}
LIMIT=${LIMIT:-500}
BATCH=${BATCH:-16}
ACCUM=${ACCUM:-8}
EPOCHS=${EPOCHS:-1}
GEN=${GEN:-outputs/e1_observation_bypass}
BASE_CODE=${BASE_CODE:-outputs/qwen25_coder_1_5b_program_25k}

if [ "$EPOCHS" != "1" ]; then
  echo "CAG frozen protocol requires EPOCHS=1; got $EPOCHS" >&2
  exit 1
fi

A_OUT="outputs/b1_1epoch_${MODALITY}_s${SEED}"
B_OUT="outputs/b2_pred_matched_${MODALITY}_s${SEED}"
A_PRED="$GEN/gen_code_${MODALITY}_A1E_s${SEED}.jsonl"
B_PRED="$GEN/gen_code_${MODALITY}_B2P_s${SEED}.jsonl"
MIX="data/25k/train_b2pred_${MODALITY}.jsonl"

rows() {
  [ -f "$1" ] || { echo 0; return; }
  wc -l "$1" | awk '{print $1}'
}

complete_a1e_dir() {
  [ -f "$A_OUT/adapter_model.safetensors" ] && [ -f "$A_OUT/soft_prefix.pt" ]
}

complete_b2p_dir() {
  [ -f "$B_OUT/adapter_model.safetensors" ]
}

complete_pred() {
  [ -f "$1" ] && [ "$(rows "$1")" -eq "$LIMIT" ]
}

partial_dir_or_pred() {
  local arm="$1" out="$2" pred="$3"
  if [ -e "$out" ]; then
    case "$arm" in
      A1E) complete_a1e_dir || return 0 ;;
      B2P) complete_b2p_dir || return 0 ;;
    esac
  fi
  if [ -f "$pred" ] && [ "$(rows "$pred")" -ne "$LIMIT" ]; then
    return 0
  fi
  return 1
}

python scratch/cag_a1e_b2p_actuals.py preflight \
  --seed "$SEED" \
  --modality "$MODALITY" \
  --limit "$LIMIT" \
  --batch-size "$BATCH" \
  --accum "$ACCUM" \
  --epochs "$EPOCHS" \
  --gen-dir "$GEN" \
  --allow-existing

if partial_dir_or_pred A1E "$A_OUT" "$A_PRED"; then
  echo "A1E seed $SEED is partial. Archive/remove it before running frozen protocol." >&2
  exit 1
fi
if partial_dir_or_pred B2P "$B_OUT" "$B_PRED"; then
  echo "B2P seed $SEED is partial. Archive/remove it before running frozen protocol." >&2
  exit 1
fi

echo
echo "=== CAG frozen protocol accepted: seed $SEED ==="
echo "A1E @ 3125 updates, B2P @ 3125 updates, final checkpoint, same 500 STEP slice, no repair."
echo "Existing complete arms may be kept; absent arms will be trained cleanly."
echo

if complete_a1e_dir; then
  echo "=== keep A1E seed $SEED training ($A_OUT complete) ==="
elif [ -e "$A_OUT" ]; then
  echo "A1E output exists but is incomplete: $A_OUT" >&2
  exit 1
else
  echo "=== train A1E seed $SEED: latent -> code, 1 epoch ==="
  python -m gen_scripts.train_soft_prefix_ir \
    --model-name Qwen/Qwen2.5-Coder-1.5B \
    --alignment-checkpoint outputs/align_25k/best.pt \
    --prior-checkpoint "outputs/prior_${MODALITY}_25k/best.pt" \
    --modality "$MODALITY" --target program \
    --train-jsonl data/25k/train.jsonl --val-jsonl data/25k/val.jsonl \
    --output-dir "$A_OUT" \
    --prefix-len 4 --load-in-4bit --bf16 \
    --per-device-train-batch-size 1 --gradient-accumulation-steps "$ACCUM" \
    --epochs "$EPOCHS" --learning-rate 2e-4 --max-length 1536 \
    --lora-r 16 --lora-alpha 32 --seed "$SEED" \
    --eval-steps 500 --save-steps 500 2>&1 | tee -a "$A_OUT.train.log"
fi

if complete_pred "$A_PRED"; then
  echo "=== keep A1E seed $SEED prediction ($A_PRED complete) ==="
elif [ -f "$A_PRED" ]; then
  echo "A1E prediction exists but is incomplete: $A_PRED ($(rows "$A_PRED")/$LIMIT)" >&2
  exit 1
else
  echo "=== generate A1E seed $SEED predictions ==="
  python training_25k/scripts/gen_b1_direct_latent.py \
    --modality "$MODALITY" \
    --alignment-checkpoint outputs/align_25k/best.pt \
    --prior-checkpoint "outputs/prior_${MODALITY}_25k/best.pt" \
    --b1-dir "$A_OUT" \
    --input-jsonl data/25k/test.jsonl --limit "$LIMIT" \
    --output-jsonl "$A_PRED" \
    --max-length 1536 --max-new-tokens 1536 --batch-size "$BATCH"
fi

if complete_b2p_dir; then
  echo "=== keep B2P seed $SEED training ($B_OUT complete) ==="
elif [ -e "$B_OUT" ]; then
  echo "B2P output exists but is incomplete: $B_OUT" >&2
  exit 1
else
  echo "=== train B2P seed $SEED: predicted plan -> code, 1 epoch ==="
  python train_program_lora.py \
    --model-name Qwen/Qwen2.5-Coder-1.5B \
    --init-adapter-dir "$BASE_CODE" \
    --target program --modality "$MODALITY" --max-length 1536 \
    --train-jsonl "$MIX" --val-jsonl data/25k/val.jsonl \
    --output-dir "$B_OUT" \
    --epochs "$EPOCHS" --per-device-train-batch-size 1 \
    --gradient-accumulation-steps "$ACCUM" --learning-rate 2e-4 \
    --lora-r 16 --lora-alpha 32 --load-in-4bit --bf16 \
    --seed "$SEED" 2>&1 | tee -a "$B_OUT.train.log"
fi

if complete_pred "$B_PRED"; then
  echo "=== keep B2P seed $SEED prediction ($B_PRED complete) ==="
elif [ -f "$B_PRED" ]; then
  echo "B2P prediction exists but is incomplete: $B_PRED ($(rows "$B_PRED")/$LIMIT)" >&2
  exit 1
else
  echo "=== generate B2P seed $SEED predictions ==="
  python training_25k/scripts/gen_code_from_predicted_ir.py \
    --modality "$MODALITY" \
    --lora-code-dir "$B_OUT" \
    --ir-jsonl "$GEN/pred_ir_${MODALITY}_present.jsonl" \
    --input-jsonl data/25k/test.jsonl --limit "$LIMIT" \
    --output-jsonl "$B_PRED" \
    --max-length 1536 --max-new-tokens 1536 --batch-size "$BATCH"
fi

python scratch/cag_a1e_b2p_actuals.py post \
  --seed "$SEED" \
  --modality "$MODALITY" \
  --limit "$LIMIT" \
  --batch-size "$BATCH" \
  --accum "$ACCUM" \
  --epochs "$EPOCHS" \
  --gen-dir "$GEN" \
  --allow-existing

echo
echo "=== CAG frozen seed $SEED complete ==="
echo "Next: run gate evaluation, geometry scoring, then aggregate across seeds."
