#!/bin/bash
# B3 + B4: two cheap sample-size fixes that remove stated caveats from the paper.
#
# B3 -- the NN-IR baselines A and B are reported at n=100 while variant C is at
# n=2,500, so Table tab:generation mixes sample sizes within one table and the paper
# has to say so. A and B need no training and no plan generation: one retrieval plus
# one forward pass per row. Running them at the full 2,500 makes the table internally
# comparable for the first time.
#
# B4 -- the Stage 3 versus Stage 3b comparison disagrees in SIGN between n=100
# (+12pp) and n=2,500 (-4.4pp). Half of that was the first-hundred slice bias, now
# measured (Section 7.5). The other half is unresolved only because the Stage 3 arm
# was never re-run on the same random subset. It is an execution-only job: the Stage 3
# predicted plans already exist, so this needs code generation on 100 rows plus one
# Windows execution pass.
#
# Runs in WSL. No retraining.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

CODE=outputs/qwen25_coder_1_5b_program_25k_stage4b
ALIGN=outputs/align_25k
NNIR=outputs/nnir_baseline_25k_full
IDS=outputs/geometry_nbest_random100/ir_step.jsonl.ids.txt

# ===========================================================================
# B3: NN-IR baselines at the full 2,500 rows
#
# THE FIRST VERSION OF THIS BLOCK WAS WRONG AND FAILED SILENTLY. It re-ran
# gen_code_from_predicted_ir.py over outputs/nnir_baseline_25k/${MODE}_${M}.jsonl,
# which iterates the IR file -- and that file holds 100 rows, because the RETRIEVAL
# step was itself run with --limit 100. So it regenerated the same hundred rows and
# exited 0. The guard was `|| { ...; break 2; }`, which only fires on a crash; the
# actual failure mode is silent under-coverage, and it produced a directory named
# `_full` containing 100-row files.
#
# NN-IR retrieval and code generation live in the same script, so reaching 2,500 means
# re-running gen_nn_ir_baseline.py, not re-generating code from short plan files.
#
# This also fixes a second defect nobody had noticed: --limit 100 takes the FIRST
# hundred test rows, the slice docs SS9.2 measured at ~10 pp optimistic. So the
# published A/B rows of tab:generation are wrong on sample size AND on slice. At
# n=2500 there is no slice at all.
#
# COST: ~3.2 s/row at batch 16, x 2500 rows x 8 conditions ~ 18 h. Set B3_LIMIT to
# trade coverage for time (500 -> ~3.5 h, and still 5x the current n with no slice
# bias if the retrieval is drawn from the full test set).
# ===========================================================================
B3_LIMIT="${B3_LIMIT:-2500}"
B3_BATCH="${B3_BATCH:-16}"
mkdir -p "$NNIR"
echo "=== B3: NN-IR baselines at n=$B3_LIMIT ==="
echo "Re-running RETRIEVAL + generation. The retrieval index stays the TRAIN index --"
echo "rebuilding it on test would destroy the experiment."

for M in step point text image; do
  case $M in
    step)  PRIOR=outputs/prior_step_25k/best.pt ;;
    point) PRIOR=outputs/prior_point_25k/best.pt ;;
    text)  PRIOR=outputs/prior_text_25k/best.pt ;;
    image) PRIOR=outputs/prior_image_25k/best.pt ;;
  esac
  for MODE in direct prior; do
    RAW="$NNIR/${MODE}_${M}.jsonl"
    OUT="$NNIR/${MODE}_${M}_repaired_p0.jsonl"
    if [ -s "$OUT" ]; then echo "  skip $MODE/$M (exists)"; continue; fi
    echo "  --- $MODE / $M ---"
    python scratch/gen_nn_ir_baseline.py \
      --modality "$M" --retrieval-mode "$MODE" \
      --alignment-checkpoint "$ALIGN/best.pt" \
      --prior-checkpoint "$PRIOR" \
      --retrieval-index "$ALIGN/train_ir_index.npz" \
      --lora-code-dir "$CODE" \
      --input-jsonl data/25k/test.jsonl \
      --output-jsonl "$RAW" \
      --limit "$B3_LIMIT" --batch-size "$B3_BATCH" \
      --max-length 1536 --max-new-tokens 1536

    # Assert coverage BEFORE spending the next seven conditions on the same mistake.
    GOT=$(wc -l < "$RAW")
    if [ "$GOT" -lt "$B3_LIMIT" ]; then
      echo "FATAL: asked for $B3_LIMIT rows, got $GOT in $RAW." >&2
      echo "  Silent under-coverage is exactly what the previous version of this block" >&2
      echo "  did. Not continuing. Check that data/25k/test.jsonl has >= $B3_LIMIT rows" >&2
      echo "  and that every row carries the field this modality needs." >&2
      exit 1
    fi
    echo "  coverage OK: $GOT rows"

    # Same two repair passes the published A/B rows used, so the only thing that
    # changes against them is n.
    MID="$NNIR/${MODE}_${M}_repaired.jsonl"
    python3 scratch/repair_extrude_on_face.py "$RAW" "$MID"
    python3 scratch/repair_profile_cut_offset.py "$MID" "$OUT"
  done
