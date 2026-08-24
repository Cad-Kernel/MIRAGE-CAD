"""Paired equivalence / non-inferiority for A1E against B2P, which a sign test cannot give.

WHY THIS EXISTS. The paired sign test on 393 jointly exported parts returned p = 0.1577, and we
started writing that up as "textualising the representation is accuracy-free". That is a misread.
A non-significant test fails to reject Delta = 0; it does not establish |Delta| < epsilon. The
first is what we measured, the second is what "free" and "equivalent" actually claim. So this
computes the interval, and reports whether it clears a margin instead of asserting that it does.

THE MARGIN IS DERIVED, NOT PICKED. An epsilon chosen after seeing the data, or set to a round
+-5 %, would let us conclude whatever we liked. Instead each margin is the SMALLEST effect this
paper already reports as material on the same metric and the same rows: A1E's paired improvement
over the deployed arm. If the A1E-vs-B2P interval sits inside that, the honest statement is "any
difference is smaller than the smallest difference we elsewhere call meaningful" -- which is a
claim about this paper's own resolution and nothing grander.

THREE QUANTITIES, because they answer different questions and are routinely conflated:

  1. Paired median of per-pair CD differences, on parts BOTH arms exported. Pure per-part
     fidelity, blind to coverage. Median of differences, not difference of medians: the paired
     quantity, and robust to the tail that reaches 1,404 mm^2 against a median near 2.
  2. Paired mean F@1 % difference on the same parts. Scale-free where CD is not, so it can and
     does rank arms differently.
  3. Unconditional mean F@1 % difference over all 500 rows, failures scored zero. This BLENDS
     fidelity with coverage and is reported separately for that reason -- it is not evidence
     about representation form on its own.

Bootstrap is over sample_id pairs, so the pairing is preserved in every resample.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics as st
from pathlib import Path

CEILING = 0.244  # attainable F@1 % ceiling at 1,024 points; a perfect self-match scores this


# C3's geometry was never re-scored: E1's C3 programs are byte-identical to N1's prior arm, so
# 41 reuses that directory. The mapping lives here rather than in a naming convention, matching
# e1_geometry_analysis.py, so the reuse stays visible instead of becoming a silent special case.
DIRS = {"step_C3": "geom_n1_step_prior"}


def load(root: Path, arm: str, modality: str = "step") -> dict[str, dict | None]:
    """sample_id -> best exported candidate, or None where the arm produced nothing scoreable."""
    d = DIRS.get(f"{modality}_{arm}", f"geom_e1_{modality}_{arm}")
    p = root / d / "geometry_nbest_rows.jsonl"
    out: dict[str, dict | None] = {}
    with p.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            cands = [c for c in (r.get("candidate_results") or [])
                     if c.get("step_export_ok") and c.get("f_score_1pct") is not None]
            out[r["sample_id"]] = (max(cands, key=lambda c: c["f_score_1pct"])
                                   if cands else None)
    return out


def boot_ci(vals: list[float], stat, n: int, seed: int) -> tuple[float, float]:
    """Percentile bootstrap. Resamples pairs, so pairing survives."""
    rng = random.Random(seed)
    k = len(vals)
    if k == 0:
        return (float("nan"), float("nan"))
    reps = []
    for _ in range(n):
        reps.append(stat([vals[rng.randrange(k)] for _ in range(k)]))
    reps.sort()
    lo = reps[int(0.025 * (n - 1))]
    hi = reps[int(0.975 * (n - 1))]
    return (lo, hi)


def paired(a: dict, b: dict, field: str) -> tuple[list[str], list[float]]:
    ids, d = [], []
    for s in sorted(set(a) & set(b)):
        ra, rb = a[s], b[s]
        if ra is None or rb is None:
            continue
        ids.append(s)
        d.append(rb[field] - ra[field])
    return ids, d


def report(label: str, diffs: list[float], stat, margin: float | None,
           unit: str, boots: int, seed: int, better_is: str) -> None:
    point = stat(diffs)
    lo, hi = boot_ci(diffs, stat, boots, seed)
    print(f"\n  {label}")
    print(f"    n = {len(diffs)} pairs")
    print(f"    point estimate  {point:+.4f} {unit}   (positive favours "
          f"{'B2P' if better_is == 'higher' else 'A1E'})")
    print(f"    95 % bootstrap  [{lo:+.4f}, {hi:+.4f}] {unit}")
    if margin is None:
        print("    no derived margin for this quantity; interval reported for its own sake")
        return
    print(f"    derived margin  +-{margin:.4f} {unit}  "
          f"(A1E's own paired gain over the deployed arm)")
    inside = lo > -margin and hi < margin
    crosses_zero = lo < 0 < hi
    if inside:
        print("    TOST: PASSES. Both bounds are inside the margin, so any difference is smaller")
        print("          than the smallest effect this paper calls material on this metric.")
    else:
        print("    TOST: DOES NOT PASS. The interval extends beyond the margin, so equivalence is")
        print("          NOT established -- only the absence of a detected difference.")
        which = "below -margin" if lo <= -margin else "above +margin"
        print(f"          ({which})")
    if crosses_zero:
        print("    The interval contains zero, so no direction is established either.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=r"C:\Workspace\Project\Paper\MIRAGE-V2\scratch")
    ap.add_argument("--modality", default="step")
    ap.add_argument("--boots", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=20260820)
    args = ap.parse_args()
    root = Path(args.root)

    a1e = load(root, "A1E", args.modality)
    b2p = load(root, "B2P", args.modality)
    c3 = load(root, "C3", args.modality)

    print("=" * 78)
    print("A1E vs B2P -- paired equivalence, budget and exposure both matched at 3,125 updates")
    print("=" * 78)

    # ---- derive the margins from A1E's own material gain over the deployed arm -----
    _, ref_cd = paired(c3, a1e, "cd")
    _, ref_f = paired(c3, a1e, "f_score_1pct")
    if not ref_cd:
        print("no C3 reference available; cannot derive a margin without picking one")
        return 1
    m_cd = abs(st.median(ref_cd))
    m_f = abs(st.fmean(ref_f))
    print(f"\nMargin derivation, on the {len(ref_cd)} parts C3 and A1E both exported:")
    print(f"  A1E's paired median CD gain over deployed     {st.median(ref_cd):+.4f} mm^2")
    print(f"  A1E's paired mean F@1 % gain over deployed    {st.fmean(ref_f):+.4f}")
    print("  Those magnitudes are the margins. They are the smallest effects this paper")
    print("  reports as material on these metrics, measured on the same rows.")

    # ---- 1 & 2: per-part fidelity, blind to coverage ------------------------------
    print("\n" + "-" * 78)
    print("PER-PART FIDELITY, on parts both arms exported. Coverage plays no role here.")
    print("-" * 78)
    ids, d_cd = paired(a1e, b2p, "cd")
    report("median of per-pair Chamfer differences (B2P - A1E)", d_cd, st.median,
           m_cd, "mm^2", args.boots, args.seed, better_is="lower")
    _, d_f = paired(a1e, b2p, "f_score_1pct")
    report("mean of per-pair F@1 % differences (B2P - A1E)", d_f, st.fmean,
           m_f, "", args.boots, args.seed + 1, better_is="higher")

    # ---- 3: unconditional, which blends coverage in --------------------------------
    print("\n" + "-" * 78)
    print("UNCONDITIONAL F@1 %, all 500 rows, failure scored zero. This BLENDS coverage with")
    print("fidelity and is not evidence about representation form on its own.")
    print("-" * 78)
    allids = sorted(set(a1e) & set(b2p))
    du = [( (b2p[s]["f_score_1pct"] if b2p[s] else 0.0)
            - (a1e[s]["f_score_1pct"] if a1e[s] else 0.0) ) for s in allids]
    report("mean unconditional F@1 % difference (B2P - A1E)", du, st.fmean,
           None, "", args.boots, args.seed + 2, better_is="higher")
    pt = st.fmean(du)
    print(f"    as a share of the attainable ceiling: {100 * pt / CEILING:+.1f} pp of ceiling")

    print("\n" + "-" * 78)
    print("How to state the result")
    print("-" * 78)
    print("  A non-significant paired test licenses 'no detected difference', not 'equivalent'.")
    print("  Only a TOST that PASSES licenses the second, and only against a stated margin.")
    print("  Single seed: none of this separates a small real effect from run-to-run variation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
