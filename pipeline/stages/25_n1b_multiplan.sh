#!/bin/bash
# N1b: sample several PLANS per query, not just several programs per plan.
#
# The paper's opening argument is that final geometry does not determine construction
# history -- a cylinder can be an extruded circle, a revolved rectangle, or a bored
# block. But the whole pipeline is deterministic: pi_m is an MLP and plan decoding is
# greedy. A one-to-many problem solved with a one-to-one map. Where the corpus records
# only one of several valid histories, the prior is trained to hit that one and is
# penalised for proposing a legitimate alternative.
#
# The headroom is quantified: Table tab:ablation_stage4b shows Build 95% given the
# ground-truth plan against 67% given the predicted one. Twenty-eight points sit in
# plan quality.
#
# THE COMPUTE-MATCHED CONTROL IS THE WHOLE EXPERIMENT. Table tab:geometry already
# shows that sampling more PROGRAMS helps (STEP 67->82%). So "5 sampled plans beat 1
# greedy plan" proves nothing -- a reviewer will say you simply sampled more. The
# claim worth testing is that diversity is worth MORE at the plan layer than at the
# code layer, which requires equal total generations:
#
#   A  1 greedy plan  x 5 programs =  5   diversity all in the code layer (have this)
#   B  5 sampled plans x 1 program =  5   diversity all in the plan layer  <-- new
#   C  5 sampled plans x 5 programs = 25  upper bound; are the layers complementary?
#   D  1 greedy plan  x 1 program =  1   current main table
#
# A and B cost the same. B > A is the evidence. Without that row this experiment
# says nothing.
#
# EVERYTHING WSL-SIDE RUNS HERE, including the temperature choice -- the script picks
# T by a stated rule and continues, rather than stopping to ask. Only the Windows
# execution step is printed at the end, because WSL cannot `import flluma`.
# Override the automatic choice with:  N1B_TEMPERATURE=0.7 bash training_25k/25_...sh
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

IR_DIR=outputs/lora_ir_25k_stage3b
CODE_DIR=outputs/qwen25_coder_1_5b_program_25k_stage4b
WORK=outputs/ablation_multiplan
K=5
# THE PART SET IS THE WHOLE EXPERIMENT, AND THE FIRST RUN GOT IT WRONG.
# This script used --limit 100, which takes the FIRST hundred test rows. Configuration
# A -- the thing B is supposed to be compared against -- was re-run in the B5 round on a
# SEEDED RANDOM hundred, precisely because the first-N slice measures ~10 pp optimistic
# (docs §9.2: STEP N=1 79.0% first-100 vs 67.0% random-100). The two sets shared 4 parts,
# so the A-vs-B difference was confounded with that bias, in the direction that flatters
# B. Fixed by reusing A's exact sample_ids.
IDS=outputs/geometry_nbest_random100/ir_step.jsonl.ids.txt
SUBSET="$WORK/test_subset100.jsonl"
# num_return_sequences=K multiplies the decoded sequence count, so the batch must
# shrink accordingly: 16 x 5 = 80 concurrent sequences will very likely OOM on 16 GB.
BATCH=4

[ -d "$IR_DIR" ] || IR_DIR=outputs/lora_ir_25k
mkdir -p "$WORK"

python training_25k/scripts/test_n1_patches.py || {
  echo "N1 self-test failed -- not starting." >&2; exit 1; }

# ---------------------------------------------------------------------------
# Step 0: build the part set. Configuration B must run on configuration A's parts
# or the comparison is worthless, so this is a hard precondition, not a default.
# ---------------------------------------------------------------------------
if [ ! -s "$IDS" ]; then
  echo "FATAL: $IDS not found." >&2
  echo "  Configuration B must run on configuration A's exact parts. That id list is" >&2
  echo "  produced by 20_rerun_geometry_nbest_random100.sh -- run it first." >&2
  exit 1
fi
python training_25k/scripts/make_random_subset.py \
  --input data/25k/test.jsonl \
  --output "$SUBSET" \
  --ids-from "$IDS"
