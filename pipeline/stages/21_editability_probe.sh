#!/bin/bash
# B7: delta-editability probe. WSL side only assembles the inputs -- the probe
# itself runs on Windows under FllumaCLI, because it re-executes programs.
#
# WHY THIS IS THE HIGHEST-VALUE REMAINING EXPERIMENT
# --------------------------------------------------
# It is the only one that does three things at once:
#
#   * Section 3.2 defines delta-editability formally and Table tab:claims_evidence
#     currently marks it "Not measured". This measures it.
#   * The title's claim is about *programs*, not meshes -- editability is the
#     property that distinguishes a program from a reconstruction, and it is
#     presently unsupported.
#   * It is the one dimension where variant C has a STRUCTURAL reason to beat the
#     NN-IR baselines. A and B substitute another part's construction plan, so its
#     parameter names and semantics need not correspond to the query at all; C
#     generates parameters for the part it was asked about. Every other comparison
#     in the paper favours A/B. This one might not, and that is exactly why it is
#     worth running rather than assuming.
#
# Read the header of src/editability_probe.py for what the three outcomes mean.
# The short version: "rebuilt and moved" is editable, "rebuilt with no geometry
# change" is a declared-but-unused parameter (an edit that silently does nothing),
# and "broke" is brittleness. The middle one is the easy one to miss.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

S4B=outputs/qwen25_coder_1_5b_program_25k_stage4b
NNIR=outputs/nnir_baseline_25k
WORK=outputs/editability_25k
IDS="$WORK/probe_ids.txt"
N=100

mkdir -p "$WORK"

C_SRC="$S4B/gen_test_step_stage3b_repaired_p0.jsonl"
A_SRC="$NNIR/direct_step_repaired_p0.jsonl"
B_SRC="$NNIR/prior_step_repaired_p0.jsonl"
[ -f "$A_SRC" ] || A_SRC="$NNIR/direct_step.jsonl"
[ -f "$B_SRC" ] || B_SRC="$NNIR/prior_step.jsonl"

# ---------------------------------------------------------------------------
# Sample selection. STEP only: it is the strongest modality, so a low editability
# score there cannot be blamed on a weak encoder.
#
# The subset must be drawn from the INTERSECTION of the variants, not from C alone.
# Variant C covers all 2,500 test rows but the NN-IR baselines were only ever run at
# n=100, so drawing 200 ids from C's 2,500 leaves ~9 that A and B also have -- which
# is what a first version of this script did, and it silently reduced the paired
# comparison to nine samples. The intersection is the binding constraint, so it
# defines the pool.
# ---------------------------------------------------------------------------
echo "=== building the id pool from the intersection of C, A and B ==="
python3 - "$C_SRC" "$A_SRC" "$B_SRC" "$WORK/pool_ids.txt" <<'PY'
import json, sys
paths, out = sys.argv[1:4], sys.argv[4]
sets = []
for p in paths:
    ids = set()
    try:
        with open(p, encoding='utf-8') as fh:
            for line in fh:
                line = line.strip()
                if line:
                    ids.add(json.loads(line)['sample_id'])
    except FileNotFoundError:
        print(f'  MISSING {p}')
    print(f'  {len(ids):>5} ids  {p}')
    if ids:
        sets.append(ids)
inter = set.intersection(*sets) if sets else set()
print(f'  {len(inter):>5} ids  <- intersection (the usable pool)')
with open(out, 'w', encoding='utf-8', newline='\n') as fh:
    for i in sorted(inter):
        fh.write(i + '\n')
PY

POOL=$(wc -l < "$WORK/pool_ids.txt")
if [ "$POOL" -lt 20 ]; then
  echo "ERROR: intersection is only $POOL ids -- too few for a paired comparison." >&2
  echo "       Re-run the NN-IR baseline on more rows first (13_gen_nnir_baseline)." >&2
  exit 1
fi
if [ "$POOL" -lt "$N" ]; then
  echo "  note: pool ($POOL) smaller than requested N ($N); using the whole pool"
  N="$POOL"
fi

