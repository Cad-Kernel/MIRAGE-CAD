#!/bin/bash
# Upgrade Table 3's NN-IR baseline (variants A/B) from 5K/100-sample scale to
# 25K scale, so it can be compared against the Stage3b 25K "C" numbers on a
# matched corpus/scale (currently Table 3 flags this as a caveat -- this run
# removes it). Reuses scratch/gen_nn_ir_baseline.py unmodified (already
# CLI-parameterized for alignment/prior/index/LoRA-Code/input paths); no
# training involved, this is pure retrieval + decode with the EXISTING,
# unchanged Stage4b LoRA-Code checkpoint. 100 samples per modality per mode,
# matching the 5K-scale precedent (execution already saturates near ceiling
# at this size per docs SS6.6).
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

S4B_DIR=outputs/qwen25_coder_1_5b_program_25k_stage4b
WORK=outputs/nnir_baseline_25k
N=100

mkdir -p "$WORK"

for m in step point text image; do
  case $m in
    step)  PRIOR=outputs/prior_step_25k/best.pt ;;
    point) PRIOR=outputs/prior_point_25k/best.pt ;;
    text)  PRIOR=outputs/prior_text_25k/best.pt ;;
    image) PRIOR=outputs/prior_image_25k/best.pt ;;
  esac

  for mode in direct prior; do
    echo "=== [$m / $mode-NN-IR] ==="
    python scratch/gen_nn_ir_baseline.py \
      --modality $m --retrieval-mode $mode \
      --alignment-checkpoint outputs/align_25k/best.pt \
      --prior-checkpoint "$PRIOR" \
      --retrieval-index outputs/align_25k/train_ir_index.npz \
      --lora-code-dir "$S4B_DIR" \
      --input-jsonl data/25k/test.jsonl \
      --output-jsonl "$WORK/${mode}_${m}.jsonl" \
      --limit $N --max-length 1536 --max-new-tokens 1536

    echo "=== [$m / $mode-NN-IR] code repair (extrude_on_face then P0) ==="
    MID="$WORK/${mode}_${m}_repaired.jsonl"
    OUT="$WORK/${mode}_${m}_repaired_p0.jsonl"
    python3 scratch/repair_extrude_on_face.py "$WORK/${mode}_${m}.jsonl" "$MID"
    python3 scratch/repair_profile_cut_offset.py "$MID" "$OUT"
  done
done

cat <<'EOF'

=== Done (WSL side). Run these in Windows PowerShell for real execution numbers (8 conditions): ===

$Eval = "C:\Workspace\Project\Paper\MIRAGE-V2\src\scripts\evaluate_execution.ps1"
$Root = "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src"
$Work = "outputs\nnir_baseline_25k"

foreach ($m in @("step","point","text","image")) {
  foreach ($mode in @("direct","prior")) {
    & $Eval -InputJsonl (Join-Path $Root "$Work\${mode}_${m}_repaired_p0.jsonl") -OutputDir "C:\Workspace\Project\Paper\MIRAGE-V2\scratch\exec_nnir_25k_${mode}_${m}"
  }
}

Then compare scratch\exec_nnir_25k_{direct,prior}_{step,point,text,image}\execution_summary.json
against Stage3b's Table (STEP 70.0%, Point 55.4%, Text 57.2%, Image 57.8%) -- same 25K test set, same repair pipeline.
Expected (per the 5K precedent, docs SS6.6): NN-IR baseline execution will likely still saturate near 85-90%,
since it substitutes REAL training IR (not generated) -- this is not expected to be "beaten", only reported honestly.
EOF
