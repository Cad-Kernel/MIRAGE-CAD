"""Did any arm build the right part? The question Build could not answer.

Written after the outputs existed. The scorer writes `cd`, not `chamfer_distance`, and
`f_score_1pct`; guessing those names once already produced a confident "scored 0, no overlap"
in this project, so they are read from a real row rather than assumed.

WHAT BUILD LEFT UNSETTLED. Retrieval builds 99.2% of 400 externally authored parts against
69.0% for a generated plan, and the advantage is nested -- one part in 400 goes the other way.
Meanwhile retrieval CONCENTRATES on external input, 49.2% distinct neighbours against 98%
internally. The index has less to offer and the gate reads better for it, because any corpus
program builds. Only fidelity can separate "built something valid" from "built the right
thing".

HOW TO READ F@1%. The ceiling on this set, measured at the scorer's own 1,024 points, is
0.281 within the corpus scale band and 0.304 over all 400 (docs 9.19). A score is reported
both raw and as a fraction of that ceiling, because 0.20 means something quite different
against a ceiling of 0.244 than against 1.0.

HOW NOT TO READ CHAMFER. Raw mm^2 does not transfer: it grows with the square of part size,
and this set spans 1.6 mm to 4 km. Every table carries cd / target_bbox_diag^2.

THE PAIRING IS CONDITIONAL AND THAT MATTERS. A part only appears in the paired comparison if
BOTH arms produced a scoreable solid. Since retrieval builds nearly everything and the
generated plan builds 69%, the paired subset is close to the generated arm's successes -- a
subset selected for the weaker arm succeeding, which biases toward it. Stated, not corrected.

    python src/scratch/external_geometry_analysis.py
"""
from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
QUERIES = REPO / "scratch" / "ext_queries.jsonl"
CORPUS_MAX_DIAG = 134.30
CEILING = {"all": 0.304, "within": 0.281, "beyond": 0.343}      # docs 9.19, at 1024 points
ARMS = ["step_genplan", "step_nnir", "point_genplan", "point_nnir"]


def load(arm: str) -> dict[str, dict]:
    f = REPO / "scratch" / f"geom_ext_{arm}" / "geometry_nbest_rows.jsonl"
    if not f.is_file():
        return {}
    out = {}
    for line in f.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        cands = [c for c in r.get("candidate_results", []) if c.get("cd") is not None]
        out[r["sample_id"]] = cands[0] if cands else None
    return out


def sign_test(better: int, worse: int) -> float:
    n = better + worse
    if n == 0:
        return 1.0
    k = min(better, worse)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def describe(vals_cd, vals_cdn, vals_f, label, ceiling):
    if not vals_f:
        print(f"  {label:<44} nothing scoreable")
        return
    med = statistics.median
    print(f"  {label:<44} n={len(vals_f):<4} "
          f"cd {med(vals_cd):9.3g}   cd/diag^2 {med(vals_cdn):8.3g}   "
          f"F@1% {med(vals_f):.3f} = {100*med(vals_f)/ceiling:5.1f}% of ceiling")


