#!/bin/bash
# N1: where does the construction prefix's information actually come from?
#
# THIS IS THE MOST IMPORTANT REMAINING INTERNAL EXPERIMENT. Table tab:ablation_prefix
# currently holds a likelihood-level control only (teacher-forced NLL at n=200), and
# Section 9 lists the generation-level version as an open evidence gap -- the paper's
# only architectural novelty is measured in a metric the rest of the paper is not
# judged on. This closes that with the metrics that matter: IR Cosine, IR-Op-Set F1,
# IR-Op-Seq LCS, and (for three of the five modes) real Build.
#
# Five prefix sources, all decoded by the same checkpoints:
#   prior        pi_m(z_m)             -- the deployed path
#   oracle_ir    f_ir(reference IR)    -- upper bound on the prefix path.
#                                         READS GROUND TRUTH; output must never be
#                                         used as a generation result or enter training
#   zero_prefix  K all-zero embeddings -- bypasses Psi; "no latent signal"
#   zero_latent  Psi(0)                -- NOT zero. Psi opens with a LayerNorm, so a
#                                         zero input gives a learned constant prefix.
#                                         Answers "did the adapter learn a generic
#                                         prompt?", which zero_prefix cannot
#   shuffled     another row's Psi(pi_m(z_m)) -- wrong but same-distribution. The
#                                         strongest control: if this matches prior,
#                                         the decoder is not reading prefix CONTENT
#
# HOW TO READ IT (decision tree, in order):
#   1. prior vs shuffled. If indistinguishable, the mechanism in the title does not
#      hold -- the prefix is a placeholder and the plan quality comes from the
#      observation block. That would be a negative result requiring the paper to be
#      repositioned, and it is the first thing to rule out.
#   2. oracle_ir vs prior. Much better => the PRIOR is the bottleneck, the prefix path
#      has capacity. Similar => the prefix path itself is the ceiling, and a better
#      prior cannot help.
#   3. zero_latent vs zero_prefix. Far apart => the adapter learned a useful constant
#      prefix, worth one sentence in the paper.
#
# Runs in WSL. No retraining. ~500 rows x 5 modes x 2 modalities on one GPU.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

IR_DIR=outputs/lora_ir_25k_stage3b          # final checkpoint, same as the main results
CODE_DIR=outputs/qwen25_coder_1_5b_program_25k_stage4b
WORK=outputs/ablation_prefix
LIMIT=500
BATCH=16

if [ ! -d "$IR_DIR" ]; then
  echo "note: $IR_DIR missing, falling back to Stage 3 (record this in the results)" >&2
  IR_DIR=outputs/lora_ir_25k
fi
mkdir -p "$WORK"

# Fail fast rather than 40 minutes in.
python training_25k/scripts/test_n1_patches.py || {
  echo "N1 self-test failed -- not starting the runs." >&2; exit 1; }

for MODE in prior oracle_ir zero_prefix zero_latent shuffled; do
  for M in step point; do
    OUT="$WORK/pred_ir_${M}_${MODE}.jsonl"
    if [ -s "$OUT" ]; then echo "=== skip $MODE/$M (exists) ==="; continue; fi
    echo "=== generate: $MODE / $M ==="
    python training_25k/scripts/gen_predicted_ir.py \
      --modality "$M" \
      --alignment-checkpoint outputs/align_25k/best.pt \
      --prior-checkpoint "outputs/prior_${M}_25k/best.pt" \
      --lora-ir-dir "$IR_DIR" \
      --input-jsonl data/25k/test.jsonl --limit "$LIMIT" \
      --output-jsonl "$OUT" \
      --prefix-source "$MODE" \
      --max-length 1536 --max-new-tokens 1536 \
      --batch-size "$BATCH"
  done
done

echo
echo "=== scoring IR quality (all 10 runs) ==="
for MODE in prior oracle_ir zero_prefix zero_latent shuffled; do
  for M in step point; do
    python -m gen_scripts.evaluate_ir_quality \
      --predicted-jsonl "$WORK/pred_ir_${M}_${MODE}.jsonl" \
      --alignment-checkpoint outputs/align_25k/best.pt \
      --output-json "$WORK/score_${M}_${MODE}.json"
  done
done

