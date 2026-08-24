#!/bin/bash
# C-EXT1-min, the part that actually decides it: does any arm build the RIGHT part?
#
# Build already came in and settled nothing. Retrieving the nearest training plan builds at
# 99.2% on externally authored CAD against 69.0% for a generated one, and the advantage is
# nested -- exactly one part in 400 builds under a generated plan and not under retrieval.
# That is what writing code close to a program that already executed would predict, and it
# is a validity gate reading. The paper has three independent demonstrations that this gate
# is insensitive in both directions: shuffled prefixes leave it unmoved, removing the plan
# RAISES syntactic validity while halving it, and Stage 3b pays 4.4pp of it for no loss of
# fidelity. So a 99% gate is compatible with building a perfectly valid part that is not the
# one that was asked for -- which, when the plan was retrieved from a different corpus, is
# the outcome to expect.
#
# The sharpest thing in the Build table points the same way. On external input retrieval
# CONCENTRATES: 197 distinct neighbours for 400 step queries and 166 for 400 point queries,
# 49.2% and 41.5% against 98% internally, with the top five covering 16.2% and 24.5% against
# 7.0%. The index visibly has less to offer, and the gate reads BETTER for it, because any
# corpus program builds. Fidelity is the only thing left that can tell these apart.
#
# WHAT TO QUOTE. The external ceilings from docs 9.19, measured on this set at the scorer's
# own 1,024 points: F@1% = 0.281 within the corpus scale band and 0.304 over all 400. The
# internal ceiling of 0.244 is comparable now that density and threshold rule match, but the
# internal Chamfer floor of 1.963 mm^2 is NOT -- Chamfer grows with the square of part size,
# and "all 400" landing on 1.958 is a coincidence of a heavier tail offsetting smaller
# medians. External tables carry the bbox-normalized column.
#
# REFERENCE CLOUDS LIVE ON C: FOR THIS STEP. evaluate_geometry_nbest.py converts a point_path
# with as_windows_path, which understands /mnt/<drive> and nothing else, so a cloud under
# WSL's own filesystem would be handed to Windows as /home/jizong/... , fail to load, and
# score zero -- silently, as a result rather than an error. Verified before writing this:
# /mnt/c/... round-trips and the file loads with shape (8192, 3).
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

GEN=outputs/external_fusion360
WORK=outputs/external_geometry
CLOUDS="${EXT_CLOUDS:-/mnt/c/Workspace/Project/Dataset/Fusion360Gallery/clouds}"
mkdir -p "$WORK"

[ -d "$CLOUDS" ] || { echo "FATAL: $CLOUDS not found. Copy the reference clouds to a path under /mnt/c so as_windows_path can convert them." >&2; exit 1; }

for a in step_genplan step_nnir point_genplan point_nnir; do
  [ -s "$GEN/gen_${a}_repaired_p0.jsonl" ] || { echo "FATAL: missing $GEN/gen_${a}_repaired_p0.jsonl" >&2; exit 1; }
done

python - "$GEN" "$WORK" "$CLOUDS" <<'PY'
import json, sys
from pathlib import Path

gen, work, clouds = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
arms = ["step_genplan", "step_nnir", "point_genplan", "point_nnir"]
built = {}

for a in arms:
    rows_in = [json.loads(l) for l in (gen / f"gen_{a}_repaired_p0.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    out, empty, nocloud = [], 0, 0
    for r in rows_in:
        sid = r.get("sample_id", "")
        code = (r.get("prediction") or "").strip()
        if not code:
            empty += 1
        ext = sid[len("f360_"):] if sid.startswith("f360_") else sid
        cloud = f"{clouds}/{ext}.npz"
        if not Path(cloud.replace("/mnt/c/", "/mnt/c/")).is_file():
            nocloud += 1
        out.append({"sample_id": sid, "modality": a.split("_")[0],
                    "point_path": cloud, "all_candidates": [code]})
    dst = work / f"geom_input_{a}.jsonl"
    dst.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out), encoding="utf-8")
    built[a] = {r["sample_id"] for r in out}
    print(f"  {a:<16} {len(out)} rows -> {dst.name}   (empty programs {empty}, missing clouds {nocloud})")
    if nocloud:
        print(f"  ** {nocloud} reference clouds are missing; those parts cannot be scored and "
              f"would silently read as failures **", file=sys.stderr)

# Both arms of a modality must cover the same parts, or the pairing the analysis will run is
# fiction. This is the check that N1b needed and did not have: configuration B used the first
# hundred rows against configuration A's seeded random hundred, four parts overlapped, and
# nothing crashed.
for m in ("step", "point"):
    a, b = built[f"{m}_genplan"], built[f"{m}_nnir"]
    ok = a == b
    print(f"  part-set check {m}: genplan={len(a)} nnir={len(b)} shared={len(a & b)}"
          + ("  OK" if ok else "  ** MISMATCH -- not paired **"))
    if not ok:
        raise SystemExit(1)
PY

cat > "$WORK/run_metadata.json" <<JSON
{
  "experiment": "C-EXT1-min geometry: four arms against Fusion 360 reference clouds",
  "n_per_arm": 400,
  "reference_clouds": "$CLOUDS (8192 points, sampled by flluma occt_file_to_pointcloud from the .step)",
  "scored_at": "evaluate_geometry_nbest.py default 1024 points, subsampled from both sides",
  "ceilings": "external F@1% = 0.281 within the corpus scale band, 0.304 over all 400 (docs 9.19). Raw Chamfer is not comparable with the internal 1.963 mm^2; use the bbox-normalized column",
  "stratum_rule": "read the generated-plan vs NN-IR contrast on parts with bbox_diag <= 134.30 mm; beyond that the STEP descriptor extrapolates",
  "repair_applied": true
}
JSON

cat <<'EOF'

=== NOW RUN THIS IN WINDOWS POWERSHELL, one arm at a time ===

CPU only, no GPU. Do not run two at once: the geometry wrapper stages through a shared
directory the same way the execution wrapper did before it was fixed.

  foreach ($a in @("step_genplan","step_nnir","point_genplan","point_nnir")) {
    & "C:\Workspace\Project\Paper\MIRAGE-V2\src\scripts\evaluate_geometry_nbest.ps1" `
      -InputJsonl "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\outputs\external_geometry\geom_input_$a.jsonl" `
      -OutputDir  "C:\Workspace\Project\Paper\MIRAGE-V2\scratch\geom_ext_$a"
  }

Then the analysis. It is not written yet, on purpose -- the same reason as last time, and
last time that restraint was justified twice over: the field the scorer writes for Chamfer is
`cd`, not `chamfer_distance`, and an analysis script that guessed produced a plausible null
reading "scored 0, no overlap".
EOF
