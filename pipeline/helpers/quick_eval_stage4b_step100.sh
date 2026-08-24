#!/bin/bash
# Quick 100-sample gate before committing to the full 11-19 formal pipeline
# (which runs the full 2.5K test set, all 4 modalities). Compares, on the
# SAME 100 STEP test rows:
#   1. Stage 4  checkpoint (GT-IR-only trained) fed predicted_ir
#   2. Stage 4b checkpoint (70/30 mix trained)   fed predicted_ir  <- does this beat (1)?
#   3. Stage 4b checkpoint fed ground-truth IR (upper-bound sanity: did mixing hurt clean-IR capability?)
# Run the printed evaluate_execution.ps1 commands in Windows PowerShell afterward
# to get real syntax_ok/exec_ok/build_ok/solid_valid/step_export_ok numbers.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

N=100
IR_DIR=outputs/lora_ir_25k
S4_DIR=outputs/qwen25_coder_1_5b_program_25k
S4B_DIR=outputs/qwen25_coder_1_5b_program_25k_stage4b

echo "=== [1/4] predicted_ir on first $N STEP test rows ==="
python training_25k/scripts/gen_predicted_ir.py \
  --modality step \
  --alignment-checkpoint outputs/align_25k/best.pt \
  --prior-checkpoint outputs/prior_step_25k/best.pt \
  --lora-ir-dir "$IR_DIR" \
  --input-jsonl data/25k/test.jsonl \
  --output-jsonl "$IR_DIR/predicted_ir_test_step_quick100.jsonl" \
  --limit $N --max-length 1536 --max-new-tokens 1536

echo "=== [2/4] P1a repair (face-extrude alias) ==="
python scratch/repair_face_extrude_alias.py \
  --input "$IR_DIR/predicted_ir_test_step_quick100.jsonl" \
  --output "$IR_DIR/predicted_ir_test_step_quick100_p1a.jsonl" \
  --log "$IR_DIR/repair_face_extrude_alias_log_step_quick100.json" \
  --apply

echo "=== [3/4] code-gen: Stage4 (predicted_ir), Stage4b (predicted_ir), Stage4b (GT-IR upper bound) ==="
python training_25k/scripts/gen_code_from_predicted_ir.py \
  --modality step --lora-code-dir "$S4_DIR" \
  --ir-jsonl "$IR_DIR/predicted_ir_test_step_quick100_p1a.jsonl" \
  --input-jsonl data/25k/test.jsonl \
  --output-jsonl "$S4_DIR/gen_quick100_step_predictedir.jsonl" \
  --limit $N --max-length 1536 --max-new-tokens 1536

python training_25k/scripts/gen_code_from_predicted_ir.py \
  --modality step --lora-code-dir "$S4B_DIR" \
  --ir-jsonl "$IR_DIR/predicted_ir_test_step_quick100_p1a.jsonl" \
  --input-jsonl data/25k/test.jsonl \
  --output-jsonl "$S4B_DIR/gen_quick100_step_predictedir.jsonl" \
  --limit $N --max-length 1536 --max-new-tokens 1536

python training_25k/scripts/gen_code_from_predicted_ir.py \
  --modality step --lora-code-dir "$S4B_DIR" \
  --ir-jsonl "$IR_DIR/predicted_ir_test_step_quick100_p1a.jsonl" \
  --use-ground-truth-ir \
  --input-jsonl data/25k/test.jsonl \
  --output-jsonl "$S4B_DIR/gen_quick100_step_gtir.jsonl" \
  --limit $N --max-length 1536 --max-new-tokens 1536

echo "=== [4/4] code repair (extrude_on_face then P0) on all three ==="
for F in \
  "$S4_DIR/gen_quick100_step_predictedir.jsonl" \
  "$S4B_DIR/gen_quick100_step_predictedir.jsonl" \
  "$S4B_DIR/gen_quick100_step_gtir.jsonl" ; do
  MID="${F%.jsonl}_repaired.jsonl"
  OUT="${F%.jsonl}_repaired_p0.jsonl"
  python3 scratch/repair_extrude_on_face.py "$F" "$MID"
  python3 scratch/repair_profile_cut_offset.py "$MID" "$OUT"
done

cat <<'EOF'

=== Done. Run these in Windows PowerShell to get real execution numbers: ===

$Eval = "C:\Workspace\Project\Paper\MIRAGE-V2\src\scripts\evaluate_execution.ps1"
$Root = "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src"

& $Eval -InputJsonl (Join-Path $Root "outputs\qwen25_coder_1_5b_program_25k\gen_quick100_step_predictedir_repaired_p0.jsonl") -OutputDir "C:\Workspace\Project\Paper\MIRAGE-V2\scratch\exec_quick100_stage4_predictedir"
& $Eval -InputJsonl (Join-Path $Root "outputs\qwen25_coder_1_5b_program_25k_stage4b\gen_quick100_step_predictedir_repaired_p0.jsonl") -OutputDir "C:\Workspace\Project\Paper\MIRAGE-V2\scratch\exec_quick100_stage4b_predictedir"
& $Eval -InputJsonl (Join-Path $Root "outputs\qwen25_coder_1_5b_program_25k_stage4b\gen_quick100_step_gtir_repaired_p0.jsonl") -OutputDir "C:\Workspace\Project\Paper\MIRAGE-V2\scratch\exec_quick100_stage4b_gtir"

Then compare execution_summary.json in the three scratch\exec_quick100_* dirs:
  stage4_predictedir  vs  stage4b_predictedir  -> stage4b should win (this is the point of Stage 4b)
  stage4b_predictedir vs  stage4b_gtir          -> gtir should still be high (no catastrophic forgetting)
EOF
