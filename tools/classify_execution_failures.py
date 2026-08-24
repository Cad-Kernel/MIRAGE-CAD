"""Reproduce the execution-failure taxonomy of the paper (Table 11) from raw rows.

Before this script existed the five-way classification was applied by hand, so the
table could not be regenerated from the repository. It can now.

The rule is a first-match-wins scan over the ``error`` string recorded by the
execution harness. Order matters: a SyntaxError message can also contain the word
"attribute", so syntax must be tested first.

    1. "SyntaxError" / "IndentationError"   -> syntax
    2. "has no attribute"                   -> attribute hallucination
    3. "unexpected keyword argument"        -> keyword mismatch
    4. "did not resolve"                    -> topology reference
    5. anything else                        -> other

Percentages are of that modality's *failures*, not of all rows, and therefore sum
to 100 across the five categories. ``Fail rate`` is of all rows.

Usage, from the repository root:

    python src/classify_execution_failures.py \
        --rows "scratch/exec_eval_25k_stage3b_{modality}/execution_rows.jsonl"

``{modality}`` is expanded over step/point/text/image. Pass ``--latex`` to emit the
table body instead of the plain-text summary.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

MODALITIES = ["step", "point", "text", "image"]

# (label, needle) in first-match-wins order. `syntax` is deliberately first.
RULES: list[tuple[str, tuple[str, ...]]] = [
    ("syntax", ("SyntaxError", "IndentationError")),
    ("attribute", ("has no attribute",)),
    ("keyword", ("unexpected keyword argument",)),
    ("topology", ("did not resolve",)),
]
CATEGORIES = ["keyword", "attribute", "syntax", "topology", "other"]

# Column order as printed in the paper.
DISPLAY = {
    "keyword": "Keyword mismatch",
    "attribute": "Attr. hallucination",
    "syntax": "Syntax",
    "topology": "Topology ref.",
    "other": "Other",
}
ROW_LABEL = {"step": "STEP / B-Rep", "point": "Point cloud",
             "text": "Text", "image": "Image"}


def classify(error: str) -> str:
    """Return the taxonomy label for one recorded error string."""
    for label, needles in RULES:
        if any(n in error for n in needles):
            return label
    return "other"


def is_failure(row: dict) -> bool:
    """A row failed if it did not reach a built solid.

    The harness records the gate flags directly; `exec_ok`/`build_ok` are the
    authoritative signal and `error` is only populated on failure.
    """
    if "build_ok" in row:
        return not bool(row["build_ok"])
    if "exec_ok" in row:
        return not bool(row["exec_ok"])
    return bool(str(row.get("error", "")).strip())


def read_rows(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def tabulate(pattern: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for m in MODALITIES:
        path = Path(pattern.replace("{modality}", m))
        if not path.is_file():
            print(f"  skip {m}: {path} not found")
            continue
        rows = read_rows(path)
        failures = [r for r in rows if is_failure(r)]
        counts = Counter(classify(str(r.get("error", ""))) for r in failures)
        n_fail = len(failures)
        out[m] = {
            "n_rows": len(rows),
            "n_fail": n_fail,
            "fail_rate": 100.0 * n_fail / max(len(rows), 1),
            "pct": {c: 100.0 * counts.get(c, 0) / max(n_fail, 1) for c in CATEGORIES},
            "raw": {c: counts.get(c, 0) for c in CATEGORIES},
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rows", default="scratch/exec_eval_25k_stage3b_{modality}/execution_rows.jsonl",
                    help="path template containing {modality}")
    ap.add_argument("--latex", action="store_true", help="emit LaTeX table body")
    args = ap.parse_args()

    table = tabulate(args.rows)
    if not table:
        print("no input found")
        return 1

    if args.latex:
        for m in MODALITIES:
            if m not in table:
                continue
            d = table[m]
            cells = " & ".join(f"{d['pct'][c]:.1f}" for c in CATEGORIES)
            print(f"{ROW_LABEL[m]:<13} & {d['fail_rate']:.1f} & {cells} \\\\")
        return 0

    hdr = f"{'Modality':<13} {'n':>6} {'fails':>6} {'Fail%':>7}  " + \
          "  ".join(f"{DISPLAY[c]:>19}" for c in CATEGORIES)
    print(hdr)
    print("-" * len(hdr))
    for m in MODALITIES:
        if m not in table:
            continue
        d = table[m]
        cells = "  ".join(f"{d['pct'][c]:>18.1f}%" for c in CATEGORIES)
        print(f"{ROW_LABEL[m]:<13} {d['n_rows']:>6} {d['n_fail']:>6} "
              f"{d['fail_rate']:>6.1f}%  {cells}")
    print()
    print("counts (not percentages):")
    for m in MODALITIES:
        if m in table:
            print(f"  {m:<6} {table[m]['raw']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