N_SUBSET=$(wc -l < "$SUBSET")
echo "=== configuration B will run on $N_SUBSET parts, the same ones as configuration A ==="
if [ "$N_SUBSET" -lt 100 ]; then
  echo "FATAL: only $N_SUBSET of the 100 ids resolved against data/25k/test.jsonl." >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# Step 1: temperature sweep on STEP only. Sampling can break the PART/PARAM/F/END
# structure outright, which is the main risk here, so establish a temperature that
# keeps the grammar valid before spending anything else.
#
# The sweep is ~40% of this script's compute. It earns that on the re-run because the
# first sweep produced a substantive NEGATIVE finding -- five sampled plans are always
# textually distinct but their operation sets overlap 82-90%, i.e. the sampler varies
# parameters rather than construction strategy -- and that finding was measured on the
# biased first-100 slice. Re-measuring it on the same random 100 as everything else is
# what makes it reportable. Skip only if you already accept it:
#
#   N1B_SKIP_SWEEP=1 N1B_TEMPERATURE=1.0 bash training_25k/25_n1b_multiplan.sh
# ---------------------------------------------------------------------------
if [ "${N1B_SKIP_SWEEP:-0}" = "1" ]; then
  if [ -z "${N1B_TEMPERATURE:-}" ]; then
    echo "FATAL: N1B_SKIP_SWEEP=1 needs N1B_TEMPERATURE=<T> -- without the sweep" >&2
    echo "  there is nothing to choose T from." >&2
    exit 1
  fi
  echo "=== N1B_SKIP_SWEEP=1, using T=$N1B_TEMPERATURE without re-measuring diversity ==="
  echo "    (the op-Jaccard figures in docs 9.11 then remain on the first-100 slice)"
fi
for T in 0.3 0.7 1.0; do
  [ "${N1B_SKIP_SWEEP:-0}" = "1" ] && break
  OUT="$WORK/plans_step_r100_T${T}_K${K}.jsonl"
  if [ -s "$OUT" ]; then echo "=== skip T=$T (exists) ==="; continue; fi
  echo "=== temperature sweep: T=$T ==="
  python training_25k/scripts/gen_predicted_ir.py \
    --modality step \
    --alignment-checkpoint outputs/align_25k/best.pt \
    --prior-checkpoint outputs/prior_step_25k/best.pt \
    --lora-ir-dir "$IR_DIR" \
    --input-jsonl "$SUBSET" \
    --output-jsonl "$OUT" \
    --num-plans "$K" --temperature "$T" --top-p 0.95 \
    --max-length 1536 --max-new-tokens 1536 --batch-size "$BATCH"
done

# ---------------------------------------------------------------------------
# Step 2: score the sweep and CHOOSE a temperature automatically.
#
# Rule, stated so the choice is reproducible rather than a judgement call:
#   among temperatures whose IR-grammar validity is within 3 pp of the best observed,
#   take the highest one that actually produces diversity (>= 2.0 distinct plans per
#   query out of 5). If none qualifies, fall back to the lowest temperature and say so.
# The rule prefers diversity but refuses to buy it with malformed IR.
# ---------------------------------------------------------------------------
echo
if [ "${N1B_SKIP_SWEEP:-0}" = "1" ]; then
  echo "=== sweep skipped; no diversity statistics measured this run ==="
else
echo "=== grammar validity and plan diversity per temperature ==="
python - <<'PY'
import json, pathlib, itertools, sys
sys.path.insert(0, ".")
from miragecad.gen_prompts import validate_ir_grammar, extract_operation_types

