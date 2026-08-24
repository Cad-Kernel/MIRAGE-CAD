"""Paired analysis for the point-cloud observation-block A/B (docs §9.9).

Both arms decode the same test rows and differ only in whether c_obs is populated, so
every contrast here is paired: a bootstrap on the mean per-row difference for the
continuous IR metrics, McNemar's exact test for the binary Build outcome. Marginal
intervals would throw away the pairing and understate the power.

Run after 27_point_evidence_fix.sh and its PowerShell execution step:

    python src/scratch/point_evidence_analysis.py
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _roots import OUTPUTS, SCRATCH  # noqa: E402
WSL = OUTPUTS / "point_evidence_ab"

ARMS = ("off", "on")
Z = 1.959963985
BOOT = 10000
SEED = 20260806


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


def paired_boot(d: list[float]) -> tuple[float, float, float]:
    rng = random.Random(SEED)
    n = len(d)
    means = []
    for _ in range(BOOT):
        s = 0.0
        for _ in range(n):
            s += d[rng.randrange(n)]
        means.append(s / n)
    means.sort()
    return sum(d) / n, means[int(0.025 * BOOT)], means[int(0.975 * BOOT) - 1]


def main() -> int:
    meta = WSL / "run_metadata.json"
    if meta.is_file():
        print("=== run metadata ===")
        print(meta.read_text(encoding="utf-8").strip(), "\n")

    ir = {}
    for arm in ARMS:
        f = WSL / f"score_point_{arm}.json"
        if f.is_file():
            d = json.loads(f.read_text(encoding="utf-8"))
            ir[arm] = {r["sample_id"]: r for r in d.get("per_sample", [])}
            s = d.get("summary", {})
            print(f"  {arm:<4} n={s.get('n')}  IR cos {s['ir_cosine_mean']:.3f}  "
                  f"Op-Set F1 {100*s['op_set_f1_mean']:.1f}%  "
                  f"Op-Seq LCS {100*s['op_seq_lcs_mean']:.1f}%")
        else:
            print(f"  {arm:<4} (no score file at {f.name})")

    if len(ir) == 2:
        ids = sorted(set(ir["off"]) & set(ir["on"]))
        print(f"\n=== paired IR contrasts, on - off (n={len(ids)}) ===")
        for key, label, sc in [("ir_cosine", "IR cos", 1),
                               ("op_set_f1", "Op-Set F1", 100),
                               ("op_seq_lcs", "Op-Seq LCS", 100)]:
            d = [ir["on"][i][key] - ir["off"][i][key] for i in ids]
            p, lo, hi = paired_boot(d)
            better = sum(1 for x in d if x > 0)
            worse = sum(1 for x in d if x < 0)
            sig = "" if lo <= 0 <= hi else "  *"
            print(f"  {label:<11}{sc*p:>+8.2f} [{sc*lo:>+7.2f},{sc*hi:>+7.2f}]"
                  f"   better {better} / worse {worse} / tied {len(d)-better-worse}{sig}")

    ex = {}
    for arm in ARMS:
        f = SCRATCH / f"exec_point_evidence_{arm}" / "execution_rows.jsonl"
        if f.is_file():
            ex[arm] = {r["sample_id"]: r for r in
                       (json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip())}

    if ex:
        print("\n=== Build level (Wilson 95%) ===")
        for arm in ARMS:
            rows = ex.get(arm)
            if not rows:
                print(f"  {arm:<4} (missing)")
                continue
            cells = []
            for key in ("syntax_ok", "build_ok", "step_export_ok"):
                p, lo, hi = wilson(sum(1 for r in rows.values() if r.get(key)), len(rows))
                cells.append(f"{key.replace('_ok',''):<12}{p:5.1f} [{lo:.1f},{hi:.1f}]")
            print(f"  {arm:<4} " + "   ".join(cells))

    if len(ex) == 2:
        ids = sorted(set(ex["off"]) & set(ex["on"]))
        print(f"\n=== Build, paired McNemar exact (n={len(ids)}) ===")
        for key in ("build_ok", "step_export_ok"):
            b = sum(1 for i in ids if ex["on"][i][key] and not ex["off"][i][key])
            c = sum(1 for i in ids if ex["off"][i][key] and not ex["on"][i][key])
            p = mcnemar_exact(b, c)
            print(f"  {key:<16} only-on={b} only-off={c}  p={p:.4f}  "
                  f"{'DIFFERENT' if p < 0.05 else 'not separable'}")
        print("\n  Reminder: N1 showed Build cannot separate prefix SOURCES at a fixed")
        print("  prompt. This contrast changes the prompt, so Build is informative here.")

        # --- where does the Build drop live? -------------------------------
        # Code generation is greedy, so an identical plan must yield an identical
        # program and an identical outcome. Any Build delta therefore lives entirely
        # in the rows whose plan text changed. Splitting on that turns "on is worse"
        # into a statement about how much damage each changed plan does.
        plans = {}
        for arm in ARMS:
            f = WSL / f"pred_ir_point_{arm}.jsonl"
            if f.is_file():
                plans[arm] = {r["sample_id"]: r.get("predicted_ir", "")
                              for r in (json.loads(l) for l in
                                        f.read_text(encoding="utf-8").splitlines() if l.strip())}
        if len(plans) == 2:
            same = [i for i in ids if plans["off"].get(i) == plans["on"].get(i)]
            diff = [i for i in ids if plans["off"].get(i) != plans["on"].get(i)]
            print(f"\n=== diagnosis: plan text identical for {len(same)}/{len(ids)}, "
                  f"changed for {len(diff)} ===")
            bad = [i for i in same if ex["off"][i]["build_ok"] != ex["on"][i]["build_ok"]]
            print(f"  sanity: identical plans with differing Build: {len(bad)} "
                  f"(must be 0 -- greedy code generation is deterministic)")
            if diff:
                for arm in ARMS:
                    k = sum(1 for i in diff if ex[arm][i]["build_ok"])
                    p, lo, hi = wilson(k, len(diff))
                    print(f"  among CHANGED plans, {arm:<3} build {p:5.1f} "
                          f"[{lo:.1f}, {hi:.1f}]  ({k}/{len(diff)})")
                lo_ = sum(len(plans["off"][i]) for i in diff) / len(diff)
                ln_ = sum(len(plans["on"][i]) for i in diff) / len(diff)
                print(f"  mean plan length among changed: off {lo_:.0f} chars, "
                      f"on {ln_:.0f} chars  ({ln_-lo_:+.0f})")
                if ir:
                    fo = sum(ir["off"][i]["op_set_f1"] for i in diff) / len(diff)
                    fn = sum(ir["on"][i]["op_set_f1"] for i in diff) / len(diff)
                    print(f"  mean Op-Set F1 among changed: off {100*fo:.1f}%, "
                          f"on {100*fn:.1f}%  ({100*(fn-fo):+.1f}pp)")
                print("\n  If `on` is BETTER on IR and WORSE on Build among exactly these")
                print("  rows, the plan improved while the program got harder to execute --")
                print("  i.e. the cost is at the plan->code hand-off, not in the plan.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
