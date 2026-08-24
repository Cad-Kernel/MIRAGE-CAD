#!/bin/bash
# B2-Pred: a textual-plan code decoder trained on the plans it will actually receive.
#
# THE CONFOUND THIS ADDRESSES. B1 beat the deployed arm by 22 points of Build on 500 STEP
# queries. One competing explanation is not about representation form at all: B1 trains on
# exactly what it sees at inference, while the deployed code decoder was trained largely on
# ground-truth plans and meets predicted ones. §6.4.2 measures that mismatch at 95 % Build
# given a ground-truth plan against 28 % given a predicted one.
#
# READ THE COST-BENEFIT BEFORE RUNNING THIS. Two facts bound what it can find.
#
#   1. THE DEPLOYED ARM IS ALREADY 30 % EXPOSURE-CORRECTED. C3 uses the Stage 4b checkpoint,
#      trained on a 70/30 ground-truth/predicted mixture (08_build_stage4b_mix.sh,
#      --predicted-ratio 0.30). That first 30 % took predicted-plan Build from 28 % to 67 %,
#      a 39-point gain. Going from 30 % to 100 % has whatever is left, and the first slice
#      almost certainly captured most of it. The headroom here is bounded and is very unlikely
#      to be 22 points.
#
#   2. IT NEEDS 24,000 MORE PREDICTED PLANS. Only 1,000 exist
#      (07_gen_predicted_ir_train_subset.sh runs at --limit 1000). Generating plans for the
#      rest of the 25K training split costs roughly 16 hours at the measured throughput,
#      before any training starts.
#
# So this is the expensive experiment with the smaller expected effect, and B1-1E is the cheap
# one with the larger. Run B1-1E first. This script exists so the choice is informed, and so
# that if B1-1E still wins the exposure explanation can be closed properly rather than
# argued about.
#
# THE MATCHED DESIGN. Both arms then have: the same 25K rows, the same one epoch, the same
# grad-accum, the same observation block, the same code targets, the same base model and LoRA
# rank. They differ in what conditions the decoder -- a continuous prefix, or predicted plan
# text -- which is the question.
#
# ONE ASYMMETRY THAT NO BUDGET CAN REMOVE, and it favours this arm: B1 must also learn the
# prefix adapter, which this arm does not. So B1 winning at equal updates is strong evidence;
# this arm winning at equal updates is weaker, because B1 had more to learn. State that
# either way round.
#
# STAGE 1: generate the missing predicted plans. Resumable, and skipped if already complete.
# STAGE 2: train the code decoder on them. STAGE 3: inference on the same 500 test rows.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

# Fail fast if any script this runner depends on differs from the Windows checkout. This is a
# sixteen-hour experiment; the previous round lost 7 h 52 m to a stale runner whose log looked
# entirely normal, and the runner is not the only file that can be stale.
source training_25k/_guard_fresh.sh   training_25k/scripts/gen_predicted_ir.py   training_25k/scripts/gen_code_from_predicted_ir.py   train_program_lora.py

MODALITY=${MODALITY:-step}
IR_DIR=${IR_DIR:-outputs/lora_ir_25k_stage3b}
BASE_CODE=${BASE_CODE:-outputs/qwen25_coder_1_5b_program_25k}   # Stage 4, before the 4b mixture
OUT=${OUT:-outputs/b2_pred_matched_${MODALITY}}
GEN=${GEN:-outputs/e1_observation_bypass}
PLANS=${PLANS:-data/25k/predicted_ir_train_full.jsonl}
TRAIN_ROWS=${TRAIN_ROWS:-25000}      # set lower to buy a cheaper, still-matched comparison
LIMIT=${LIMIT:-500}
BATCH=${BATCH:-16}
EPOCHS=${EPOCHS:-1}
ACCUM=${ACCUM:-8}
ARM=${ARM:-B2P}

[ -d "$IR_DIR" ] || IR_DIR=outputs/lora_ir_25k

python - <<'PY' || { echo "B2-Pred preflight failed -- not starting." >&2; exit 1; }
import os, sys
ok = True
for p in ("outputs/align_25k/best.pt", "data/25k/train.jsonl", "data/25k/val.jsonl",
          "data/25k/test.jsonl"):
    print(f"{'ok  ' if os.path.exists(p) else 'FAIL'} {p}")
    ok &= os.path.exists(p)
# The point of this arm is that training conditioning equals inference conditioning. If the
# plan file is missing or short, the arm silently becomes a partial mixture and measures
# nothing in particular.
plans = os.environ.get("PLANS", "data/25k/predicted_ir_train_full.jsonl")
want = int(os.environ.get("TRAIN_ROWS", "25000"))
have = sum(1 for _ in open(plans, encoding="utf-8")) if os.path.exists(plans) else 0
print(f"{'ok  ' if have >= want else 'note'} predicted training plans: {have}/{want}"
      f"{'' if have >= want else '  -> stage 1 will generate the rest'}")

