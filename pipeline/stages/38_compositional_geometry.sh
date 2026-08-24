#!/bin/bash
# Re-measure the compositional holdout with geometry, because its conclusion rests entirely
# on a metric that has just been shown to invert.
#
# WHAT WAS CONCLUDED, AND ON WHAT. tab:compositional holds two columns, Build and STEP export,
# and no geometry was ever run on this split -- there is no geom_*comp* directory anywhere.
# On Build, retrieval sits at 100.00% for STEP and 98.32% for point against 46.73% and 44.95%
# for a generated plan, and the paper concluded "hypothesis rejected: retrieval stays near
# saturation on a genuine family holdout while variant C falls". That downgraded the paper's
# central claim on 2026-08-04.
#
# WHY THAT IS NOW IN DOUBT. The external evaluation ran the same pair of arms on 400
# externally authored parts. Build said retrieval by 30 points, 99.2% against 69.0%. Geometry
# said the opposite and not narrowly: on the parts both could build, the generated plan won
# F@1% 160 times to 55, sign p = 4.4e-13, with normalised Chamfer 0.042 against 0.074. The
# clearest number was the bounding box -- generated within 0.7% of the target's size, retrieval
# off by 42% -- because retrieval hands back a corpus part of whatever size that part was.
#
# The mechanism transfers to this split by construction, and should be stronger here. The
# held-out families are precisely the ones the index does not contain, so retrieval must
# return a plan belonging to a DIFFERENT family. That plan is a real corpus program, so it
# builds; whether it resembles the held-out part is what Build cannot see.
#
# READINGS FIXED BEFORE THE RUN.
#
#   generated wins on geometry    the 2026-08-04 downgrade was an artifact of the gate metric.
#                                 tab:compositional needs geometry columns and its conclusion
#                                 needs rewriting -- as does anything downstream of it,
#                                 including tab:positioning and the claims audit.
#   the two are comparable        retrieval is genuinely competitive on unseen families. The
#                                 downgrade stands, now on better evidence than before.
#   retrieval wins on geometry    the downgrade stands and is strengthened. Report it, and the
#                                 external result becomes the anomaly needing explanation
#                                 rather than the rule.
#
# This is cheap: the generated programs for both variants already exist, comp_test's
# point_path is already a /mnt/c path the scorer can convert, and nothing needs a GPU. Four
# arms of 2,923 rows, CPU only.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

OURS=outputs/qwen25_coder_1_5b_program_25k_comp_stage4b
NNIR=outputs/nnir_baseline_comp
TEST=data/25k_comp/comp_test.jsonl
WORK=outputs/compositional_geometry
MODS="${COMP_MODS:-step point}"
mkdir -p "$WORK"

[ -s "$TEST" ] || { echo "FATAL: $TEST missing" >&2; exit 1; }
for m in $MODS; do
  for f in "$OURS/gen_test_${m}_comp_repaired_p0.jsonl" "$NNIR/prior_${m}_repaired_p0.jsonl"; do
    [ -s "$f" ] || { echo "FATAL: $f missing" >&2; exit 1; }
  done
done

python - "$OURS" "$NNIR" "$TEST" "$WORK" "$MODS" <<'PY'
import json, sys
from pathlib import Path

ours, nnir, test, work, mods = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]), sys.argv[5].split()
targets = {}
for line in test.read_text(encoding="utf-8").splitlines():
    if line.strip():
        r = json.loads(line)
        targets[r.get("sample_id", "")] = r.get("point_path", "")

built = {}
for m in mods:
    for arm, src in (("ours", ours / f"gen_test_{m}_comp_repaired_p0.jsonl"),
                     ("nnir", nnir / f"prior_{m}_repaired_p0.jsonl")):
        rows_in = [json.loads(l) for l in src.read_text(encoding="utf-8").splitlines() if l.strip()]
        out, missing, empty = [], 0, 0
        for r in rows_in:
            sid = r.get("sample_id", "")
            tp = targets.get(sid, "")
            if not tp:
                missing += 1
            code = (r.get("prediction") or "").strip()
            if not code:
                empty += 1
            out.append({"sample_id": sid, "modality": m, "point_path": tp,
                        "all_candidates": [code]})
        dst = work / f"geom_input_{m}_{arm}.jsonl"
        dst.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out), encoding="utf-8")
        built[(m, arm)] = {r["sample_id"] for r in out}
        print(f"  {m:<6}{arm:<6} {len(out)} rows -> {dst.name}   "
              f"(no target {missing}, empty programs {empty})")
        if missing:
            print(f"  ** {missing} rows have no point_path; they cannot be scored and would "
                  f"read as failures **", file=sys.stderr)

# The pairing has to be real, or the sign test on it is theatre. This is the check N1b lacked.
for m in mods:
    a, b = built[(m, "ours")], built[(m, "nnir")]
    ok = a == b
    print(f"  part-set check {m}: ours={len(a)} nnir={len(b)} shared={len(a & b)}"
          + ("  OK" if ok else "  ** MISMATCH -- not paired **"))
    if not ok:
        raise SystemExit(1)
PY

cat > "$WORK/run_metadata.json" <<JSON
{
  "experiment": "Compositional holdout, re-measured with geometry",
  "why": "tab:compositional carries Build and STEP export only, and no geometry was ever run on this split. The external evaluation showed Build inverting the architectural conclusion on the same pair of arms, so the 2026-08-04 downgrade rests on a metric now known to be capable of pointing the wrong way.",
  "modalities": "$MODS",
  "n_per_arm": 2923,
  "arms": "variant C (generated plan) vs variant B (prior-NN-IR), the pair the downgrade compared",
  "targets": "comp_test point_cloud.npz, the corpus's own reference clouds",
  "no_new_generation": true,
  "repair_applied": true
}
JSON

cat <<'EOF'

=== NOW RUN THIS IN WINDOWS POWERSHELL, one arm at a time ===

CPU only. The wrapper retries by itself if a candidate crashes the kernel; rows already scored
are kept and the offending candidate is recorded as a crash rather than retried.

  foreach ($m in @("step","point")) {
    foreach ($arm in @("ours","nnir")) {
      & "C:\Workspace\Project\Paper\MIRAGE-V2\src\scripts\evaluate_geometry_nbest.ps1" `
        -InputJsonl "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\outputs\compositional_geometry\geom_input_${m}_${arm}.jsonl" `
        -OutputDir  "C:\Workspace\Project\Paper\MIRAGE-V2\scratch\geom_comp_${m}_${arm}"
    }
  }

Roughly 50 minutes per 2,500 rows, so about four hours for all four.

The ceilings to quote are the INTERNAL ones -- F@1% = 0.244, Chamfer floor 1.963 mm^2, both
measured at 1,024 points on FllumaOne parts (docs 9.15). These are FllumaOne parts, so unlike
the external set they transfer directly. Do not use the external 0.281.
EOF
