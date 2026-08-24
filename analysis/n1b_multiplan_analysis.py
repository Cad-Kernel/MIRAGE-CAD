"""N1b: is sampling budget worth more at the PLAN layer than at the CODE layer?

Configurations, all on the SAME seeded random 100 parts, all decoding five sequences
per query except D:

    D     1 greedy plan  x 1 greedy program   -- configuration A's candidate 0
    A@5   1 greedy plan  x 5 programs         -- diversity entirely in the code layer
    B@5   5 sampled plans x 1 program each    -- diversity entirely in the plan layer

A@5 and B@5 cost the same. **B@5 > A@5 is the claim worth testing**; "sampling beats
greedy" is not, because tab:geometry already established that sampling programs helps.

The first run of this experiment could not make that comparison: configuration B used
--limit 100 (the first hundred rows) against configuration A's seeded random hundred,
sharing 4 parts, and the first-N slice runs ~10 pp optimistic (docs SS9.2). The runner now
takes A's ids.txt as a hard precondition and tags its outputs `r100`. This script still
verifies the part sets agree and REFUSES to report the contrast if they do not -- the
guard stays in even though it now passes, because the failure was silent last time.

One asymmetry remains and is not fixable from here: configuration A applied the three
deterministic repair rules of SS5.9 and configuration B did not. That favours A, so a
B > A result is conservative; a B < A result would need the rules ruled out first.

    python src/scratch/n1b_multiplan_analysis.py
"""
from __future__ import annotations

import itertools
import json
import math
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _roots import OUTPUTS, SCRATCH  # noqa: E402
WSL = OUTPUTS / "ablation_multiplan"

Z = 1.959963985
K = 5

B_DIRS = {"step": "exec_n1b_B_r100_step", "point": "exec_n1b_B_r100_point"}
A_DIRS = {"step": "exec_nbest_random100_step", "point": "exec_nbest_random100_point"}


def wilson(k: int, n: int) -> tuple[float, float, float]:
    if n == 0:
        return (float("nan"),) * 3
    p = k / n
    d = 1.0 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return 100 * p, 100 * max(0.0, c - h), 100 * min(1.0, c + h)


def mcnemar_exact(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n))


def rows(d: str, name: str = "execution_rows.jsonl") -> list[dict]:
    f = SCRATCH / d / name
    if not f.is_file():
        return []
    return [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]


def outcomes(mod: str) -> tuple[dict, dict, dict] | None:
    """Per-part booleans for D, A@5 and B@5, restricted to the shared parts."""
    a = {r["sample_id"]: r for r in rows(A_DIRS[mod], "execution_nbest_rows.jsonl")}
    b_rows = rows(B_DIRS[mod])
    if not a or not b_rows:
        return None
    by_q: dict[str, list[dict]] = {}
    for r in b_rows:
        by_q.setdefault(r["sample_id"], []).append(r)
    ids = sorted(set(a) & set(by_q))
    if not ids:
        return None
    D = {i: bool(a[i]["candidate_results"][0].get("build_ok")) for i in ids}
    A5 = {i: any(c.get("build_ok") for c in a[i]["candidate_results"][:K]) for i in ids}
    B5 = {i: any(r.get("build_ok") for r in by_q[i][:K]) for i in ids}
    return D, A5, B5


