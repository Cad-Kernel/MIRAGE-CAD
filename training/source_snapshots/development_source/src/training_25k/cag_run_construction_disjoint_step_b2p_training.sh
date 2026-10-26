#!/bin/bash
# Phase 4: construction-disjoint STEP MIRAGE textual-plan pathway retraining.
#
# Do not run this before the train-only NN baseline is generated. By default the
# script refuses to start unless the NN baseline prediction file has 500 rows.
set -euo pipefail
source __USER_HOME__/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

source training_25k/_guard_fresh.sh \
  training_25k/cag_run_construction_disjoint_step_b2p_training.sh \
  training_25k/scripts/gen_predicted_ir.py \
  training_25k/scripts/gen_code_from_predicted_ir.py \
  training_25k/scripts/build_stage4b_mix.py \
  training_25k/cag_prepare_construction_disjoint_geometry.py \
  train_alignment.py \
  train_latent_prior.py \
  train_program_lora.py \
  gen_scripts/train_soft_prefix_ir.py

DATA=${DATA:-data/construction_disjoint_step_v1}
WORK=${WORK:-outputs/construction_disjoint_step_v1}
LIMIT=${LIMIT:-500}
BATCH=${BATCH:-16}
ALLOW_WITHOUT_BASELINE=${ALLOW_WITHOUT_BASELINE:-0}

ALIGN=${ALIGN:-outputs/align_25k_cd_step}
PRIOR=${PRIOR:-outputs/prior_step_25k_cd_step}
IR_DIR=${IR_DIR:-outputs/lora_ir_25k_cd_step}
CODE_GT=${CODE_GT:-outputs/qwen25_coder_1_5b_program_25k_cd_step}
CODE_B2P=${CODE_B2P:-outputs/qwen25_coder_1_5b_program_25k_cd_step_stage4b}

NN_PRED="$WORK/nn_step_descriptor_train_only.jsonl"
if [ "$ALLOW_WITHOUT_BASELINE" != "1" ]; then
  if [ ! -f "$NN_PRED" ] || [ "$(wc -l < "$NN_PRED")" -ne 500 ]; then
    echo "Refusing MIRAGE retraining: NN baseline is not complete at $NN_PRED." >&2
    echo "Run first: bash training_25k/cag_run_construction_disjoint_nn_baseline.sh" >&2
    echo "Override only with ALLOW_WITHOUT_BASELINE=1 if you intentionally defer baseline." >&2
    exit 1
  fi
fi

python - <<'PY'
import json, pathlib, sys
base = pathlib.Path("data/construction_disjoint_step_v1")
actuals = json.loads((base / "cag_construction_split_actuals.json").read_text())
ok = True
checks = {
    "sample_ids_frozen": actuals.get("freeze_status", {}).get("sample_ids") == "FROZEN",
    "leakage_pass": actuals.get("overlap_audit", {}).get("status") == "PASS",
    "train_rows_25000": actuals.get("counts", {}).get("train", {}).get("rows") == 25000,
    "val_rows_2500": actuals.get("counts", {}).get("val", {}).get("rows") == 2500,
    "test_rows_500": actuals.get("counts", {}).get("test", {}).get("rows") == 500,
}
for k, v in checks.items():
    print(f"{'ok  ' if v else 'FAIL'} {k}")
    ok &= v
sys.exit(0 if ok else 1)
PY

mkdir -p "$WORK" logs

if [ -f "$ALIGN/best.pt" ]; then
  echo "[$(date)] alignment already complete -- skipping: $ALIGN"
else
  echo "=== Stage 1: train STEP/IR alignment on construction-disjoint train split ==="
  python train_alignment.py \
    --train-jsonl "$DATA/train.jsonl" --val-jsonl "$DATA/val.jsonl" \
    --output-dir "$ALIGN" \
    --modalities step ir --image-mode iso \
    --epochs 5 --batch-size 8 --grad-accum 4 \
    --max-text-length 128 --max-ir-length 256 --point-count 1024 \
    --rare-op-boost 2.0 \
    --bf16 2>&1 | tee -a logs/cd_step_training.log
fi

if [ -f "$PRIOR/best.pt" ]; then
  echo "[$(date)] STEP prior already complete -- skipping: $PRIOR"
else
  echo "=== Stage 2: train STEP latent prior ==="
  python train_latent_prior.py \
    --alignment-checkpoint "$ALIGN/best.pt" \
    --train-jsonl "$DATA/train.jsonl" --val-jsonl "$DATA/val.jsonl" \
    --output-dir "$PRIOR" --modality step \
    --epochs 8 --batch-size 48 --learning-rate 1e-4 \
    --temperature 0.07 --lambda-cos 1.0 --lambda-nce 1.0 2>&1 | tee -a logs/cd_step_training.log
