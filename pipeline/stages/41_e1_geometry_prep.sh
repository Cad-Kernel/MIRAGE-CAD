#!/bin/bash
# E1 geometry: prepare the arms that still need scoring, and say which ones do not.
#
# WHY GEOMETRY AT ALL. Every E1 and E1b number so far is Build -- a gate. The paper's own
# methodological result is that a gate is not a ruler, so "plan-only builds 58.0 % against
# the deployed 71.4 %" says nothing yet about whether the surviving programs reconstruct the
# queried part any less well. Two arms could build at the same rate and differ entirely in
# fidelity, and §6.2 already demonstrated exactly that for the prefix intervention: Build
# moved 2.8 points while median Chamfer went from 2.84 to 22.11 mm^2.
#
# TWO OF THE FOUR CELLS ARE ALREADY SCORED, AND NOT BY ASSUMPTION.
#   C3, correct + observation present : E1's C3 programs are BYTE-IDENTICAL to N1's prior
#     arm -- same SHA-256 over all 500 predictions -- because both were produced by the same
#     script, checkpoint and decoding settings. Its geometry is scratch/geom_n1_step_prior.
#   S3, shuffled + observation present : staged from N1's shuffled arm unchanged by
#     40_e1b, so its geometry is scratch/geom_n1_step_shuffled.
# This script verifies both identities before relying on them, and prepares only what is
# genuinely missing.
#
# WHAT IS MISSING:
#   step C2   correct plan,  observation suppressed
#   step S2   shuffled plan, observation suppressed
#   text C3   deployed, for the modality contrast
#   text C2   plan-only, for the modality contrast
#
# WHAT THE FOUR CELLS THEN ANSWER:
#   C3 vs C2  does removing the observation cost fidelity as well as Build? The 13.4-point
#             Build gap could be all of the damage, or the tip of it.
#   C2 vs S2  the geometric counterpart of E1b. Build did not move there; if Chamfer does,
#             that is the gate-not-a-ruler result reproduced with the bypass closed, which
#             is a stronger form of the paper's central methodological claim.
#   text vs STEP  whether the fidelity cost of suppression splits by modality the way the
#             Build cost did (13.4 points on STEP, nothing measurable on text).
#
# MEDIAN, NOT MEAN. The protocol makes median Chamfer the headline because the distribution
# is heavy-tailed -- the deployed arm's values run to 1,404.66 mm^2 against a median of 2.84,
# so a handful of degenerate parts would set any mean. The analysis script pairs and uses a
# sign test for that reason.
#
# THIS SCRIPT ONLY PREPARES. Scoring needs FllumaCLI, so it runs on Windows.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

WORK=${WORK:-outputs/e1_observation_bypass}
N1=${N1:-outputs/ablation_prefix}

python - <<'PY'
import hashlib, json, os, pathlib, sys

work = pathlib.Path(os.environ.get("WORK", "outputs/e1_observation_bypass"))
n1   = pathlib.Path(os.environ.get("N1", "outputs/ablation_prefix"))

def preds(p):
    out = {}
    for line in pathlib.Path(p).read_text(encoding="utf8").splitlines():
        if line.strip():
            r = json.loads(line)
            out[r["sample_id"]] = r.get("prediction") or ""
    return out

def digest(d):
    return hashlib.sha256("".join(d[k] for k in sorted(d)).encode()).hexdigest()[:16]

# ---- verify the two reuse claims rather than asserting them -------------------
print("=== reuse checks ===")
reuse_ok = True
for label, mine, theirs, geom in (
    ("C3 = N1 prior",    work / "gen_code_step_C3.jsonl", n1 / "gen_step_prior.jsonl",
     "scratch/geom_n1_step_prior"),
    ("S3 = N1 shuffled", work / "gen_code_step_S3.jsonl", n1 / "gen_step_shuffled.jsonl",
     "scratch/geom_n1_step_shuffled"),
):
    if not (mine.exists() and theirs.exists()):
        print(f"  MISSING one side of {label}"); reuse_ok = False; continue
    a, b = preds(mine), preds(theirs)
    if digest(a) == digest(b) and a.keys() == b.keys():
        print(f"  ok   {label}: {len(a)}/{len(a)} identical, sha {digest(a)} "
              f"-> reuse {geom}")
    else:
        same = sum(1 for k in a.keys() & b.keys() if a[k] == b[k])
        print(f"  FAIL {label}: only {same}/{len(a.keys() & b.keys())} identical. "
              f"Score this arm separately instead of reusing {geom}.")
        reuse_ok = False