def main() -> int:
    meta = WSL / "run_metadata.json"
    if meta.is_file():
        m = json.loads(meta.read_text(encoding="utf-8"))
        parts = m.get("n_parts", m.get("limit", "?"))
        print(f"=== N1b: K={m['num_plans']} plans/query, T={m['temperature']}, "
              f"top-p={m['top_p']}, {parts} parts, repair={m['repair_applied']} ===")
        if "part_set" in m:
            print(f"    part set: {m['part_set']}")

    # ---- diversity: the sweep is a finding in its own right ----------------
    sweep = WSL / "sweep_stats_r100.json"
    if not sweep.is_file():
        sweep = WSL / "sweep_stats.json"
    if sweep.is_file():
        s = json.loads(sweep.read_text(encoding="utf-8"))
        print(f"\n=== temperature sweep (STEP, {sweep.name}) ===")
        print(f"  {'T':>5}{'grammar valid':>15}{'distinct plans/query':>22}"
              f"{'mean pairwise op-Jaccard':>26}")
        for T, v in s["stats"].items():
            print(f"  {T:>5}{v['grammar_valid_pct']:>14.1f}%{v['distinct_per_query']:>22.2f}"
                  f"{v['op_jaccard']:>26.3f}")
        ch = s["chosen_temperature"]
        print(f"\n  chosen T = {ch}  ({s['rule']})")
        j = s["stats"][ch]["op_jaccard"]
        print(f"\n  The Jaccard column is the finding. Distinct plans/query is at or near")
        print(f"  {K}.00 at every temperature -- the plans are never literally identical --")
        print(f"  but their OPERATION SETS overlap {100*j:.0f}% at the chosen T. The sampler")
        print(f"  varies parameters and phrasing, not construction strategy. Whatever B@{K}")
        print(f"  buys below, it is not the alternative construction histories Section 1's")
        print(f"  one-to-many argument appeals to.")

    # ---- the guard that failed silently last time -------------------------
    print("\n=== part-set check (configurations A and B must cover the same parts) ===")
    ok = True
    for mod in ("step", "point"):
        a_ids = {r["sample_id"] for r in rows(A_DIRS[mod], "execution_nbest_rows.jsonl")}
        b_ids = {r["sample_id"] for r in rows(B_DIRS[mod])}
        shared = len(a_ids & b_ids)
        good = a_ids and b_ids and shared == len(a_ids) == len(b_ids)
        ok &= bool(good)
        print(f"  {mod:<6} A={len(a_ids)}  B={len(b_ids)}  shared={shared}  "
              f"{'OK' if good else '** MISMATCH -- contrast not reportable **'}")
    if not ok:
        print("\n  Refusing to report A vs B. Re-run 25_n1b_multiplan.sh, which takes")
        print("  configuration A's ids.txt as a hard precondition.")
        return 1

    # ---- the comparison the experiment exists for -------------------------
    print(f"\n=== compute-matched: A@{K} (code layer) vs B@{K} (plan layer) ===")
    print("    same parts, same checkpoints, five sequences per query in both.")
    print("    CAVEAT: A had the SS5.9 repair rules applied, B did not -- favours A.\n")
    for mod in ("step", "point"):
        o = outcomes(mod)
        if not o:
            print(f"  {mod}: missing data")
            continue
        D, A5, B5 = o
        ids = sorted(D)
        n = len(ids)
        print(f"  --- {mod}  (n={n}) ---")
        for label, d in (("D   greedy 1x1", D), (f"A@{K} code layer", A5),
                         (f"B@{K} plan layer", B5)):
            k = sum(d.values())
            p, lo, hi = wilson(k, n)
            closed = (100 * k / n - 100 * sum(D.values()) / n) / \
                     (100 - 100 * sum(D.values()) / n) if sum(D.values()) < n else float("nan")
            extra = "" if label.startswith("D") else f"   closes {100*closed:.0f}% of D's headroom"
            print(f"    {label:<16}{p:5.1f} [{lo:.1f}, {hi:.1f}]{extra}")
        only_b = sum(1 for i in ids if B5[i] and not A5[i])
        only_a = sum(1 for i in ids if A5[i] and not B5[i])
        p = mcnemar_exact(only_b, only_a)
        gap = 100 * (sum(B5.values()) - sum(A5.values())) / n
        print(f"    paired B@{K} vs A@{K}: only B {only_b}, only A {only_a}, "
              f"gap {gap:+.1f} pp, McNemar p={p:.4f}")
        if p < 0.05:
            side = "PLAN" if only_b > only_a else "CODE"
            print(f"    => SEPARABLE: the {side} layer is the better place to spend the "
                  f"sampling budget.")
        else:
            print(f"    => NOT separable at n={n}. The honest claim is only that sampling "
                  f"helps,\n       which tab:geometry already established.")

        # are the layers complementary? relevant to whether C (5x5) is worth running
        either = sum(1 for i in ids if A5[i] or B5[i])
        both = sum(1 for i in ids if A5[i] and B5[i])
        pe, loe, hie = wilson(either, n)
        print(f"    union of the two (upper bound on a 5x5 run): {pe:.1f} "
              f"[{loe:.1f}, {hie:.1f}]  (both {both}, either {either})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
