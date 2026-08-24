#!/bin/bash
# E1: how much of the result is the plan, and how much is the observation block?
#
# THE QUESTION. The code decoder is conditioned on the construction plan AND on a
# query-derived evidence block. So is the plan carrying the construction information, or
# is it corroborating an observation the decoder could already see? Every claim that the
# plan is the mechanism depends on the answer, and no experiment has separated them.
#
# INFERENCE ONLY. No training. Same checkpoints, same rows, same decoding settings; the
# only thing that changes is which blocks reach which prompt.
#
# THE BLOCK ENTERS BOTH PROMPTS, SO BOTH MUST BE SUPPRESSED. gen_prompts.py appends
# "Query-derived evidence" in build_ir_prompt (line 192) and again in
# build_program_prompt (line 241), under the same `if evidence:` guard. An earlier
# version of this protocol suppressed the code side only and justified it as reproducing
# what happens for image queries -- but for image the block is absent from BOTH prompts,
# so one-sided suppression leaves a plan that was still generated with the observation
# present. That is not a plan-only condition. Hence two plan runs per modality, not one.
#
# THE FOUR CONDITIONS:
#   C3  deployed        plan present,    observation present     the shipped system
#   C2  plan-only       plan present,    observation suppressed  <- the one that matters
#   C1  observation     plan suppressed, observation present     bounds from below
#   C0  neither         plan suppressed, observation suppressed  floor
#
# HOW TO READ IT, in order:
#   C2 ~= C3   the plan carries essentially the construction information the code decoder
#              uses. The bottleneck framing is sound and the observation is corroborative.
#   C2 << C3   the observation is doing substantial work. Reframe as "plan alongside
#              observation-conditioned evidence" and re-examine the RQ2 interpretation.
#   C1 ~= C3   the most awkward outcome: the plan is largely redundant given the
#              observation. Would need reporting plainly and would reshape the claim.
#
# ONE CONFOUND, STATED NOT HIDDEN. The code decoder was TRAINED with the block present, so
# suppressing it at inference is a distribution shift. C2 is therefore a LOWER BOUND on
# what a plan-only architecture would achieve. E2 removes the confound by training one.
# The same applies to C1 and C0 in the other direction: suppressing the plan at inference
# is also a shift, so C1 is not equivalent to a trained observation-only model and must
# not be compared against B0's trained numbers as if it were.
#
# POINT CLOUD IS A SPECIAL CASE AND WILL LOOK ODD. gen_predicted_ir.py defaults to
# --point-evidence off, so for point the PLAN prompt already receives only the constant
# string "Point cloud query." rather than the statistics. Suppressing it therefore removes
# a block that carried no query information in the first place, and C3-vs-C2 on the plan
# side is nearly a no-op for point. The real manipulation for point is the code side,
# where the statistics ARE populated. Read point's C2 with that in mind, and see
# 27_point_evidence_fix.sh, which measures what the plan side is missing.
#
# COST. Two plan passes and four code passes per modality. At LIMIT=500 and four
# modalities that is 24 generation passes. Start with MODALITIES=step if you want the
# headline first; it is the modality every framing claim is built on.
#
# THIS SCRIPT ONLY GENERATES. Execution and geometry run on the Windows side, because the
# kernel does; run scripts/run_e1_execution.ps1 afterwards.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

IR_DIR=${IR_DIR:-outputs/lora_ir_25k_stage3b}
CODE_DIR=${CODE_DIR:-outputs/qwen25_coder_1_5b_program_25k_stage4b}
WORK=${WORK:-outputs/e1_observation_bypass}
LIMIT=${LIMIT:-500}
BATCH=${BATCH:-16}
MODALITIES=${MODALITIES:-"step point text image"}

if [ ! -d "$IR_DIR" ]; then
  echo "note: $IR_DIR missing, falling back to Stage 3 (record this in the results)" >&2
  IR_DIR=outputs/lora_ir_25k
fi
mkdir -p "$WORK"

