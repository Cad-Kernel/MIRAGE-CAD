"""Stage 3 vs Stage 3b, geometric fidelity -- the measurement tab:stage3b_ablation lacks.

Stage 3b is the paper's adopted configuration. Its failure diagnosis is stated in IR
Cosine and its remedy in Build, and docs SS9.14 showed neither tracks the fidelity of the
resulting part: one is agreement with the reference plan, the other a validity gate that
has now failed three times to register a real change in plan content. This asks the
question those two cannot.

ARM LABELLING IS VERIFIED, NOT ASSUMED. Swapping the two files would invert every
conclusion here, and `gen_test_X` versus `gen_test_X_stage3b` is a naming convention, not
evidence. The geometry scorer re-runs all five gates, so each arm's build rate is
recomputed from its own output and checked against the published values of
tab:stage3b_ablation. A mismatch aborts rather than reports.

Medians and a paired sign test carry the argument; Chamfer is heavy-tailed on this corpus
(N1g found a solid 9,943x oversized), so a mean can move by orders of magnitude on one
part. Only parts scored in BOTH arms enter the comparison.

    python src/scratch/stage3b_geometry_analysis.py
"""
from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _roots import SCRATCH  # noqa: E402

# tab:stage3b_ablation, Build %. The geometry pass must reproduce these.
#
# Transcribed from paper/main.tex, not from memory -- the first version of this table had
# text/stage3 at 48.7 and image/stage3 at 18.6, both invented. The published values are
# 28.5 and 38.8. Wrong baselines here would have failed a correct run at those two
# modalities, so verify against the source before editing:
#   grep -A8 'label{tab:stage3b_ablation}' paper/main.tex
PUBLISHED = {
    ("step", "stage3"): 74.3, ("step", "stage3b"): 70.0,
    ("point", "stage3"): 29.9, ("point", "stage3b"): 55.4,
    ("text", "stage3"): 28.5, ("text", "stage3b"): 57.2,
    ("image", "stage3"): 38.8, ("image", "stage3b"): 57.8,
}
TOL = 2.0    # pp; the geometry pass re-executes, and execution is not bit-deterministic


def sign_test(better: int, worse: int) -> float:
    n = better + worse
    if n == 0:
        return 1.0
    k = min(better, worse)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n))


def load(m: str, arm: str) -> dict[str, dict]:
    f = SCRATCH / f"geom_stage3b_{m}_{arm}" / "geometry_nbest_rows.jsonl"
    if not f.is_file():
        return {}
    out = {}
    for line in f.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        c = (r.get("candidate_results") or [None])[0]
        if c:
            out[r["sample_id"]] = c
    return out


def main() -> int:
    mods = [m for m in ("step", "point", "text", "image")
            if load(m, "stage3") and load(m, "stage3b")]
    if not mods:
        print("No scored arms found. Expected")
        print(f"  {SCRATCH}\\geom_stage3b_<modality>_<stage3|stage3b>\\geometry_nbest_rows.jsonl")
        print("Run 32_stage3b_geometry.sh and its PowerShell step first.")
        return 1

    print("=== arm verification: build rate recomputed vs tab:stage3b_ablation ===")
    ok = True
    for m in mods:
        for arm in ("stage3", "stage3b"):
            d = load(m, arm)
            got = 100 * sum(1 for r in d.values() if r.get("build_ok")) / len(d)
            want = PUBLISHED.get((m, arm))
            if want is None:
                print(f"  {m:<6}{arm:<9}{got:5.1f}%   (no published value)")
                continue
            bad = abs(got - want) > TOL
            ok &= not bad
            print(f"  {m:<6}{arm:<9}{got:5.1f}%   published {want:5.1f}%   "
                  f"{'OK' if not bad else '** MISMATCH **'}")
    if not ok:
        print("\nA recomputed build rate disagrees with the published table by more than")
        print(f"{TOL} pp. Either the arms are swapped or these are not the files the paper")
        print("reports. Refusing to report a fidelity comparison built on that.")
        return 1

    for m in mods:
        a, b = load(m, "stage3"), load(m, "stage3b")
        ids = sorted(set(a) & set(b))
        both = [i for i in ids
                if a[i].get("cd") is not None and b[i].get("cd") is not None]
        ua = sum(1 for i in ids if a[i].get("cd") is not None and b[i].get("cd") is None)
        ub = sum(1 for i in ids if b[i].get("cd") is not None and a[i].get("cd") is None)
        print(f"\n=== {m}: paired on the {len(both)} parts BOTH scored (of {len(ids)}) ===")
        print(f"  only Stage 3 scored {ua}, only Stage 3b scored {ub}"
              + ("   -- asymmetric, read the comparison with that in mind"
                 if max(ua, ub) > 2 * max(min(ua, ub), 1) else "   -- roughly symmetric"))
        if not both:
            print("  nothing to compare")
            continue
        for key, label, lower_better in [("cd", "Chamfer (mm^2)", True),
                                         ("f_score_1pct", "F@1%", False)]:
            va = [a[i][key] for i in both]
            vb = [b[i][key] for i in both]
            d = [y - x for x, y in zip(va, vb)]          # 3b - 3
            better = sum(1 for x in d if (x < 0) == lower_better and x != 0)
            worse = sum(1 for x in d if (x > 0) == lower_better and x != 0)
            p = sign_test(better, worse)
            print(f"  {label}")
            print(f"    median   Stage 3 {statistics.median(va):.4g}   "
                  f"Stage 3b {statistics.median(vb):.4g}")
            print(f"    paired   3b better on {better}, 3 better on {worse}, "
                  f"tied {len(both)-better-worse}   sign p={p:.3g}  "
                  f"{'DIFFERENT' if p < 0.05 else 'not separable'}")

    print("\n=== reading it ===")
    print("  Stage 3b better    the adopted configuration wins end to end, and")
    print("                     tab:stage3b_ablation's STEP '-4.4 pp cost' is a cost in")
    print("                     executability only.")
    print("  not separable      Stage 3b buys executability without fidelity -- still a")
    print("                     real result, since far more queries reach a solid at all,")
    print("                     but the paper must say exactly that and no more.")
    print("  Stage 3b worse     the adopted configuration trades part accuracy for build")
    print("                     success, which bears on which checkpoint to recommend.")
    print("\n  Note the selection effect: parts only one arm could score are excluded, and")
    print("  at point/image the arms differ hugely in build rate, so the shared set is")
    print("  biased toward parts Stage 3 could already handle.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