fi

if [ -f "$IR_DIR/soft_prefix_training_report.json" ]; then
  echo "[$(date)] LoRA-IR already complete -- skipping: $IR_DIR"
else
  echo "=== Stage 3: train STEP LoRA-IR ==="
  python -m gen_scripts.train_soft_prefix_ir \
    --model-name Qwen/Qwen2.5-Coder-1.5B \
    --alignment-checkpoint "$ALIGN/best.pt" \
    --prior-checkpoint "$PRIOR/best.pt" \
    --modality step \
    --train-jsonl "$DATA/train.jsonl" --val-jsonl "$DATA/val.jsonl" \
    --output-dir "$IR_DIR" \
    --prefix-len 4 --load-in-4bit --bf16 \
    --per-device-train-batch-size 1 --gradient-accumulation-steps 16 \
    --epochs 3 --learning-rate 2e-4 --max-length 1536 --lora-r 8 2>&1 | tee -a logs/cd_step_training.log
fi

PRED_TRAIN="$IR_DIR/predicted_ir_train_subset.jsonl"
MIX="$DATA/train_stage4b_mix.jsonl"
if [ -f "$MIX" ]; then
  echo "[$(date)] Stage4b mix already complete -- skipping: $MIX"
else
  echo "=== Stage 4b prep: generate predicted IR train subset and 70/30 mix ==="
  python training_25k/scripts/gen_predicted_ir.py \
    --modality step \
    --alignment-checkpoint "$ALIGN/best.pt" \
    --prior-checkpoint "$PRIOR/best.pt" \
    --lora-ir-dir "$IR_DIR" \
    --input-jsonl "$DATA/train.jsonl" \
    --output-jsonl "$PRED_TRAIN" \
    --limit 1000 --require-split train \
    --max-length 1536 --max-new-tokens 1536 --batch-size "$BATCH"

  python training_25k/scripts/build_stage4b_mix.py \
    --predicted-ir-jsonl "$PRED_TRAIN" \
    --full-train-jsonl "$DATA/train.jsonl" \
    --output-jsonl "$MIX" \
    --predicted-ratio 0.30
fi

latest_checkpoint() {
  shopt -s nullglob
  local matches=("$1"/checkpoint-*)
  shopt -u nullglob
  if [ "${#matches[@]}" -eq 0 ]; then return 0; fi
  printf '%s\n' "${matches[@]}" | sed -E 's/.*checkpoint-([0-9]+)$/\1 &/' | sort -n | tail -n1 | cut -d' ' -f2-
}

if [ -f "$CODE_GT/training_report.json" ]; then
  echo "[$(date)] GT-IR code decoder already complete -- skipping: $CODE_GT"
else
  RESUME_ARG=()
  CKPT=$(latest_checkpoint "$CODE_GT")
  if [ -n "$CKPT" ]; then RESUME_ARG=(--resume-from-checkpoint "$CKPT"); fi
  echo "=== Stage 4: train program decoder on ground-truth IR ==="
  python train_program_lora.py \
    --model-name Qwen/Qwen2.5-Coder-1.5B \
    --train-jsonl "$DATA/train.jsonl" --val-jsonl "$DATA/val.jsonl" \
    --output-dir "$CODE_GT" \
    --target program --modality step --max-length 1536 \
    --epochs 1 --per-device-train-batch-size 1 --per-device-eval-batch-size 1 \
    --gradient-accumulation-steps 8 --learning-rate 2e-4 \
    --eval-steps 500 --save-steps 500 --logging-steps 20 --save-total-limit 2 \
    --lora-r 16 --lora-alpha 32 --load-in-4bit --bf16 \
    "${RESUME_ARG[@]}" 2>&1 | tee -a logs/cd_step_training.log
fi

if [ -f "$CODE_B2P/training_report.json" ]; then
  echo "[$(date)] Stage4b code decoder already complete -- skipping: $CODE_B2P"
