#!/bin/bash
# Stage 3 vs Stage 3b, scored geometrically -- the measurement tab:stage3b_ablation
# never had.
#
# WHY. Stage 3b is the paper's adopted configuration and its case rests on two metrics
# that B1-K showed do not track part fidelity (docs SS9.14):
#
#   the DIAGNOSIS is IR Cosine -- plan quality fell 0.057-0.156 for the three non-STEP
#     modalities, which is what identifies the failure Stage 3b repairs;
#   the REMEDY is Build -- four-modality average 42.9% -> 60.1%.
#
# IR Cosine measures agreement with the reference PLAN. Build is a validity gate; it
# failed three separate times to register a real change in plan content. Neither says
# whether the resulting SOLID is closer to the target. Worse, the 0.057-0.156 gap sits
# above the 0.05 at which the plan and geometry metrics were seen to diverge and far
# below the 0.84 at which they agreed emphatically -- exactly the range where these
# metrics cannot settle the direction.
#
# So the paper currently says Stage 3b improves executability and declines to claim it
# improves fidelity. This closes that, and it is cheap: no GPU, no generation, the
# programs for both arms already exist at n=2,500 per modality.
#
# WHAT IT SETTLES:
#   3b better on Chamfer          the adopted configuration is better end to end, and
#                                 tab:stage3b_ablation's "-4.4 pp cost" on STEP is a
#                                 cost in executability only.
#   indistinguishable             Stage 3b buys executability without fidelity. Still a
#                                 real result -- more queries reach a solid at all -- but
#                                 the paper must say exactly that.
#   3b worse                      the adopted configuration trades part accuracy for
#                                 build success. That would need saying plainly and would
#                                 bear on which checkpoint should be recommended.
#
# ARM LABELLING IS VERIFIED, NOT ASSUMED. Swapping the two files would invert every
# conclusion, and the filenames alone (gen_test_X vs gen_test_X_stage3b) are not proof.
# The geometry scorer re-runs all five gates, so the analysis script recomputes each arm's
# build rate and checks it against the published values in tab:stage3b_ablation
# (STEP 74.3 / 70.0, point 29.9 / 55.4). If they do not match, it refuses to report.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

CODE=outputs/qwen25_coder_1_5b_program_25k_stage4b
WORK=outputs/stage3b_geometry
MODS="${S3B_GEOM_MODALITIES:-step point}"   # text image add ~3.3 h of Windows CPU
EXPECT=2500
mkdir -p "$WORK"

for m in $MODS; do
  for f in "$CODE/gen_test_${m}_repaired_p0.jsonl" "$CODE/gen_test_${m}_stage3b_repaired_p0.jsonl"; do
    [ -s "$f" ] || { echo "FATAL: $f missing." >&2; exit 1; }
    n=$(wc -l < "$f")
    [ "$n" -eq "$EXPECT" ] || { echo "FATAL: $f has $n rows, expected $EXPECT." >&2; exit 1; }
  done
done

python - "$MODS" <<'PY'
import json, pathlib, sys

mods = sys.argv[1].split()
code = pathlib.Path("outputs/qwen25_coder_1_5b_program_25k_stage4b")
work = pathlib.Path("outputs/stage3b_geometry")
test = {}
for line in pathlib.Path("data/25k/test.jsonl").read_text(encoding="utf8").splitlines():
    if line.strip():
        r = json.loads(line)
        test[r["sample_id"]] = r

# stage3 = the file WITHOUT the stage3b infix; the analysis verifies this by build rate
for m in mods:
    for arm, src in (("stage3", code / f"gen_test_{m}_repaired_p0.jsonl"),
                     ("stage3b", code / f"gen_test_{m}_stage3b_repaired_p0.jsonl")):
        rows, missing, empty = [], 0, 0
        for line in src.read_text(encoding="utf8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            t = test.get(r["sample_id"])
            if t is None:
                missing += 1
                continue
            code_text = r.get("prediction") or r.get("program") or ""
            if not code_text.strip():
                empty += 1
            rows.append({"sample_id": r["sample_id"], "modality": m,
                         "point_path": t.get("point_path", ""),
                         "all_candidates": [code_text]})
        dst = work / f"geom_input_{m}_{arm}.jsonl"
        dst.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                       encoding="utf8")
        no_t = sum(1 for r in rows if not r["point_path"])
        print(f"  {m:<6}{arm:<9} {len(rows)} rows -> {dst.name}"
              f"   (unmatched {missing}, empty {empty}, no point_path {no_t})")
        if empty:
            print(f"  note: {empty} empty programs will score as failures, which is "
                  f"correct -- they are failures.", file=sys.stderr)

# both arms of a modality must cover the same parts or the pairing is fiction
for m in mods:
    a = {json.loads(l)["sample_id"] for l in
         (work / f"geom_input_{m}_stage3.jsonl").read_text(encoding="utf8").splitlines() if l.strip()}
    b = {json.loads(l)["sample_id"] for l in
         (work / f"geom_input_{m}_stage3b.jsonl").read_text(encoding="utf8").splitlines() if l.strip()}
    ok = a == b
    print(f"  part-set check {m}: stage3={len(a)} stage3b={len(b)} shared={len(a & b)}"
          + ("  OK" if ok else "  ** MISMATCH -- not paired **"))
PY

cat > "$WORK/run_metadata.json" <<JSON
{
  "experiment": "Stage 3 vs Stage 3b, geometric fidelity",
  "modalities": "$MODS",
  "n_per_arm": $EXPECT,
  "source": "outputs/qwen25_coder_1_5b_program_25k_stage4b/gen_test_{m}{,_stage3b}_repaired_p0.jsonl",
  "repair_applied": true,
  "note": "Both arms carry the published repair pipeline (_repaired_p0), matching tab:stage3b_ablation, so the only variable is the Stage 3 vs Stage 3b plan generator."
}
JSON

cat <<EOF

=== NOW RUN THIS IN WINDOWS POWERSHELL (the only part WSL cannot do) ===

About 50 minutes per arm at 2,500 rows, so roughly $(echo "$MODS" | wc -w) x 2 x 50 min. CPU only, no GPU --
safe to run alongside anything training.

  foreach (\$m in @($(echo "$MODS" | sed 's/ /","/g;s/^/"/;s/$/"/'))) {
    foreach (\$arm in @("stage3","stage3b")) {
      & "C:\\Workspace\\Project\\Paper\\MIRAGE-V2\\src\\scripts\\evaluate_geometry_nbest.ps1" \`
        -InputJsonl "\\\\wsl.localhost\\Ubuntu\\home\\jizong\\workspace\\MIRAGE\\src\\outputs\\stage3b_geometry\\geom_input_\${m}_\${arm}.jsonl" \`
        -OutputDir  "C:\\Workspace\\Project\\Paper\\MIRAGE-V2\\scratch\\geom_stage3b_\${m}_\${arm}"
    }
  }

Then:

  python C:\\Workspace\\Project\\Paper\\MIRAGE-V2\\src\\scratch\\stage3b_geometry_analysis.py

That script recomputes each arm's build rate from the geometry pass and checks it against
tab:stage3b_ablation before reporting anything, so a swapped arm cannot go unnoticed.
EOF
