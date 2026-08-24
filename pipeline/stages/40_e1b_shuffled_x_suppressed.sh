#!/bin/bash
# E1b: the one cell missing from {correct, shuffled} x {observation present, suppressed}.
#
# WHY THIS EXISTS. Section 6.2's result is the paper's strongest experiment: corrupt the
# prefix and plan quality collapses 53 points while Build does not move, p = 0.37. It has
# one alternative reading, stated in three places in the draft and never closed -- that the
# code decoder recovers from a corrupted plan by reading the query-derived observation block
# instead. E1 did not close it: E1 measured what the observation adds when the plan is
# CORRECT. This measures whether the observation is what holds Build flat when the plan is
# WRONG.
#
# THREE OF THE FOUR CELLS ALREADY EXIST:
#
#                        observation present      observation suppressed
#   plan correct         71.4  (E1 C3)            58.0  (E1 C2)
#   plan shuffled        68.6  (N1 shuffled)      <- THIS SCRIPT
#
# HOW TO READ THE RESULT:
#   S2 ~= C2   Build is insensitive to plan quality even with no observation to fall back
#              on. The alternative reading is dead and section 6.2 is secure.
#   S2 << C2   the observation WAS compensating. Section 6.2's conclusion has to be
#              restated: Build's blindness was partly the bypass, not purely the metric.
# Either outcome is worth having. The second would be the more valuable.
#
# THE PERMUTATION MUST MATCH N1'S, OR THE TWO SHUFFLED CELLS DIFFER IN TWO WAYS AT ONCE.
# gen_predicted_ir.py computes a GLOBAL permutation up front from --shuffle-seed, before
# batching (see its comment at the shuffled branch: permuting within a batch would be the
# identity at batch 1 and near-identity at 16, which would silently understate the control).
# So the same seed over the same rows in the same order gives the same permutation. N1 ran
# at the default seed 1234, limit 500, batch 16; this script passes all three explicitly and
# asserts the row set matches before it decodes anything.
#
# SUPPRESSION IS APPLIED AT BOTH INJECTION POINTS, matching E1's C2, so that C2 and S2
# differ only in the prefix. Suppressing one side would reintroduce the confound E1 fixed.
#
# COST. One plan pass and one code pass, about 70 minutes. No training.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

IR_DIR=${IR_DIR:-outputs/lora_ir_25k_stage3b}
CODE_DIR=${CODE_DIR:-outputs/qwen25_coder_1_5b_program_25k_stage4b}
WORK=${WORK:-outputs/e1_observation_bypass}          # same directory as E1, so the 2x2 lives together
N1=${N1:-outputs/ablation_prefix}                    # where N1 left the shuffled arm
LIMIT=${LIMIT:-500}
BATCH=${BATCH:-16}
SEED=${SEED:-1234}                                   # N1's default; do not change without redoing N1

[ -d "$IR_DIR" ] || IR_DIR=outputs/lora_ir_25k
mkdir -p "$WORK"

complete() { [ -f "$1" ] && [ "$(wc -l < "$1")" -eq "$2" ]; }

# ---------------------------------------------------------------------------
# Preflight. Everything that would invalidate the comparison is checked before
# the GPU is touched.
# ---------------------------------------------------------------------------
python - <<'PY' || { echo "E1b preflight failed -- not starting." >&2; exit 1; }
import json, os, subprocess, sys
sys.path.insert(0, '.')
from miragecad.gen_prompts import build_ir_prompt, build_program_prompt

work = os.environ.get("WORK", "outputs/e1_observation_bypass")
n1   = os.environ.get("N1", "outputs/ablation_prefix")
ok = True

def rows(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(l)["sample_id"] for l in f]

