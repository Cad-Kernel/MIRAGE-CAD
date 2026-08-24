"""What does Prog-Op-F1 actually count, and do the paper's conclusions survive counting
operations instead?

Review item B8 blamed the metric's regex for ending in `\\w*`, so that `extrude_add` and
`extrude` share no multiset element. That is real but secondary. Classifying every match
in the reference programs shows the primary problem:

    parameter names inside string literals   61.6%   params.add('hole_radius', 1.55, ...)
    other identifiers                        20.6%   holes = part.hole_pattern(...)
    ACTUAL FUNCTION CALLS                    16.7%   solid = part.extrude(name=..., ...)
    variable assignment                       1.1%

So roughly six parts in ten of "Prog-Op-F1" measure agreement on how parameters are
NAMED, not on which operations are performed. The most frequent single token in the
reference programs is `hole_radius` at 2,324 occurrences -- a parameter.

This recomputes the metric three ways over the same files and reports whether the
paper's conclusions change:

    as_published   the current regex, everything it matches
    calls_only     identifiers immediately followed by "(" -- actual invocations
    calls_folded   calls_only with the leading operation family folded together, which
                   is the fix B8 asked for (extrude_add and extrude both -> extrude),
                   at the cost of erasing the add/cut distinction

The third is reported precisely so the cost of B8's proposed fix is visible rather than
assumed: folding raises agreement by discarding a semantic contrast that matters.

    python src/scratch/prog_op_f1_recount.py [--limit N]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter

WSL = "//wsl.localhost/Ubuntu/home/jizong/workspace/MIRAGE/src/outputs"
CODE = f"{WSL}/qwen25_coder_1_5b_program_25k_stage4b"
NNIR = f"{WSL}/nnir_baseline_25k_full"
MODS = ("text", "image", "point", "step")

# exactly the pattern evaluate_programs.py uses
PUBLISHED = re.compile(
    r"\b(?:add_|create_|make_|cut|union|intersect|extrude|revolve|fillet|chamfer|hole|"
    r"pattern|mirror|shell|loft)\w*", re.I)
# same vocabulary, but only where the identifier is actually invoked
CALL = re.compile(
    r"\b((?:add_|create_|make_|cut|union|intersect|extrude|revolve|fillet|chamfer|hole|"
    r"pattern|mirror|shell|loft)\w*)\s*\(", re.I)
FAMILIES = ("extrude", "revolve", "fillet", "chamfer", "hole", "pattern", "mirror",
            "shell", "loft", "cut", "union", "intersect")


def ops_published(t: str) -> list[str]:
    return [m.group(0).lower() for m in PUBLISHED.finditer(t)]


def ops_calls(t: str) -> list[str]:
    return [m.group(1).lower() for m in CALL.finditer(t)]


def fold(op: str) -> str:
    for f in FAMILIES:
        if f in op:
            return f
    return op


def ops_folded(t: str) -> list[str]:
    return [fold(o) for o in ops_calls(t)]


def prf(pred: list[str], ref: list[str]) -> float:
    pc, rc = Counter(pred), Counter(ref)
    inter = sum((pc & rc).values())
    if not pred or not ref:
        return 0.0
    p, r = inter / sum(pc.values()), inter / sum(rc.values())
    return 0.0 if p + r == 0 else 2 * p * r / (p + r)


def load(path: str, limit: int | None) -> list[dict]:
    # Read as bytes and decode explicitly: these files carry UTF-8 that the shell's
    # default codepage cannot decode, and text=True silently hands back None on failure.
    cmd = ["head", "-n", str(limit), path] if limit else ["cat", path]
    out = subprocess.run(cmd, capture_output=True)
    if out.returncode != 0 or not out.stdout:
        return []
    text = out.stdout.decode("utf-8", errors="replace")
    return [json.loads(l) for l in text.splitlines() if l.strip()]


def score(rows: list[dict]) -> dict[str, float]:
    res = {}
    for name, fn in (("as_published", ops_published), ("calls_only", ops_calls),
                     ("calls_folded", ops_folded)):
        vals = [prf(fn(r.get("prediction", "")), fn(r.get("reference", ""))) for r in rows]
        res[name] = 100 * sum(vals) / len(vals) if vals else float("nan")
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="rows per file; default all")
    args = ap.parse_args()

    variants = [("C: generated", lambda m: f"{CODE}/gen_test_{m}_stage3b_repaired_p0.jsonl"),
                ("A: direct-NN", lambda m: f"{NNIR}/direct_{m}_repaired_p0.jsonl"),
                ("B: prior-NN", lambda m: f"{NNIR}/prior_{m}_repaired_p0.jsonl")]

    print(f"  {'variant':<14}{'modality':<9}{'as published':>14}{'calls only':>13}"
          f"{'calls folded':>15}{'n':>7}")
    table: dict[tuple[str, str], dict] = {}
    for label, pathfn in variants:
        for m in MODS:
            rows = load(pathfn(m), args.limit)
            if not rows:
                print(f"  {label:<14}{m:<9}(missing)")
                continue
            s = score(rows)
            table[(label, m)] = s
            print(f"  {label:<14}{m:<9}{s['as_published']:>13.1f}%{s['calls_only']:>12.1f}%"
                  f"{s['calls_folded']:>14.1f}%{len(rows):>7}")

    print("\n=== does the paper's one positive claim about the prior survive? ===")
    print("  Section 7: 'B exceeds A on Prog-Op-F1 in every modality'\n")
    print(f"  {'modality':<9}{'metric':<14}{'A':>8}{'B':>8}{'B-A':>8}")
    for m in MODS:
        a, b = table.get(("A: direct-NN", m)), table.get(("B: prior-NN", m))
        if not (a and b):
            continue
        for k in ("as_published", "calls_only", "calls_folded"):
            d = b[k] - a[k]
            print(f"  {m:<9}{k:<14}{a[k]:>7.1f}%{b[k]:>7.1f}%{d:>+7.1f}"
                  + ("" if d > 0 else "   <-- reverses"))

    print("\n=== and the A/B vs C ordering? ===")
    for m in MODS:
        c = table.get(("C: generated", m))
        b = table.get(("B: prior-NN", m))
        if not (c and b):
            continue
        row = "  " + f"{m:<9}"
        for k in ("as_published", "calls_only", "calls_folded"):
            row += f"{k.split('_')[0][:4]}: B{b[k]:.0f} vs C{c[k]:.0f}   "
        print(row)
    print("\n  Folding is B8's proposed fix. It raises agreement by collapsing")
    print("  extrude_add and extrude_cut into one token, which erases a distinction the")
    print("  kernel very much observes -- report the cost, not just the gain.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
