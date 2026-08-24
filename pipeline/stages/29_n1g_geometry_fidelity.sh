#!/bin/bash
# N1g: the fidelity half of the prefix ablation, which Build could not supply.
#
# N1 established that the plan decoder reads the prefix's CONTENTS -- another sample's
# latent costs 53 points of IR-Op-Set F1 -- and, in the same run, that **Build cannot
# see any of it**: prior 71.4%, oracle_ir 69.2%, shuffled 68.6%, McNemar p = 0.37 /
# 0.26 / 0.89, none separable. Among the 246 STEP rows that build under both prior and
# shuffled, exact operation-set agreement with the reference is 80.1% against 5.3%.
#
# So a program can execute, validate as a solid and export STEP while describing the
# WRONG PART. Build is a validity gate. The fidelity claim needs geometry.
#
# This scores generated solids against the query's own reference point cloud:
# symmetric Chamfer Distance and F-score@1% of the target's bbox diagonal, the same
# metrics as tab:geometry, via the same scorer (evaluate_geometry_nbest.py).
#
# CORRECTION TO AN EARLIER PLAN NOTE. This was described as "scoring only, the STEP
# files already exist". They do not: evaluate_execution.ps1 exports each candidate to a
# temp directory and discards it, so scratch/exec_n1_step_*/ holds only the gate
# booleans. This re-executes. It is still cheap -- no GPU, no generation, ~1,000
# candidates total -- but it is not free.
#
# WHAT IT SETTLES:
#   CD(prior) << CD(shuffled)   the prefix controls geometry, not just plan text.
#                               Build's blindness is a property of the METRIC, and the
#                               conditioning claim is fully evidenced.
#   CD(prior) ~= CD(shuffled)   far more serious: the prefix would be steering plan
#                               text without steering the resulting SHAPE, and every
#                               geometric claim in the paper would need re-examining.
#                               Report it either way.
#
# WSL prepares the inputs; Windows scores them (FllumaCLI hosts the only Python that
# can import flluma).
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

WORK=outputs/ablation_prefix
TEST=data/25k/test.jsonl
MODES="prior shuffled oracle_ir"

for MODE in $MODES; do
  [ -s "$WORK/gen_step_${MODE}.jsonl" ] || {
    echo "FATAL: $WORK/gen_step_${MODE}.jsonl missing -- run 24_n1_prefix_source_ablation.sh first." >&2
    exit 1; }
done

# ---------------------------------------------------------------------------
# Prep: evaluate_geometry_nbest.py expects `all_candidates` (a list of programs) and
# `point_path` (the reference cloud). The N1 files carry one `prediction` per row and
# no point_path, so join against the test set and wrap. One candidate per row means
# the scorer's N-best machinery degenerates to a single evaluation, which is what we
# want -- this is a fidelity comparison at N=1, not a selection experiment.
# ---------------------------------------------------------------------------
python - <<'PY'
import json, pathlib, sys

work = pathlib.Path("outputs/ablation_prefix")
test = {}
for line in pathlib.Path("data/25k/test.jsonl").read_text(encoding="utf8").splitlines():
    if line.strip():
        r = json.loads(line)
        test[r["sample_id"]] = r

for mode in ("prior", "shuffled", "oracle_ir"):
    src = work / f"gen_step_{mode}.jsonl"
    dst = work / f"geom_input_{mode}.jsonl"
    rows, missing, empty = [], 0, 0
    for line in src.read_text(encoding="utf8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        t = test.get(r["sample_id"])
        if t is None:
            missing += 1
            continue
        code = r.get("prediction") or ""
        if not code.strip():
            empty += 1
        rows.append({
            "sample_id": r["sample_id"],
            "modality": r.get("modality", "step"),
            "point_path": t.get("point_path", ""),
            "all_candidates": [code],
        })
    # A row without point_path scores as has_target=false and silently drops out of
    # every mean -- check now rather than discovering it in the output.
    no_target = sum(1 for r in rows if not r["point_path"])
    dst.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                   encoding="utf8")
    print(f"  {mode:<10} wrote {len(rows)} rows -> {dst.name}"
          f"   (unmatched sample_id {missing}, empty program {empty}, "
          f"no point_path {no_target})")
    if no_target:
        print(f"  WARNING: {no_target} rows lack point_path and cannot be scored.",
              file=sys.stderr)
PY

echo
echo "=== prepared. Row counts must match across modes for the comparison to be paired ==="
wc -l "$WORK"/geom_input_*.jsonl | sed 's|^|  |'

cat <<'EOF'

=== NOW RUN THIS IN WINDOWS POWERSHELL (the only part WSL cannot do) ===

Everything above already ran. Scoring needs FllumaCLI. Paste as-is -- PowerShell
syntax, not bash. Roughly ten minutes for all three.

  foreach ($MODE in @("prior","shuffled","oracle_ir")) {
    & "C:\Workspace\Project\Paper\MIRAGE-V2\src\scripts\evaluate_geometry_nbest.ps1" `
      -InputJsonl "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\outputs\ablation_prefix\geom_input_$MODE.jsonl" `
      -OutputDir  "C:\Workspace\Project\Paper\MIRAGE-V2\scratch\geom_n1_step_$MODE"
  }

Then, for the paired comparison:

  python C:\Workspace\Project\Paper\MIRAGE-V2\src\scratch\n1g_geometry_analysis.py

CONSISTENCY: same no-repair setting as the rest of N1 (run_metadata.json records
repair_applied=false), and the same batch-16 generations, so these numbers are
internally comparable and must not be mixed with tab:geometry.
EOF