# The entire arm hinges on one field name. Verify the trainer honours it, rather than
# discovering after sixteen hours of generation that it silently used ground-truth plans.
import pathlib
src = pathlib.Path("train_program_lora.py").read_text(encoding="utf8")
hook = "ir_text_for_program" in src and 'read_text(row["ir_path"])' in src
print(f"{'ok  ' if hook else 'FAIL'} train_program_lora.py reads ir_text_for_program, with a "
      f"ground-truth fallback")
if not hook:
    print("     If that field name has changed, the mix builder must change with it or this "
          "arm trains on ground-truth plans and measures nothing.")
ok &= hook

sys.exit(0 if ok else 1)
PY

# ---------------------------------------------------------------------------
# Stage 1: predicted plans for the training split. The expensive part.
# ---------------------------------------------------------------------------
HAVE=$( [ -f "$PLANS" ] && wc -l < "$PLANS" || echo 0 )
if [ "$HAVE" -ge "$TRAIN_ROWS" ]; then
  echo "=== skip plan generation ($HAVE >= $TRAIN_ROWS) ==="
else
  echo "=== generating predicted plans for the training split: $HAVE -> $TRAIN_ROWS ==="
  echo "    this is the ~16 hour step; it is resumable by row count"
  python training_25k/scripts/gen_predicted_ir.py \
    --modality "$MODALITY" \
    --alignment-checkpoint outputs/align_25k/best.pt \
    --prior-checkpoint "outputs/prior_${MODALITY}_25k/best.pt" \
    --lora-ir-dir "$IR_DIR" \
    --input-jsonl data/25k/train.jsonl --limit "$TRAIN_ROWS" \
    --require-split train \
    --output-jsonl "$PLANS" \
    --max-length 1536 --max-new-tokens 1536 \
    --batch-size "$BATCH"
fi

# ---------------------------------------------------------------------------
# Stage 2: build a training file whose plan field is the PREDICTED plan, then train.
# 100 % predicted, not a mixture: the whole point is conditioning parity.
# ---------------------------------------------------------------------------
MIX=data/25k/train_b2pred_${MODALITY}.jsonl
if [ -s "$MIX" ]; then
  echo "=== skip mix build ($MIX exists) ==="
else
  echo "=== building 100%-predicted training file ==="
  python - <<PY
import json, pathlib
plans = {}
for line in pathlib.Path("$PLANS").read_text(encoding="utf8").splitlines():
    if line.strip():
        r = json.loads(line)
        plans[r["sample_id"]] = r.get("predicted_ir", "")
out, missing = [], 0
for line in pathlib.Path("data/25k/train.jsonl").read_text(encoding="utf8").splitlines():
    if not line.strip():
        continue
    r = json.loads(line)
    p = plans.get(r["sample_id"])
    if not p:
        missing += 1
        continue
    # train_program_lora.py reads `ir_text_for_program` and falls back to the GROUND-TRUTH
    # ir_path when it is absent. Any other field name here would train this arm on
    # ground-truth plans and measure nothing at all, without raising.
    r["ir_text_for_program"] = p
    r["predicted_ir"] = p          # provenance only; the trainer does not read this
    out.append(r)
