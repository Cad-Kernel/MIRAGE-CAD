#!/bin/bash
# Review/03 frozen runner: B0 vs B2 full-stack multi-seed replication.
#
# Scope:
#   B0: independently retrain direct query -> code, no-plan condition.
#   B2: independently retrain the deployed generated-plan pathway components:
#       alignment, four latent priors, Stage 3 LoRA-IR, Stage 3b LoRA-IR,
#       Stage 4 code decoder, and Stage 4b code decoder.
#
# This script is intentionally seed-scoped and refuses partial outputs. Re-running
# after a completed stage may keep that completed stage; it will not silently
# resume from an incomplete checkpoint or reuse historical B0/B2 outputs.
set -euo pipefail

source __USER_HOME__/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

source training_25k/_guard_fresh.sh \
  training_25k/cag_run_b0_b2_fullstack_seed.sh \
  training_25k/cag_b0_b2_fullstack_actuals.py \
  training_25k/cag_prepare_b0_b2_seed_geometry.py \
  train_alignment.py \
  train_latent_prior.py \
  gen_scripts/train_soft_prefix_ir.py \
  train_program_lora.py \
  training_25k/scripts/gen_predicted_ir.py \
  training_25k/scripts/gen_code_from_predicted_ir.py \
  training_25k/scripts/build_stage4b_mix.py \
  scratch/repair_face_extrude_alias.py

SEED=${SEED:?set SEED, e.g. SEED=1}
MODALITY=${MODALITY:-step}
LIMIT=${LIMIT:-2500}
BATCH=${BATCH:-16}
DRY_RUN=${DRY_RUN:-0}

case "$SEED" in
  1|2|3|4) ;;
  *) echo "Review/03 frozen seeds are 1,2,3,4; got SEED=$SEED" >&2; exit 1 ;;
esac
if [ "$SEED" = "42" ]; then
  echo "Seed 42 is the historical reference seed and is refused." >&2
  exit 1
fi
if [ "$MODALITY" != "step" ]; then
  echo "Review/03 is frozen for STEP only; got MODALITY=$MODALITY" >&2
  exit 1
fi
if [ "$LIMIT" != "2500" ]; then
  echo "Review/03 fixed evaluation slice requires LIMIT=2500; got $LIMIT" >&2
  exit 1
fi

BASE="outputs/b0_b2_fullstack_s${SEED}"
DATA_DIR="data/b0_b2_fullstack_s${SEED}"
WORK="$BASE/predictions"

ALIGN="$BASE/align_25k"
PRIOR_BASE="$BASE/priors"
STAGE3="$BASE/lora_ir_25k"
STAGE3B="$BASE/lora_ir_25k_stage3b"
STAGE4="$BASE/qwen25_coder_1_5b_program_25k"
STAGE4B="$BASE/qwen25_coder_1_5b_program_25k_stage4b"
B0_OUT="$BASE/b0_lora_code_noplan_25k"

TRAIN_PRED="$STAGE3/predicted_ir_train_subset_${MODALITY}.jsonl"
MIX="$DATA_DIR/train_stage4b_mix.jsonl"
B0_PRED="$WORK/gen_${MODALITY}_B0_s${SEED}.jsonl"
B2_IR_RAW="$WORK/predicted_ir_test_${MODALITY}_raw_s${SEED}.jsonl"
B2_IR_P1A="$WORK/predicted_ir_test_${MODALITY}_p1a_s${SEED}.jsonl"
B2_P1A_LOG="$WORK/repair_face_extrude_alias_log_${MODALITY}_s${SEED}.json"
B2_PRED="$WORK/gen_${MODALITY}_B2_s${SEED}.jsonl"

mkdir -p "$BASE" "$DATA_DIR" "$WORK"

rows() {
  [ -f "$1" ] || { echo 0; return; }
  wc -l "$1" | awk '{print $1}'
}

complete_files() {
  local missing=0
  for f in "$@"; do
    [ -s "$f" ] || missing=1
  done
  [ "$missing" -eq 0 ]
}

complete_jsonl() {
  local path="$1" expected="$2"
  [ -s "$path" ] && [ "$(rows "$path")" -eq "$expected" ]
}

refuse_partial_dir() {
  local label="$1"; shift
  local dir="$1"; shift
  if [ -e "$dir" ] && ! complete_files "$@"; then
    echo "$label exists but is incomplete: $dir" >&2
    printf '  required: %s\n' "$@" >&2
    exit 1
  fi
}

