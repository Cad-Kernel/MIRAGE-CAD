"""N1g: does the construction prefix control the resulting SHAPE, or only the plan text?

N1 showed the prefix determines which plan is decoded (another sample's latent costs
53 points of IR-Op-Set F1) and that Build cannot detect the substitution at all. Build
is a validity gate: it asks whether a program runs, not whether it describes the query.
This script supplies the missing half by comparing generated geometry against each
query's own reference cloud -- symmetric Chamfer Distance and F-score@1% of the target's
bounding-box diagonal.

The comparison is paired: all modes decode the same sample_ids, so we report the
distribution of PER-PART differences rather than a difference of means. That matters
here more than usual, because Chamfer distance is heavy-tailed -- a handful of wildly
wrong solids can move a mean by more than a systematic shift across every part -- so the
median and the sign test carry the argument and the mean is reported only alongside them.

Only parts that reach step_export_ok in BOTH arms can be compared; a part that fails to
export has no geometry to score, and dropping it from one arm only would bias the other.
The count of such parts is reported, because it is itself a selection effect.

    python src/scratch/n1g_geometry_analysis.py
"""
from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _roots import OUTPUTS, SCRATCH  # noqa: E402

MODES = ["prior", "shuffled", "oracle_ir"]
SEED = 20260808
BOOT = 10000


def sign_test(better: int, worse: int) -> float:
    """Two-sided exact binomial test on the discordant pairs."""
    n = better + worse
    if n == 0:
        return 1.0
    k = min(better, worse)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n))


def load(mode: str) -> dict[str, dict]:
    f = SCRATCH / f"geom_n1_step_{mode}" / "geometry_nbest_rows.jsonl"
    if not f.is_file():
        return {}
    out = {}
    for line in f.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        cands = r.get("candidate_results") or []
        if not cands:
            continue
        out[r["sample_id"]] = {"has_target": r.get("has_target"), **cands[0]}
    return out


def med(xs: list[float]) -> float:
    return statistics.median(xs) if xs else float("nan")


def main() -> int:
    data = {m: load(m) for m in MODES}
    have = [m for m in MODES if data[m]]
    if len(have) < 2:
        missing = [m for m in MODES if not data[m]]
        print("Not enough data to compare. Missing: " + ", ".join(missing))
        print(f"Expected {SCRATCH}\\geom_n1_step_<mode>\\geometry_nbest_rows.jsonl")
        print("Run 29_n1g_geometry_fidelity.sh and its PowerShell step first.")
        return 1

    print("=== coverage ===")
    for m in have:
        d = data[m]
        exported = sum(1 for r in d.values() if r.get("step_export_ok"))
        scored = sum(1 for r in d.values() if r.get("cd") is not None)
        no_t = sum(1 for r in d.values() if not r.get("has_target"))
        print(f"  {m:<10} rows {len(d):<5} exported {exported:<5} scored {scored:<5} "
              f"no reference cloud {no_t}")
        if exported and not scored:
            keys = sorted(next(iter(d.values())).keys())
            print(f"  ** {exported} candidates exported but NONE carry a geometry score.")
            print(f"     That is a schema mismatch, not a result. Keys present: {keys}")
            print(f"     This script expects 'cd' and 'f_score_1pct'.")

    for a, b in [("prior", "shuffled"), ("prior", "oracle_ir")]:
        if not (data.get(a) and data.get(b)):
            continue
        ids = sorted(set(data[a]) & set(data[b]))
        both = [i for i in ids
                if data[a][i].get("cd") is not None
                and data[b][i].get("cd") is not None]
        print(f"\n=== {a} vs {b}: paired on the {len(both)} parts BOTH scored "
              f"(of {len(ids)}) ===")
        if not both:
            print("  no overlap -- nothing to compare")
            continue

        for key, label, lower_better in [("cd", "Chamfer (mm^2)", True),
                                         ("f_score_1pct", "F@1%", False)]:
            va = [data[a][i][key] for i in both if data[a][i].get(key) is not None]
            vb = [data[b][i][key] for i in both if data[b][i].get(key) is not None]
            if len(va) != len(both) or len(vb) != len(both):
                print(f"  {label}: incomplete ({len(va)} vs {len(vb)}), skipping")
                continue
            diffs = [x - y for x, y in zip(va, vb)]
            # "better" means lower for CD, higher for F@1%
            better = sum(1 for d in diffs if (d < 0) == lower_better and d != 0)
            worse = sum(1 for d in diffs if (d > 0) == lower_better and d != 0)
            p = sign_test(better, worse)
            print(f"  {label}")
            print(f"    median   {a} {med(va):.4g}   {b} {med(vb):.4g}")
            print(f"    mean     {a} {statistics.fmean(va):.4g}   "
                  f"{b} {statistics.fmean(vb):.4g}")
            print(f"    paired   {a} better on {better} parts, {b} better on {worse}, "
                  f"tied {len(both)-better-worse}")
            print(f"    sign test p={p:.3g}  "
                  f"{'DIFFERENT' if p < 0.05 else 'not separable'}")

        print("\n  Read the median and the sign test, not the mean: Chamfer distance is")
        print("  heavy-tailed, so a few grossly wrong solids can dominate an average in")
        print("  either direction.")

    print("\n=== what this settles ===")
    print("  If prior is clearly better than shuffled here, the prefix controls the")
    print("  SHAPE and not merely the plan text, so Build's blindness (N1: 71.4 vs 68.6,")
    print("  p=0.37) is a limitation of that metric rather than of the mechanism.")
    print("  If they are indistinguishable, the mechanism steers plan text without")
    print("  steering geometry, and every geometric claim in the paper needs revisiting.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
