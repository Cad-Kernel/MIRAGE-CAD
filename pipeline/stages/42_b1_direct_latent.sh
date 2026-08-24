#!/bin/bash
# B1 / A1: does the construction latent alone recover the gap, without the plan text?
#
# THE PAPER'S TITULAR CLAIM RESTS ON THIS. The title is "Construction Plans as an
# Intermediate Representation", and the one thing the evidence does not separate is
# conditioning on a construction REPRESENTATION from writing the construction down as TEXT.
# B0 removes the plan and the whole pathway together -- the prefix, the latent, the prior --
# so 35.4 % against 70.0 % cannot be attributed to either. The claims table's first
# Not-established row is exactly this, and the abstract carries a three-branch placeholder
# waiting for the answer.
#
# WHAT B1 IS. The latent conditions the CODE decoder through a soft prefix. No plan text
# anywhere. The query-derived observation block is present exactly as the deployed code
# decoder receives it, so B1 differs from the deployed arm in ONE respect: the plan is gone.
# Any other difference would make the contrast uninterpretable.
#
# HOW TO READ IT, against the deployed 70.0 % and the plan-free 35.4 %:
#   B1 ~= A3   the continuous representation is the mechanism and the plan text contributes
#              inspectability, not accuracy. The title still holds -- it names the plan as an
#              intermediate representation, not as a necessary textual form -- but the
#              abstract's sentence 6 changes and the paper must say so plainly.
#   B1 << A3   the plan text carries structure the latent does not survive without. This is
#              the result most favourable to the paper, and E1c sharpens the prediction: since
#              B1 keeps the observation, it keeps ABSOLUTE SCALE, so its failures should be
#              structural rather than scale errors. Check the bbox ratio to confirm that;
#              if B1 also loses scale, something else is wrong.
#   B1 >  A3   the textual bottleneck is losing information. Would need reporting plainly.
#
# B1 PRODUCES NO PLAN, SO PLAN-QUALITY METRICS DO NOT EXIST FOR IT. No IR cosine, no
# operation-set F1, no Op-Seq LCS -- there is nothing to score them on. The comparison is
# Build, the five gates, geometry, and the failure taxonomy. That is a property of the arm,
# not a gap in the measurement, and the results table must show blanks rather than zeros.
#
# TRAINING BUDGET IS DELIBERATELY GENEROUS, WHICH BIASES AGAINST OUR PREFERRED ANSWER.
# B1 has to learn the prefix adapter as well as the code LoRA, which Stage 4 did not. Giving
# it Stage 4's single epoch could under-train it, and an under-trained B1 would look like
# evidence that the plan matters -- the conclusion we would like. So B1 gets 3 epochs at
# grad-accum 8, which is at least what the deployed code path received across Stage 4 and
# Stage 4b. If B1 still loses, the loss is not a budget artefact. Checkpoints every 500 steps
# so the 1-epoch point can be reported too.
#
# IMPLEMENTATION. train_soft_prefix_ir.py gained --target {ir,program}: two lines, because
# the prior loading, latent computation, prefix adapter, 4-bit base, LoRA and eval loop are
# already exactly what B1 needs. Writing a second trainer would give B1 its own
# implementation to keep in step with the deployed one, which is the divergence that would
# make this comparison meaningless. Default stays `ir`, so every published path reproduces.
#
# COST. One 3-epoch soft-prefix run on 25K rows, then one 500-row inference pass. Disable
# sleep first: this machine has already lost one training run and one generation run to it.
#   powercfg /change standby-timeout-ac 0
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

# Fail fast if any script this runner depends on differs from the Windows checkout. This arm is
# why the guard exists: an earlier run of it trained for 7 h 52 m and then silently skipped
# inference, because the WSL copy predated the configurable ARM label below.
source training_25k/_guard_fresh.sh   gen_scripts/train_soft_prefix_ir.py   training_25k/scripts/gen_b1_direct_latent.py

