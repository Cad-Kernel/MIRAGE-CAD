#!/bin/bash
# Full 2.5K x 4-modality formal re-run using outputs/lora_ir_25k_stage3b
# instead of outputs/lora_ir_25k (docs/MIRAGE-CAD_experiment_results.md
# SS8.12's 100-sample gate PASSED -- point/text/image +31 to +47pp, STEP -4pp
# on n=100). This is the equivalent of steps 11+12+13+14+17+19 of the
# training_25k/README.md runbook, EXCEPT every output path is suffixed
# _stage3b so the ORIGINAL 25K results (outputs/lora_ir_25k/*, gen_test_{m}.jsonl,
# ir_quality_{m}_25k.json, eval_{m}_25k/) are never touched -- both versions
# must remain independently available for the Original-vs-Stage3b ablation
# comparison. Stage 4b LoRA-Code is intentionally NOT retrained here (per
# plan: confirm the LoRA-IR fix at full scale first, decide on a Stage4b
# refresh only afterward if still needed).
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

IR_S3B=outputs/lora_ir_25k_stage3b
S4B_DIR=outputs/qwen25_coder_1_5b_program_25k_stage4b

for m in step point text image; do
  case $m in
    step)  PRIOR=outputs/prior_step_25k/best.pt ;;
    point) PRIOR=outputs/prior_point_25k/best.pt ;;
    text)  PRIOR=outputs/prior_text_25k/best.pt ;;
    image) PRIOR=outputs/prior_image_25k/best.pt ;;
  esac

  echo "=== [11-equiv][$m] predicted_ir, full 2.5K test set, lora_ir_25k_stage3b ==="
  python training_25k/scripts/gen_predicted_ir.py \
    --modality $m \
    --alignment-checkpoint outputs/align_25k/best.pt \
    --prior-checkpoint "$PRIOR" \
    --lora-ir-dir "$IR_S3B" \
    --input-jsonl data/25k/test.jsonl \
    --output-jsonl "$IR_S3B/predicted_ir_test_${m}.jsonl" \
    --max-length 1536 --max-new-tokens 1536

  echo "=== [12-equiv][$m] P1a repair ==="
  python scratch/repair_face_extrude_alias.py \
    --input "$IR_S3B/predicted_ir_test_${m}.jsonl" \
    --output "$IR_S3B/predicted_ir_test_${m}_p1a.jsonl" \
    --log "$IR_S3B/repair_face_extrude_alias_log_${m}.json" \
    --apply

  echo "=== [13-equiv][$m] code-gen with the SAME (unchanged) Stage4b LoRA-Code ==="
  python training_25k/scripts/gen_code_from_predicted_ir.py \
    --modality $m --lora-code-dir "$S4B_DIR" \
    --ir-jsonl "$IR_S3B/predicted_ir_test_${m}_p1a.jsonl" \
    --input-jsonl data/25k/test.jsonl \
    --output-jsonl "$S4B_DIR/gen_test_${m}_stage3b.jsonl" \
    --max-length 1536 --max-new-tokens 1536

  echo "=== [14-equiv][$m] code repair (extrude_on_face then P0) ==="
  MID="$S4B_DIR/gen_test_${m}_stage3b_repaired.jsonl"
  OUT="$S4B_DIR/gen_test_${m}_stage3b_repaired_p0.jsonl"
  python3 scratch/repair_extrude_on_face.py "$S4B_DIR/gen_test_${m}_stage3b.jsonl" "$MID"
  python3 scratch/repair_profile_cut_offset.py "$MID" "$OUT"

  echo "=== [17-equiv][$m] IR quality (cosine/op-F1/op-LCS vs reference) ==="
  python -m gen_scripts.evaluate_ir_quality \
    --predicted-jsonl "$IR_S3B/predicted_ir_test_${m}_p1a.jsonl" \
    --alignment-checkpoint outputs/align_25k/best.pt \
    --output-json "$IR_S3B/ir_quality_${m}_25k.json"

  echo "=== [19-equiv][$m] program-level text metrics (no execution) ==="
  python evaluate_programs.py \
    --predictions "$OUT" \
    --output-dir "$S4B_DIR/eval_${m}_25k_stage3b"
done

cat <<'EOF'

=== Done. Run these in Windows PowerShell for real execution numbers (4 modalities, full 2.5K): ===

$Eval = "C:\Workspace\Project\Paper\MIRAGE-V2\src\scripts\evaluate_execution.ps1"
$Root = "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src"
$S4B  = "outputs\qwen25_coder_1_5b_program_25k_stage4b"

foreach ($m in @("step","point","text","image")) {
  & $Eval -InputJsonl (Join-Path $Root "$S4B\gen_test_${m}_stage3b_repaired_p0.jsonl") -OutputDir "C:\Workspace\Project\Paper\MIRAGE-V2\scratch\exec_eval_25k_stage3b_${m}"
}

Then compare against the ORIGINAL 25K results (scratch\exec_eval_25k_{step,point,text,image}\execution_summary.json,
untouched by this run) to build the Original-vs-Stage3b full-scale ablation table.
EOF