refuse_partial_jsonl() {
  local label="$1" path="$2" expected="$3"
  if [ -f "$path" ] && ! complete_jsonl "$path" "$expected"; then
    echo "$label exists but has $(rows "$path")/$expected rows: $path" >&2
    exit 1
  fi
}

run_or_keep_dir() {
  local label="$1"; shift
  local dir="$1"; shift
  local -a required=("$@")
  refuse_partial_dir "$label" "$dir" "${required[@]}"
  if complete_files "${required[@]}"; then
    echo "=== keep $label ($dir complete) ==="
    return 0
  fi
  return 1
}

run_or_keep_jsonl() {
  local label="$1" path="$2" expected="$3"
  refuse_partial_jsonl "$label" "$path" "$expected"
  if complete_jsonl "$path" "$expected"; then
    echo "=== keep $label ($path complete) ==="
    return 0
  fi
  return 1
}

DRY_ARGS=()
if [ "$DRY_RUN" = "1" ]; then
  DRY_ARGS+=(--dry-run)
fi
python training_25k/cag_b0_b2_fullstack_actuals.py preflight \
  --seed "$SEED" \
  --modality "$MODALITY" \
  --limit "$LIMIT" \
  --base "$BASE" \
  --data-dir "$DATA_DIR" \
  --work "$WORK" \
  "${DRY_ARGS[@]}"

cat <<EOF

=== Review/03 B0/B2 full-stack protocol accepted ===
seed:              $SEED
modality:          $MODALITY
evaluation rows:   $LIMIT
base output:       $BASE
data output:       $DATA_DIR
prediction output: $WORK
checkpoint rule:   final
program repair:    false
B2 plan P1a:       enabled, logged at $B2_P1A_LOG

EOF

if [ "$DRY_RUN" = "1" ]; then
  echo "DRY_RUN=1: preflight only; no training or generation was started."
  exit 0
fi

for f in data/25k/train.jsonl data/25k/val.jsonl data/25k/test.jsonl; do
  [ -s "$f" ] || { echo "FATAL: missing $f" >&2; exit 1; }
done

# ---------------------------------------------------------------------------
# B0: direct query -> code, no construction plan.
# ---------------------------------------------------------------------------
if ! run_or_keep_dir "B0 no-plan code model seed $SEED" "$B0_OUT" \
  "$B0_OUT/adapter_config.json" "$B0_OUT/adapter_model.safetensors" "$B0_OUT/training_report.json"; then
  echo "=== train B0 seed $SEED: direct STEP query -> code, no plan ==="
  python train_program_lora.py \
    --model-name Qwen/Qwen2.5-Coder-1.5B \
    --train-jsonl data/25k/train.jsonl --val-jsonl data/25k/val.jsonl \
    --output-dir "$B0_OUT" \
    --target program --modality "$MODALITY" --max-length 2048 \
    --no-plan \
    --epochs 1 --per-device-train-batch-size 1 --per-device-eval-batch-size 1 \
    --gradient-accumulation-steps 8 --learning-rate 2e-4 \
    --eval-steps 500 --save-steps 500 --logging-steps 20 --save-total-limit 2 \
    --lora-r 16 --lora-alpha 32 --load-in-4bit --bf16 \
    --seed "$SEED" 2>&1 | tee -a "$B0_OUT.train.log"
fi

# ---------------------------------------------------------------------------
# B2 full stack: alignment + priors + plan generation + deployed code decoder.
# Final checkpoint rule is implemented by using last.pt for alignment/priors
# and --checkpoint-rule final for Stage 3/3b soft-prefix training.
# ---------------------------------------------------------------------------
if ! run_or_keep_dir "B2 alignment seed $SEED" "$ALIGN" \
  "$ALIGN/last.pt" "$ALIGN/training_report.json"; then
  echo "=== train B2 alignment seed $SEED ==="
  python train_alignment.py \
    --train-jsonl data/25k/train.jsonl --val-jsonl data/25k/val.jsonl \
    --output-dir "$ALIGN" \
    --modalities text image point step ir --image-mode iso \
    --epochs 5 --batch-size 8 --grad-accum 4 \
    --max-text-length 128 --max-ir-length 256 --point-count 1024 \
    --rare-op-boost 2.0 \
    --bf16 --seed "$SEED" 2>&1 | tee -a "$ALIGN.train.log"