# Resume must mean "finished", not "started". A machine that dies mid-write leaves a
# short file, and a plain -s test would skip it for good -- the arm would then be scored
# on however many rows happened to land, with nothing in the output saying so.
complete() {            # complete <file> <expected-rows>
  [ -f "$1" ] || return 1
  [ "$(wc -l < "$1")" -eq "$2" ] || return 1
}
ROWS_AVAILABLE=$(wc -l < data/25k/test.jsonl)
EXPECT_PLANS=$(( LIMIT < ROWS_AVAILABLE ? LIMIT : ROWS_AVAILABLE ))

# ---------------------------------------------------------------------------
# Fail fast. Forty minutes in is the wrong moment to discover the flag is absent
# from this copy of the tree, or that a builder ignores an empty evidence string.
# ---------------------------------------------------------------------------
python - <<'PY' || { echo "E1 self-test failed -- not starting the runs." >&2; exit 1; }
import subprocess, sys
sys.path.insert(0, '.')
from miragecad.gen_prompts import build_ir_prompt, build_program_prompt, get_query_evidence

row = {"text": "a 40 mm flanged bracket with four M6 holes"}
ok = True

for name, fn, extra in (("build_ir_prompt", build_ir_prompt, {}),
                        ("build_program_prompt", build_program_prompt,
                         {"predicted_ir": "PART 1 CAT bracket"})):
    on  = fn(row, "text", **extra)
    off = fn(row, "text", evidence_text="", **extra)
    if "Query-derived evidence" not in on or "Query-derived evidence" in off:
        print(f"FAIL {name}: evidence_text='' does not drop the block"); ok = False
    else:
        print(f"ok   {name}: evidence_text='' drops the block")

for script in ("training_25k/scripts/gen_predicted_ir.py",
               "training_25k/scripts/gen_code_from_predicted_ir.py"):
    h = subprocess.run([sys.executable, script, "--help"], capture_output=True, text=True).stdout
    if "--suppress-evidence" in h:
        print(f"ok   {script} exposes --suppress-evidence")
    else:
        print(f"FAIL {script} has no --suppress-evidence: this tree is unpatched"); ok = False

# the constant the point plan prompt actually receives, recorded so the log shows it
print(f"note point plan-side fallback = {get_query_evidence({}, 'point')!r}")
print(f"note image evidence           = {get_query_evidence({}, 'image')!r}")
sys.exit(0 if ok else 1)
PY

# ---------------------------------------------------------------------------
# Step 1: plans. Two per modality -- with the evidence block, and without it.
# ---------------------------------------------------------------------------
for M in $MODALITIES; do
  for EV in present suppressed; do
    OUT="$WORK/pred_ir_${M}_${EV}.jsonl"
    if complete "$OUT" "$EXPECT_PLANS"; then echo "=== skip plans $M/$EV (complete) ==="; continue; fi
    [ -f "$OUT" ] && echo "note: $OUT is short ($(wc -l < "$OUT")/$EXPECT_PLANS), regenerating" >&2
    echo "=== plans: $M / evidence $EV ==="
    EXTRA=()
    [ "$EV" = "suppressed" ] && EXTRA+=(--suppress-evidence)
    python training_25k/scripts/gen_predicted_ir.py \
      --modality "$M" \
      --alignment-checkpoint outputs/align_25k/best.pt \
      --prior-checkpoint "outputs/prior_${M}_25k/best.pt" \
      --lora-ir-dir "$IR_DIR" \
      --input-jsonl data/25k/test.jsonl --limit "$LIMIT" \
      --output-jsonl "$OUT" \
      --max-length 1536 --max-new-tokens 1536 \
      --batch-size "$BATCH" "${EXTRA[@]}"
  done
done

