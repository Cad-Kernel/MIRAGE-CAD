#!/bin/bash
# Does the plan improve the SHAPE, or only how often a program builds?
#
# The no-plan baseline settled executability: 70.0% build against 35.4%, McNemar
# p < 1e-160 (docs SS9.18). What it did not settle is whether the parts that DO build
# are any closer to their targets, and this round has shown three times that build rate
# is a validity gate insensitive to plan content (SS9.8, SS9.10, SS9.14). SS9.13 showed
# geometry is what discriminates. So the no-plan claim is currently scoped to executable
# validity, and this is what would widen it.
#
# ONLY ONE ARM NEEDS SCORING. The with-plan arm is variant C on STEP, which
# 32_stage3b_geometry.sh already scored into scratch/geom_stage3b_step_stage3b -- its
# export count (1,654) matches tab:main_25k exactly, so the identity is checked rather
# than assumed. This preps the no-plan arm only. Roughly 50 minutes of Windows CPU.
#
# THE SELECTION EFFECT IS SEVERE HERE, AND IT RUNS THE OTHER WAY FROM SS9.17.
# The no-plan arm exports 864 parts, the plan-mediated arm 1,654. Only parts BOTH export
# can be compared geometrically, so the shared set is at most 864 and consists precisely
# of the parts the plan-free model could already handle -- the easiest ones. The plan's
# value on the ~800 parts only it can build is invisible to this comparison BY
# CONSTRUCTION, because those parts have no no-plan geometry to compare against.
#
# HOW TO READ IT, fixed before the run:
#
#   with-plan better    the plan improves fidelity on top of buildability, and it does so
#                       even on the subset that favours the baseline. Strong.
#   not separable       the plan's value is concentrated in buildability. On the easy
#                       parts both arms reconstruct comparably. This is NOT a negative
#                       result given the selection: it says the plan converts failures
#                       into successes rather than refining successes. Report it that way.
#   with-plan worse     would be surprising and would need reporting -- the plan would be
#                       buying build success at the cost of accuracy on easy parts.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

WORK=outputs/noplan_baseline
SRC="$WORK/gen_step_noplan_repaired_p0.jsonl"

[ -s "$SRC" ] || { echo "FATAL: $SRC missing -- run 33_noplan_baseline.sh first." >&2; exit 1; }
N=$(wc -l < "$SRC"); [ "$N" -eq 2500 ] || { echo "FATAL: $SRC has $N rows, expected 2500." >&2; exit 1; }

python - <<'PY'
import json, pathlib, sys

work = pathlib.Path("outputs/noplan_baseline")
test = {}
for line in pathlib.Path("data/25k/test.jsonl").read_text(encoding="utf8").splitlines():
    if line.strip():
        r = json.loads(line)
        test[r["sample_id"]] = r

src = work / "gen_step_noplan_repaired_p0.jsonl"
dst = work / "geom_input_noplan.jsonl"
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
    rows.append({"sample_id": r["sample_id"], "modality": "step",
                 "point_path": t.get("point_path", ""), "all_candidates": [code]})
no_target = sum(1 for r in rows if not r["point_path"])
dst.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf8")
print(f"  wrote {len(rows)} rows -> {dst.name}   (unmatched {missing}, empty {empty}, "
      f"no point_path {no_target})")

# The with-plan arm must cover the same parts or the pairing is fiction.
ref = pathlib.Path("outputs/stage3b_geometry/geom_input_step_stage3b.jsonl")
if ref.exists():
    a = {json.loads(l)["sample_id"] for l in ref.read_text(encoding="utf8").splitlines() if l.strip()}
    b = {r["sample_id"] for r in rows}
    print(f"  part-set check vs with-plan arm: {len(a)} / {len(b)} shared {len(a & b)}"
          + ("  OK" if a == b else "  ** MISMATCH -- not paired **"))
else:
    print("  note: outputs/stage3b_geometry/geom_input_step_stage3b.jsonl absent; run 32 first.",
          file=sys.stderr)
PY

cat <<'EOF'

=== NOW RUN THIS IN WINDOWS POWERSHELL (the only part WSL cannot do) ===

Only the no-plan arm needs scoring; the with-plan arm is already at
scratch\geom_stage3b_step_stage3b from 32_stage3b_geometry.sh.

  & "C:\Workspace\Project\Paper\MIRAGE-V2\src\scripts\evaluate_geometry_nbest.ps1" `
    -InputJsonl "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\outputs\noplan_baseline\geom_input_noplan.jsonl" `
    -OutputDir  "C:\Workspace\Project\Paper\MIRAGE-V2\scratch\geom_noplan_step"

Then, for the full no-plan comparison including geometry:

  python C:\Workspace\Project\Paper\MIRAGE-V2\src\scratch\noplan_analysis.py

The analysis reports the shared-set size and the export counts of both arms alongside
the result, because with 864 against 1,654 exports the comparison sits on the parts the
plan-free model could already handle and says nothing about the ~800 it could not.
EOF
