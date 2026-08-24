#!/bin/bash
# B1-K: does the construction prefix need more than K=4 vectors?
#
# WHY THIS IS THE NEXT EXPERIMENT. Two independent metric families now place the
# ceiling in the prefix PATHWAY rather than in the prior:
#
#   IR level    oracle_ir (the reference plan's own embedding, i.e. a perfect prior)
#               beats the deployed prior by +0.70 pp [-0.55, +2.03] Op-Set F1 on STEP
#               and +2.60 pp [-0.06, +5.23] on point -- both intervals contain zero.
#   Geometry    the same comparison is indistinguishable: median Chamfer 2.485 vs
#               2.432, sign test p = 0.31 (docs SS9.13).
#
# So a better prior cannot help. What is left is the channel between the latent and the
# decoder, and K is the only knob on its capacity. Section 9 already names the missing
# K-sweep as the most informative remaining ablation.
#
# IT IS ALSO THE DECISION EXPERIMENT FOR N2/N3:
#   K=8 clearly better  -> the bottleneck is channel WIDTH. N2/N3 change what the latent
#                          contains, not how much of it reaches the decoder, so they are
#                          second-order and the 2-3 days each is probably misspent.
#   K makes no difference -> the channel is saturated and the deficit is in the latent
#                          itself. N2/N3 become the right next move.
#
# NO CODE CHANGES NEEDED. --prefix-len already exists (train_soft_prefix_ir.py:80) and
# 06/06b already pass it. Stage 4/4b are untouched: train_program_lora.py contains the
# string "prefix" zero times, because the code model consumes plan TEXT, not the prefix.
# So the existing Stage 4b checkpoint is reused for every K -- one variable changes.
#
# K=4 IS NOT RE-RUN. The N1 `prior` arm already measured it under exactly the protocol
# below (n=500, batch 16, greedy, no repair), so it is the sweep's middle point for free:
#   STEP  IR cos 0.886  Op-Set F1 88.0  Op-Seq LCS 80.1  Build 71.4 [67.3, 75.2]
#   point IR cos 0.694  Op-Set F1 76.8  Op-Seq LCS 67.7
#
# TIMING IS RECORDED. No training report in this repository carries a runtime field,
# which is the last open item of review B11. Each stage here is wrapped and the seconds
# written to timings.json, so the sweep closes that too.
#
# COST: two K values x (Stage 3 + Stage 3b + generation). Stage 3 is the long pole --
# 3 epochs over the full train split at batch 1 / accum 16. Wall time is unknown because
# nobody measured it; this script will tell you.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# K=4 is free (N1's `prior` arm). Each additional K costs a full Stage 3 -- 3 epochs over
# the whole train split, the long pole of this script by far.
#
# ORDER MATTERS, WHICH IS WHY 8 COMES FIRST. K=8 alone answers the decision question:
# does widening the channel help at all, and therefore are N2/N3 worth their two to three
# days each. K=2's value is CONDITIONAL on that answer -- it is worth running only if K=8
# turns out flat against K=4, where a flat 2/4/8 curve is strong evidence of saturation
# and a single point at 8 cannot separate "saturated" from "insensitive in this range".
# So the honest way to spend the GPU is one K at a time:
#
#   B1K_VALUES="8"  bash training_25k/30_b1k_prefix_length_sweep.sh   # then look
#   B1K_VALUES="2"  ...   if K=8 came out flat
#   B1K_VALUES="16" ...   if K=8 came out clearly better
#
# The exists-checks below make each invocation resumable, so running them separately
# costs nothing over running them together.
KS="${B1K_VALUES:-8 2}"
BATCH=16                     # matches N1
# --limit 500 takes the FIRST 500 test rows, and preflight_runners.py warns about that
# because docs SS9.2 measured the first-N slice ~10 pp optimistic. Kept deliberately:
# N1 measured K=4 on exactly this slice, so reusing it makes K=4 a free arm instead of a
# full retrain. The bias shifts every arm's ABSOLUTE level together and leaves the
# K-to-K comparison -- the only thing this experiment claims -- unaffected. Say so when
# reporting, and do not compare these absolute numbers against tab:main_25k.
LIMIT=500
WORK=outputs/b1k_sweep
mkdir -p "$WORK"

python training_25k/scripts/test_n1_patches.py || {
  echo "self-test failed -- not starting a multi-hour run." >&2; exit 1; }

for f in outputs/align_25k/best.pt outputs/prior_step_25k/best.pt \
         outputs/prior_point_25k/best.pt data/25k/train.jsonl data/25k/val.jsonl; do
  [ -e "$f" ] || { echo "FATAL: $f missing." >&2; exit 1; }
