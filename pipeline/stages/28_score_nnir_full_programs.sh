#!/bin/bash
# Program-level metrics for the n=2,500 NN-IR baselines, so tab:generation's A/B rows
# can be replaced in FULL rather than half.
#
# WHY THIS EXISTS. B3 (26_b3_b4_sample_size_fixes.sh) raised variants A and B from
# n=100 to n=2,500, but execution only supplies two of tab:generation's four columns:
# Syn and Build. Prog-Op-F1 and Source Similarity come from evaluate_programs.py, which
# is a torch-only scoring pass with no kernel and no generation.
#
# Moving Syn/Build to n=2,500 while leaving Prog-Op-F1/Sim at n=100 would put two
# sample sizes inside a single ROW -- a worse version of the defect B3 exists to remove,
# and harder for a reader to notice. So the table does not move until this runs.
#
# Reads the same _repaired_p0 files execution scored, so every column of the new A/B
# rows describes one identical set of programs.
#
# Runs in WSL. No GPU generation, no kernel. Minutes, not hours.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

NNIR=outputs/nnir_baseline_25k_full
EXPECT=2500

[ -d "$NNIR" ] || { echo "FATAL: $NNIR missing -- run 26_b3_b4_sample_size_fixes.sh first." >&2; exit 1; }

for m in step point text image; do
  for mode in direct prior; do
    SRC="$NNIR/${mode}_${m}_repaired_p0.jsonl"
    OUT="$NNIR/eval_${mode}_${m}"

    if [ ! -s "$SRC" ]; then
      echo "FATAL: $SRC missing. B3 did not finish this condition." >&2
      exit 1
    fi
    # The same coverage assertion B3 makes. Scoring a short file would silently
    # produce a confident-looking mean over the wrong denominator, which is the
    # failure mode that cost a run earlier in this round.
    GOT=$(wc -l < "$SRC")
    if [ "$GOT" -ne "$EXPECT" ]; then
      echo "FATAL: $SRC has $GOT rows, expected $EXPECT. Not scoring a partial file." >&2
      exit 1
    fi

    if [ -s "$OUT/evaluation_summary.json" ]; then
      echo "  skip $mode/$m (exists)"; continue
    fi
    echo "=== program-level eval: $mode / $m  ($GOT rows) ==="
    python evaluate_programs.py --predictions "$SRC" --output-dir "$OUT"
  done
done

echo
echo "=== summary: the four tab:generation columns, n=2,500 ==="
python - <<'PY'
import json, pathlib
w = pathlib.Path("outputs/nnir_baseline_25k_full")
s = pathlib.Path("/mnt/c/Workspace/Project/Paper/MIRAGE-V2/scratch")
print(f"  {'condition':<15}{'n':>6}{'Syn %':>8}{'Prog-Op-F1 %':>14}{'Build %':>9}{'Sim %':>8}")
for m in ("text", "image", "point", "step"):
    for mode in ("direct", "prior"):
        f = w / f"eval_{mode}_{m}" / "evaluation_summary.json"
        if not f.exists():
            print(f"  {mode+'/'+m:<15}(missing)"); continue
        d = json.loads(f.read_text(encoding="utf8"))
        # Syn and Build come from the execution pass, which is the authority for both;
        # evaluate_programs.py leaves syntax_valid_rate null on these inputs.
        e = s / f"exec_nnir_full_{mode}_{m}" / "execution_summary.json"
        syn = bld = float("nan")
        if e.exists():
            ed = json.loads(e.read_text(encoding="utf8"))
            syn, bld = 100 * ed["syntax_ok_rate"], 100 * ed["build_ok_rate"]
        print(f"  {mode+'/'+m:<15}{d['count']:>6}{syn:>8.1f}"
              f"{100*d['mean_operation_f1']:>14.1f}{bld:>9.1f}"
              f"{100*d['mean_source_similarity']:>8.1f}")
print()
print("  If any row shows nan for Syn/Build, the Windows execution pass has not been run")
print("  for that condition -- see 26_b3_b4_sample_size_fixes.sh's PowerShell block.")
PY

cat <<'EOF'

=== No Windows step. This one is WSL-only. ===

Next, from WSL:  python scratch/b3_b4_analysis.py
     or Windows:  python C:\Workspace\Project\Paper\MIRAGE-V2\src\scratch\b3_b4_analysis.py

Then tab:generation's A and B rows can be replaced wholesale at n=2,500. Until every
condition above reports all four columns, leave the table alone -- a row mixing n=100
and n=2,500 across its own columns is worse than the mixed-row table B3 set out to fix.
EOF