fi

for m in step point text image; do
  PRIOR="$PRIOR_BASE/prior_${m}_25k"
  if ! run_or_keep_dir "B2 $m prior seed $SEED" "$PRIOR" \
    "$PRIOR/last.pt" "$PRIOR/training_report.json"; then
    echo "=== train B2 $m latent prior seed $SEED ==="
    POINT_FLAGS=()
    if [ "$m" = "point" ]; then
      POINT_FLAGS+=(--train-point-sampling hybrid --eval-point-sampling fps)
    fi
    python train_latent_prior.py \
      --alignment-checkpoint "$ALIGN/last.pt" \
      --train-jsonl data/25k/train.jsonl --val-jsonl data/25k/val.jsonl \
      --output-dir "$PRIOR" --modality "$m" \
      --epochs 8 --batch-size 48 --learning-rate 1e-4 \
      --temperature 0.07 --lambda-cos 1.0 --lambda-nce 1.0 \
      --seed "$SEED" "${POINT_FLAGS[@]}" 2>&1 | tee -a "$PRIOR.train.log"
  fi
done

if ! run_or_keep_dir "B2 Stage 3 LoRA-IR seed $SEED" "$STAGE3" \
  "$STAGE3/adapter_config.json" "$STAGE3/adapter_model.safetensors" \
  "$STAGE3/soft_prefix.pt" "$STAGE3/soft_prefix_training_report.json"; then
  echo "=== train B2 Stage 3 LoRA-IR seed $SEED ==="
  python -m gen_scripts.train_soft_prefix_ir \
    --model-name Qwen/Qwen2.5-Coder-1.5B \
    --alignment-checkpoint "$ALIGN/last.pt" \
    --prior-checkpoint "$PRIOR_BASE/prior_step_25k/last.pt" \
    --modality "$MODALITY" \
    --train-jsonl data/25k/train.jsonl --val-jsonl data/25k/val.jsonl \
    --output-dir "$STAGE3" \
    --prefix-len 4 --load-in-4bit --bf16 \
    --per-device-train-batch-size 1 --per-device-eval-batch-size 1 \
    --gradient-accumulation-steps 16 \
    --epochs 3 --learning-rate 2e-4 --max-length 1536 --lora-r 8 \
    --eval-steps 500 --save-steps 500 --logging-steps 20 --save-total-limit 2 \
    --checkpoint-rule final --seed "$SEED" 2>&1 | tee -a "$STAGE3.train.log"
fi

if ! run_or_keep_jsonl "B2 Stage 4b train-subset predicted IR seed $SEED" "$TRAIN_PRED" 1000; then
  echo "=== generate B2 train-subset predicted IR seed $SEED ==="
  python training_25k/scripts/gen_predicted_ir.py \
    --modality "$MODALITY" \
    --alignment-checkpoint "$ALIGN/last.pt" \
    --prior-checkpoint "$PRIOR_BASE/prior_step_25k/last.pt" \
    --lora-ir-dir "$STAGE3" \
    --input-jsonl data/25k/train.jsonl \
    --output-jsonl "$TRAIN_PRED" \
    --limit 1000 --require-split train \
    --max-length 1536 --max-new-tokens 1536 --batch-size "$BATCH" \
    --seed "$SEED"
fi

if [ -f "$MIX" ]; then
  [ "$(rows "$MIX")" -gt 0 ] || { echo "Stage4b mix exists but is empty: $MIX" >&2; exit 1; }
  echo "=== keep B2 Stage 4b mix seed $SEED ($MIX, $(rows "$MIX") rows) ==="
else
  echo "=== build B2 Stage 4b mix seed $SEED ==="
  python training_25k/scripts/build_stage4b_mix.py \
    --predicted-ir-jsonl "$TRAIN_PRED" \
    --full-train-jsonl data/25k/train.jsonl \
    --output-jsonl "$MIX" \
    --predicted-ratio 0.30 \
    --seed "$SEED"
fi

