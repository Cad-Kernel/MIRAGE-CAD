r"""Derive Appendix A's operation inventory: the vocabulary and per-operation training frequency.

The manuscript promises "the complete inventory with per-operation training frequencies", and it
says the vocabulary has 44 tokens. Both must come from the corpus rather than from memory, so this
script reads the training split's reference IR files and counts.

Path note: scratch/corpus_step_train.jsonl records WSL paths (/mnt/c/...). The same files are
reachable from Windows at C:/..., so the paths are translated rather than the corpus copied.

Usage:  python appendix_ir_grammar.py [--limit N] [--tex out.tex]
"""
import argparse
import io
import json
import re
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "scratch" / "corpus_step_train.jsonl"
# The IR is line-oriented and an operation token is the THIRD field of an F line, not the first
# field of anything:
#     F extrude_001 OP_EXTRUDE SEM extruded_solid ROLE secondary_feature DEP sketch_001 ...
# A start-anchored OP_ pattern matches nothing at all, which the first run of this script reported
# as "read 0 IR files" rather than as a wrong answer.
OP = re.compile(r"(?m)^F\s+\S+\s+(OP_[A-Z0-9_]+)")
SEM = re.compile(r"\bSEM\s+(\S+)")
ROLE = re.compile(r"\bROLE\s+(\S+)")
LINE_KIND = re.compile(r"(?m)^([A-Z]+)\b")


def to_windows(p):
    """/mnt/c/... -> C:/...  Anything else is returned unchanged."""
    m = re.match(r"^/mnt/([a-z])/(.*)$", p)
    return f"{m.group(1).upper()}:/{m.group(2)}" if m else p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--tex", default=None)
    a = ap.parse_args()

    rows = []
    with io.open(MANIFEST, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if a.limit is not None and i >= a.limit:
                break
            if line.strip():
                rows.append(json.loads(line))
    print(f"manifest: {len(rows)} training rows from {MANIFEST.name}")

    counts = Counter()          # occurrences
    docs = Counter()            # rows containing the operation at least once
    sems, roles, kinds = Counter(), Counter(), Counter()
    n_read = n_missing = 0
    for r in rows:
        p = r.get("ir_path")
        if not p:
            continue
        wp = Path(to_windows(p))
        if not wp.exists():
            n_missing += 1
            continue
        text = wp.read_text(encoding="utf-8", errors="ignore")
        ops = OP.findall(text)
        if not ops:
            continue
        n_read += 1
        counts.update(ops)
        docs.update(set(ops))
        sems.update(SEM.findall(text))
        roles.update(ROLE.findall(text))
        kinds.update(LINE_KIND.findall(text))

    print(f"read {n_read} IR files, {n_missing} unreachable")
    if not counts:
        raise SystemExit("no operations counted; nothing is written rather than guessing")

    print(f"vocabulary: {len(counts)} distinct OP_ tokens")
    print(f"total occurrences: {sum(counts.values()):,d}")
    print()
    print(f"{'operation':32s} {'rows':>8s} {'% of rows':>10s} {'occurrences':>12s}")
    for op, c in counts.most_common():
        print(f"{op:32s} {docs[op]:>8,d} {100.0 * docs[op] / n_read:>9.2f}% {c:>12,d}")

    print()
    print(f"line kinds:  {dict(kinds.most_common())}")
    print(f"SEM values:  {len(sems)} distinct, most common "
          f"{[k for k, _ in sems.most_common(8)]}")
    print(f"ROLE values: {len(roles)} distinct -> {sorted(roles)}")

    if a.tex:
        lines = [r"\begin{tabular}{lrrr}", r"\toprule",
                 r"operation & training rows & \% of rows & occurrences \\", r"\midrule"]
        for op, c in counts.most_common():
            esc = op.replace("_", r"\_")
            lines.append(f"\\texttt{{{esc}}} & {docs[op]:,d} & "
                         f"{100.0 * docs[op] / n_read:.2f} & {c:,d} \\\\")
        lines += [r"\bottomrule", r"\end{tabular}"]
        Path(a.tex).write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\nwrote {a.tex}  ({len(counts)} rows, denominator n = {n_read})")


if __name__ == "__main__":
    main()
