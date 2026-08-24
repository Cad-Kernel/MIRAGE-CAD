#!/bin/bash
# C-EXT1-min: four arms on Fusion 360 Gallery, and what they can and cannot settle.
#
# THE ONE QUESTION. Inside FllumaOne, retrieving the nearest training IR is close to an
# oracle -- median Op-Set F1 of 1.0, Build in the high nineties. Does that survive contact
# with CAD authored by another tool?
#
# THE ARMS. Two modalities crossed with two ways of getting a plan. Same checkpoints, same
# repair passes, same execution harness as the published runs; only the input rows change.
#
#   A  step  · generated plan   comparable with every internal ablation
#   B  step  · prior-NN-IR      the core contrast
#   C  point · generated plan   scale-invariant input, so it survives the size problem below
#   D  point · prior-NN-IR      same
#
# A VERSUS B IS A DESIGNED DISCRIMINATOR, because both arms share one encoder:
#
#   both collapse            the common cause is the encoder or domain shift, and this says
#                            nothing about whether the corpus holds compatible history
#   generated holds, NN-IR   points at the INDEX -- the finding the paper wants
#   collapses
#   NN-IR still strong       procedural retrieval is a strong cross-source prior. Negative
#                            for the framing, valuable, and it must be reported
#   both build, both wrong   executability and target fidelity are decoupled, which is the
#   geometrically            same lesson the internal Build gate already taught
#
# WHAT CANNOT BE MEASURED HERE. External models ship no reference plan and no reference
# program, so Op-Set F1, LCS and Prog-Op-F1 do not exist on this set -- they are all
# agreement-with-a-reference-plan measures. Build, STEP export and geometry are the whole
# metric set. That is not a loss: the internal work established that the IR metrics track
# plan agreement rather than part fidelity, so geometry was always going to carry this.
#
# THE STRATUM RULE, FIXED BEFORE THE RUN. FllumaOne parts span 9 to 134 mm; 35.5% of the
# external set is larger, up to four kilometres, and those extents are real -- the sibling
# .obj agrees to a factor of ten on every file. The STEP descriptor carries bbox, area and
# volume under log1p as ABSOLUTE quantities, so those parts are extrapolation for the
# encoder, while `load_point_cloud_sampled` normalises and the point arms are unaffected.
# So: report all four arms on all 400, but read A-vs-B only on the 258 within-band parts.
# Nothing is filtered out -- trimming the published test split would spoil the sampling
# frame and would look like dropping the hard cases.
#
# The descriptor shift is narrower than the bbox spread suggests, which is what makes the
# within-band reading trustworthy: of fifty descriptor dimensions, the thirteen magnitude
# ones are the only ones out of range, and the median count/topology dimensions outside is
# zero in every stratum against a held-out corpus control of zero. Fusion 360 geometry is
# structurally familiar to this encoder and differently sized.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

EXT=data/external/fusion360
WORK=outputs/external_fusion360
ROWS="$EXT/rows.jsonl"
S4B_DIR="${S4B_DIR:-outputs/qwen25_coder_1_5b_program_25k_stage4b}"
LORA_IR="${LORA_IR:-outputs/lora_ir_25k_stage3b}"
ALIGN=outputs/align_25k/best.pt
INDEX=outputs/align_25k/train_ir_index.npz
# gen_nn_ir_baseline.py defaults --limit to 20, a smoke-test leftover, and --batch-size to
# 1. Omitting the first produced a 20-row arm that the row assertion caught; omitting the
# second costs 25 seconds a row, so 2.8 hours per arm against about ten minutes batched.
# Whether batching is free here is measured, not assumed -- scratch/nnir_batch_equivalence.py
# compares the two on the same twenty rows. Set NNIR_BATCH=1 to run it the published way.
NNIR_BATCH="${NNIR_BATCH:-16}"
mkdir -p "$WORK"

# --- preconditions: fail here, not four hours in --------------------------------
for f in "$EXT/step_index.jsonl" "$ALIGN" "$INDEX" "$S4B_DIR/adapter_config.json" \
         "$LORA_IR/adapter_config.json"; do
  [ -e "$f" ] || { echo "FATAL: missing $f" >&2; exit 1; }
done

python training_25k/scripts/make_external_rows.py \
  --index "$EXT/step_index.jsonl" --output "$ROWS"

N=$(wc -l < "$ROWS")
[ "$N" -ge 300 ] || { echo "FATAL: only $N rows; expected ~400." >&2; exit 1; }

# Every row must resolve on both paths before anything is generated: a missing feature file
# would make gen_predicted_ir raise mid-run, and a missing cloud would silently drop the
# part from geometry scoring afterwards, which is worse because it looks like a result.
python - "$ROWS" <<'PY'
import json, sys
from pathlib import Path
rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
bad = [(r["sample_id"], k) for r in rows for k in ("step_feature_path", "point_path")
       if not Path(r[k]).is_file()]
if bad:
    print(f"FATAL: {len(bad)} unresolved paths, e.g. {bad[:3]}", file=sys.stderr)
    raise SystemExit(1)
inside = sum(1 for r in rows if (r.get("bbox_diag") or 0) <= 134.30)
print(f"  {len(rows)} rows, all paths resolve; {inside} within the corpus scale band")
PY

