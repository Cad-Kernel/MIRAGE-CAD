"""B1-K geometry: does K=8's plan-level gain reach the shape?

B1-K raised plan quality (Op-Set F1 +3.78pp [+2.02, +5.58] on STEP) and Build did not
move (McNemar p=0.203) -- the third time Build has failed to register a real change in
plan content. SS9.13 showed geometry is what discriminates, so this asks the question
Build cannot answer.

K=4's geometry comes from N1g (scratch/geom_n1_step_prior), K=8's from 31_b1k_geometry.sh.
Both decode the same 500 rows, so the contrast is paired; only parts scored in BOTH arms
enter it, since a part that fails to export has no geometry and dropping it from one side
only would bias the other.

Medians and a sign test carry the argument. Chamfer is heavy-tailed on this corpus -- N1g
found a single part whose solid was 9,943x too large, enough to move a mean by eight
orders of magnitude -- so the mean is reported only as a companion.

    python src/scratch/b1k_geometry_analysis.py
"""
from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _roots import SCRATCH  # noqa: E402

ARMS = {"K=4": "geom_n1_step_prior", "K=8": "geom_b1k_step_K8"}


def sign_test(better: int, worse: int) -> float:
    n = better + worse
    if n == 0:
        return 1.0
    k = min(better, worse)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n))


def load(d: str) -> dict[str, dict]:
    f = SCRATCH / d / "geometry_nbest_rows.jsonl"
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
    data = {k: load(v) for k, v in ARMS.items()}
    missing = [k for k, v in data.items() if not v]
    if missing:
        print("Missing arms: " + ", ".join(missing))
        for k in missing:
            print(f"  expected {SCRATCH / ARMS[k] / 'geometry_nbest_rows.jsonl'}")
        print("Run 31_b1k_geometry.sh (K=8) / 29_n1g_geometry_fidelity.sh (K=4) first.")
        return 1

    print("=== coverage ===")
    for k, d in data.items():
        exp = sum(1 for r in d.values() if r.get("step_export_ok"))
        sc = sum(1 for r in d.values() if r.get("cd") is not None)
        print(f"  {k:<5} rows {len(d):<5} exported {exp:<5} scored {sc}")
        if exp and not sc:
            print(f"  ** exported but unscored -- schema mismatch, keys: "
                  f"{sorted(next(iter(d.values())))}")

    a, b = data["K=4"], data["K=8"]
    ids = sorted(set(a) & set(b))
    both = [i for i in ids if a[i].get("cd") is not None and b[i].get("cd") is not None]
    print(f"\n=== K=8 vs K=4, paired on the {len(both)} parts BOTH scored (of {len(ids)}) ===")
    if not both:
        print("  no overlap -- nothing to compare")
        return 1

    for key, label, lower_better in [("cd", "Chamfer (mm^2)", True),
                                     ("f_score_1pct", "F@1%", False)]:
        va = [a[i][key] for i in both]
        vb = [b[i][key] for i in both]
        d = [y - x for x, y in zip(va, vb)]          # K8 - K4
        better = sum(1 for x in d if (x < 0) == lower_better and x != 0)
        worse = sum(1 for x in d if (x > 0) == lower_better and x != 0)
        p = sign_test(better, worse)
        print(f"  {label}")
        print(f"    median   K=4 {statistics.median(va):.4g}   K=8 {statistics.median(vb):.4g}")
        print(f"    mean     K=4 {statistics.fmean(va):.4g}   K=8 {statistics.fmean(vb):.4g}")
        print(f"    paired   K=8 better on {better}, K=4 better on {worse}, "
              f"tied {len(both)-better-worse}")
        print(f"    sign test p={p:.3g}  {'DIFFERENT' if p < 0.05 else 'not separable'}")

    print("\n  Medians and the sign test carry this; Chamfer's tail can move a mean by")
    print("  orders of magnitude (N1g found one solid 9,943x oversized).")
    print("\n=== what this settles ===")
    print("  K=8 better    the plan-level gain reaches the shape; B1-K is an end-to-end")
    print("                improvement and the paper can recommend a larger K.")
    print("  not separable K=8 matches the reference PLAN more closely without producing")
    print("                closer GEOMETRY. Report the IR gain, decline the end-to-end")
    print("                claim, and note what that implies for IR-Op-Set F1 as a metric.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
