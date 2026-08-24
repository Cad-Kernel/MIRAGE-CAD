#!/bin/bash
# B1-K, geometry: does K=8's plan-level gain reach the SHAPE?
#
# WHY THIS IS NEEDED. B1-K raised plan quality substantially -- Op-Set F1 +3.78 pp
# [+2.02, +5.58] on STEP, +7.83 [+4.75, +10.98] on point -- and Build did not move
# (68.4% vs 71.4%, McNemar p = 0.203). That is the third time Build has failed to
# register a real change in plan content (docs SS9.8, SS9.10, SS9.14), and SS9.13
# established what does discriminate: geometry. Chamfer separated the correct prefix from
# a shuffled one by a factor of eight where Build separated them not at all.
#
# So the honest statement of B1-K is currently "K=8 produces better plans, and we do not
# know whether the resulting solids are closer to the target". This closes that.
#
# It is the same shape as 29_n1g_geometry_fidelity.sh: join the generated programs with
# the test set to attach point_path, wrap as all_candidates, score on Windows. No GPU,
# no generation, roughly ten minutes per arm.
#
# K=4's programs come from N1 (outputs/ablation_prefix/gen_step_prior.jsonl) and its
# geometry was already scored by 29 into scratch/geom_n1_step_prior -- so only the K=8
# arm needs preparing here, and the comparison is paired on the same 500 rows.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

WORK=outputs/b1k_sweep
SRC="$WORK/gen_step_K8.jsonl"

[ -s "$SRC" ] || { echo "FATAL: $SRC missing -- run 30_b1k_prefix_length_sweep.sh first." >&2; exit 1; }

python - <<'PY'
import json, pathlib, sys

work = pathlib.Path("outputs/b1k_sweep")
test = {}
for line in pathlib.Path("data/25k/test.jsonl").read_text(encoding="utf8").splitlines():
    if line.strip():
        r = json.loads(line)
        test[r["sample_id"]] = r

src = work / "gen_step_K8.jsonl"
dst = work / "geom_input_K8.jsonl"
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
print(f"  wrote {len(rows)} rows -> {dst.name}   (unmatched {missing}, empty program "
      f"{empty}, no point_path {no_target})")
if no_target:
    print(f"  WARNING: {no_target} rows lack point_path and cannot be scored.", file=sys.stderr)

# The K=4 arm must be the same 500 parts or the pairing is fiction.
k4 = pathlib.Path("outputs/ablation_prefix/geom_input_prior.jsonl")
if k4.exists():
    a = {json.loads(l)["sample_id"] for l in k4.read_text(encoding="utf8").splitlines() if l.strip()}
    b = {r["sample_id"] for r in rows}
    print(f"  part-set check vs K=4: K4={len(a)} K8={len(b)} shared={len(a & b)}"
          + ("  OK" if a == b else "  ** MISMATCH -- the comparison would not be paired **"))
else:
    print("  note: outputs/ablation_prefix/geom_input_prior.jsonl absent; run 29 first "
          "so the K=4 geometry arm exists.")
PY

cat <<'EOF'

=== NOW RUN THIS IN WINDOWS POWERSHELL (the only part WSL cannot do) ===

  & "C:\Workspace\Project\Paper\MIRAGE-V2\src\scripts\evaluate_geometry_nbest.ps1" `
    -InputJsonl "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\outputs\b1k_sweep\geom_input_K8.jsonl" `
    -OutputDir  "C:\Workspace\Project\Paper\MIRAGE-V2\scratch\geom_b1k_step_K8"

Then:

  python C:\Workspace\Project\Paper\MIRAGE-V2\src\scratch\b1k_geometry_analysis.py

K=4's geometry is already scored at scratch\geom_n1_step_prior (from 29_n1g), so nothing
needs re-running for that arm.

=== HOW TO READ IT, decided in advance ===

  K=8 clearly better on Chamfer/F@1%   the plan-level gain reaches the shape. B1-K is a
                                       genuine end-to-end improvement and the paper should
                                       recommend a larger K.
  indistinguishable                    K=8 writes plans that match the reference IR more
                                       closely without producing closer geometry. Report
                                       the IR gain and explicitly decline the end-to-end
                                       claim -- and note that IR-Op-Set F1 would then be
                                       measuring plan agreement rather than part fidelity,
                                       which matters for every table that uses it.
  K=8 worse                            the plan got closer to the reference text while the
                                       solid got further from the reference shape. That
                                       would be the most informative outcome of the three
                                       and needs reporting whatever it does to the story.
EOF
