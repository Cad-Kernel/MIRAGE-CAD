"""B10: how well are the held-out families' operations covered by the retained ones?

The compositional split is meant to isolate unseen operation *combinations* from
unseen *operations*: every operation a held-out family uses must still occur in a
retained family. That was verified as a yes/no coverage audit, but never quantified,
and the paper flags the resulting confound -- `sweep_tube` is both a held-out family
and the first member of the oversampled rare-operation union, so for that family the
two factors are not separated.

This produces the numbers. For each of the four held-out families, list its
operations and how many rows of the retained training partition contain each one. An
operation present in thousands of retained rows supports the "combination only"
reading; one present in a few hundred does not.

    python src/scratch/heldout_family_op_coverage.py [--latex]
"""
from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter, defaultdict

WSL = "//wsl.localhost/Ubuntu/home/jizong/workspace/MIRAGE/src"
BS = chr(92)
OP = re.compile(r"\bOP_[A-Z0-9]+(?:_[A-Z0-9]+)*\b")
HELD_OUT = ["cross_tab_profile_mount", "stepped_profile_mount",
            "face_recursive_mount", "sweep_tube"]
OVERSAMPLED = {"OP_SWEEP_TUBE", "OP_CIRCULAR_PATTERN", "OP_SKETCH_ON_FACE",
               "OP_FACE_EXTRUDE_ADD", "OP_FACE_EXTRUDE_CUT", "OP_PROFILE_CUT"}


def win(p: str) -> str:
    t = str(p).replace(BS, "/")
    if t.startswith("/mnt/") and len(t) > 6:
        return t[5].upper() + ":/" + t[7:]
    return t


def read_rows(path):
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def ops_and_family(row):
    p = win(row.get("ir_path", ""))
    if not os.path.exists(p):
        return None, None
    txt = open(p, encoding="utf-8", errors="replace").read()
    m = re.search(r"^PART\s+\S+\s+CAT\s+(\S+)", txt, re.M)
    return (m.group(1) if m else None), set(OP.findall(txt))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--latex", action="store_true")
    args = ap.parse_args()

    # Retained training partition of the compositional split.
    retained_op_rows: Counter = Counter()
    retained_families: set[str] = set()
    n_retained = 0
    for row in read_rows(f"{WSL}/data/25k_comp/train.jsonl"):
        fam, ops = ops_and_family(row)
        if ops is None:
            continue
        n_retained += 1
        retained_families.add(fam)
        for o in ops:
            retained_op_rows[o] += 1

    # Operations actually used by each held-out family, from the held-out test set.
    family_ops: dict[str, Counter] = defaultdict(Counter)
    family_rows: Counter = Counter()
    for row in read_rows(f"{WSL}/data/25k_comp/comp_test.jsonl"):
        fam, ops = ops_and_family(row)
        if ops is None:
            continue
        family_rows[fam] += 1
        for o in ops:
            family_ops[fam][o] += 1

    print(f"retained training partition: {n_retained} rows, "
          f"{len(retained_families)} families")
    print(f"held-out families found in comp_test: {dict(family_rows)}")
    print()

    rows_out = []
    for fam in HELD_OUT:
        if fam not in family_ops:
            print(f"--- {fam}: NOT FOUND in comp_test (CAT may differ) ---")
            continue
        print(f"--- {fam}  ({family_rows[fam]} held-out rows) ---")
        print(f"    {'operation':<30} {'rows in retained':>17} {'% of retained':>14}")
        for op, _ in family_ops[fam].most_common():
            k = retained_op_rows.get(op, 0)
            pct = 100.0 * k / n_retained if n_retained else 0.0
            flag = "  <- oversampled" if op in OVERSAMPLED else ""
            if k == 0:
                flag += "  <<< ABSENT: split does NOT isolate combination"
            print(f"    {op:<30} {k:>17} {pct:>13.2f}%{flag}")
            rows_out.append((fam, op, k, pct, op in OVERSAMPLED))
        worst = min((retained_op_rows.get(o, 0) for o in family_ops[fam]), default=0)
        print(f"    rarest constituent operation: {worst} retained rows "
              f"({100.0*worst/max(n_retained,1):.2f}%)")
        print()

    if args.latex:
        print("% fam & op & retained rows & % \\\\")
        for fam, op, k, pct, over in rows_out:
            name = op.replace("_", r"\_")
            star = "$^\\dagger$" if over else ""
            print(f"\\texttt{{{fam.replace('_', r'_')}}} & \\texttt{{{name}}}{star} "
                  f"& {k:,} & {pct:.2f} \\\\".replace("_", r"\_"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
