#!/bin/bash
# Compositional-split evaluation, chained: build index + "Ours" (Stage3b-comp
# generated-IR) pipeline, then NN-IR baseline (Direct + Prior), both on the
# full 2,923-sample comp_test.jsonl, all 4 modalities. Run this AFTER
# comp_run_stages_2to4b.sh (training) has fully finished.
#
# Same crash-recovery approach as the training pipeline: output tee'd to a
# persistent log, and each sub-script internally skips per-modality work
# that's already done (checked via existence of that step's own final output
# file, not `ls globs` -- the earlier bug in comp_09_10 was `ls` on a
# non-matching glob dying under `set -e`; every skip-check here uses plain
# `[ -f exact/file/path ]`, which cannot fail that way).
set -euo pipefail
cd ~/workspace/MIRAGE/src
mkdir -p logs
exec > >(tee -a logs/comp_eval.log) 2>&1

if [ ! -f outputs/qwen25_coder_1_5b_program_25k_comp_stage4b/training_report.json ]; then
  echo "ERROR: training pipeline (comp_run_stages_2to4b.sh) has not finished -- Stage4b-comp checkpoint missing." >&2
  exit 1
fi

echo "=============================================="
echo "[$(date)] Resuming/starting evaluation run"
echo "=============================================="

echo "=============================================="
echo "[$(date)] Part 1: retrieval index + Ours (Stage3b-comp) pipeline"
echo "=============================================="
bash training_25k/comp_11_build_index_and_gen_ours.sh

echo "=============================================="
echo "[$(date)] Part 2: NN-IR baseline (Direct + Prior)"
echo "=============================================="
bash training_25k/comp_13_gen_nnir_baseline.sh

echo "=============================================="
echo "[$(date)] WSL-side generation ALL COMPLETE."
echo "Next: run the Windows PowerShell execution block (see comp_run_eval.sh's own trailing instructions, or ask Claude)."
echo "=============================================="