pathlib.Path("$MIX").write_text(
    "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out), encoding="utf8")
print(f"  wrote {len(out)} rows to $MIX  (no predicted plan for {missing})")
if missing:
    print(f"  note: {missing} training rows have no predicted plan and are excluded. The "
          f"matched B1 arm must be trained on the SAME row set for the comparison to hold.")
PY
fi

if [ -f "$OUT/adapter_model.safetensors" ]; then
  echo "=== skip training ($OUT exists) ==="
else
  echo "=== training B2-Pred: predicted plan -> code, 100% predicted conditioning ==="
  # tee, because eval loss is printed and never written to training_report.json. pipefail is
  # set, so a python failure still fails the pipeline.
  python train_program_lora.py \
    --model-name Qwen/Qwen2.5-Coder-1.5B \
    --init-adapter-dir "$BASE_CODE" \
    --target program --modality "$MODALITY" --max-length 1536 \
    --train-jsonl "$MIX" --val-jsonl data/25k/val.jsonl \
    --output-dir "$OUT" \
    --epochs "$EPOCHS" --per-device-train-batch-size 1 \
    --gradient-accumulation-steps "$ACCUM" --learning-rate 2e-4 \
    --lora-r 16 --lora-alpha 32 --load-in-4bit --bf16 2>&1 | tee "$OUT.train.log"
fi

# ---------------------------------------------------------------------------
# Record what ACTUALLY happened, not what was requested. `train_rows_requested` is a
# statement about our intent; a comparison needs the realised numbers.
# ---------------------------------------------------------------------------
# Exported BEFORE the heredoc: it is single-quoted, so the block reads these from the
# environment rather than having them substituted in.
export OUT MIX ACCUM EPOCHS
python - <<'PY' > "$OUT/actuals.json" || echo "note: could not derive actuals" >&2
import json, os, pathlib, re
out = os.environ["OUT"]; mix = os.environ["MIX"]
accum = int(os.environ["ACCUM"]); epochs = int(os.environ["EPOCHS"])
a = {}
rep = pathlib.Path(out, "training_report.json")
if rep.exists():
    a["training_report"] = json.loads(rep.read_text(encoding="utf8"))
    rows = a["training_report"].get("train_rows")
    if rows:
        # Derived, not read from a trainer state file: this run writes no trainer_state.json
        # because it sets no save_steps. Labelled so it is never mistaken for a logged value.
        a["optimizer_updates_derived"] = -(-rows // accum) * epochs
        a["updates_formula"] = "ceil(train_rows / grad_accum) * epochs"
log = pathlib.Path(out + ".train.log")
if log.exists():
    # The value is QUOTED in this trainer's log -- {'eval_loss': '0.06868'} -- so the quote
    # must be optional. Without it the parse silently found nothing and recorded
    # "not found in the training log" while the number sat in the log all along.
    ev = re.findall(r"'eval_loss':\s*'?([0-9.eE+-]+)'?",
                    log.read_text(encoding="utf8", errors="replace"))
    if ev:
        a["eval_loss_first"], a["eval_loss_last"] = float(ev[0]), float(ev[-1])
        a["eval_loss_all"] = [float(v) for v in ev]
    else:
        a["eval_loss"] = "not found in the training log"
# Mean input length, so the exposure-matched arm's prompt budget is comparable to B1's.
try:
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-1.5B")
    n = tot = 0
    for line in pathlib.Path(mix).read_text(encoding="utf8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        tot += len(tok(r.get("ir_text_for_program", ""), add_special_tokens=False)["input_ids"])
        n += 1
        if n >= 2000:
            break
    a["mean_plan_tokens"] = round(tot / max(n, 1), 1)
    a["mean_plan_tokens_sampled_rows"] = n
except Exception as e:
    a["mean_plan_tokens"] = f"unavailable: {e}"
print(json.dumps(a, indent=2))
PY
echo "  actuals -> $OUT/actuals.json"


# ---------------------------------------------------------------------------
# Stage 3: inference on the same 500 test rows, with the deployed test plans.
# ---------------------------------------------------------------------------
PRED="$GEN/gen_code_${MODALITY}_${ARM}.jsonl"
if [ -f "$PRED" ] && [ "$(wc -l < "$PRED")" -eq "$LIMIT" ]; then
  echo "=== skip inference (complete) ==="
else
  echo "=== inference: $ARM on $LIMIT rows ==="
  python training_25k/scripts/gen_code_from_predicted_ir.py \
    --modality "$MODALITY" \
    --lora-code-dir "$OUT" \
    --ir-jsonl "$GEN/pred_ir_${MODALITY}_present.jsonl" \
    --input-jsonl data/25k/test.jsonl --limit "$LIMIT" \
    --output-jsonl "$PRED" \
    --max-length 1536 --max-new-tokens 1536 --batch-size "$BATCH"
fi

cat > "$GEN/${ARM}_metadata.json" <<JSON
{
  "arm": "$ARM, textual plan with training/inference conditioning parity",
  "addresses": "the exposure-bias explanation for B1's advantage",
  "conditioning_at_training": "100% predicted plans",
  "conditioning_at_inference": "predicted plans (same file the deployed arm uses)",
  "deployed_comparator": "Stage 4b, already a 70/30 GT/predicted mixture, so it is 30% exposure-corrected",
  "expected_headroom": "bounded: the 0->30% step bought 39 points of predicted-plan Build (28 -> 67), so 30 -> 100% has at most the remainder",
  "epochs": $EPOCHS, "grad_accum": $ACCUM, "train_rows_requested": $TRAIN_ROWS,
  "asymmetry_that_remains": "B1 must also learn a prefix adapter and this arm need not, so this arm winning at equal updates is weaker evidence than B1 winning at equal updates",
  "repair_applied": false
}
JSON

echo
echo "=== NOW IN WINDOWS POWERSHELL ==="
echo "  & \"C:\\Workspace\\Project\\Paper\\MIRAGE-V2\\src\\scripts\\run_e1_execution.ps1\" -Modalities $MODALITY -Conditions $ARM"
echo "  then 41_e1_geometry_prep.sh, and the geometry loop it prints"