w = pathlib.Path("outputs/ablation_multiplan")
stats = {}
print(f"{'T':>5}{'rows':>7}{'grammar valid':>15}{'distinct plans/query':>22}{'mean pairwise op-Jaccard':>26}")
for T in ("0.3", "0.7", "1.0"):
    f = w / f"plans_step_r100_T{T}_K5.jsonl"
    if not f.exists():
        continue
    rows = [json.loads(l) for l in f.read_text(encoding="utf8").splitlines() if l.strip()]
    by_q = {}
    for r in rows:
        by_q.setdefault(r["sample_id"], []).append(r)
    valid = sum(validate_ir_grammar(r["predicted_ir"])["valid"] for r in rows)
    distinct, jac = [], []
    for plans in by_q.values():
        texts = [p["predicted_ir"] for p in plans]
        distinct.append(len(set(texts)))
        opsets = [set(extract_operation_types(t)) for t in texts]
        pairs = [len(a & b) / len(a | b) for a, b in itertools.combinations(opsets, 2) if (a | b)]
        if pairs:
            jac.append(sum(pairs) / len(pairs))
    v = 100 * valid / max(len(rows), 1)
    d = sum(distinct) / max(len(distinct), 1)
    j = sum(jac) / max(len(jac), 1)
    stats[T] = {"grammar_valid_pct": v, "distinct_per_query": d, "op_jaccard": j,
                "rows": len(rows), "queries": len(by_q)}
    print(f"{T:>5}{len(rows):>7}{v:>14.1f}%{d:>22.2f}{j:>26.3f}")

best_valid = max((s["grammar_valid_pct"] for s in stats.values()), default=0.0)
ok = [T for T, s in stats.items()
      if s["grammar_valid_pct"] >= best_valid - 3.0 and s["distinct_per_query"] >= 2.0]
if ok:
    chosen = max(ok, key=float)
    why = (f"highest T within 3pp of the best grammar validity ({best_valid:.1f}%) "
           f"that still yields >=2.0 distinct plans per query")
else:
    chosen = min(stats, key=float) if stats else "0.3"
    why = ("NO temperature met both conditions -- falling back to the lowest. Either "
           "sampling is destroying the IR grammar, or the decoder's output distribution "
           "is too peaked for sampling to find alternatives near greedy. Check the table "
           "above before trusting configuration B.")
pathlib.Path("outputs/ablation_multiplan/sweep_stats_r100.json").write_text(
    json.dumps({"stats": stats, "chosen_temperature": chosen, "rule": why}, indent=2),
    encoding="utf8")
pathlib.Path("outputs/ablation_multiplan/chosen_T_r100.txt").write_text(chosen, encoding="utf8")
print()
print(f"CHOSEN TEMPERATURE: {chosen}")
print(f"  reason: {why}")
print("  (override with N1B_TEMPERATURE=... and re-run)")
PY
fi

T="${N1B_TEMPERATURE:-$(cat "$WORK/chosen_T_r100.txt")}"
# The sweep block writes chosen_T.txt from the rule alone. If N1B_TEMPERATURE
# overrode it, the output filenames use the override while chosen_T.txt still holds
# the rule's pick -- and the PowerShell block below reads chosen_T.txt, so it would
# point at files that were never written. Record the EFFECTIVE T.
printf '%s' "$T" > "$WORK/chosen_T_r100.txt"
echo
echo "=== using T=$T for the compute-matched configurations ==="
if [ -n "${N1B_TEMPERATURE:-}" ]; then
  echo "    (N1B_TEMPERATURE override; chosen_T.txt updated to match so the"
  echo "     PowerShell step below resolves to the files that actually exist)"
fi

# ---------------------------------------------------------------------------
# Step 3: configuration B -- 5 sampled plans x 1 program each.
# Compute-matched against configuration A, which already exists as Table
# tab:geometry at N=5 (scratch/geometry_nbest_random100_*).
# ---------------------------------------------------------------------------
for M in step point; do
  PLANS="$WORK/planB_r100_${M}_T${T}.jsonl"
  GEN="$WORK/genB_r100_${M}_T${T}.jsonl"

  if [ -s "$PLANS" ]; then
    echo "=== skip plans B/$M (exists) ==="
  else
    echo "=== [B] $M: $K sampled plans per query, T=$T ==="
    python training_25k/scripts/gen_predicted_ir.py \
      --modality "$M" \
      --alignment-checkpoint outputs/align_25k/best.pt \
      --prior-checkpoint "outputs/prior_${M}_25k/best.pt" \
      --lora-ir-dir "$IR_DIR" \
      --input-jsonl "$SUBSET" \
      --output-jsonl "$PLANS" \
      --num-plans "$K" --temperature "$T" --top-p 0.95 \
      --max-length 1536 --max-new-tokens 1536 --batch-size "$BATCH"
  fi

  if [ -s "$GEN" ]; then
    echo "=== skip code B/$M (exists) ==="
  else
    echo "=== [B] $M: one program per plan ==="
    python training_25k/scripts/gen_code_from_predicted_ir.py \
      --modality "$M" \
      --ir-jsonl "$PLANS" \
      --lora-code-dir "$CODE_DIR" \
      --input-jsonl data/25k/test.jsonl \
      --output-jsonl "$GEN" \
      --max-length 1536 --max-new-tokens 1536 --batch-size 8
  fi