def main() -> int:
    arms = {a: load(a) for a in ARMS}
    have = [a for a, d in arms.items() if d]
    if not have:
        print("no geometry rows found")
        return 1
    missing = [a for a in ARMS if a not in have]
    if missing:
        print(f"NOTE: still missing {', '.join(missing)} -- reporting what exists\n")

    diag = {}
    if QUERIES.is_file():
        for line in QUERIES.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                diag[r["sample_id"]] = r["bbox_diag"]

    strata = {"all": lambda s: True,
              "within": lambda s: diag.get(s, 1e9) <= CORPUS_MAX_DIAG,
              "beyond": lambda s: diag.get(s, 1e9) > CORPUS_MAX_DIAG}

    print("=== per arm, unconditional (every part that produced a scoreable solid) ===")
    for a in have:
        print(f"\n{a}")
        for st, keep in strata.items():
            sel = [c for s, c in arms[a].items() if c and keep(s)]
            describe([c["cd"] for c in sel],
                     [c["cd"] / c["target_bbox_diag"] ** 2 for c in sel if c.get("target_bbox_diag")],
                     [c["f_score_1pct"] for c in sel], st, CEILING[st])

    print("\n=== paired: generated plan vs prior-NN-IR, on parts BOTH could build ===")
    for mod in ("step", "point"):
        A, B = arms.get(f"{mod}_genplan", {}), arms.get(f"{mod}_nnir", {})
        if not A or not B:
            continue
        for st, keep in strata.items():
            shared = [s for s in A if A[s] and B.get(s) and keep(s)]
            if not shared:
                continue
            fa = [A[s]["f_score_1pct"] for s in shared]
            fb = [B[s]["f_score_1pct"] for s in shared]
            ca = [A[s]["cd"] / A[s]["target_bbox_diag"] ** 2 for s in shared]
            cb = [B[s]["cd"] / B[s]["target_bbox_diag"] ** 2 for s in shared]
            a_better = sum(1 for s in shared if A[s]["f_score_1pct"] > B[s]["f_score_1pct"])
            b_better = sum(1 for s in shared if B[s]["f_score_1pct"] > A[s]["f_score_1pct"])
            med = statistics.median
            print(f"  {mod:<6}{st:<8} n={len(shared):<4} "
                  f"F@1% genplan {med(fa):.3f} vs nnir {med(fb):.3f}   "
                  f"cd/diag^2 {med(ca):.3g} vs {med(cb):.3g}   "
                  f"genplan wins {a_better}, nnir wins {b_better}, "
                  f"sign p={sign_test(a_better, b_better):.3g}")
        n_a = sum(1 for c in A.values() if c)
        n_b = sum(1 for c in B.values() if c)
        print(f"         (scoreable: genplan {n_a}, nnir {n_b} of 400 -- the paired subset is "
              f"selected for the weaker arm succeeding)")

    print("\n=== sensitivity to the oversized tail ===")
    print("  Fusion 360 Gallery is user-uploaded and 19 of these 400 parts exceed a metre, one")
    print("  of them four kilometres. Those are modelling errors by whoever uploaded them, and")
    print("  the obvious impulse is to delete them. The reason not to is that the frame is")
    print("  currently 'the published test split', which is one sentence in the paper, and")
    print("  filtering on a property correlated with difficulty is exactly what a reviewer")
    print("  should query. So: keep them, and show the conclusion does not depend on them.")
    for mod in ("step", "point"):
        A, B = arms.get(f"{mod}_genplan", {}), arms.get(f"{mod}_nnir", {})
        if not A or not B:
            continue
        print(f"\n  {mod}")
        print(f"    {'excluding':<24}{'n':>5}{'genplan':>10}{'nnir':>9}{'wins':>6}{'losses':>7}{'p':>11}")
        for lbl, thr in (("nothing", float("inf")), ("> 1000 mm", 1000.0), ("> 500 mm", 500.0),
                         ("> 300 mm", 300.0), (f"> {CORPUS_MAX_DIAG} mm", CORPUS_MAX_DIAG)):
            shared = [s for s in A if A[s] and B.get(s) and diag.get(s, float("inf")) <= thr]
            if not shared:
                continue
            fa = statistics.median(A[s]["f_score_1pct"] for s in shared)
            fb = statistics.median(B[s]["f_score_1pct"] for s in shared)
            w = sum(1 for s in shared if A[s]["f_score_1pct"] > B[s]["f_score_1pct"])
            l = sum(1 for s in shared if B[s]["f_score_1pct"] > A[s]["f_score_1pct"])
            print(f"    {lbl:<24}{len(shared):>5}{fa:>10.4f}{fb:>9.4f}{w:>6}{l:>7}"
                  f"{sign_test(w, l):>11.2g}")

    print("\n=== how far from the target, in plain terms ===")
    for a in have:
        sel = [c for c in arms[a].values() if c and c.get("target_bbox_diag")]
        if not sel:
            continue
        ratio = statistics.median(c["bbox_ratio_to_gt"] for c in sel
                                  if c.get("bbox_ratio_to_gt"))
        berr = statistics.median(c["bbox_err"] for c in sel if c.get("bbox_err") is not None)
        near = sum(1 for c in sel if c["f_score_1pct"] >= 0.5 * CEILING["all"])
        print(f"  {a:<16} median bbox ratio to target {ratio:.3f}   median bbox err "
              f"{berr:.3g} mm   parts reaching half the ceiling: {near}/{len(sel)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