MODALITY=${MODALITY:-step}
OUT=${OUT:-outputs/b1_direct_latent_${MODALITY}}
GEN=${GEN:-outputs/e1_observation_bypass}       # alongside the other arms
LIMIT=${LIMIT:-500}
BATCH=${BATCH:-16}
EPOCHS=${EPOCHS:-3}
ACCUM=${ACCUM:-8}
# The arm label goes into the prediction filename, so a second budget must not overwrite the
# first. A1 is the 3-epoch diagnostic; A1E is the budget-conservative one.
ARM=${ARM:-A1}

# ---------------------------------------------------------------------------
# Preflight. A three-epoch run is the wrong place to discover a missing flag.
# ---------------------------------------------------------------------------
python - <<'PY' || { echo "B1 preflight failed -- not starting." >&2; exit 1; }
import os, subprocess, sys
sys.path.insert(0, '.')
from miragecad.gen_prompts import build_program_prompt

ok = True
m = os.environ.get("MODALITY", "step")

# 1. the flag must exist in THIS tree
h = subprocess.run([sys.executable, "-m", "gen_scripts.train_soft_prefix_ir", "--help"],
                   capture_output=True, text=True).stdout
for flag in ("--target", "--prefix-len", "--load-in-4bit"):
    print(f"{'ok  ' if flag in h else 'FAIL'} train_soft_prefix_ir.py exposes {flag}")
    ok &= flag in h
if "--target" in h and "program" not in h:
    print("FAIL --target exists but does not offer 'program'"); ok = False

# 2. the B1 prompt must differ from the deployed one in exactly one respect
row = {"text": "a 40 mm flanged bracket with four M6 holes"}
b1 = build_program_prompt(row, "text", "", include_plan=False)
a3 = build_program_prompt(row, "text", "PART 1 CAT bracket")
checks = [
    ("plan block absent from B1",        "Construction IR plan" not in b1),
    ("plan instruction absent from B1",  "Use the Construction IR plan" not in b1),
    ("observation present in B1",        "Query-derived evidence" in b1),
    ("plan block present in A3",         "Construction IR plan" in a3),
    ("observation present in A3",        "Query-derived evidence" in a3),
]
for label, good in checks:
    print(f"{'ok  ' if good else 'FAIL'} {label}")
    ok &= good

# 3. the inference script must import cleanly against this tree
r = subprocess.run([sys.executable, "training_25k/scripts/gen_b1_direct_latent.py", "--help"],
                   capture_output=True, text=True)
print(f"{'ok  ' if r.returncode == 0 else 'FAIL'} gen_b1_direct_latent.py imports and parses args")
if r.returncode != 0:
    print(r.stderr[-600:]); ok = False

# 4. the checkpoints B1 must reuse
for p in ("outputs/align_25k/best.pt", f"outputs/prior_{m}_25k/best.pt",
          "data/25k/train.jsonl", "data/25k/val.jsonl", "data/25k/test.jsonl"):
    print(f"{'ok  ' if os.path.exists(p) else 'FAIL'} {p}")
    ok &= os.path.exists(p)

sys.exit(0 if ok else 1)
PY

# ---------------------------------------------------------------------------
# Step 1: train. Same alignment checkpoint and same prior as the deployed arm, so the
# latent B1 conditions on is the latent A3 conditions on.
# ---------------------------------------------------------------------------
if [ -f "$OUT/soft_prefix.pt" ] && [ -f "$OUT/adapter_model.safetensors" ]; then
  echo "=== skip training ($OUT already holds an adapter and a soft prefix) ==="
else
  echo "=== training B1: latent -> code decoder, no plan text ($MODALITY) ==="
  python -m gen_scripts.train_soft_prefix_ir \
    --model-name Qwen/Qwen2.5-Coder-1.5B \
    --alignment-checkpoint outputs/align_25k/best.pt \
    --prior-checkpoint "outputs/prior_${MODALITY}_25k/best.pt" \
    --modality "$MODALITY" \
    --target program \
    --train-jsonl data/25k/train.jsonl --val-jsonl data/25k/val.jsonl \
    --output-dir "$OUT" \
    --prefix-len 4 --load-in-4bit --bf16 \
    --per-device-train-batch-size 1 --gradient-accumulation-steps "$ACCUM" \
    --epochs "$EPOCHS" --learning-rate 2e-4 --max-length 1536 \
    --lora-r 16 --lora-alpha 32 \
    --eval-steps 500 --save-steps 500