cat > "$WORK/run_metadata.json" <<JSON
{
  "experiment": "N1 prefix-source ablation",
  "lora_ir_dir": "$IR_DIR",
  "limit": $LIMIT,
  "batch_size": $BATCH,
  "note": "All five modes share one batch size, so internal comparison is fair. Batched greedy decoding is NOT bit-identical to sequential, so do NOT compare these against batch-size-1 results elsewhere in the paper.",
  "repair_applied": false,
  "modes": ["prior","oracle_ir","zero_prefix","zero_latent","shuffled"]
}
JSON

echo
echo "=== IR-quality summary ==="
python - <<'PY'
import json, pathlib
w = pathlib.Path("outputs/ablation_prefix")
print(f"{'mode':<12}{'modality':<10}{'IR cos':>9}{'Op-Set F1':>11}{'Op-Seq LCS':>12}")
for mode in ["zero_prefix","zero_latent","shuffled","prior","oracle_ir"]:
    for m in ["step","point"]:
        p = w / f"score_{m}_{mode}.json"
        if not p.exists():
            print(f"{mode:<12}{m:<10}{'(missing)':>9}"); continue
        # evaluate_ir_quality writes {"summary": {...}, "per_sample": [...]}
        d = json.loads(p.read_text()).get("summary", {})
        g = lambda *ks: next((d[k] for k in ks if k in d), float('nan'))
        print(f"{mode:<12}{m:<10}{g('ir_cosine_mean','ir_cosine'):>9.3f}"
              f"{100*g('op_set_f1_mean','op_set_f1'):>10.1f}%"
              f"{100*g('op_seq_lcs_mean','op_seq_lcs'):>11.1f}%")
print()
print("Decision 1: is prior clearly better than shuffled?  If not, the mechanism fails.")
print("Decision 2: is oracle_ir clearly better than prior? If yes, the prior is the bottleneck.")
print("Decision 3: zero_latent vs zero_prefix -- did the adapter learn a constant prefix?")
PY

# ---------------------------------------------------------------------------
# Build for the three decisive modes. prior / oracle_ir / shuffled are what settle
# the decision tree; zero_* need no execution because their IR quality already
# answers decision 3.
#
# This runs here rather than being printed for you to paste: it is WSL work, and the
# only reason anything gets printed at the end is that WSL cannot `import flluma`.
# Skip with:  N1_SKIP_BUILD=1 bash training_25k/24_n1_prefix_source_ablation.sh
# ---------------------------------------------------------------------------
if [ "${N1_SKIP_BUILD:-0}" = "1" ]; then
  echo "=== N1_SKIP_BUILD=1, skipping code generation ==="
else
  for MODE in prior oracle_ir shuffled; do
    GEN="$WORK/gen_step_${MODE}.jsonl"
    if [ -s "$GEN" ]; then echo "=== skip code $MODE (exists) ==="; continue; fi
    echo "=== generate programs: $MODE / step ==="
    python training_25k/scripts/gen_code_from_predicted_ir.py \
      --modality step \
      --ir-jsonl "$WORK/pred_ir_step_${MODE}.jsonl" \
      --lora-code-dir "$CODE_DIR" \
      --input-jsonl data/25k/test.jsonl \
      --output-jsonl "$GEN" \
      --max-length 1536 --max-new-tokens 1536 --batch-size 16
  done
  echo
  echo "=== programs written ==="
  ls -la "$WORK"/gen_step_*.jsonl 2>/dev/null | awk '{print "  "$NF, $5" bytes"}'
fi

cat <<'EOF'

=== NOW RUN THIS IN WINDOWS POWERSHELL (the only part WSL cannot do) ===

Everything above already ran. Execution needs FllumaCLI, which WSL cannot load, so
this last step is yours. Paste as-is -- it is PowerShell syntax, not bash.

  foreach ($MODE in @("prior","oracle_ir","shuffled")) {
    & "C:\Workspace\Project\Paper\MIRAGE-V2\src\scripts\evaluate_execution.ps1" `
      -InputJsonl "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\outputs\ablation_prefix\gen_step_$MODE.jsonl" `
      -OutputDir  "C:\Workspace\Project\Paper\MIRAGE-V2\scratch\exec_n1_step_$MODE"
  }

CONSISTENCY: this batch skips the three deterministic repair rules entirely
(run_metadata.json records repair_applied=false). That is fine because all modes skip
them equally, and Section 5.9 measured the rules to be worth at most +0.60pp anyway --
but state it when reporting, and do not mix these Build numbers with the main tables.
EOF
