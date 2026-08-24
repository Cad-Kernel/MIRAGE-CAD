#!/bin/bash
# Stage 3b validation gate (docs/MIRAGE-CAD_experiment_results.md SS8.10-8.11):
# compare BASELINE lora_ir_25k (STEP-only trained) vs. lora_ir_25k_stage3b
# (mixed 4-modality continuation) across all four modalities, 100-sample,
# holding Stage 4b LoRA-Code fixed (qwen25_coder_1_5b_program_25k_stage4b) so
# the only variable is which LoRA-IR checkpoint produced the predicted_ir.
#
# Decision rule (pre-registered, do not relax after seeing results):
#   - point/text exec_ok must show a REAL improvement over baseline
#   - STEP/image exec_ok must NOT meaningfully regress
# If both hold: lora_ir_25k_stage3b becomes the new recommended checkpoint,
# re-run the full 11-19 formal pipeline with it. If not: keep outputs/lora_ir_25k
# as-is; lora_ir_25k_stage3b is a documented negative result, nothing is lost.
#
# Baseline predicted_ir is NOT regenerated -- it's the first 100 rows of the
# already-computed formal-eval file (outputs/lora_ir_25k/predicted_ir_test_
# {m}_p1a.jsonl), which was built row-order-aligned with data/25k/test.jsonl.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

N=100
S4B_DIR=outputs/qwen25_coder_1_5b_program_25k_stage4b
IR_BASE=outputs/lora_ir_25k
IR_S3B=outputs/lora_ir_25k_stage3b
WORK=outputs/stage3b_gate

mkdir -p "$WORK"

for m in step point text image; do
  echo "=== [$m] baseline predicted_ir (reused from formal eval, first $N rows) ==="
  head -n $N "$IR_BASE/predicted_ir_test_${m}_p1a.jsonl" > "$WORK/predicted_ir_${m}_baseline_p1a.jsonl"

  echo "=== [$m] stage3b predicted_ir (freshly generated, first $N rows) ==="
  case $m in
    step)  ALIGN_ARGS="--prior-checkpoint outputs/prior_step_25k/best.pt" ;;
    point) ALIGN_ARGS="--prior-checkpoint outputs/prior_point_25k/best.pt" ;;
    text)  ALIGN_ARGS="--prior-checkpoint outputs/prior_text_25k/best.pt" ;;
    image) ALIGN_ARGS="--prior-checkpoint outputs/prior_image_25k/best.pt" ;;
  esac
  python training_25k/scripts/gen_predicted_ir.py \
    --modality $m \
    --alignment-checkpoint outputs/align_25k/best.pt \
    $ALIGN_ARGS \
    --lora-ir-dir "$IR_S3B" \
    --input-jsonl data/25k/test.jsonl \
    --output-jsonl "$WORK/predicted_ir_${m}_stage3b.jsonl" \
    --limit $N --max-length 1536 --max-new-tokens 1536

  echo "=== [$m] P1a repair (stage3b output) ==="
  python scratch/repair_face_extrude_alias.py \
    --input "$WORK/predicted_ir_${m}_stage3b.jsonl" \
    --output "$WORK/predicted_ir_${m}_stage3b_p1a.jsonl" \
    --log "$WORK/repair_log_${m}_stage3b.json" \
    --apply

  for cond in baseline stage3b; do
    echo "=== [$m / $cond] code-gen with the SAME Stage4b LoRA-Code checkpoint ==="
    python training_25k/scripts/gen_code_from_predicted_ir.py \
      --modality $m --lora-code-dir "$S4B_DIR" \
      --ir-jsonl "$WORK/predicted_ir_${m}_${cond}_p1a.jsonl" \
      --input-jsonl data/25k/test.jsonl \
      --output-jsonl "$WORK/gen_${m}_${cond}.jsonl" \
      --limit $N --max-length 1536 --max-new-tokens 1536
  done
done

echo "=== code repair (extrude_on_face then P0) on all 8 conditions ==="
FILES=()
for m in step point text image; do
  for cond in baseline stage3b; do
    F="$WORK/gen_${m}_${cond}.jsonl"
    MID="${F%.jsonl}_repaired.jsonl"
    OUT="${F%.jsonl}_repaired_p0.jsonl"
    python3 scratch/repair_extrude_on_face.py "$F" "$MID"
    python3 scratch/repair_profile_cut_offset.py "$MID" "$OUT"
    FILES+=("$OUT")
  done
done

cat <<'EOF'

=== Done. Run these in Windows PowerShell for real execution numbers (8 conditions): ===

$Eval = "C:\Workspace\Project\Paper\MIRAGE-V2\src\scripts\evaluate_execution.ps1"
$Root = "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src"
$Work = "outputs\stage3b_gate"

foreach ($m in @("step","point","text","image")) {
  foreach ($cond in @("baseline","stage3b")) {
    & $Eval -InputJsonl (Join-Path $Root "$Work\gen_${m}_${cond}_repaired_p0.jsonl") -OutputDir "C:\Workspace\Project\Paper\MIRAGE-V2\scratch\exec_stage3b_gate_${m}_${cond}"
  }
}

Then compare scratch\exec_stage3b_gate_{step,point,text,image}_{baseline,stage3b}\execution_summary.json against
the pre-registered rule: point/text exec_ok must clearly improve, STEP/image exec_ok must NOT meaningfully drop.
Only if BOTH hold should lora_ir_25k_stage3b replace lora_ir_25k for the full 11-19 formal re-run.
EOF
