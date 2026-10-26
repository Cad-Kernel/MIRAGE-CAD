"""Was the 2026-08-04 downgrade an artifact of the Build gate?

tab:compositional carries Build and STEP export and nothing else, and on Build retrieval sits
at 100.00% for STEP against 46.73% for a generated plan. From that the paper concluded that
retrieval stays near saturation on a genuine family holdout while the generative variant
falls, and downgraded its central claim. Geometry was never run on this split.

The external evaluation then ran the same pair of arms on 400 externally authored parts and
found Build pointing the wrong way for the STEP modality: it gave retrieval a 30-point lead,
while geometry gave the generated plan the win 160 times to 55, p = 4.4e-13. On the point
modality Build gave retrieval 40 points and geometry gave a tie -- so Build misled in both,
just differently. The mechanism was scale: only the STEP descriptor carries absolute size, and
only the arm that reads it lands on the target's envelope (bbox ratio 0.993 against 0.575,
0.478 and 0.339 for the other three).

This script asks the same question of the compositional split, where the mechanism should be
stronger still: the held-out families are by construction absent from the index, so retrieval
must return a plan from a different family. That plan is a real corpus program and builds.

CEILINGS ARE THE INTERNAL ONES. These are FllumaOne parts, so F@1% = 0.244 and the Chamfer
floor of 1.963 mm^2 (docs 9.15, measured at 1,024 points) transfer directly. The external
0.281 does NOT apply here, and the two numbers are close enough that mixing them would not
announce itself.

    python src/scratch/compositional_geometry_analysis.py
"""
from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
CEILING_F1 = 0.244          # internal, 1024 points, docs 9.15
FLOOR_CD = 1.963            # internal, mm^2

# Build rates from tab:compositional, to be reproduced from the geometry pass before anything
# else is reported -- a swapped arm would otherwise be invisible.
PUBLISHED_BUILD = {("step", "ours"): 0.4673, ("step", "nnir"): 1.0000,
                   ("point", "ours"): 0.4495, ("point", "nnir"): 0.9832}


def load(mod: str, arm: str) -> dict[str, dict | None]:
    f = REPO / "scratch" / f"geom_comp_{mod}_{arm}" / "geometry_nbest_rows.jsonl"
    if not f.is_file():
        return {}
    out: dict[str, dict | None] = {}
    for line in f.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        cands = r.get("candidate_results", [])
        scored = [c for c in cands if c.get("cd") is not None]
        built = [c for c in cands if c.get("build_ok")]
        out[r["sample_id"]] = scored[0] if scored else ({"__built_only__": True} if built else None)
    return out


def sign_test(better: int, worse: int) -> float:
    n = better + worse
    if n == 0:
        return 1.0
    k = min(better, worse)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def main() -> int:
    arms = {(m, a): load(m, a) for m in ("step", "point") for a in ("ours", "nnir")}
    have = [k for k, v in arms.items() if v]
    if not have:
        print("no compositional geometry rows found")
        return 1

    print("=== arm identity check: build rate recomputed from the geometry pass ===")
    for (m, a) in have:
        rows = arms[(m, a)]
        n = len(rows)
        built = sum(1 for c in rows.values() if c is not None)
        pub = PUBLISHED_BUILD.get((m, a))
        flag = ""
        if pub is not None:
            flag = "  OK" if abs(built / n - pub) < 0.03 else f"  ** off by {100*(built/n - pub):+.1f}pp -- ARM MAY BE SWAPPED **"
        print(f"  {m:<6}{a:<6} {built}/{n} = {100*built/n:5.2f}%   published {100*pub:5.2f}%{flag}"
              if pub is not None else
              f"  {m:<6}{a:<6} {built}/{n} = {100*built/n:5.2f}%")

    print("\n=== per arm, every part that produced a scoreable solid ===")
    print(f"  {'arm':<14}{'n':>6}{'cd mm^2':>12}{'F@1%':>9}{'% of ceiling':>14}"
          f"{'bbox ratio':>12}{'bbox err':>10}")
    for (m, a) in have:
        sel = [c for c in arms[(m, a)].values() if c and c.get("cd") is not None]
        if not sel:
            continue
        med = statistics.median
        br = [c["bbox_ratio_to_gt"] for c in sel if c.get("bbox_ratio_to_gt")]
        be = [c["bbox_err"] for c in sel if c.get("bbox_err") is not None]
        f1 = med(c["f_score_1pct"] for c in sel)
        print(f"  {m + '/' + a:<14}{len(sel):>6}{med(c['cd'] for c in sel):>12.4g}"
              f"{f1:>9.3f}{100*f1/CEILING_F1:>13.1f}%"
              f"{med(br):>12.3f}{med(be):>10.3g}")

    print(f"\n  internal ceiling F@1% = {CEILING_F1}, Chamfer floor = {FLOOR_CD} mm^2")

    print("\n=== paired: generated plan vs prior-NN-IR, parts BOTH could build ===")
    for m in ("step", "point"):
        A, B = arms.get((m, "ours"), {}), arms.get((m, "nnir"), {})
        if not A or not B:
            continue
        shared = [s for s in A
                  if A[s] and B.get(s) and A[s].get("cd") is not None and B[s].get("cd") is not None]
        if not shared:
            print(f"  {m}: no shared scoreable parts")
            continue
        med = statistics.median
        fa = med(A[s]["f_score_1pct"] for s in shared)
        fb = med(B[s]["f_score_1pct"] for s in shared)
        ca = med(A[s]["cd"] for s in shared)
        cb = med(B[s]["cd"] for s in shared)
        w = sum(1 for s in shared if A[s]["f_score_1pct"] > B[s]["f_score_1pct"])
        l = sum(1 for s in shared if B[s]["f_score_1pct"] > A[s]["f_score_1pct"])
        n_a = sum(1 for c in A.values() if c and c.get("cd") is not None)
        n_b = sum(1 for c in B.values() if c and c.get("cd") is not None)
        print(f"  {m:<6} n={len(shared):<5} F@1% ours {fa:.3f} ({100*fa/CEILING_F1:.1f}% of ceiling) "
              f"vs nnir {fb:.3f} ({100*fb/CEILING_F1:.1f}%)   "
              f"cd {ca:.4g} vs {cb:.4g}   ours wins {w}, nnir wins {l}, "
              f"sign p={sign_test(w, l):.3g}")
        print(f"         (scoreable: ours {n_a}, nnir {n_b} of {len(A)} -- the paired subset is "
              f"conditioned on the weaker arm succeeding, which favours it)")

    print("\n=== the reading, against what was fixed before the run ===")
    print("  Build gave retrieval 100.00% against 46.73% on STEP and 98.32% against 44.95% on")
    print("  point, and that is what the 2026-08-04 downgrade was based on. Compare the paired")
    print("  geometry above. If the generated plan wins, tab:compositional needs geometry")
    print("  columns and its conclusion needs rewriting, along with tab:positioning and the")
    print("  claims audit. If retrieval wins, the downgrade stands on better evidence than it")
    print("  had, and the external STEP result becomes the anomaly to explain.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