done

TIMINGS="$WORK/timings.json"
[ -f "$TIMINGS" ] || echo "{}" > "$TIMINGS"

record () {   # record <key> <seconds>
  python - "$TIMINGS" "$1" "$2" <<'PY'
import json, sys
p, k, v = sys.argv[1], sys.argv[2], float(sys.argv[3])
d = json.load(open(p, encoding="utf8"))
d[k] = round(v, 1)
json.dump(d, open(p, "w", encoding="utf8"), indent=2, sort_keys=True)
PY
}

for K in $KS; do
  S3="outputs/lora_ir_25k_K${K}"
  S3B="outputs/lora_ir_25k_stage3b_K${K}"

  # ---- Stage 3: STEP-only, identical to 06 except --prefix-len ----------
  if [ -f "$S3/soft_prefix.pt" ]; then
    echo "=== skip Stage 3 K=$K (exists) ==="
  else
    echo "=== Stage 3, K=$K ==="
    T0=$(date +%s)
    python -m gen_scripts.train_soft_prefix_ir \
      --model-name Qwen/Qwen2.5-Coder-1.5B \
      --alignment-checkpoint outputs/align_25k/best.pt \
      --prior-checkpoint outputs/prior_step_25k/best.pt \
      --modality step \
      --train-jsonl data/25k/train.jsonl --val-jsonl data/25k/val.jsonl \
      --output-dir "$S3" \
      --prefix-len "$K" --load-in-4bit --bf16 \
      --per-device-train-batch-size 1 --gradient-accumulation-steps 16 \
      --epochs 3 --learning-rate 2e-4 --max-length 1536 --lora-r 8
    record "stage3_K${K}_seconds" "$(( $(date +%s) - T0 ))"
  fi

  # ---- Stage 3b: multimodal continuation, identical to 06b --------------
  if [ -f "$S3B/soft_prefix.pt" ]; then
    echo "=== skip Stage 3b K=$K (exists) ==="
  else
    echo "=== Stage 3b, K=$K ==="
    T0=$(date +%s)
    python -m gen_scripts.train_soft_prefix_ir \
      --model-name Qwen/Qwen2.5-Coder-1.5B \
      --alignment-checkpoint outputs/align_25k/best.pt \
      --modality-prior step:outputs/prior_step_25k/best.pt \
      --modality-prior point:outputs/prior_point_25k/best.pt \
      --modality-prior text:outputs/prior_text_25k/best.pt \
      --modality-prior image:outputs/prior_image_25k/best.pt \
      --init-lora-ir-dir "$S3" \
      --train-jsonl data/25k/train.jsonl --val-jsonl data/25k/val.jsonl \
      --limit-train 2000 --limit-val 200 \
      --output-dir "$S3B" \
      --prefix-len "$K" --load-in-4bit --bf16 \
      --per-device-train-batch-size 1 --gradient-accumulation-steps 16 \
      --epochs 1 --learning-rate 1e-5 --max-length 1536 \
      --eval-steps 50 --save-steps 50 --logging-steps 10 --save-total-limit 2
    record "stage3b_K${K}_seconds" "$(( $(date +%s) - T0 ))"
  fi

  # ---- Generation + IR scoring, N1's protocol exactly -------------------
  for M in step point; do
    OUT="$WORK/pred_ir_${M}_K${K}.jsonl"
    if [ -s "$OUT" ]; then echo "=== skip gen $M/K=$K (exists) ==="; continue; fi
    echo "=== generate: $M, K=$K ==="
    T0=$(date +%s)
    python training_25k/scripts/gen_predicted_ir.py \
      --modality "$M" \
      --alignment-checkpoint outputs/align_25k/best.pt \
      --prior-checkpoint "outputs/prior_${M}_25k/best.pt" \
      --lora-ir-dir "$S3B" \
      --input-jsonl data/25k/test.jsonl --limit "$LIMIT" \
      --output-jsonl "$OUT" \
      --max-length 1536 --max-new-tokens 1536 --batch-size "$BATCH"
    record "gen_${M}_K${K}_seconds" "$(( $(date +%s) - T0 ))"

    python -m gen_scripts.evaluate_ir_quality \
      --predicted-jsonl "$OUT" \
      --alignment-checkpoint outputs/align_25k/best.pt \
      --output-json "$WORK/score_${M}_K${K}.json"
  done

  # ---- Programs for STEP, so the sweep reaches Build --------------------
  GEN="$WORK/gen_step_K${K}.jsonl"
  if [ -s "$GEN" ]; then
    echo "=== skip code K=$K (exists) ==="
  else
    echo "=== generate programs: K=$K / step ==="
    python training_25k/scripts/gen_code_from_predicted_ir.py \
      --modality step \
      --ir-jsonl "$WORK/pred_ir_step_K${K}.jsonl" \
      --lora-code-dir outputs/qwen25_coder_1_5b_program_25k_stage4b \
      --input-jsonl data/25k/test.jsonl \
      --output-jsonl "$GEN" \
      --max-length 1536 --max-new-tokens 1536 --batch-size 16
  fi
