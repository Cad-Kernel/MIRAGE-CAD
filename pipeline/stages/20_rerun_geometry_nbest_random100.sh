#!/bin/bash
# Re-run the best-of-N geometry evaluation on a SEEDED RANDOM 100-sample subset,
# with the sampling parameters passed explicitly and recorded.
#
# Two reasons this run exists (review items B5 and sampling-params):
#
#   B5 -- every existing 100-sample table used `--limit 100`, which takes the FIRST
#   hundred rows of the file. Those slices run about ten points optimistic against
#   the full 2,500-row test set: STEP 79.0% vs 70.0%, point-cloud 67.0% vs 55.4%.
#   Same direction, similar size, both modalities -- a systematic offset, not noise.
#   A seeded random subset removes it.
#
#   sampling-params -- the parameters were never stated in the paper. They are in
#   fact determinate from code (scratch/gen_nbest_candidates.py: candidate 0 is
#   generate_text(..., 0.0, 1.0) = greedy; candidates 1..N-1 use args.temperature,
#   default 0.8, with top_p hard-coded 1.0; there is no --top-p flag). Section 5.8
#   now states N=10, T=0.8, top-p=1.0. This run passes --temperature and --seed
#   EXPLICITLY rather than relying on defaults, and writes a run-metadata JSON, so
#   the next person does not have to re-derive them from the source.
#
# Both modalities are scored on the SAME parts (point-cloud reuses STEP's drawn
# ids), which the old run did not guarantee -- so a point-vs-STEP comparison
# becomes legitimate for the first time.
#
# Everything downstream of generation is unchanged and reuses the existing
# CLI-parameterized scripts.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

IR_S3B=outputs/lora_ir_25k_stage3b
S4B_DIR=outputs/qwen25_coder_1_5b_program_25k_stage4b
WORK=outputs/geometry_nbest_random100
N_SAMPLES=100
N_CAND=10
TEMPERATURE=0.8
SEED=20260804

mkdir -p "$WORK"

# ---------------------------------------------------------------------------
# 0. Draw the subset once, from STEP, then reuse the same sample_ids for point.
#    Both modalities have predicted_ir for the whole test set, so the same parts
#    exist in both files.
# ---------------------------------------------------------------------------
echo "=== drawing seeded random $N_SAMPLES-sample subset (seed $SEED) ==="
python training_25k/scripts/make_random_subset.py \
  --input  "$IR_S3B/predicted_ir_test_step_p1a.jsonl" \
  --output "$WORK/ir_step.jsonl" \
  --n "$N_SAMPLES" --seed "$SEED"

python training_25k/scripts/make_random_subset.py \
  --input  "$IR_S3B/predicted_ir_test_point_p1a.jsonl" \
  --output "$WORK/ir_point.jsonl" \
  --ids-from "$WORK/ir_step.jsonl.ids.txt"

# ---------------------------------------------------------------------------
# 1. Candidate generation, sampling parameters passed explicitly.
# ---------------------------------------------------------------------------
for m in step point; do
  echo "=== [$m] N-best generation: N=$N_CAND (1 greedy + $((N_CAND-1)) sampled), T=$TEMPERATURE ==="
  python scratch/gen_nbest_candidates.py \
    --modality "$m" \
    --ir-jsonl "$WORK/ir_${m}.jsonl" \
    --lora-code-dir "$S4B_DIR" \
    --input-jsonl data/25k/test.jsonl \
    --output-jsonl "$WORK/nbest_${m}.jsonl" \
    --limit "$N_SAMPLES" \
    --num-candidates "$N_CAND" \
    --temperature "$TEMPERATURE" \
    --seed "$SEED" \
    --point-count 1024 \
    --max-length 1536 --max-new-tokens 1536

  echo "=== [$m] repair (extrude_on_face + P0) on every candidate ==="
  python3 scratch/repair_nbest_candidates.py \
    "$WORK/nbest_${m}.jsonl" "$WORK/nbest_${m}_repaired.jsonl"
done

