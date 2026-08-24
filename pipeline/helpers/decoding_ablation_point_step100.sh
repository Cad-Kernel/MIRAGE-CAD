#!/bin/bash
# Decoding ablation (docs/MIRAGE-CAD_experiment_results.md SS8.8): does
# repetition_penalty reduce greedy-decoding degenerate repeated-coordinate-
# list generations? Found: 53-78% of syntax_ok failures across ALL FOUR
# modalities are degenerate (no real part.xxx(...) structure, no __all__
# marker -- just a repeating numeric-list loop), not a bracket-typo issue.
# Point triggers this most often in absolute terms (192/2500), which is why
# it's tested here alongside STEP (the "safe" reference modality, to check
# repetition_penalty doesn't hurt otherwise-healthy generation).
#
# Reuses the EXISTING formal-eval P1a-repaired predicted_ir (--limit 100
# slice of it) -- no new predicted_ir generation needed, this only varies
# the Stage 4b code-generation decoding parameters.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

S4B_DIR=outputs/qwen25_coder_1_5b_program_25k_stage4b
IR_DIR=outputs/lora_ir_25k
N=100

for m in point step; do
  for rp_tag in baseline rp110 rp115 rp120; do
    case $rp_tag in
      baseline) RP_ARGS="" ;;
      rp110) RP_ARGS="--repetition-penalty 1.10" ;;
      rp115) RP_ARGS="--repetition-penalty 1.15" ;;
      rp120) RP_ARGS="--repetition-penalty 1.20" ;;
    esac
    echo "=== [$m / $rp_tag] code generation ==="
    python training_25k/scripts/gen_code_from_predicted_ir.py \
      --modality $m --lora-code-dir "$S4B_DIR" \
      --ir-jsonl "$IR_DIR/predicted_ir_test_${m}_p1a.jsonl" \
      --input-jsonl data/25k/test.jsonl \
      --output-jsonl "$S4B_DIR/ablation_${m}_${rp_tag}.jsonl" \
      --limit $N --max-length 1536 --max-new-tokens 1536 $RP_ARGS
  done
done

echo "=== code repair (extrude_on_face then P0) on all 8 ablation outputs ==="
FILES=()
for m in point step; do
  for rp_tag in baseline rp110 rp115 rp120; do
    F="$S4B_DIR/ablation_${m}_${rp_tag}.jsonl"
    MID="${F%.jsonl}_repaired.jsonl"
    OUT="${F%.jsonl}_repaired_p0.jsonl"
    python3 scratch/repair_extrude_on_face.py "$F" "$MID"
    python3 scratch/repair_profile_cut_offset.py "$MID" "$OUT"
    FILES+=("$OUT")
  done
done

echo "=== [pre-execution] degenerate-generation rate per condition (no FllumaCLI needed) ==="
python3 training_25k/scripts/analyze_decoding_ablation.py --files "${FILES[@]}"

cat <<'EOF'

=== Done. Run these in Windows PowerShell to get real execution numbers for all 8 conditions: ===

$Eval = "C:\Workspace\Project\Paper\MIRAGE-V2\src\scripts\evaluate_execution.ps1"
$Root = "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src"
$S4B  = "outputs\qwen25_coder_1_5b_program_25k_stage4b"

foreach ($m in @("point","step")) {
  foreach ($rp in @("baseline","rp110","rp115","rp120")) {
    & $Eval -InputJsonl (Join-Path $Root "$S4B\ablation_${m}_${rp}_repaired_p0.jsonl") -OutputDir "C:\Workspace\Project\Paper\MIRAGE-V2\scratch\exec_ablation_${m}_${rp}"
  }
}

Then compare scratch\exec_ablation_{point,step}_{baseline,rp110,rp115,rp120}\execution_summary.json:
  - point: does exec_ok/syntax_ok improve as repetition_penalty increases, without a length/truncation side effect?
  - step: does repetition_penalty leave STEP's already-healthy generation unharmed (syntax_ok/exec_ok should NOT drop)?
Decision rule: pick the smallest repetition_penalty that meaningfully reduces point's degenerate rate
without regressing step's exec_ok -- do not just take the largest value tested.
EOF