# 1. the three existing cells must be present and 500 rows each
need = {
    "C3, correct + present":   f"{work}/gen_code_step_C3.jsonl",
    "C2, correct + suppressed": f"{work}/gen_code_step_C2.jsonl",
    "S3, shuffled + present":  f"{n1}/gen_step_shuffled.jsonl",
    "N1 shuffled plans":       f"{n1}/pred_ir_step_shuffled.jsonl",
}
ids = {}
for label, p in need.items():
    if not os.path.exists(p):
        print(f"FAIL missing {label}: {p}"); ok = False; continue
    ids[label] = rows(p)
    print(f"ok   {label}: {len(ids[label])} rows")

# 2. the row set and ORDER must match N1's, or the global permutation differs
if "N1 shuffled plans" in ids and "C3, correct + present" in ids:
    a, b = ids["N1 shuffled plans"], ids["C3, correct + present"]
    if a == b:
        print(f"ok   row set and order identical to N1's ({len(a)} rows), so seed {os.environ.get('SEED','1234')} "
              f"reproduces N1's permutation")
    else:
        same = sum(1 for x, y in zip(a, b) if x == y)
        print(f"FAIL row order differs from N1's ({same}/{min(len(a),len(b))} aligned). "
              f"The shuffled permutation would not match and the two shuffled cells would "
              f"differ in two ways at once."); ok = False

# 3. both builders must still honour an empty evidence string
row = {"text": "a 40 mm flanged bracket"}
for name, fn, extra in (("build_ir_prompt", build_ir_prompt, {}),
                        ("build_program_prompt", build_program_prompt, {"predicted_ir": "PART 1"})):
    on, off = fn(row, "text", **extra), fn(row, "text", evidence_text="", **extra)
    good = "Query-derived evidence" in on and "Query-derived evidence" not in off
    print(f"{'ok  ' if good else 'FAIL'} {name} drops the block on an empty evidence string")
    ok &= good

# 4. the flags this script depends on must exist in this tree
h = subprocess.run([sys.executable, "training_25k/scripts/gen_predicted_ir.py", "--help"],
                   capture_output=True, text=True).stdout
for flag in ("--suppress-evidence", "--prefix-source", "--shuffle-seed"):
    print(f"{'ok  ' if flag in h else 'FAIL'} gen_predicted_ir.py exposes {flag}")
    ok &= flag in h

sys.exit(0 if ok else 1)
PY

# ---------------------------------------------------------------------------
# Step 1: shuffled plans, decoded with the observation block suppressed.
# ---------------------------------------------------------------------------
PLANS="$WORK/pred_ir_step_shuffled_suppressed.jsonl"
if complete "$PLANS" "$LIMIT"; then
  echo "=== skip plans (complete) ==="
else
  [ -f "$PLANS" ] && echo "note: $PLANS is short ($(wc -l < "$PLANS")/$LIMIT), regenerating" >&2
  echo "=== plans: shuffled prefix, evidence suppressed (seed $SEED) ==="
  python training_25k/scripts/gen_predicted_ir.py \
    --modality step \
    --alignment-checkpoint outputs/align_25k/best.pt \
    --prior-checkpoint outputs/prior_step_25k/best.pt \
    --lora-ir-dir "$IR_DIR" \
    --input-jsonl data/25k/test.jsonl --limit "$LIMIT" \
    --output-jsonl "$PLANS" \
    --prefix-source shuffled --shuffle-seed "$SEED" \
    --suppress-evidence \
    --max-length 1536 --max-new-tokens 1536 \
    --batch-size "$BATCH"
fi

# ---------------------------------------------------------------------------
# Step 2: programs, also with the block suppressed. Named S2 so that the Windows
# gate runner picks it up with -Conditions S2, no new PowerShell needed.
# ---------------------------------------------------------------------------
OUT="$WORK/gen_code_step_S2.jsonl"
EXPECT=$(wc -l < "$PLANS")
if complete "$OUT" "$EXPECT"; then
  echo "=== skip code S2 (complete) ==="
