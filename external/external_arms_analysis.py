"""The four external arms: what Build shows, and what it cannot.

Written only after the runs existed, so every field and every baseline here is read rather
than assumed.

THE HEADLINE IS A NEGATIVE ONE FOR THE PAPER'S FRAMING. Retrieving the nearest training plan
builds at 99.2% (step) and 98.8% (point) on externally authored CAD, against 69.0% and 59.2%
for a generated plan. That was the third of four outcomes fixed in script 36's header before
the run: procedural retrieval is a strong cross-source prior, which is valuable and has to be
reported whichever way it cuts.

BUT BUILD CANNOT SETTLE THIS, AND THE PAPER ALREADY KNOWS WHY. A retrieved plan comes from a
real corpus program, so the code written from it is close to something that executed before --
of course it builds. Whether it resembles the FUSION 360 part it was asked for is a different
question, and the paper's own evidence says the two come apart: Build is a validity gate,
insensitive in both directions, demonstrated three separate ways (shuffled prefixes leave it
unmoved, the no-plan baseline raises syntactic validity while halving it, Stage 3b pays 4.4pp
of it for no loss of fidelity). So the numbers below are a gate reading, and the geometry that
follows is the experiment.

McNemar's exact test on the paired arms, because both decode the same 400 rows.

Stratified at the corpus scale band. FllumaOne parts span 9-134 mm; 35.5% of these are
larger. The STEP descriptor carries bbox, area and volume under log1p as absolute quantities
while the point path normalises, so the step arms extrapolate on that third and the
discriminator is only readable inside the band.

    python src/scratch/external_arms_analysis.py
"""
from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
EXEC = REPO / "scratch"
QUERIES = REPO / "scratch" / "ext_queries.jsonl"
CORPUS_MAX_DIAG = 134.30

ARMS = {"step_genplan": ("step", "generated plan"), "step_nnir": ("step", "prior-NN-IR"),
        "point_genplan": ("point", "generated plan"), "point_nnir": ("point", "prior-NN-IR")}

# Internal comparison points, transcribed from docs 9.17 / 9.19 and the NN-IR baseline run.
INTERNAL = {("step", "generated plan"): ("Stage 3b step, n=2500", 1749, 2500),
            ("step", "prior-NN-IR"): ("prior-NN-IR step, n=100", 100, 100)}


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    z, p = 1.959964, k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact p for discordant counts b and c."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def load(arm: str) -> dict[str, dict]:
    f = EXEC / f"exec_ext_{arm}" / "execution_rows.jsonl"
    if not f.is_file():
        return {}
    return {r["sample_id"]: r
            for r in (json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip())}


def main() -> int:
    arms = {a: load(a) for a in ARMS}
    missing = [a for a, d in arms.items() if not d]
    if missing:
        print(f"missing execution rows for: {', '.join(missing)}")
        return 1

    diag = {}
    if QUERIES.is_file():
        for line in QUERIES.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                diag[r["sample_id"]] = r["bbox_diag"]

    print("=== Build, all 400 ===")
    print(f"{'arm':<28}{'build':>12}{'95% CI':>18}{'STEP export':>13}{'crash':>7}")
    for a, (mod, plan) in ARMS.items():
        d = arms[a]
        n = len(d)
        k = sum(1 for r in d.values() if r.get("build_ok"))
        se = sum(1 for r in d.values() if r.get("step_export_ok"))
        cr = sum(1 for r in d.values() if str(r.get("error", "")).startswith("kernel access"))
        lo, hi = wilson(k, n)
        print(f"{mod + ' / ' + plan:<28}{k}/{n} = {100*k/n:5.1f}%"
              f"   [{100*lo:4.1f}, {100*hi:4.1f}]{se:>13}{cr:>7}")

    print("\n=== against the internal runs ===")
    for (mod, plan), (label, ik, inn) in INTERNAL.items():
        arm = next(a for a, v in ARMS.items() if v == (mod, plan))
        d = arms[arm]
        k, n = sum(1 for r in d.values() if r.get("build_ok")), len(d)
        print(f"  {mod}/{plan}: external {100*k/n:.1f}%   internal {100*ik/inn:.1f}% ({label})")
    print("  Neither comparison is paired -- different parts -- so no test is run on it.")

    print("\n=== the discriminator: generated plan vs prior-NN-IR, paired ===")
    for mod in ("step", "point"):
        A, B = arms[f"{mod}_genplan"], arms[f"{mod}_nnir"]
        for label, keep in (("all", lambda s: True),
                            (f"within corpus scale (<= {CORPUS_MAX_DIAG} mm)",
                             lambda s: diag.get(s, 1e9) <= CORPUS_MAX_DIAG),
                            ("beyond corpus scale", lambda s: diag.get(s, 1e9) > CORPUS_MAX_DIAG)):
            shared = [s for s in A if s in B and keep(s)]
            if not shared:
                continue
            a_only = sum(1 for s in shared if A[s].get("build_ok") and not B[s].get("build_ok"))
            b_only = sum(1 for s in shared if B[s].get("build_ok") and not A[s].get("build_ok"))
            both = sum(1 for s in shared if A[s].get("build_ok") and B[s].get("build_ok"))
            neither = len(shared) - a_only - b_only - both
            p = mcnemar_exact(a_only, b_only)
            print(f"  {mod:<6} {label:<38} n={len(shared):<4} "
                  f"both={both:<4} genplan only={a_only:<3} NN-IR only={b_only:<4} "
                  f"neither={neither:<3} p={p:.3g}")

    print("\n=== retrieval concentration, the one thing Build cannot confound ===")
    for mod in ("step", "point"):
        f = REPO / "scratch" / f"_chk_gen_{mod}_nnir.jsonl"
        if not f.is_file():
            continue
        rows = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
        c = Counter(r.get("nn_sample_id") for r in rows)
        n = len(rows)
        top5 = sum(v for _, v in c.most_common(5))
        print(f"  {mod:<6} {len(c)} distinct neighbours for {n} queries ({100*len(c)/n:.1f}%), "
              f"top-5 cover {100*top5/n:.1f}%")
    print("  internal reference: 98 distinct for 100 queries (98.0%), top-5 cover 7.0%")

    print("\n=== what is NOT established by any of the above ===")
    print("  Whether any arm produced geometry resembling the Fusion 360 target. A retrieved")
    print("  plan comes from a real corpus program, so its code builds -- that is what a")
    print("  99% gate reading means and all it means. The paper's own evidence is that Build")
    print("  and fidelity come apart, so the claim to make here is decided by the geometry")
    print("  run, not by this table.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