done

# ===========================================================================
# B4: Stage 3 arm on the same seeded random 100 subset as Stage 3b
# ===========================================================================
echo
echo "=== B4: Stage 3 arm on the random-100 subset ==="
if [ ! -f "$IDS" ]; then
  echo "  ERROR: $IDS not found -- run 20_rerun_geometry_nbest_random100.sh first," >&2
  echo "         it is what defines the shared subset." >&2
  exit 1
fi
W=outputs/b4_stage3_random100
mkdir -p "$W"

# Same ids, Stage 3 plans (outputs/lora_ir_25k), so the only variable against
# Stage 3b is the plan generator.
python training_25k/scripts/make_random_subset.py \
  --input outputs/lora_ir_25k/predicted_ir_test_step_p1a.jsonl \
  --output "$W/ir_step_stage3.jsonl" \
  --ids-from "$IDS"

python training_25k/scripts/gen_code_from_predicted_ir.py \
  --modality step \
  --ir-jsonl "$W/ir_step_stage3.jsonl" \
  --lora-code-dir "$CODE" \
  --input-jsonl data/25k/test.jsonl \
  --output-jsonl "$W/gen_step_stage3.jsonl" \
  --max-length 1536 --max-new-tokens 1536 --batch-size 16

python3 scratch/repair_extrude_on_face.py "$W/gen_step_stage3.jsonl" "$W/gen_step_stage3_r.jsonl"
python3 scratch/repair_profile_cut_offset.py "$W/gen_step_stage3_r.jsonl" "$W/gen_step_stage3_repaired_p0.jsonl"

cat <<'EOF'

=== Windows PowerShell: execute both arms ===

  # B4: Stage 3 arm on the shared random subset
  & "C:\Workspace\Project\Paper\MIRAGE-V2\src\scripts\evaluate_execution.ps1" `
    -InputJsonl "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\outputs\b4_stage3_random100\gen_step_stage3_repaired_p0.jsonl" `
    -OutputDir  "C:\Workspace\Project\Paper\MIRAGE-V2\scratch\exec_b4_stage3_random100_step"

  # B3: the NN-IR baselines. The WSL side asserts row coverage before it gets here,
  # so if this block prints at all the files are full-length. Same repair pipeline
  # (_repaired_p0) as the published n=100 rows, so n is the only thing that changed.
  foreach ($m in @("step","point","text","image")) {
    foreach ($mode in @("direct","prior")) {
      & "C:\Workspace\Project\Paper\MIRAGE-V2\src\scripts\evaluate_execution.ps1" `
        -InputJsonl "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\outputs\nnir_baseline_25k_full\${mode}_${m}_repaired_p0.jsonl" `
        -OutputDir  "C:\Workspace\Project\Paper\MIRAGE-V2\scratch\exec_nnir_full_${mode}_${m}"
    }
  }

  # The published n=100 rows live in outputs\nnir_baseline_25k\ and are NOT touched
  # by this run -- outputs\nnir_baseline_25k_full\ is a separate directory, so
  # tab:generation's current numbers stay reproducible until they are replaced
  # deliberately.

=== What B4 settles ===

Compare exec_b4_stage3_random100_step against Table tab:geometry's STEP N=1 (67.0%,
Stage 3b on the identical 100 parts). Both arms are then the same subset, the same
code decoder and the same repair, so the difference is attributable to the plan
generator alone and the sign conflict resolves one way or the other. Whichever way it
goes, Section 8.3's "we decline to compute a difference from them" can be replaced by
a number.
EOF