# Draw N from the pool, then take exactly those ids from all three variants.
echo "=== drawing seeded random $N from the $POOL-id pool ==="
python3 - "$WORK/pool_ids.txt" "$IDS" "$N" <<'PY'
import random, sys
pool = [l.strip() for l in open(sys.argv[1], encoding='utf-8') if l.strip()]
rng = random.Random(20260804)
chosen = rng.sample(pool, min(int(sys.argv[3]), len(pool)))
with open(sys.argv[2], 'w', encoding='utf-8', newline='\n') as fh:
    for i in chosen:
        fh.write(i + '\n')
print(f'  wrote {len(chosen)} ids to {sys.argv[2]}')
PY

for spec in "c:$C_SRC" "direct:$A_SRC" "prior:$B_SRC"; do
  v="${spec%%:*}"; src="${spec#*:}"
  if [ ! -f "$src" ]; then
    echo "  WARNING: no file for $v ($src) -- skipping this variant"
    continue
  fi
  echo "=== [$v] selecting the shared ids ==="
  python training_25k/scripts/make_random_subset.py \
    --input "$src" --output "$WORK/${v}_step.jsonl" --ids-from "$IDS"
done

echo
echo "=== row counts (all three must match, or the comparison is not paired) ==="
for v in c direct prior; do
  f="$WORK/${v}_step.jsonl"
  [ -f "$f" ] && printf "  %-8s %s rows\n" "$v" "$(wc -l < "$f")"
done

echo
echo "=== inputs prepared in $WORK ==="
ls -la "$WORK"

cat <<'EOF'

=== Now in Windows PowerShell (needs FllumaCLI; re-executes every perturbation) ===

$Root = "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src"
$Work = "outputs\editability_25k"
$Out  = "C:\Workspace\Project\Paper\MIRAGE-V2\scratch"

# Runtime warning: each row costs (number of declared parameters) x (4 deltas) + 1
# executions. At ~4 parameters per part that is ~17 kernel runs per row, so 200 rows
# is on the order of 3,400 executions per variant. Budget accordingly, and consider
# -Limit 50 for a first pass to confirm the plumbing before committing to all three.

foreach ($v in @("c","direct","prior")) {
  $in = Join-Path $Root "$Work\${v}_step.jsonl"
  if (-not (Test-Path -LiteralPath $in)) { Write-Output "skip $v (no input)"; continue }
  & "C:\Workspace\Project\Paper\MIRAGE-V2\src\scripts\editability_probe.ps1" `
    -InputJsonl $in `
    -OutputDir  "$Out\editability_25k_step_${v}" `
    -Deltas "-0.25,-0.1,0.1,0.25"
}

=== Then aggregate into the paper table (WSL or local Python): ===

  python3 src/scratch/aggregate_editability.py \
    --dirs /mnt/c/Workspace/Project/Paper/MIRAGE-V2/scratch/editability_25k_step_c \
           /mnt/c/Workspace/Project/Paper/MIRAGE-V2/scratch/editability_25k_step_direct \
           /mnt/c/Workspace/Project/Paper/MIRAGE-V2/scratch/editability_25k_step_prior \
    --labels "C: Generated IR" "A: Direct-NN-IR" "B: Prior-NN-IR" \
    --latex

=== HOW TO WRITE IT UP, whichever way it comes out ===

The result is publishable in both directions, which is the reason to run it:

  * If C beats A/B -- the first dimension on which the generated plan wins. It
    would support the paper's framing directly: retrieval gets an executable
    program, but not one whose parameters mean what the query needs. Add a row to
    Table tab:positioning and change the tab:claims_evidence "Not measured" row.
  * If C does not beat A/B -- then delta-editability, which Section 3.2 defines and
    the title implies, is not delivered, and that must be stated as plainly as the
    compositional-split result already is. Change the claims table from
    "Not measured" to "No", and say so in Section 9.
  * If parametric coverage is low for everyone -- the most likely single finding,
    given that generated programs inline sketch coordinates and translation offsets
    (`points=[[-12.31, -28.8], ...]`, `offset=[0.0, 0.0, 3.25]`). Then the honest
    claim shrinks to "the declared dimensions are editable; the profile geometry is
    not", which is still worth having precisely because nobody currently knows it.

Do not report only the build-survival number. "Rebuilt with no geometry change"
must appear in the table: a parameter that is declared, edited, and silently
ignored is a worse user experience than one that errors, and it is invisible to a
build-rate-only metric.
EOF
