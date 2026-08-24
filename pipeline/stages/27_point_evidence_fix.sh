#!/bin/bash
# Does populating the point-cloud observation block at inference help?
#
# THE DEFECT (found 2026-08-06 while analysing N1; see docs §9.9). The plan-generation
# script has always called build_ir_prompt(..., point_xyz=None), so for the point
# modality get_query_evidence() returns the constant string "Point cloud query." rather
# than the point_count / bbox / bbox_ratios / centroid / std / PCA-ratio block that
#
#   * Stage 3 and Stage 3b TRAINING did populate (train_soft_prefix_ir.py:190), and
#   * the sibling program-generation script DOES populate for the code stage
#     (gen_code_from_predicted_ir.py:79), and
#   * this very script already has in hand -- encode_query() samples the points four
#     lines earlier to feed the point encoder, then throws the array away.
#
# So every reported point-cloud number was produced under a train/inference prompt
# mismatch, with the plan decoder seeing strictly less than it was fitted on. They are
# lower bounds of unknown tightness. This measures the tightness.
#
# WHY THE DEFAULT WAS NOT SIMPLY CHANGED. `--point-evidence off` is still the default so
# that every path in PROVENANCE.md keeps reproducing its published numbers. This script
# runs the `on` arm as a separate, clearly-labelled comparison. Nothing in the paper
# moves until these numbers exist.
#
# HOW TO READ IT:
#   on >> off   the point-cloud column of tab:main_25k is understated and should be
#               re-run at 2,500 for the reported configuration. Also weakens the
#               "STEP is the strongest modality" reading, since part of that gap was
#               prompt informativeness rather than representation quality.
#   on ~= off   the prefix already carries what the text block would add -- a genuinely
#               interesting result, and it makes §8.1's attribution of all point-cloud
#               plan quality to the prefix a designed property rather than an accident.
#   on << off   the decoder has adapted to the placeholder over Stage 3b, and the
#               mismatch is self-correcting. Report it and keep `off`.
#
# Runs in WSL. No retraining. Two generation passes + two scorings, ~1,000 rows total.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

IR_DIR=outputs/lora_ir_25k_stage3b
CODE_DIR=outputs/qwen25_coder_1_5b_program_25k_stage4b
WORK=outputs/point_evidence_ab
LIMIT=500          # matches N1 so the `off` arm is directly comparable to it
BATCH=16

[ -d "$IR_DIR" ] || IR_DIR=outputs/lora_ir_25k
mkdir -p "$WORK"

python training_25k/scripts/test_n1_patches.py || {
  echo "self-test failed -- not starting." >&2; exit 1; }

# ---------------------------------------------------------------------------
# Step 1: the same rows, decoded twice, differing only in c_obs.
# ---------------------------------------------------------------------------
for EV in off on; do
  OUT="$WORK/pred_ir_point_${EV}.jsonl"
  if [ -s "$OUT" ]; then echo "=== skip plans $EV (exists) ==="; continue; fi
  echo "=== generate plans: --point-evidence $EV ==="
  python training_25k/scripts/gen_predicted_ir.py \
    --modality point \
    --alignment-checkpoint outputs/align_25k/best.pt \
    --prior-checkpoint outputs/prior_point_25k/best.pt \
    --lora-ir-dir "$IR_DIR" \
    --input-jsonl data/25k/test.jsonl --limit "$LIMIT" \
    --output-jsonl "$OUT" \
    --point-evidence "$EV" \
    --max-length 1536 --max-new-tokens 1536 \
    --batch-size "$BATCH"
done

echo
echo "=== scoring IR quality ==="
for EV in off on; do
  python -m gen_scripts.evaluate_ir_quality \
    --predicted-jsonl "$WORK/pred_ir_point_${EV}.jsonl" \
    --alignment-checkpoint outputs/align_25k/best.pt \
    --output-json "$WORK/score_point_${EV}.json"
done

# ---------------------------------------------------------------------------
# Step 2: programs, so the comparison reaches Build and not just IR quality.
# N1 established that Build cannot separate prefix sources -- but that was a
# same-prompt comparison. This one changes the prompt, so Build may well move,
# and it is the metric tab:main_25k reports.
# ---------------------------------------------------------------------------
for EV in off on; do
  GEN="$WORK/gen_point_${EV}.jsonl"
  if [ -s "$GEN" ]; then echo "=== skip code $EV (exists) ==="; continue; fi
  echo "=== generate programs: $EV ==="
  python training_25k/scripts/gen_code_from_predicted_ir.py \
    --modality point \
    --ir-jsonl "$WORK/pred_ir_point_${EV}.jsonl" \
    --lora-code-dir "$CODE_DIR" \
    --input-jsonl data/25k/test.jsonl \
    --output-jsonl "$GEN" \
    --max-length 1536 --max-new-tokens 1536 --batch-size 16
done

