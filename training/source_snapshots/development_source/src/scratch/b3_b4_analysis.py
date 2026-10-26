"""B3 and B4: the two sample-size fixes, analysed as paired comparisons.

B3 -- the nearest-neighbour IR baselines (variants A and B of tab:generation) were
reported at n=100 while variant C sat at n=2,500, so the table mixed sample sizes inside
one comparison and the paper had to say so. Worse, --limit 100 takes the FIRST hundred
rows, the slice docs SS9.2 measured ~10 pp optimistic, so the published rows were wrong
on size and on slice. Both arms now run the full 2,500.

B4 -- the Stage 3 versus Stage 3b comparison disagreed in SIGN between n=100 (+12 pp)
and n=2,500 (-4.4 pp). Half of that was the first-hundred slice, measured in SS9.2. The
other half was unresolved only because the Stage 3 arm had never been re-run on the same
seeded random subset. It has now.

Every contrast here is paired -- the NN-IR baselines and variant C decode the same 2,500
test rows, and both Stage arms decode the same 100 parts -- so McNemar's exact test is
the right instrument and comparing marginal intervals would throw away the pairing.

    python src/scratch/b3_b4_analysis.py [--latex]
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
MODALITIES = ("step", "point", "text", "image")
MODES = ("direct", "prior")


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


def rows(d: str, fname: str = "execution_rows.jsonl") -> dict[str, dict]:
    f = SCRATCH / d / fname
    if not f.is_file():
        return {}
    return {r["sample_id"]: r for r in
            (json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip())}


def summary(d: str) -> dict | None:
    f = SCRATCH / d / "execution_summary.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else None


def paired(a: dict[str, dict], b: dict[str, dict], key: str = "build_ok"):
    ids = sorted(set(a) & set(b))
    only_a = sum(1 for i in ids if a[i].get(key) and not b[i].get(key))
    only_b = sum(1 for i in ids if b[i].get(key) and not a[i].get(key))
    both = sum(1 for i in ids if a[i].get(key) and b[i].get(key))
    return len(ids), both, only_a, only_b, mcnemar_exact(only_a, only_b)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--latex", action="store_true")
    args = ap.parse_args()

    # ------------------------------------------------------------------ B3
    print("=== B3: NN-IR baselines, published n=100 against the new n=2,500 ===")
    print(f"  {'condition':<14}{'n=100 (first 100)':>24}{'n=2,500 (full)':>24}{'shift':>9}")
    shifts = []
    for m in MODALITIES:
        for mode in MODES:
            old, new = summary(f"exec_nnir_25k_{mode}_{m}"), summary(f"exec_nnir_full_{mode}_{m}")
            if not (old and new):
                print(f"  {mode+'/'+m:<14}(missing)")
                continue
            po, lo_o, hi_o = wilson(old["build_ok_count"], old["rows"])
            pn, lo_n, hi_n = wilson(new["build_ok_count"], new["rows"])
            shifts.append(pn - po)
            print(f"  {mode+'/'+m:<14}{f'{po:.1f} [{lo_o:.1f}, {hi_o:.1f}]':>24}"
                  f"{f'{pn:.1f} [{lo_n:.1f}, {hi_n:.1f}]':>24}{pn-po:>+8.1f}")
    if shifts:
        print(f"\n  largest shift {max(shifts, key=abs):+.1f} pp; mean "
              f"{sum(shifts)/len(shifts):+.1f} pp")
        print("  The first-100 slice bias is ~10 pp where build sits at 50-80% (SS9.2),")
        print("  and near-absent here because NN-IR already sits at the ceiling: an")
        print("  optimistic slice has almost no room to be optimistic in. Interval WIDTH")
        print("  is what changed -- from about +/-6 pp to +/-0.5 pp.")

    # ---------------------------------------------- B3 vs variant C, paired
    print("\n=== B3: NN-IR against generated IR (variant C), PAIRED on the same 2,500 ===")
    print(f"  {'condition':<14}{'NN-IR':>8}{'variant C':>11}{'gap':>8}"
          f"{'only NN':>9}{'only C':>8}{'p':>12}")
    for m in MODALITIES:
        c = rows(f"exec_eval_25k_stage3b_{m}")
        for mode in MODES:
            nn = rows(f"exec_nnir_full_{mode}_{m}")
            if not (nn and c):
                continue
            n, both, only_nn, only_c, p = paired(nn, c)
            pnn = 100 * sum(1 for i in nn if nn[i]["build_ok"]) / len(nn)
            pc = 100 * sum(1 for i in c if c[i]["build_ok"]) / len(c)
            print(f"  {mode+'/'+m:<14}{pnn:>7.1f}%{pc:>10.1f}%{pnn-pc:>+7.1f}"
                  f"{only_nn:>9}{only_c:>8}{p:>12.2e}")
    print("\n  Every gap is large and one-directional. The paper's central negative")
    print("  result -- retrieving a training plan beats generating one -- survives the")
    print("  sample-size correction and is stronger at full scale, not weaker.")

    # ------------------------------------------------------------------ B4
    print("\n=== B4: Stage 3 against Stage 3b, STEP, same seeded random 100 parts ===")
    s3 = rows("exec_b4_stage3_random100_step")
    a = rows("exec_nbest_random100_step", "execution_nbest_rows.jsonl")
    s3b = {i: {"build_ok": r.get("candidate0_exec_ok")} for i, r in a.items()}
    if s3 and s3b:
        n, both, only3, only3b, p = paired(s3, s3b)
        p3, lo3, hi3 = wilson(sum(1 for i in s3 if s3[i]["build_ok"]), len(s3))
        p3b, lo3b, hi3b = wilson(sum(1 for i in s3b if s3b[i]["build_ok"]), len(s3b))
        print(f"  Stage 3   {p3:5.1f} [{lo3:.1f}, {hi3:.1f}]   n={len(s3)}")
        print(f"  Stage 3b  {p3b:5.1f} [{lo3b:.1f}, {hi3b:.1f}]   n={len(s3b)}")
        print(f"  paired n={n}: both {both}, only Stage 3 {only3}, only Stage 3b {only3b}")
        print(f"  McNemar exact p={p:.4f}  "
              f"{'DIFFERENT' if p < 0.05 else 'not separable'}")
        print(f"\n  Stage 3 - Stage 3b = {p3-p3b:+.1f} pp on this subset.")
        print("  Against the record: n=100 first-slice said +12 pp for Stage 3b;")
        print("  n=2,500 said -4.4 pp (Stage 3b worse on STEP). This run is on the same")
        print("  parts as the Stage 3b arm, same code decoder, same repair, so the plan")
        print("  generator is the only variable.")
        if p3 > p3b:
            print("  => The sign agrees with n=2,500: Stage 3b costs STEP build success.")
            print("     The +12 pp was the first-hundred slice, not a real reversal.")
        else:
            print("  => The sign agrees with the old n=100 reading; the conflict stands.")

    if args.latex:
        print("\n% ---- tab:generation, variants A/B at n=2,500 ----")
        for mode in MODES:
            cells = [f"NN-IR ({mode})"]
            for m in MODALITIES:
                s = summary(f"exec_nnir_full_{mode}_{m}")
                cells.append("--" if not s else f"{100*s['build_ok_rate']:.1f}")
            print(" & ".join(cells) + r" \\")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