done

cat > "$WORK/run_metadata.json" <<JSON
{
  "experiment": "B1-K prefix-length sweep",
  "k_values_trained": "$KS",
  "k_reference": "K=4 is NOT retrained -- the N1 'prior' arm measured it under this exact protocol (outputs/ablation_prefix/score_{step,point}_prior.json)",
  "limit": $LIMIT,
  "batch_size": $BATCH,
  "lora_code_dir": "outputs/qwen25_coder_1_5b_program_25k_stage4b (shared across K -- the code model consumes plan text, not the prefix)",
  "repair_applied": false,
  "note": "Stage 3 and Stage 3b differ from 06/06b only in --prefix-len. Generation matches 24_n1_prefix_source_ablation.sh so the K=4 arm is directly comparable."
}
JSON

echo
echo "=== IR-quality sweep (K=4 row is N1's prior arm, not re-run) ==="
python - <<'PY'
import json, pathlib
w = pathlib.Path("outputs/b1k_sweep")
n1 = pathlib.Path("outputs/ablation_prefix")
print(f"  {'K':>4}{'modality':<9}{'IR cos':>9}{'Op-Set F1':>11}{'Op-Seq LCS':>12}")
rows = []
for m in ("step", "point"):
    f = n1 / f"score_{m}_prior.json"
    if f.exists():
        rows.append((4, m, json.loads(f.read_text(encoding="utf8"))["summary"]))
for f in sorted(w.glob("score_*_K*.json")):
    m = f.stem.split("_")[1]
    k = int(f.stem.split("_K")[1])
    rows.append((k, m, json.loads(f.read_text(encoding="utf8"))["summary"]))
for k, m, s in sorted(rows, key=lambda r: (r[1], r[0])):
    print(f"  {k:>4}{m:<9}{s['ir_cosine_mean']:>9.3f}"
          f"{100*s['op_set_f1_mean']:>10.1f}%{100*s['op_seq_lcs_mean']:>11.1f}%")
t = w / "timings.json"
if t.exists():
    print("\n  timings (seconds) -- closes review item B11:")
    for k, v in sorted(json.loads(t.read_text(encoding="utf8")).items()):
        print(f"    {k:<28}{v:>10.0f}  ({v/3600:.2f} h)")
PY

# The K list is substituted in, so this block never points at a K that was not trained
# -- printing a hardcoded @(2,8) after training only K=8 sends the user to a file that
# does not exist, which is exactly what happened the first time.
KLIST=$(echo "$KS" | tr ' ' ',')
sed "s/__KLIST__/$KLIST/" <<'EOF'

=== NOW RUN THIS IN WINDOWS POWERSHELL (the only part WSL cannot do) ===

Everything above already ran. Build needs FllumaCLI. Paste as-is -- PowerShell syntax.

  foreach ($K in @(__KLIST__)) {
    & "C:\Workspace\Project\Paper\MIRAGE-V2\src\scripts\evaluate_execution.ps1" `
      -InputJsonl "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\outputs\b1k_sweep\gen_step_K$K.jsonl" `
      -OutputDir  "C:\Workspace\Project\Paper\MIRAGE-V2\scratch\exec_b1k_step_K$K"
  }

Compare against K=4: scratch\exec_n1_step_prior (71.4% Build, same protocol, same
no-repair setting), and use McNemar rather than the marginal intervals -- all arms
decode the same 500 rows.

=== HOW TO READ IT, decided in advance ===

  K=8 >> K=4   the prefix channel was the constraint. Report the sweep, adopt the
               better K if the cost is acceptable, and DEPRIORITISE N2/N3 -- they
               change what the latent holds, not how much of it gets through.
  K=8 ~= K=4   the channel is saturated at four vectors. The deficit is in the latent
               itself, so N2 (alignment topology) becomes the right next experiment
               and its patch is worth writing.
  K=2 ~= K=4   four vectors are already more than needed, same conclusion as above
               and a cheaper deployment.

Whichever way it goes, Section 9's "no sweep over the prefix length K" limitation is
replaced by a measurement.
EOF