else
  RESUME_ARG=()
  CKPT=$(latest_checkpoint "$CODE_B2P")
  if [ -n "$CKPT" ]; then RESUME_ARG=(--resume-from-checkpoint "$CKPT"); fi
  echo "=== Stage 4b: continue program decoder on 70/30 GT/predicted mix ==="
  python train_program_lora.py \
    --model-name Qwen/Qwen2.5-Coder-1.5B \
    --train-jsonl "$MIX" --val-jsonl "$DATA/val.jsonl" \
    --output-dir "$CODE_B2P" \
    --init-adapter-dir "$CODE_GT" \
    --target program --modality step --max-length 1536 \
    --epochs 3 --per-device-train-batch-size 1 --per-device-eval-batch-size 1 \
    --gradient-accumulation-steps 8 --learning-rate 5e-5 \
    --eval-steps 100 --save-steps 100 --logging-steps 10 --save-total-limit 2 \
    --lora-r 16 --lora-alpha 32 --load-in-4bit --bf16 \
    "${RESUME_ARG[@]}" 2>&1 | tee -a logs/cd_step_training.log
fi

PRED_IR="$IR_DIR/predicted_ir_test_step.jsonl"
PRED_IR_P1A="$IR_DIR/predicted_ir_test_step_p1a.jsonl"
PRED_CODE="$WORK/gen_code_step_B2P_CD.jsonl"
GEOM="$WORK/geom_input_step_B2P_CD.jsonl"
GEOM_MANIFEST="$WORK/geom_input_step_B2P_CD_manifest.json"

if [ ! -f "$PRED_IR" ] || [ "$(wc -l < "$PRED_IR")" -ne "$LIMIT" ]; then
  echo "=== Inference 1: predicted IR on construction-disjoint test ==="
  python training_25k/scripts/gen_predicted_ir.py \
    --modality step \
    --alignment-checkpoint "$ALIGN/best.pt" \
    --prior-checkpoint "$PRIOR/best.pt" \
    --lora-ir-dir "$IR_DIR" \
    --input-jsonl "$DATA/test.jsonl" \
    --output-jsonl "$PRED_IR" \
    --limit "$LIMIT" --require-split test \
    --max-length 1536 --max-new-tokens 1536 --batch-size "$BATCH"
fi

echo "=== P1a repair predicted IR ==="
python scratch/repair_face_extrude_alias.py \
  --input "$PRED_IR" \
  --output "$PRED_IR_P1A" \
  --log "$IR_DIR/repair_face_extrude_alias_log_step_cd.json" \
  --apply

if [ ! -f "$PRED_CODE" ] || [ "$(wc -l < "$PRED_CODE")" -ne "$LIMIT" ]; then
  echo "=== Inference 2: code generation from predicted IR ==="
  python training_25k/scripts/gen_code_from_predicted_ir.py \
    --modality step --lora-code-dir "$CODE_B2P" \
    --ir-jsonl "$PRED_IR_P1A" \
    --input-jsonl "$DATA/test.jsonl" \
    --output-jsonl "$PRED_CODE" \
    --limit "$LIMIT" \
    --max-length 1536 --max-new-tokens 1536 --batch-size "$BATCH"
fi

python training_25k/cag_prepare_construction_disjoint_geometry.py \
  --predictions "$PRED_CODE" \
  --test-jsonl "$DATA/test.jsonl" \
  --output-jsonl "$GEOM" \
  --manifest-json "$GEOM_MANIFEST" \
  --arm B2P_CD \
  --expected-rows "$LIMIT"

cat > "$WORK/B2P_CD_metadata.json" <<JSON
{
  "arm": "B2P_CD",
  "description": "Construction-disjoint STEP MIRAGE textual-plan pathway",
  "data": "$DATA",
  "alignment": "$ALIGN",
  "prior": "$PRIOR",
  "lora_ir": "$IR_DIR",
  "code_gt": "$CODE_GT",
  "code_stage4b": "$CODE_B2P",
  "repair": false,
  "test_limit": $LIMIT,
  "baseline_first_guard": "$ALLOW_WITHOUT_BASELINE"
}
JSON

echo
echo "=== MIRAGE CD STEP inference COMPLETE; NOW RUN GATE + GEOMETRY IN WINDOWS POWERSHELL ==="
cat <<'EOF'
$Root = "__RUN_SOURCE_ROOT__"

& "__DEV_ROOT__\src\scripts\evaluate_execution.ps1" `
  -InputJsonl "$Root\outputs\construction_disjoint_step_v1\gen_code_step_B2P_CD.jsonl" `
  -OutputDir "__DEV_ROOT__\scratch\exec_cd_step_B2P_CD" `
  -CodeField prediction

& "__DEV_ROOT__\src\scripts\evaluate_geometry_nbest.ps1" `
  -InputJsonl "$Root\outputs\construction_disjoint_step_v1\geom_input_step_B2P_CD.jsonl" `
  -OutputDir "__DEV_ROOT__\scratch\geom_cd_step_B2P_CD"
EOF
