r"""Trace where the manuscript's Prog-Op-F1 columns come from, and whether the empty-set convention
inconsistency reaches them.

The two scorers disagree on the same degenerate input:

  src/evaluate_programs.py            operation_f1 via prf()  -> 0.0   for two empty lists
                                      operation_lcs_ratio via difflib -> 1.0
  src/gen_scripts/evaluate_ir_quality.py   op_set_metrics -> 1.0 for two empty sets
                                           op_seq_lcs_ratio -> 1.0

The first is internally inconsistent. This script answers the four questions the review asked, in
order, and answers only those: which script produced the published columns, what the convention is
on that path, how many published rows are affected, and whether the headline ordering could move.

It changes nothing. Tracing before recomputing is the point.
"""
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
S = REPO / "scratch"


def jl(p):
    return [json.loads(l) for l in io.open(p, encoding="utf-8", errors="ignore") if l.strip()]


def head(t):
    print(f"\n{'=' * 96}\n{t}\n{'=' * 96}")


head("Q1  which script writes the fields each scorer owns?")
FIELDS = {
    "src/evaluate_programs.py": ["operation_f1", "operation_lcs_ratio", "operation_precision",
                                 "operation_count_error", "source_similarity", "defines_part"],
    "src/gen_scripts/evaluate_ir_quality.py": ["op_set_f1", "op_seq_lcs", "ir_cosine"],
}
for script, fields in FIELDS.items():
    p = REPO / script
    t = p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""
    own = [f for f in fields if f'"{f}"' in t]
    print(f"  {script}")
    print(f"      emits: {own}")

head("Q1  which Windows-side result files carry which field set?")
sig = {}
for p in sorted(S.rglob("*.jsonl")):
    if p.stat().st_size > 60_000_000:
        continue
    try:
        first = io.open(p, encoding="utf-8", errors="ignore").readline()
    except OSError:
        continue
    has_prog = "operation_f1" in first
    has_ir = "op_set_f1" in first or "op_seq_lcs" in first
    if has_prog or has_ir:
        sig[str(p.relative_to(S))] = ("evaluate_programs" if has_prog else "") + \
                                     ("+evaluate_ir_quality" if has_ir else "")
for k, v in sorted(sig.items()):
    print(f"  {k:52s} {v}")
if not sig:
    print("  none: every per-sample metric file is WSL-side")

head("Q2 and Q3  the degenerate convention, and how many rows carry it")
tot_deg = 0
for name in sorted(p.name for p in S.glob("tab3_*_evaluation_rows.jsonl")):
    rows = jl(S / name)
    deg = [r for r in rows
           if (r.get("operation_f1") or 0) == 0.0 and (r.get("operation_lcs_ratio") or 0) >= 0.999]
    tot_deg += len(deg)
    n = len(rows)
    with_f1 = sum(r["operation_f1"] for r in rows) / n * 100
    # Under the OTHER scorer's convention a degenerate row would score 1.0 on both.
    alt_f1 = (sum(r["operation_f1"] for r in rows) + len(deg)) / n * 100
    alt_lcs_drop = (sum(r["operation_lcs_ratio"] for r in rows)) / n * 100
    print(f"\n  {name}")
    print(f"      rows {n}, degenerate {len(deg)} ({100.0 * len(deg) / n:.1f} %)")
    print(f"      mean operation_f1 as published-by-this-file : {with_f1:.2f} %")
    print(f"      the same under evaluate_ir_quality's rule    : {alt_f1:.2f} %  "
          f"(delta {alt_f1 - with_f1:+.2f} pp)")
    print(f"      mean operation_lcs_ratio (already 1.0 there) : {alt_lcs_drop:.2f} %")

head("Q4  could the headline ordering move?")
print("""  The affected quantity is an ABSOLUTE level, not an ordering. Every degenerate row scores 0.0
  under evaluate_programs' rule and 1.0 under the other, so switching convention can only RAISE a
  mean operation_f1, by (degenerate rows / n) points, and it raises every arm's mean by that arm's
  own degenerate share. An ordering between two arms flips only if their degenerate shares differ
  by more than their measured gap.""")
shares = {}
for name in sorted(p.name for p in S.glob("tab3_*_evaluation_rows.jsonl")):
    rows = jl(S / name)
    deg = sum(1 for r in rows
              if (r.get("operation_f1") or 0) == 0.0
              and (r.get("operation_lcs_ratio") or 0) >= 0.999)
    shares[name] = 100.0 * deg / len(rows)
    print(f"      {name:44s} degenerate share {shares[name]:.1f} %")
if len(shares) >= 2:
    v = sorted(shares.values())
    print(f"      spread across these files: {v[-1] - v[0]:.2f} pp")

head("what this script does NOT settle")
print("""  Whether tab:main and tab:generation's Prog-Op-F1 columns were produced by
  evaluate_programs.py at all. The tab3_* files here do not match either table's printed values --
  tab3_step_C's mean operation_f1 is 84.68 % and tab3_text_C's 62.52 %, against tab:generation's
  80.1 % for text/C -- so these are an intermediate or superseded run, not the published source.
  Answering Q1 for the published columns needs the WSL-side outputs/ tree. Until then the
  convention question is open for the published numbers and settled only for these files.""")
