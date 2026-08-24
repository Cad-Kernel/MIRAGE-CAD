"""Regenerate Appendix D's operation vocabulary table (tab:op_inventory).

Counts every OP_* token in the training split's reference IR, plus the ROLE value set.
Committed because the appendix asserts specific frequencies and a reader should be able
to check them -- the same reason the failure taxonomy needed
classify_execution_failures.py.

    python src/scratch/op_vocabulary_frequencies.py [--split train] [--latex]

Reads the IR file named by each row's `ir_path`. Paths in the manifest are WSL-style
(/mnt/c/...) and are translated for Windows automatically.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter

WSL_SRC = "//wsl.localhost/Ubuntu/home/jizong/workspace/MIRAGE/src"
BS = chr(92)
OP = re.compile(r"\bOP_[A-Z0-9]+(?:_[A-Z0-9]+)*\b")
ROLE = re.compile(r"\bROLE\s+(\S+)")
# The six oversampled during alignment (Sec. 5.3); marked with a dagger in the table.
OVERSAMPLED = {"OP_SWEEP_TUBE", "OP_CIRCULAR_PATTERN", "OP_SKETCH_ON_FACE",
               "OP_FACE_EXTRUDE_ADD", "OP_FACE_EXTRUDE_CUT", "OP_PROFILE_CUT"}


def to_local(p: str) -> str:
    t = str(p).replace(BS, "/")
    if t.startswith("/mnt/") and len(t) > 6:
        return t[5].upper() + ":/" + t[7:]
    return t


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=None,
                    help="defaults to <wsl>/data/25k/<split>.jsonl")
    ap.add_argument("--split", default="train", choices=["train", "val", "test"])
    ap.add_argument("--latex", action="store_true")
    args = ap.parse_args()

    manifest = args.manifest or f"{WSL_SRC}/data/25k/{args.split}.jsonl"
    with open(manifest, encoding="utf-8") as fh:
        rows = [json.loads(l) for l in fh if l.strip()]

    op_rows, op_total, roles = Counter(), Counter(), Counter()
    missing = 0
    for r in rows:
        p = to_local(r.get("ir_path", ""))
        if not os.path.exists(p):
            missing += 1
            continue
        txt = open(p, encoding="utf-8", errors="replace").read()
        ops = OP.findall(txt)
        for o in set(ops):
            op_rows[o] += 1
        op_total.update(ops)
        roles.update(ROLE.findall(txt))

    n = len(rows) - missing
    print(f"manifest: {manifest}")
    print(f"rows: {len(rows)}, IR files read: {n}, missing: {missing}")
    print(f"distinct OP_* tokens: {len(op_rows)}")
    print()

    if args.latex:
        items = op_rows.most_common()
        half = (len(items) + 1) // 2
        left, right = items[:half], items[half:]
        for i in range(half):
            cells = []
            for col in (left, right):
                if i < len(col):
                    o, c = col[i]
                    star = "$^\\dagger$" if o in OVERSAMPLED else ""
                    name = o.replace("_", BS + "_")
                    cells.append(f"\\texttt{{{name}}}{star} & {c:,} & {100*c/n:.2f} & {op_total[o]:,}")
                else:
                    cells.append(" & & & ")
            print(" & ".join(cells).replace(",", "{,}") + r" \\")
        print()
    else:
        print(f"{'OP token':<32}{'rows':>8}{'% rows':>9}{'total':>9}")
        print("-" * 58)
        for o, c in op_rows.most_common():
            flag = " +" if o in OVERSAMPLED else ""
            print(f"{o:<32}{c:>8}{100*c/n:>8.2f}%{op_total[o]:>9}{flag}")
        print("\n(+ = oversampled during alignment)")

    print()
    print("ROLE values:", len(roles))
    for k, v in roles.most_common():
        print(f"  {k:<24}{v:>8}")
    print()
    below10 = [o for o, c in op_rows.items() if 100 * c / n < 10]
    print(f"operations below 10% of rows: {len(below10)} of {len(op_rows)}")
    print("  -- the paper states the six OVERSAMPLED ops span "
          f"{min(100*op_rows[o]/n for o in OVERSAMPLED if o in op_rows):.1f}"
          f"-{max(100*op_rows[o]/n for o in OVERSAMPLED if o in op_rows):.1f}% "
          "and are a CHOSEN subset, not a frequency band; this line is the check.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