# ---------------------------------------------------------------------------
# Step 3: confirm the two arms really did differ in the prompt. Without this the
# whole experiment can silently be a no-op -- if the flag failed to take effect,
# both arms would be identical and we would report "no difference" as a finding.
# ---------------------------------------------------------------------------
echo
echo "=== sanity: did the prompt actually change? ==="
python - <<'PY'
import sys
sys.path.insert(0, ".")
import json
from miragecad.gen_prompts import build_ir_prompt
from miragecad.point_sampling import load_point_cloud_sampled

row = next(json.loads(l) for l in open("data/25k/test.jsonl", encoding="utf8") if l.strip())
pts = load_point_cloud_sampled(row["point_path"], point_count=1024, sampling="fps", seed=42)
off = build_ir_prompt(row, "point", retrieved_ir=None, point_xyz=None)
on = build_ir_prompt(row, "point", retrieved_ir=None, point_xyz=pts)
print(f"  off: {len(off)} chars   on: {len(on)} chars   delta {len(on)-len(off):+d}")
assert off != on, "FATAL: the flag is a no-op -- the two arms would be identical"
print("  off block:", repr(off.split("Query-derived evidence:")[-1].split("Output Construction")[0].strip()[:80]))
print("  on  block:", repr(on.split("Query-derived evidence:")[-1].split("Output Construction")[0].strip()[:160]))
print("  OK -- the arms differ.")
PY

echo
echo "=== IR-quality comparison ==="
python - <<'PY'
import json, pathlib
w = pathlib.Path("outputs/point_evidence_ab")
print(f"{'arm':<6}{'n':>6}{'IR cos':>10}{'Op-Set F1':>12}{'Op-Seq LCS':>13}")
vals = {}
for ev in ("off", "on"):
    p = w / f"score_point_{ev}.json"
    if not p.exists():
        print(f"{ev:<6}(missing)"); continue
    d = json.loads(p.read_text(encoding="utf8")).get("summary", {})
    vals[ev] = d
    print(f"{ev:<6}{d.get('n',0):>6}{d['ir_cosine_mean']:>10.3f}"
          f"{100*d['op_set_f1_mean']:>11.1f}%{100*d['op_seq_lcs_mean']:>12.1f}%")
if len(vals) == 2:
    print()
    for k, lbl, sc in [("ir_cosine_mean", "IR cos", 1),
                       ("op_set_f1_mean", "Op-Set F1", 100),
                       ("op_seq_lcs_mean", "Op-Seq LCS", 100)]:
        d = sc * (vals["on"][k] - vals["off"][k])
        print(f"  on - off  {lbl:<11}{d:+8.2f}")
    print("\n  For a PAIRED interval on these differences (which is what should be")
    print(r"  reported), run: python C:\Workspace\Project\Paper\MIRAGE-V2\src\scratch\point_evidence_analysis.py")
PY

cat > "$WORK/run_metadata.json" <<JSON
{
  "experiment": "point-cloud observation block, inference-time A/B",
  "defect": "training populated c_obs for point (train_soft_prefix_ir.py:190); the plan-generation script did not (gen_predicted_ir.py, point_xyz=None). Affects every reported 25K point-cloud number.",
  "arms": ["off = every published run", "on = matches Stage 3/3b training"],
  "limit": $LIMIT,
  "batch_size": $BATCH,
  "lora_ir_dir": "$IR_DIR",
  "lora_code_dir": "$CODE_DIR",
  "repair_applied": false,
  "note": "The 'off' arm at LIMIT=500 batch 16 is directly comparable to N1's prior/point row (76.8% Op-Set F1). If it differs materially, something other than this flag changed."
}
JSON

echo
echo "=== WSL side complete. Outputs in $WORK ==="
ls -la "$WORK"/*.jsonl 2>/dev/null | awk '{print "  "$NF, $5" bytes"}'

cat <<'EOF'

=== NOW RUN THIS IN WINDOWS POWERSHELL (the only part WSL cannot do) ===

Everything above already ran. Execution needs FllumaCLI, which WSL cannot load. Paste
as-is -- PowerShell syntax, not bash.

  foreach ($EV in @("off","on")) {
    & "C:\Workspace\Project\Paper\MIRAGE-V2\src\scripts\evaluate_execution.ps1" `
      -InputJsonl "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\outputs\point_evidence_ab\gen_point_$EV.jsonl" `
      -OutputDir  "C:\Workspace\Project\Paper\MIRAGE-V2\scratch\exec_point_evidence_$EV"
  }

Then, for the paired tests and Wilson intervals:

  python C:\Workspace\Project\Paper\MIRAGE-V2\src\scratch\point_evidence_analysis.py

REPAIR: repair_applied=false for both arms, so they are matched on that axis but are
not directly comparable to tab:main_25k's 55.4% point Build. If `on` wins, the follow-up
is a full 2,500-row re-run under the reported configuration, not a patch of the table
from these 500 rows.
EOF
