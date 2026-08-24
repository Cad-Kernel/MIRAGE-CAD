#!/bin/bash
# The no-plan baseline: does the construction plan earn its place in the architecture?
#
# THE QUESTION THE PAPER CANNOT CURRENTLY ANSWER. Its whole design is
# query -> construction plan -> program, and the title is "construction-plan-guided".
# But no experiment removes the plan. tab:ablation_stage4b shows a BETTER plan gives
# better code (95% build from ground-truth plans against 67% from predicted ones); it
# does not show that ANY plan beats NO plan. A reviewer asks this first.
#
# WHY IT HAS TO BE RETRAINED. Feeding an empty plan to the published Stage 4b checkpoint
# would measure only that a model trained with plans expects one -- an off-distribution
# prompt, not an ablation. The fair comparison trains a code model that never saw a plan,
# so it learns to work from the observation block from the start. That is one Stage 4 run:
# 1 epoch, ~3-4 h by the Stage 3 timings in outputs/b1k_sweep/timings.json.
#
# WHAT IT ABLATES, STATED PRECISELY. The plan pathway carries information through two
# channels: the soft prefix from the query encoder, and the textual plan. Removing the
# plan from the code model's prompt removes BOTH, because the prefix only ever reaches
# the code model *through* the plan. So this ablates the plan-mediated pathway AS A
# WHOLE against a direct query-to-code fine-tune. It does NOT isolate the plan text from
# the latent -- that would need the prefix adapter wired into LoRA-Code, which the
# architecture does not do. Report it as the pathway, never as "the plan text is useless".
#
# HOW TO READ IT, fixed before the run so the conclusion is not chosen after seeing it:
#
#   with-plan >> no-plan   the plan-mediated pathway earns its place. This is the paper's
#                          missing positive architectural claim, and the strongest
#                          outcome for the current framing.
#   with-plan ~= no-plan   the plan buys no execution success. The paper is not void, but
#                          its contribution must be restated: an explicit plan makes the
#                          pipeline inspectable and editable before code exists, which is
#                          a real property (SS3.2, tab:editability) and independent of
#                          build rate. The abstract's framing would need to change.
#   no-plan >> with-plan   the plan is a bottleneck, not a guide. The paper becomes a
#                          diagnostic: an interpretable intermediate that costs accuracy.
#                          Least comfortable, most informative, and it must be reported.
#
# COMPARISON ARM. Variant C of tab:generation, STEP, n=2500 -- same test rows, same base
# model, same LoRA rank and quantisation, same repair pipeline, same execution harness.
# The only difference is whether the prompt carries a plan.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

OUT=outputs/lora_code_noplan_25k
WORK=outputs/noplan_baseline
MOD="${NOPLAN_MODALITY:-step}"
mkdir -p "$WORK"

for f in data/25k/train.jsonl data/25k/val.jsonl data/25k/test.jsonl; do
  [ -s "$f" ] || { echo "FATAL: $f missing." >&2; exit 1; }
done

# Fail before a multi-hour run rather than after it: the flag must actually change the
# prompt. If build_program_prompt ignored include_plan, both arms would be identical and
# we would report "no difference" as a finding.
python - <<'PY'
import sys
sys.path.insert(0, ".")
import json
from miragecad.gen_prompts import build_program_prompt
row = next(json.loads(l) for l in open("data/25k/test.jsonl", encoding="utf8") if l.strip())
a = build_program_prompt(row, "step", "PART x OP_EXTRUDE ...")
b = build_program_prompt(row, "step", "PART x OP_EXTRUDE ...", include_plan=False)
assert a != b, "FATAL: include_plan is a no-op -- the two arms would be identical"
assert "Construction IR plan" not in b, "FATAL: the plan block survives include_plan=False"
assert "primary guide" not in b, "FATAL: the instruction still refers to a plan that is absent"
print(f"  prompt check OK: with-plan {len(a)} chars, no-plan {len(b)} chars "
      f"({len(b)-len(a):+d})")
PY