if ! run_or_keep_dir "B2 Stage 3b LoRA-IR seed $SEED" "$STAGE3B" \
  "$STAGE3B/adapter_config.json" "$STAGE3B/adapter_model.safetensors" \
  "$STAGE3B/soft_prefix.pt" "$STAGE3B/soft_prefix_training_report.json"; then
  echo "=== train B2 Stage 3b LoRA-IR seed $SEED ==="
  python -m gen_scripts.train_soft_prefix_ir \
    --model-name Qwen/Qwen2.5-Coder-1.5B \
    --alignment-checkpoint "$ALIGN/last.pt" \
    --modality-prior step:"$PRIOR_BASE/prior_step_25k/last.pt" \
    --modality-prior point:"$PRIOR_BASE/prior_point_25k/last.pt" \
    --modality-prior text:"$PRIOR_BASE/prior_text_25k/last.pt" \
    --modality-prior image:"$PRIOR_BASE/prior_image_25k/last.pt" \
    --init-lora-ir-dir "$STAGE3" \
    --train-jsonl data/25k/train.jsonl --val-jsonl data/25k/val.jsonl \
    --limit-train 2000 --limit-val 200 \
    --output-dir "$STAGE3B" \
    --prefix-len 4 --load-in-4bit --bf16 \
    --per-device-train-batch-size 1 --per-device-eval-batch-size 1 \
    --gradient-accumulation-steps 16 \
    --epochs 1 --learning-rate 1e-5 --max-length 1536 \
    --eval-steps 50 --save-steps 50 --logging-steps 10 --save-total-limit 2 \
    --checkpoint-rule final --seed "$SEED" 2>&1 | tee -a "$STAGE3B.train.log"
fi

if ! run_or_keep_dir "B2 Stage 4 code decoder seed $SEED" "$STAGE4" \
  "$STAGE4/adapter_config.json" "$STAGE4/adapter_model.safetensors" "$STAGE4/training_report.json"; then
  echo "=== train B2 Stage 4 code decoder seed $SEED ==="
  python train_program_lora.py \
    --model-name Qwen/Qwen2.5-Coder-1.5B \
    --train-jsonl data/25k/train.jsonl --val-jsonl data/25k/val.jsonl \
    --output-dir "$STAGE4" \
    --target program --modality "$MODALITY" --max-length 1536 \
    --epochs 1 --per-device-train-batch-size 1 --per-device-eval-batch-size 1 \
    --gradient-accumulation-steps 8 --learning-rate 2e-4 \
    --eval-steps 500 --save-steps 500 --logging-steps 20 --save-total-limit 2 \
    --lora-r 16 --lora-alpha 32 --load-in-4bit --bf16 \
    --seed "$SEED" 2>&1 | tee -a "$STAGE4.train.log"
fi

if ! run_or_keep_dir "B2 Stage 4b code decoder seed $SEED" "$STAGE4B" \
  "$STAGE4B/adapter_config.json" "$STAGE4B/adapter_model.safetensors" "$STAGE4B/training_report.json"; then
  echo "=== train B2 Stage 4b code decoder seed $SEED ==="
  python train_program_lora.py \
    --model-name Qwen/Qwen2.5-Coder-1.5B \
    --train-jsonl "$MIX" --val-jsonl data/25k/val.jsonl \
    --output-dir "$STAGE4B" \
    --init-adapter-dir "$STAGE4" \
    --target program --modality "$MODALITY" --max-length 1536 \
    --epochs 3 --per-device-train-batch-size 1 --per-device-eval-batch-size 1 \
    --gradient-accumulation-steps 8 --learning-rate 5e-5 \
    --eval-steps 100 --save-steps 100 --logging-steps 10 --save-total-limit 2 \
    --lora-r 16 --lora-alpha 32 --load-in-4bit --bf16 \
    --seed "$SEED" 2>&1 | tee -a "$STAGE4B.train.log"
fi

# ---------------------------------------------------------------------------
# Prediction: raw generated programs only. No deterministic code repair.
# ---------------------------------------------------------------------------
if ! run_or_keep_jsonl "B0 raw code prediction seed $SEED" "$B0_PRED" "$LIMIT"; then
  echo "=== generate B0 raw code seed $SEED ==="
  python training_25k/scripts/gen_code_from_predicted_ir.py \
    --no-plan \
    --modality "$MODALITY" \
    --lora-code-dir "$B0_OUT" \
    --input-jsonl data/25k/test.jsonl \
    --output-jsonl "$B0_PRED" \
    --limit "$LIMIT" \
    --max-length 1536 --max-new-tokens 1536 --batch-size "$BATCH" \
    --seed "$SEED"
fi