run_generated_plan () {           # arm A (step) and arm C (point)
  local m=$1
  local prior="outputs/prior_${m}_25k/best.pt"
  [ -f "$prior" ] || { echo "FATAL: missing $prior" >&2; exit 1; }
  local ir="$WORK/ir_${m}.jsonl"
  local raw="$WORK/gen_${m}_genplan.jsonl"
  local out="$WORK/gen_${m}_genplan_repaired_p0.jsonl"
  if [ -s "$out" ]; then echo "=== skip [$m/generated plan] (exists) ==="; return; fi

  # The plan stage is the expensive half -- fifty minutes for 400 rows -- and the code
  # stage downstream of it has crashed once already on a field external rows do not carry.
  # Skipping a COMPLETE plan file means a failure in the cheap half costs minutes, not
  # another hour. The row count is what makes "complete" mean something: a short file is a
  # truncated run and gets redone.
  local n
  if [ -s "$ir" ] && [ "$(wc -l < "$ir")" -eq "$N" ]; then
    echo "=== [$m / generated plan] reusing $ir ($N rows) ==="
  else
    echo "=== [$m / generated plan] predicting construction plans ==="
    python training_25k/scripts/gen_predicted_ir.py \
      --modality "$m" \
      --alignment-checkpoint "$ALIGN" --prior-checkpoint "$prior" \
      --lora-ir-dir "$LORA_IR" \
      --input-jsonl "$ROWS" --output-jsonl "$ir" \
      --max-length 1024 --max-new-tokens 512
    n=$(wc -l < "$ir")
    [ "$n" -eq "$N" ] || { echo "FATAL: IR rows $n != $N" >&2; exit 1; }
  fi

  echo "=== [$m / generated plan] generating programs ==="
  python training_25k/scripts/gen_code_from_predicted_ir.py \
    --modality "$m" --lora-code-dir "$S4B_DIR" \
    --ir-jsonl "$ir" --input-jsonl "$ROWS" --output-jsonl "$raw" \
    --max-length 1536 --max-new-tokens 1536 --batch-size 16
  n=$(wc -l < "$raw")
  [ "$n" -eq "$N" ] || { echo "FATAL: program rows $n != $N" >&2; exit 1; }

  python3 scratch/repair_extrude_on_face.py "$raw" "$WORK/gen_${m}_genplan_r.jsonl"
  python3 scratch/repair_profile_cut_offset.py "$WORK/gen_${m}_genplan_r.jsonl" "$out"
}

run_nn_ir () {                    # arm B (step) and arm D (point)
  local m=$1
  local prior="outputs/prior_${m}_25k/best.pt"
  local raw="$WORK/gen_${m}_nnir.jsonl"
  local out="$WORK/gen_${m}_nnir_repaired_p0.jsonl"
  if [ -s "$out" ]; then echo "=== skip [$m/prior-NN-IR] (exists) ==="; return; fi

  echo "=== [$m / prior-NN-IR] retrieving and generating ==="
  python scratch/gen_nn_ir_baseline.py \
    --modality "$m" --retrieval-mode prior \
    --alignment-checkpoint "$ALIGN" --prior-checkpoint "$prior" \
    --retrieval-index "$INDEX" --lora-code-dir "$S4B_DIR" \
    --input-jsonl "$ROWS" --output-jsonl "$raw" \
    --limit "$N" --batch-size "$NNIR_BATCH" \
    --max-length 1536 --max-new-tokens 1536
  local n; n=$(wc -l < "$raw")
  [ "$n" -eq "$N" ] || { echo "FATAL: NN-IR rows $n != $N" >&2; exit 1; }

  python3 scratch/repair_extrude_on_face.py "$raw" "$WORK/gen_${m}_nnir_r.jsonl"
  python3 scratch/repair_profile_cut_offset.py "$WORK/gen_${m}_nnir_r.jsonl" "$out"
}

for m in step point; do
  run_generated_plan "$m"
  run_nn_ir "$m"
done

cat > "$WORK/run_metadata.json" <<JSON
{
  "experiment": "C-EXT1-min, four arms on Fusion 360 Gallery",
  "n": $N,
  "frame": "published test split of train_test.json, sampled with seed 20260810",
  "arms": ["step/generated-plan", "step/prior-NN-IR", "point/generated-plan", "point/prior-NN-IR"],
  "checkpoints": {"align": "$ALIGN", "lora_ir": "$LORA_IR", "lora_code": "$S4B_DIR", "index": "$INDEX"},
  "metrics_available": ["build", "step_export", "chamfer", "f_at_1pct"],
  "metrics_unavailable": "IR-level metrics -- external models ship no reference plan or program",
  "stratum_rule": "A-vs-B is readable only on parts with bbox_diag <= 134.30 mm, the corpus range; the STEP descriptor is absolute while the point path normalises",
  "repair_applied": true
}
JSON

cat <<'EOF'

=== generation done. Execution needs Windows PowerShell ===

Run all four, one at a time. Outputs go to Windows-local directories on purpose: a Python
process reading \\wsl.localhost fails intermittently, so nothing here touches a UNC path.

  foreach ($a in @("step_genplan","step_nnir","point_genplan","point_nnir")) {
    & "C:\Workspace\Project\Paper\MIRAGE-V2\src\scripts\evaluate_execution.ps1" `
      -InputJsonl "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\outputs\external_fusion360\gen_${a}_repaired_p0.jsonl" `
      -OutputDir  "C:\Workspace\Project\Paper\MIRAGE-V2\scratch\exec_ext_$a"
  }

If the PowerShell harness itself trips on the UNC input, copy the four files across first
from a WSL shell and point the harness at the local copies instead.

Then post the four execution summaries. The analysis script is deliberately NOT written
yet: it has to stratify by bbox_diag and run McNemar on the paired arms, and both depend
on the exact fields the execution harness emits for external rows, which no run has
produced. Writing it now would mean guessing a schema and, worse, guessing baselines --
that is how an earlier analysis script ended up with two invented comparison numbers.

Geometry is scored against the reference clouds already built, at the scorer's default
1024 points. Quote the external ceilings from docs 9.19, never the internal 0.244.
EOF