# ---------------------------------------------------------------------------
# Step 2: programs. Four conditions per modality.
#
# C1 and C0 drop the plan with --no-plan, so which plan file they are handed is
# immaterial; they read the evidence-present file purely because the argument is
# required. That is deliberate: it keeps the row set identical across all four.
# ---------------------------------------------------------------------------
for M in $MODALITIES; do
  for COND in C3 C2 C1 C0; do
    OUT="$WORK/gen_code_${M}_${COND}.jsonl"
    case "$COND" in
      C3) IR="$WORK/pred_ir_${M}_present.jsonl";    EXTRA=() ;;
      C2) IR="$WORK/pred_ir_${M}_suppressed.jsonl"; EXTRA=(--suppress-evidence) ;;
      C1) IR="$WORK/pred_ir_${M}_present.jsonl";    EXTRA=(--no-plan) ;;
      C0) IR="$WORK/pred_ir_${M}_present.jsonl";    EXTRA=(--no-plan --suppress-evidence) ;;
    esac
    EXPECT_CODE=$(wc -l < "$IR")
    if complete "$OUT" "$EXPECT_CODE"; then echo "=== skip code $M/$COND (complete) ==="; continue; fi
    [ -f "$OUT" ] && echo "note: $OUT is short ($(wc -l < "$OUT")/$EXPECT_CODE), regenerating" >&2
    echo "=== code: $M / $COND  (${EXTRA[*]:-deployed}) ==="
    python training_25k/scripts/gen_code_from_predicted_ir.py \
      --modality "$M" \
      --lora-code-dir "$CODE_DIR" \
      --ir-jsonl "$IR" \
      --input-jsonl data/25k/test.jsonl --limit "$LIMIT" \
      --output-jsonl "$OUT" \
      --max-length 1536 --max-new-tokens 1536 \
      --batch-size "$BATCH" "${EXTRA[@]}"
  done
done

cat > "$WORK/run_metadata.json" <<JSON
{
  "experiment": "E1 observation-bypass ablation, inference only",
  "lora_ir_dir": "$IR_DIR",
  "lora_code_dir": "$CODE_DIR",
  "limit": $LIMIT,
  "batch_size": $BATCH,
  "modalities": "$MODALITIES",
  "conditions": {
    "C3": "plan present, observation present",
    "C2": "plan present, observation suppressed in BOTH prompts",
    "C1": "plan suppressed, observation present",
    "C0": "plan suppressed, observation suppressed"
  },
  "point_evidence": "off (default), so the point PLAN prompt carries only the constant string",
  "repair_applied": false,
  "note": "Batched greedy decoding is NOT bit-identical to sequential, so these are internally comparable but must NOT be compared against the batch-size-1 numbers in the main tables. C2 is a lower bound: the code decoder was trained with the block present."
}
JSON

echo
echo "=== plan-level check: did suppression change the plans at all? ==="
python - <<'PY'
import json, os, pathlib
w = pathlib.Path(os.environ.get("WORK", "outputs/e1_observation_bypass"))
for m in os.environ.get("MODALITIES", "step point text image").split():
    a, b = w / f"pred_ir_{m}_present.jsonl", w / f"pred_ir_{m}_suppressed.jsonl"
    if not (a.exists() and b.exists()):
        print(f"{m:<7} (missing)"); continue
    A = {json.loads(l)["sample_id"]: json.loads(l)["predicted_ir"] for l in a.open(encoding="utf-8")}
    B = {json.loads(l)["sample_id"]: json.loads(l)["predicted_ir"] for l in b.open(encoding="utf-8")}
    keys = A.keys() & B.keys()
    same = sum(1 for k in keys if A[k] == B[k])
    print(f"{m:<7} {len(keys):>4} paired plans, {same:>4} byte-identical "
          f"({100*same/max(len(keys),1):.1f}%)")
print()
print("For point, near-100% identical is EXPECTED: its plan prompt carried only the")
print("constant 'Point cloud query.' to begin with, so suppression removes no information.")
print("For text and STEP, near-100% identical would be the finding -- it would mean the")
print("plan decoder was ignoring the evidence block it was given.")
PY

echo
echo "Next, on Windows:  src\\scripts\\run_e1_execution.ps1"