# ---------------------------------------------------------------------------
# 2. Record exactly what was run. This file is the point of the exercise.
# ---------------------------------------------------------------------------
cat > "$WORK/run_metadata.json" <<JSON
{
  "purpose": "B5 (random rather than first-100 slice) + explicit sampling parameters",
  "subset": {"n": $N_SAMPLES, "seed": $SEED, "selection": "random.Random(seed).sample",
             "ids_file": "$WORK/ir_step.jsonl.ids.txt",
             "shared_across_modalities": true},
  "generation": {"num_candidates": $N_CAND,
                 "candidate_0": "greedy (temperature 0.0, top_p 1.0, do_sample=False)",
                 "candidates_1_to_N": {"temperature": $TEMPERATURE, "top_p": 1.0,
                                        "note": "top_p is hard-coded 1.0 in gen_nbest_candidates.py; no CLI flag exists"},
                 "torch_manual_seed": $SEED,
                 "per_call_seeding": false,
                 "point_count": 1024, "max_length": 1536, "max_new_tokens": 1536},
  "checkpoints": {"lora_ir": "$IR_S3B", "lora_code": "$S4B_DIR"},
  "repair": ["scratch/repair_nbest_candidates.py (extrude_on_face + P0)"],
  "supersedes": "outputs/geometry_nbest_25k_stage3b (first-100 slice, defaults not recorded)"
}
JSON
echo "=== wrote $WORK/run_metadata.json ==="

cat <<'EOF'

=== WSL side done. Now in Windows PowerShell (real Flluma/OpenCASCADE execution): ===

$Root = "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src"
$Work = "outputs\geometry_nbest_random100"

foreach ($m in @("step","point")) {
  # Step 1: per-candidate five-gate execution.
  & "C:\Workspace\Project\Paper\MIRAGE-V2\src\scripts\evaluate_execution_nbest.ps1" `
    -InputJsonl (Join-Path $Root "$Work\nbest_${m}_repaired.jsonl") `
    -OutputDir "C:\Workspace\Project\Paper\MIRAGE-V2\scratch\exec_nbest_random100_${m}"

  # Step 2: Chamfer + F@1% geometry scoring. Feed it the SAME repaired-candidates
  # file, NOT step 1's output -- step 1 drops modality/point_path/step_path/
  # all_candidates, and without them every row silently gets has_target=False and
  # the aggregator divides by zero. This bit has bitten this project before.
  & "C:\Workspace\Project\Paper\MIRAGE-V2\src\scripts\evaluate_geometry_nbest.ps1" `
    -InputJsonl (Join-Path $Root "$Work\nbest_${m}_repaired.jsonl") `
    -OutputDir "C:\Workspace\Project\Paper\MIRAGE-V2\scratch\geometry_nbest_random100_${m}"
}

=== Then aggregate (WSL, or any Python with numpy): ===

  for m in step point; do
    echo "--- $m ---"
    python3 scratch/aggregate_geometry_nbest.py \
      "/mnt/c/Workspace/Project/Paper/MIRAGE-V2/scratch/geometry_nbest_random100_${m}/geometry_nbest_rows.jsonl"
  done

This prints Median CD / Median F@1% per N=1/3/5/10 for both modalities. Those
numbers replace Table tab:geometry and Table tab:ablation_selection.

WHEN UPDATING THE PAPER, three things change besides the numbers:
  1. The captions must say "seeded random 100-sample subset (seed 20260804)"
     instead of the current wording, and the sentence about not being comparable
     to the pilot-scale table stays true.
  2. Section 8.3's "unreconciled disagreement between sample sizes" paragraph
     should be revisited: if the random-slice N=1 STEP Build lands near the full-set
     70.0% rather than 79.0%, the +12pp/-4.4pp sign conflict is explained by the
     slice bias and that paragraph can be shortened to say so.
  3. Both modalities now share one sample set, so a point-vs-STEP CD comparison is
     finally licensed -- but CD is still in mm^2 on unnormalised geometry, so the
     comparison is of reconstruction quality on a shared reference, not of
     scale-free accuracy.
EOF