done

cat > "$WORK/run_metadata.json" <<JSON
{
  "experiment": "N1b plan-layer sampling",
  "temperature": $T,
  "top_p": 0.95,
  "num_plans": $K,
  "part_set": "configuration A's seeded random 100 (seed 20260804), via $IDS",
  "n_parts": $N_SUBSET,
  "lora_ir_dir": "$IR_DIR",
  "lora_code_dir": "$CODE_DIR",
  "repair_applied": false,
  "compute_matched_against": "configuration A = tab:geometry at N=5, scratch/geometry_nbest_random100_{step,point}",
  "note": "A and B decode 5 sequences per query in total. A puts the diversity in the code layer, B in the plan layer."
}
JSON
echo
echo "=== WSL side complete. Outputs in $WORK ==="
ls -la "$WORK"/*.jsonl 2>/dev/null | awk '{print "  "$NF, $5" bytes"}'

cat <<'EOF'

=== NOW RUN THIS IN WINDOWS POWERSHELL (the only part WSL cannot do) ===

WSL cannot `import flluma`, so execution has to happen on the Windows side. Paste this
into PowerShell as-is; it is PowerShell syntax, not bash.

  $T = Get-Content "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\outputs\ablation_multiplan\chosen_T_r100.txt"
  foreach ($m in @("step","point")) {
    & "C:\Workspace\Project\Paper\MIRAGE-V2\src\scripts\evaluate_execution.ps1" `
      -InputJsonl "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\outputs\ablation_multiplan\genB_r100_${m}_T$T.jsonl" `
      -OutputDir  "C:\Workspace\Project\Paper\MIRAGE-V2\scratch\exec_n1b_B_r100_$m"
  }

=== Then compare against configuration A ===

  A (code-layer diversity, N=5):  scratch/exec_nbest_random100_{step,point}/
  B (plan-layer diversity, K=5):  scratch/exec_n1b_B_r100_{step,point}/

Both decode five sequences per query AND now run on the same 100 parts, so the
comparison is compute-matched and part-matched. The first run of this script was
neither: it used --limit 100 (the first hundred) against A's seeded random hundred,
sharing 4 parts. Those outputs are kept untagged in outputs/ablation_multiplan/ and
scratch/exec_n1b_B_{step,point}/; everything from this run carries an `r100` tag.
Do not mix them.

The comparison A needs is best-of-5 against best-of-5:
  A: any of candidate_results[0:5] with build_ok, per query, from execution_nbest_rows.jsonl
  B: any of the 5 plans' programs with build_ok, per query
Run it from either side -- WSL: `python scratch/n1b_multiplan_analysis.py`; Windows,
from any directory: `python C:\Workspace\Project\Paper\MIRAGE-V2\src\scratch\n1b_multiplan_analysis.py`.\nIt does exactly that and
refuses to report the contrast if the part sets still disagree.

  B > A   plan-layer diversity is worth more. Supports the one-to-many argument in
          Section 1 directly, and the determinism of the prior becomes a measured
          limitation rather than an observation. Promote Section 9.7's "sampling plans,
          not just programs" from future work to a result.
  B ~ A   the two layers are equivalent. The honest claim is then only "sampling
          helps", which Table tab:geometry already established.
  B < A   plan sampling hurts. Check sweep_stats.json first -- most likely the sampled
          plans are malformed rather than merely different.

NOTE ON REPAIR: this batch skips the three deterministic repair rules
(run_metadata.json records repair_applied=false). Configuration A in tab:geometry DID
apply them, so the A-vs-B comparison is not perfectly matched on that axis. Section 5.9
measured the rules to be worth at most +0.60pp, so the mismatch is small relative to
any effect worth reporting -- but state it, and do not mix these Build numbers into the
main tables.
EOF