if ! run_or_keep_jsonl "B2 raw predicted IR seed $SEED" "$B2_IR_RAW" "$LIMIT"; then
  echo "=== generate B2 predicted IR seed $SEED ==="
  python training_25k/scripts/gen_predicted_ir.py \
    --modality "$MODALITY" \
    --alignment-checkpoint "$ALIGN/last.pt" \
    --prior-checkpoint "$PRIOR_BASE/prior_step_25k/last.pt" \
    --lora-ir-dir "$STAGE3B" \
    --input-jsonl data/25k/test.jsonl \
    --output-jsonl "$B2_IR_RAW" \
    --limit "$LIMIT" \
    --max-length 1536 --max-new-tokens 1536 --batch-size "$BATCH" \
    --seed "$SEED"
fi

if ! run_or_keep_jsonl "B2 P1a predicted IR seed $SEED" "$B2_IR_P1A" "$LIMIT"; then
  echo "=== apply B2 P1a plan canonicalization seed $SEED ==="
  python scratch/repair_face_extrude_alias.py \
    --input "$B2_IR_RAW" \
    --output "$B2_IR_P1A" \
    --log "$B2_P1A_LOG" \
    --apply
fi

if ! run_or_keep_jsonl "B2 raw code prediction seed $SEED" "$B2_PRED" "$LIMIT"; then
  echo "=== generate B2 raw code seed $SEED ==="
  python training_25k/scripts/gen_code_from_predicted_ir.py \
    --modality "$MODALITY" \
    --lora-code-dir "$STAGE4B" \
    --ir-jsonl "$B2_IR_P1A" \
    --input-jsonl data/25k/test.jsonl \
    --output-jsonl "$B2_PRED" \
    --limit "$LIMIT" \
    --max-length 1536 --max-new-tokens 1536 --batch-size "$BATCH" \
    --seed "$SEED"
fi

python training_25k/cag_prepare_b0_b2_seed_geometry.py \
  --seed "$SEED" \
  --modality "$MODALITY" \
  --work "$WORK" \
  --test-jsonl data/25k/test.jsonl \
  --expected-rows "$LIMIT"

python training_25k/cag_b0_b2_fullstack_actuals.py post \
  --seed "$SEED" \
  --modality "$MODALITY" \
  --limit "$LIMIT" \
  --base "$BASE" \
  --data-dir "$DATA_DIR" \
  --work "$WORK"

cat <<EOF

=== Review/03 seed $SEED generation complete; run gate + geometry in Windows PowerShell ===

\$Root = "__RUN_SOURCE_ROOT__"

& "__DEV_ROOT__\\src\\scripts\\evaluate_execution.ps1" \`
  -InputJsonl "\$Root\\outputs\\b0_b2_fullstack_s${SEED}\\predictions\\gen_${MODALITY}_B0_s${SEED}.jsonl" \`
  -OutputDir "__DEV_ROOT__\\scratch\\exec_b0b2_${MODALITY}_B0_s${SEED}" \`
  -CodeField prediction

& "__DEV_ROOT__\\src\\scripts\\evaluate_execution.ps1" \`
  -InputJsonl "\$Root\\outputs\\b0_b2_fullstack_s${SEED}\\predictions\\gen_${MODALITY}_B2_s${SEED}.jsonl" \`
  -OutputDir "__DEV_ROOT__\\scratch\\exec_b0b2_${MODALITY}_B2_s${SEED}" \`
  -CodeField prediction

& "__DEV_ROOT__\\src\\scripts\\evaluate_geometry_nbest.ps1" \`
  -InputJsonl "\$Root\\outputs\\b0_b2_fullstack_s${SEED}\\predictions\\geom_input_${MODALITY}_B0_s${SEED}.jsonl" \`
  -OutputDir "__DEV_ROOT__\\scratch\\geom_b0b2_${MODALITY}_B0_s${SEED}"

& "__DEV_ROOT__\\src\\scripts\\evaluate_geometry_nbest.ps1" \`
  -InputJsonl "\$Root\\outputs\\b0_b2_fullstack_s${SEED}\\predictions\\geom_input_${MODALITY}_B2_s${SEED}.jsonl" \`
  -OutputDir "__DEV_ROOT__\\scratch\\geom_b0b2_${MODALITY}_B2_s${SEED}"

After those finish, summarize/register seed $SEED before running seed $((SEED + 1)).
EOF