# ---------------------------------------------------------------------------
# Stage 4, no plan. Every hyper-parameter matches 09_train_lora_code_stage4.sh; the
# only difference is --no-plan. There is no Stage 4b equivalent because Stage 4b exists
# to fix exposure bias to PREDICTED plans, and this arm has no plans at all.
# ---------------------------------------------------------------------------
if [ -f "$OUT/adapter_config.json" ]; then
  echo "=== skip training (exists at $OUT) ==="
else
  echo "=== training LoRA-Code with no plan in the prompt ==="
  T0=$(date +%s)
  python train_program_lora.py \
    --model-name Qwen/Qwen2.5-Coder-1.5B \
    --train-jsonl data/25k/train.jsonl --val-jsonl data/25k/val.jsonl \
    --output-dir "$OUT" \
    --target program --modality "$MOD" \
    --no-plan \
    --load-in-4bit --bf16 \
    --epochs 1 --per-device-train-batch-size 1 --per-device-eval-batch-size 1 \
    --gradient-accumulation-steps 8 --learning-rate 2e-4 \
    --eval-steps 500 --save-steps 500 --logging-steps 20 --save-total-limit 2
  echo "{\"stage4_noplan_seconds\": $(( $(date +%s) - T0 ))}" > "$WORK/timings.json"
fi

# ---------------------------------------------------------------------------
# Generation over the full test set, no plan, then the same two repair passes the
# published variant C uses -- so repair is not a confound in either direction.
# ---------------------------------------------------------------------------
RAW="$WORK/gen_${MOD}_noplan.jsonl"
if [ -s "$WORK/gen_${MOD}_noplan_repaired_p0.jsonl" ]; then
  echo "=== skip generation (exists) ==="
else
  echo "=== generating programs with no plan ($MOD, full test set) ==="
  python training_25k/scripts/gen_code_from_predicted_ir.py \
    --no-plan \
    --modality "$MOD" \
    --lora-code-dir "$OUT" \
    --input-jsonl data/25k/test.jsonl \
    --output-jsonl "$RAW" \
    --max-length 1536 --max-new-tokens 1536 --batch-size 16

  N=$(wc -l < "$RAW")
  [ "$N" -eq 2500 ] || { echo "FATAL: got $N rows, expected 2500." >&2; exit 1; }
  echo "  coverage OK: $N rows"

  python3 scratch/repair_extrude_on_face.py "$RAW" "$WORK/gen_${MOD}_noplan_r.jsonl"
  python3 scratch/repair_profile_cut_offset.py "$WORK/gen_${MOD}_noplan_r.jsonl" \
    "$WORK/gen_${MOD}_noplan_repaired_p0.jsonl"
fi

python evaluate_programs.py \
  --predictions "$WORK/gen_${MOD}_noplan_repaired_p0.jsonl" \
  --output-dir "$WORK/eval_${MOD}" || true

cat > "$WORK/run_metadata.json" <<JSON
{
  "experiment": "no-plan baseline",
  "modality": "$MOD",
  "n": 2500,
  "checkpoint": "$OUT",
  "ablates": "the plan-mediated pathway as a whole -- plan text AND, transitively, the query encoder, since the soft prefix reaches the code model only through the plan",
  "does_not_ablate": "the plan text in isolation; that would need the prefix adapter wired into LoRA-Code",
  "comparison_arm": "variant C of tab:generation, same modality, same 2500 test rows, same repair pipeline",
  "repair_applied": true
}
JSON

cat <<EOF

=== NOW RUN THIS IN WINDOWS POWERSHELL (the only part WSL cannot do) ===

  & "C:\\Workspace\\Project\\Paper\\MIRAGE-V2\\src\\scripts\\evaluate_execution.ps1" \`
    -InputJsonl "\\\\wsl.localhost\\Ubuntu\\home\\jizong\\workspace\\MIRAGE\\src\\outputs\\noplan_baseline\\gen_${MOD}_noplan_repaired_p0.jsonl" \`
    -OutputDir  "C:\\Workspace\\Project\\Paper\\MIRAGE-V2\\scratch\\exec_noplan_${MOD}"

Then:

  python C:\\Workspace\\Project\\Paper\\MIRAGE-V2\\src\\scratch\\noplan_analysis.py

The comparison is paired -- both arms decode the same 2,500 rows -- so the analysis uses
McNemar's exact test rather than comparing marginal intervals.
EOF
