"""E1b: does the observation block explain why Build survives a corrupted plan?

Section 6.2 reports that shuffling the construction prefix collapses plan quality by 53
points while Build does not move (71.4 % against 68.6 %, p = 0.37). The paper reads that as
a property of the METRIC -- execution gates validity, not fidelity. There has always been a
competing reading: the code decoder might be recovering from the corrupted plan by reading
the query-derived observation block instead, in which case Build's blindness would be partly
the bypass rather than purely the metric.

This crosses the two interventions:

                          observation present     observation suppressed
      plan correct        C3                      C2
      plan shuffled       S3                      S2

and asks whether the shuffle still fails to move Build once there is nothing to fall back
on. C3, C2 and S3 already existed; S2 is the cell E1b adds.

Everything is paired on sample_id -- all four cells decode the same 500 rows -- and McNemar
is exact, from the discordant pairs, no normal approximation.

Run:  python src/scratch/e1b_crossed_analysis.py
"""
from __future__ import annotations

import argparse
import json
from math import comb
from pathlib import Path

CELLS = {
    "C3": ("plan correct",  "observation present"),
    "C2": ("plan correct",  "observation suppressed"),
    "S3": ("plan shuffled", "observation present"),
    "S2": ("plan shuffled", "observation suppressed"),
}
# What section 6.2 already reports, so a re-score that disagrees is visible immediately
# rather than quietly changing the baseline the new cell is compared against.
KNOWN = {"C3": 357, "S3": 343}


def two_sided_binom(k: int, n: int) -> float:
    """Exact two-sided binomial tail at p = 1/2. Used for McNemar and for the sign test."""
    if n == 0:
        return 1.0
    k = min(k, n - k)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    z = 1.959963984540054
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (100 * max(0.0, c - h), 100 * min(1.0, c + h))


def load(root: Path, cell: str) -> dict[str, dict]:
    p = root / f"exec_e1_step_{cell}" / "execution_rows.jsonl"
    if not p.exists():
        return {}
    with p.open(encoding="utf-8") as f:
        return {json.loads(l)["sample_id"]: json.loads(l) for l in f if l.strip()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path,
                    default=Path(r"C:\Workspace\Project\Paper\MIRAGE-V2\scratch"))
    ap.add_argument("--gate", default="build_ok")
    args = ap.parse_args()

    arms = {c: load(args.root, c) for c in CELLS}
    missing = [c for c, v in arms.items() if not v]
    if missing:
        print(f"not scored yet: {', '.join(missing)}")
        print("run:  run_e1_execution.ps1 -Modalities step -Conditions " + ",".join(missing))
        return 2

    ids = sorted(set.intersection(*(set(v) for v in arms.values())))
    n = len(ids)
    got = {c: sum(1 for i in ids if arms[c][i].get(args.gate)) for c in CELLS}

    print(f"\n{'=' * 74}\nE1b crossed design   gate = {args.gate}   n = {n} paired rows\n{'=' * 74}\n")
    print(f"{'':<18}{'observation present':>24}{'observation suppressed':>26}")
    for plan, a, b in (("plan correct", "C3", "C2"), ("plan shuffled", "S3", "S2")):
        def cell(c):
            lo, hi = wilson(got[c], n)
            return f"{c} {100*got[c]/n:5.1f} % [{lo:4.1f},{hi:4.1f}]"
        print(f"{plan:<18}{cell(a):>24}{cell(b):>26}")

    # Re-score check against the numbers section 6.2 already reports.
    print()
    for c, want in KNOWN.items():
        mark = "ok  " if got[c] == want else "DIFFERS"
        print(f"  {mark} {c} scored {got[c]}/{n}; section 6.2 reports {want}/500")
    if any(got[c] != w for c, w in KNOWN.items()):
        print("  A cell that already had a published number came back different. Resolve that")
        print("  before reading the new one -- the baseline is what S2 is compared against.")

    # The two simple effects of shuffling the prefix.
    print(f"\n{'-' * 74}\nEffect of shuffling the prefix, in each observation condition\n{'-' * 74}")
    effects = {}
    for label, hi, lo in (("with the observation", "C3", "S3"),
                          ("with it suppressed", "C2", "S2")):
        b01 = sum(1 for i in ids if arms[hi][i].get(args.gate) and not arms[lo][i].get(args.gate))
        b10 = sum(1 for i in ids if not arms[hi][i].get(args.gate) and arms[lo][i].get(args.gate))
        p = two_sided_binom(b01, b01 + b10)
        effects[lo] = p
        d = 100 * (got[hi] - got[lo]) / n
        print(f"  {label:<22} {hi} vs {lo}   {d:+6.1f} pp   {b01:>4} : {b10:<4}  "
              f"p = {p:.4g}   {'separable' if p < 0.05 else 'NOT separable'}")

    # Interaction: does the shuffle hurt more when there is nothing to fall back on?
    # Per row, d = (correct - shuffled) in each condition; sign test on the difference.
    diffs = []
    for i in ids:
        dp = int(bool(arms["C3"][i].get(args.gate))) - int(bool(arms["S3"][i].get(args.gate)))
        ds = int(bool(arms["C2"][i].get(args.gate))) - int(bool(arms["S2"][i].get(args.gate)))
        if dp != ds:
            diffs.append(dp - ds)
    pos = sum(1 for d in diffs if d > 0)
    p_int = two_sided_binom(pos, len(diffs))
    print(f"\n  interaction, sign test on the per-row difference of differences:")
    print(f"    {len(diffs)} rows where the two conditions disagree, {pos} favouring "
          f"a larger shuffle effect with the observation present, p = {p_int:.4g}")
    print("    (a paired sign test, not a fitted model; it asks only whether the shuffle")
    print("     effect is bigger in one observation condition than the other)")

    # What the paper may say.
    print(f"\n{'-' * 74}\nWhat this licenses\n{'-' * 74}")
    if effects["S2"] >= 0.05:
        print("  Build does not move under a shuffled prefix even with the observation block")
        print("  removed. The competing reading of section 6.2 is closed: Build's blindness is")
        print("  a property of the metric, not of the bypass. Section 6.2 may drop its caveat")
        print("  and cite this cell.")
    else:
        print("  Build DOES move under a shuffled prefix once the observation is removed. The")
        print("  observation was compensating, and section 6.2 must be restated: its p = 0.37")
        print("  measured a metric blind spot AND a bypass, not the metric alone. This is the")
        print("  more consequential outcome and should be reported as prominently as the")
        print("  original result.")
    print("\n  Either way: no repair was applied and decoding was batched, so these four cells")
    print("  are comparable to each other and not to the main tables.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
