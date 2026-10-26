"""No-plan baseline: does the construction plan earn its place in the architecture?

The paper is called construction-plan-guided and no experiment removes the plan.
tab:ablation_stage4b shows a BETTER plan gives better code; it does not show that ANY
plan beats NO plan. This compares a code model trained and evaluated with no plan in its
prompt against variant C, on the same 2,500 test rows, same base model, same LoRA rank
and quantisation, same repair pipeline, same execution harness.

WHAT IS BEING ABLATED. Removing the plan from the code model's prompt removes the query
encoder too, because the soft prefix reaches the code model only through the plan. So
this contrasts the plan-mediated pathway AS A WHOLE against a direct query-to-code
fine-tune. It does not isolate the plan text from the latent, and no conclusion here
licenses "the plan text is useless".

The comparison is paired -- both arms decode the same rows -- so McNemar's exact test
applies and marginal intervals would discard the pairing.

    python src/scratch/noplan_analysis.py [--modality step]
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _roots import OUTPUTS, SCRATCH  # noqa: E402

Z = 1.959963985
GATES = ("syntax_ok", "build_ok", "step_export_ok")


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


def rows(d: str) -> dict[str, dict]:
    f = SCRATCH / d / "execution_rows.jsonl"
    if not f.is_file():
        return {}
    return {r["sample_id"]: r for r in
            (json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip())}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--modality", default="step")
    args = ap.parse_args()
    m = args.modality

    a = rows(f"exec_eval_25k_stage3b_{m}")      # variant C, with plan
    b = rows(f"exec_noplan_{m}")                # no plan
    if not b:
        print(f"No-plan arm not found at {SCRATCH}\\exec_noplan_{m}\\execution_rows.jsonl")
        print("Run 33_noplan_baseline.sh and its PowerShell step first.")
        return 1
    if not a:
        print(f"With-plan arm (variant C) not found at exec_eval_25k_stage3b_{m}")
        return 1

    ids = sorted(set(a) & set(b))
    print(f"=== {m}: with-plan (variant C) vs no-plan, paired on {len(ids)} rows "
          f"(C={len(a)}, no-plan={len(b)}) ===\n")
    print(f"  {'gate':<16}{'with plan':>22}{'no plan':>22}")
    for g in GATES:
        pa = wilson(sum(1 for i in ids if a[i].get(g)), len(ids))
        pb = wilson(sum(1 for i in ids if b[i].get(g)), len(ids))
        print(f"  {g:<16}{f'{pa[0]:.1f} [{pa[1]:.1f}, {pa[2]:.1f}]':>22}"
              f"{f'{pb[0]:.1f} [{pb[1]:.1f}, {pb[2]:.1f}]':>22}")

    print("\n=== paired McNemar (exact, two-sided) ===")
    verdicts = {}
    for g in GATES:
        only_plan = sum(1 for i in ids if a[i].get(g) and not b[i].get(g))
        only_none = sum(1 for i in ids if b[i].get(g) and not a[i].get(g))
        p = mcnemar_exact(only_plan, only_none)
        gap = 100 * (only_plan - only_none) / len(ids)
        verdicts[g] = (gap, p)
        print(f"  {g:<16} only with-plan {only_plan:<5} only no-plan {only_none:<5} "
              f"gap {gap:+6.1f} pp   p={p:.4g}   "
              f"{'DIFFERENT' if p < 0.05 else 'not separable'}")

    gap, p = verdicts["build_ok"]
    print("\n=== reading it, per the criteria fixed before the run ===")
    if p < 0.05 and gap > 0:
        print(f"  with-plan >> no-plan ({gap:+.1f} pp on Build, p={p:.3g}).")
        print("  The plan-mediated pathway earns its place. This is the paper's missing")
        print("  positive architectural claim -- state it as the pathway as a whole, not")
        print("  as the plan text in isolation.")
    elif p >= 0.05:
        print(f"  with-plan ~= no-plan ({gap:+.1f} pp on Build, p={p:.3g}, not separable).")
        print("  The plan buys no execution success. The contribution has to be restated:")
        print("  an explicit plan makes the pipeline inspectable and editable before any")
        print("  code exists, which is real and measured (tab:editability) and independent")
        print("  of build rate. The abstract's framing would need to change.")
    else:
        print(f"  no-plan >> with-plan ({gap:+.1f} pp on Build, p={p:.3g}).")
        print("  The plan is a bottleneck rather than a guide. The paper becomes a")
        print("  diagnostic: an interpretable intermediate that costs accuracy. Least")
        print("  comfortable of the three, most informative, and it must be reported.")

    print("\n  Caveat that belongs with any of the three: Build is a validity gate and has")
    print("  failed three times in this paper to register real changes in plan content.")
    print("  A build-rate verdict here should be checked geometrically before it is")
    print("  written as a claim -- 31_b1k_geometry.sh is the pattern to copy.")
    geometry(m)
    return 0




# --------------------------------------------------------------------- geometry
# Calibration from docs SS9.15, measured on this corpus: two disjoint samplings of the
# SAME reference surface score these, so they bound what the metrics can express.
CD_FLOOR = 1.963      # mm^2
F_CEILING = 0.244


def geom(d: str) -> dict[str, dict]:
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


def sign_test(better: int, worse: int) -> float:
    n = better + worse
    if n == 0:
        return 1.0
    k = min(better, worse)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n))


def geometry(m: str) -> None:
    """Does the plan improve the SHAPE, or only how often a program builds?

    The with-plan arm is variant C on STEP, already scored by 32_stage3b_geometry.sh --
    its export count matches tab:main_25k exactly, so the identity is checked rather than
    assumed. Only the no-plan arm needed its own pass.
    """
    import statistics
    a = geom("geom_stage3b_step_stage3b")
    b = geom(f"geom_noplan_{m}")
    print("\n" + "=" * 70)
    if not b:
        print("Geometry not yet scored for the no-plan arm.")
        print(f"  expected {SCRATCH / ('geom_noplan_' + m) / 'geometry_nbest_rows.jsonl'}")
        print("  run 34_noplan_geometry.sh and its PowerShell step to widen the claim")
        print("  from executable validity to fidelity.")
        return
    if not a:
        print("With-plan geometry arm missing (scratch/geom_stage3b_step_stage3b).")
        print("  run 32_stage3b_geometry.sh first.")
        return

    ea = sum(1 for r in a.values() if r.get("cd") is not None)
    eb = sum(1 for r in b.values() if r.get("cd") is not None)
    ids = sorted(set(a) & set(b))
    both = [i for i in ids if a[i].get("cd") is not None and b[i].get("cd") is not None]
    print(f"=== geometry: with-plan vs no-plan, paired on {len(both)} parts ===")
    print(f"  scorable: with-plan {ea}, no-plan {eb}")
    print(f"  ** The shared set is capped by the weaker arm and consists of the parts the")
    print(f"     PLAN-FREE model could already handle. The ~{ea - len(both)} parts only the")
    print(f"     plan-mediated arm builds are invisible here BY CONSTRUCTION, so this")
    print(f"     comparison is biased toward the baseline and understates the plan. **")
    if not both:
        print("  nothing to compare")
        return

    for key, label, lower_better, ref in (("cd", "Chamfer (mm^2)", True, CD_FLOOR),
                                          ("f_score_1pct", "F@1%", False, F_CEILING)):
        va = [a[i][key] for i in both]
        vb = [b[i][key] for i in both]
        d = [y - x for x, y in zip(va, vb)]          # no-plan minus with-plan
        wp = sum(1 for x in d if (x > 0) == lower_better and x != 0)   # with-plan better
        np_ = sum(1 for x in d if (x < 0) == lower_better and x != 0)  # no-plan better
        p = sign_test(wp, np_)
        ma, mb = statistics.median(va), statistics.median(vb)
        scale = (f"   ({ma/ref:.2f}x / {mb/ref:.2f}x the noise floor)" if lower_better
                 else f"   ({100*ma/ref:.0f}% / {100*mb/ref:.0f}% of the ceiling)")
        print(f"\n  {label}")
        print(f"    median   with-plan {ma:.4g}   no-plan {mb:.4g}{scale}")
        print(f"    paired   with-plan better on {wp}, no-plan better on {np_}, "
              f"tied {len(both)-wp-np_}")
        print(f"    sign test p={p:.3g}   {'DIFFERENT' if p < 0.05 else 'not separable'}")

    print("\n  Reading it, per the criteria fixed before the run:")
    print("    with-plan better   the plan improves fidelity on top of buildability, and")
    print("                       does so even on the subset that favours the baseline.")
    print("    not separable      the plan's value is concentrated in buildability -- it")
    print("                       converts failures into successes rather than refining")
    print("                       successes. Given the selection that is NOT a negative")
    print("                       result, and it is the honest way to report it.")


if __name__ == "__main__":
    raise SystemExit(main())