# ---- prepare what is missing -------------------------------------------------
test = {}
for line in pathlib.Path("data/25k/test.jsonl").read_text(encoding="utf8").splitlines():
    if line.strip():
        r = json.loads(line)
        test[r["sample_id"]] = r

ARMS = [("step", "C2"), ("step", "S2"), ("text", "C3"), ("text", "C2"),
        # A1/A1E are B1, the direct-latent arm at two budgets; B2P is the exposure-matched
        # textual-plan arm. All three emit the same schema, so they prep identically.
        ("step", "A1"), ("step", "A1E"), ("step", "B2P")]
print("\n=== preparing geometry inputs ===")
counts = {}
for modality, cond in ARMS:
    src = work / f"gen_code_{modality}_{cond}.jsonl"
    dst = work / f"geom_input_{modality}_{cond}.jsonl"
    if not src.exists():
        print(f"  skip {modality}/{cond}: {src.name} not generated"); continue
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
            "modality": r.get("modality", modality),
            "point_path": t.get("point_path", ""),
            # One candidate per row, so the scorer's N-best machinery degenerates to a
            # single evaluation. This is a fidelity comparison at N = 1, not a selection
            # experiment, and it must stay that way to be comparable to the main tables.
            "all_candidates": [code],
        })
    no_target = sum(1 for r in rows if not r["point_path"])
    dst.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                   encoding="utf8")
    counts[f"{modality}/{cond}"] = len(rows)
    print(f"  {modality}/{cond:<3} wrote {len(rows)} rows -> {dst.name}"
          f"   (unmatched {missing}, empty program {empty}, no point_path {no_target})")
    if no_target:
        # A row without point_path scores has_target=false and silently drops out of every
        # median. Discovering that in the output would mean re-reading the whole arm.
        print(f"  WARNING: {no_target} rows lack point_path and cannot be scored.",
              file=sys.stderr)

# ---- the comparison is paired, so the counts must agree ---------------------
print()
if len(set(counts.values())) > 1:
    print(f"  WARNING: row counts differ across arms: {counts}. The comparison is paired "
          f"on sample_id, so unequal counts mean some cells lose rows.", file=sys.stderr)
else:
    print(f"  all prepared arms have {next(iter(counts.values()), 0)} rows")

# Publish the arms actually prepared, so the block printed below cannot drift from them. It
# already had: ARMS carried step_A1E while the printed loop did not, which would have scored one
# arm fewer than was prepped without anything looking wrong.
(work / "geom_arms.txt").write_text(
    ",".join(f'"{m}_{c}"' for m, c in ARMS if (work / f"geom_input_{m}_{c}.jsonl").exists()),
    encoding="utf8")

sys.exit(0 if reuse_ok else 1)
PY

# WORK, not GEN -- GEN is what 42 and 43 call their output directory, and copying the name here
# meant this expansion failed under `set -u`. The fallback then printed a plausible one-arm list
# instead of stopping, which is the exact failure this whole mechanism exists to prevent: a step
# that looks finished and covered less than you think. So there is no fallback now.
if [ ! -s "$WORK/geom_arms.txt" ]; then
  echo "FAIL: $WORK/geom_arms.txt was not written, so the arms actually prepared are unknown." >&2
  echo "      Refusing to print a scoring loop that might silently cover fewer arms." >&2
  exit 1
fi
GEOM_ARMS=$(cat "$WORK/geom_arms.txt")

cat <<'EOF'

=== NOW IN WINDOWS POWERSHELL (scoring needs FllumaCLI) ===

Roughly ten minutes per arm-set. Each is resumable; re-running skips finished ones. The arm list
below is what this run actually prepared, read from geom_arms.txt rather than restated here,
because a hand-copied list had already fallen out of step with the prep.
EOF
printf '\n  foreach ($A in @(%s)) {\n' "$GEOM_ARMS"
cat <<'EOF'
    & "C:\Workspace\Project\Paper\MIRAGE-V2\src\scripts\evaluate_geometry_nbest.ps1" `
      -InputJsonl "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\outputs\e1_observation_bypass\geom_input_$A.jsonl" `
      -OutputDir  "C:\Workspace\Project\Paper\MIRAGE-V2\scratch\geom_e1_$A"
  }

Then:

  python C:\Workspace\Project\Paper\MIRAGE-V2\src\scratch\e1_geometry_analysis.py

EOF