fi

# ---------------------------------------------------------------------------
# Step 2: inference on the same 500 rows every other arm used.
# ---------------------------------------------------------------------------
PRED="$GEN/gen_code_${MODALITY}_${ARM}.jsonl"
if [ -f "$PRED" ] && [ "$(wc -l < "$PRED")" -eq "$LIMIT" ]; then
  echo "=== skip inference (complete) ==="
else
  [ -f "$PRED" ] && echo "note: $PRED is short ($(wc -l < "$PRED")/$LIMIT), regenerating" >&2
  echo "=== inference: B1 on $LIMIT rows ==="
  python training_25k/scripts/gen_b1_direct_latent.py \
    --modality "$MODALITY" \
    --alignment-checkpoint outputs/align_25k/best.pt \
    --prior-checkpoint "outputs/prior_${MODALITY}_25k/best.pt" \
    --b1-dir "$OUT" \
    --input-jsonl data/25k/test.jsonl --limit "$LIMIT" \
    --output-jsonl "$PRED" \
    --max-length 1536 --max-new-tokens 1536 --batch-size "$BATCH"
fi

cat > "$GEN/b1_${ARM}_metadata.json" <<JSON
{
  "arm": "$ARM (B1, direct construction latent to code decoder)",
  "answers": "the claims table's first Not-established row, and the abstract's three-branch placeholder",
  "modality": "$MODALITY",
  "checkpoint": "$OUT",
  "predictions": "$PRED",
  "training": {
    "epochs": $EPOCHS, "grad_accum": $ACCUM, "lr": 2e-4, "lora_r": 16, "lora_alpha": 32,
    "prefix_len": 4, "load_in_4bit": true, "max_length": 1536,
    "note": "Deliberately at least the deployed code path's total budget across Stage 4 and Stage 4b, because B1 must also learn the prefix adapter. Under-training B1 would manufacture support for our preferred conclusion."
  },
  "differs_from_deployed_in": "the plan text is absent; the observation block is present and identical",
  "plan_quality_metrics": "do not exist for this arm -- it produces no plan. Report blanks, not zeros.",
  "repair_applied": false,
  "comparability": "Batched greedy decoding, no repair. Comparable to the E1 arms in the same directory, not to the main tables."
}
JSON

echo
echo "=== what to look at, in order ==="
echo "  1. Build against the deployed 71.4 % and the plan-free 35.4 %."
echo "  2. If B1 loses, check the bbox ratio. B1 keeps the observation, so it should keep"
echo "     absolute scale (median ratio near 1.000). Structural failure is the expected"
echo "     shape; a scale failure would mean something else is wrong."
echo "  3. No plan-quality metric applies. Blanks, not zeros."
echo
echo "=== NOW IN WINDOWS POWERSHELL ==="
cat <<'EOF'
  & "C:\Workspace\Project\Paper\MIRAGE-V2\src\scripts\run_e1_execution.ps1" -Modalities step -Conditions $ARM

  # geometry: prep writes geom_input_step_$ARM.jsonl, then
  & "C:\Workspace\Project\Paper\MIRAGE-V2\src\scripts\evaluate_geometry_nbest.ps1" `
    -InputJsonl "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\outputs\e1_observation_bypass\geom_input_step_$ARM.jsonl" `
    -OutputDir  "C:\Workspace\Project\Paper\MIRAGE-V2\scratch\geom_e1_step_$ARM"

  python C:\Workspace\Project\Paper\MIRAGE-V2\src\scratch\e1_analysis.py --modalities step
EOF
