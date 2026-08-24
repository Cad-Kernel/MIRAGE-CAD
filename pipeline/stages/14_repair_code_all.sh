#!/bin/bash
# Phase 6 repair steps 2+3: extrude_on_face keyword/value repair, then P0
# (profile_cut offset padding), applied to generated CODE (the 'prediction'
# field -- not predicted_ir; P1a in step 12 already handled the IR-level
# repair). Order matters, do not swap: extrude_on_face first, then P0.
#
# WARNING: scratch/repair_extrude_on_face.py and scratch/repair_profile_cut_offset.py
# have NO argparse (bare sys.argv[1]/[2] positional args) and NO dry-run gate
# -- they always write, and silently fall back to hardcoded 5K-scale default
# paths if you forget to pass both arguments. This script always passes both
# explicitly; do not invoke either script manually without doing the same.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

for m in step point text image; do
  echo "=== code repair: $m ==="
  IN="outputs/qwen25_coder_1_5b_program_25k_stage4b/gen_test_${m}.jsonl"
  MID="outputs/qwen25_coder_1_5b_program_25k_stage4b/gen_test_${m}_repaired.jsonl"
  OUT="outputs/qwen25_coder_1_5b_program_25k_stage4b/gen_test_${m}_repaired_p0.jsonl"
  python3 scratch/repair_extrude_on_face.py "$IN" "$MID"
  python3 scratch/repair_profile_cut_offset.py "$MID" "$OUT"
done

echo "=== Wrote outputs/qwen25_coder_1_5b_program_25k_stage4b/gen_test_{step,point,text,image}_repaired_p0.jsonl ==="