else
  [ -f "$OUT" ] && echo "note: $OUT is short ($(wc -l < "$OUT")/$EXPECT), regenerating" >&2
  echo "=== code: shuffled + suppressed  (S2) ==="
  python training_25k/scripts/gen_code_from_predicted_ir.py \
    --modality step \
    --lora-code-dir "$CODE_DIR" \
    --ir-jsonl "$PLANS" \
    --input-jsonl data/25k/test.jsonl --limit "$LIMIT" \
    --output-jsonl "$OUT" \
    --suppress-evidence \
    --max-length 1536 --max-new-tokens 1536 \
    --batch-size "$BATCH"
fi

# ---------------------------------------------------------------------------
# Step 3: stage the existing shuffled + present arm under the same naming, so all
# four cells are scored by one harness with one set of settings. Copied rather
# than re-generated: it was produced by the same script, checkpoint and decoding
# settings as E1, and re-running it would only add decoding noise.
# ---------------------------------------------------------------------------
S3="$WORK/gen_code_step_S3.jsonl"
if complete "$S3" "$EXPECT"; then
  echo "=== skip S3 (already staged) ==="
else
  echo "=== staging N1's shuffled + present arm as S3 ==="
  cp "$N1/gen_step_shuffled.jsonl" "$S3"
  echo "    from $N1/gen_step_shuffled.jsonl ($(wc -l < "$S3") rows)"
  echo "    provenance: 24_n1_prefix_source_ablation.sh, same CODE_DIR, same max-length/"
  echo "    max-new-tokens 1536, same batch size 16. Not regenerated."
fi

cat > "$WORK/e1b_metadata.json" <<JSON
{
  "experiment": "E1b, shuffled prefix crossed with observation suppression",
  "closes": "the alternative reading of section 6.2 -- that the code decoder recovers from a corrupted plan via the observation block",
  "cells": {
    "C3": "correct prefix, observation present    (E1)",
    "C2": "correct prefix, observation suppressed (E1)",
    "S3": "shuffled prefix, observation present   (N1, staged here unchanged)",
    "S2": "shuffled prefix, observation suppressed (this script)"
  },
  "shuffle_seed": $SEED,
  "note": "The permutation is global and computed before batching, so the same seed over the same rows in the same order reproduces N1's. Suppression is applied at both injection points, matching C2, so C2 and S2 differ only in the prefix.",
  "limit": $LIMIT,
  "batch_size": $BATCH,
  "repair_applied": false
}
JSON

echo
echo "=== plan-level check ==="
python - <<'PY'
import json, os
work = os.environ.get("WORK", "outputs/e1_observation_bypass")
n1   = os.environ.get("N1", "outputs/ablation_prefix")
def plans(p):
    return {json.loads(l)["sample_id"]: json.loads(l)["predicted_ir"]
            for l in open(p, encoding="utf-8")}
new = plans(f"{work}/pred_ir_step_shuffled_suppressed.jsonl")
old = plans(f"{n1}/pred_ir_step_shuffled.jsonl")
c2  = plans(f"{work}/pred_ir_step_suppressed.jsonl")
k = sorted(new.keys() & old.keys())
print(f"shuffled+suppressed vs shuffled+present : {sum(1 for i in k if new[i]==old[i])}/{len(k)} identical"
      f"   (low expected: suppression changes the plan)")
k2 = sorted(new.keys() & c2.keys())
print(f"shuffled+suppressed vs correct+suppressed: {sum(1 for i in k2 if new[i]==c2[i])}/{len(k2)} identical"
      f"   (low expected: the prefix differs)")
PY

echo
echo "Next, on Windows PowerShell:"
echo '  & "C:\Workspace\Project\Paper\MIRAGE-V2\src\scripts\run_e1_execution.ps1" -Modalities step -Conditions S2,S3'
echo '  python C:\Workspace\Project\Paper\MIRAGE-V2\src\scratch\e1b_crossed_analysis.py'
