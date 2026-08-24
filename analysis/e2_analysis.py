"""E2 step 2: is the explicit plan a more informative diagnostic than the continuous latent?

Protocol frozen in docs/E2_protocol_frozen.md before any number here was computed. Conventions the
protocol fixes, restated so this file can be read alone:

  * every diagnostic is oriented higher = better plan agreement;
  * both AUROCs predict SUCCESS, so 0.5 is no signal and above 0.5 means a better-agreeing plan is
    more often followed by a successful build or export;
  * lower CD is better, so a NEGATIVE Spearman rho marks a useful diagnostic there;
  * higher F@1 is better, so a POSITIVE rho marks a useful one;
  * the headline is dAUROC = AUROC(plan diagnostic) - AUROC(lat_cos), paired bootstrap over
    samples, B = 10000, seed 20260821;
  * no classifier is trained and no threshold is chosen.

lat_cos comes from scratch/e2_latent_cosine.py. The script refuses to run without it rather than
dropping it and silently answering a different, easier question.

RUN (either side, CPU only):

    PYTHONPATH=. python scratch/e2_analysis.py
"""
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

from _roots import SCRATCH

BOOTSTRAP_B = 10_000
BOOTSTRAP_SEED = 20260821

# name -> (label, whether the diagnostic needs an explicit plan to exist)
DIAGNOSTICS = [
    ("lat_cos", "Latent cosine  cos(z_ir_hat, z_ir)", False),
    ("plan_cos", "Plan cosine    cos(E(pred plan), z_ir)", True),
    ("op_set_f1", "Plan Op-Set F1", True),
    ("op_seq_lcs", "Plan Op-Seq LCS", True),
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--latent", type=Path, default=SCRATCH / "e2_latent_cosine.jsonl")
    p.add_argument("--plan-metrics", type=Path,
                   default=Path("outputs/ablation_prefix/score_step_prior.json"),
                   help="per_sample ir_cosine / op_set_f1 / op_seq_lcs for the plans this arm "
                        "consumed. Must be the prior arm of ablation_prefix: its 500 rows are the "
                        "E1 rows, and its predicted_ir is byte-identical to B2-Pred's for all 500. "
                        "outputs/tab_ir_quality_step_C.json is a DIFFERENT 500-row draw -- 82 ids "
                        "in common -- and using it silently analysed that overlap.")
    p.add_argument("--geometry", type=Path,
                   default=SCRATCH / "geom_e1_step_B2P" / "geometry_nbest_rows.jsonl")
    p.add_argument("--out", type=Path, default=SCRATCH / "e2_results.json")
    return p.parse_args()


# --------------------------------------------------------------------------- stats
def auroc(scores: list[float], labels: list[int]) -> float | None:
    """Mann-Whitney AUROC of `scores` against a binary `labels`, ties at half credit.

    Returns None where one class is absent, because an AUROC over a single class is undefined
    rather than 0.5.
    """
    pos = [s for s, y in zip(scores, labels) if y]
    neg = [s for s, y in zip(scores, labels) if not y]
    if not pos or not neg:
        return None
    order = sorted(range(len(scores)), key=lambda i: scores[i])
    ranks = [0.0] * len(scores)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and scores[order[j + 1]] == scores[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    rsum = sum(r for r, y in zip(ranks, labels) if y)
    n1, n0 = len(pos), len(neg)
    return (rsum - n1 * (n1 + 1) / 2.0) / (n1 * n0)


def spearman(xs: list[float], ys: list[float]) -> float | None:
    """Spearman rho via Pearson on average ranks."""
    n = len(xs)
    if n < 3:
        return None

    def rank(v: list[float]) -> list[float]:
        order = sorted(range(n), key=lambda i: v[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    rx, ry = rank(xs), rank(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    dy = math.sqrt(sum((b - my) ** 2 for b in ry))
    return None if dx == 0 or dy == 0 else num / (dx * dy)


def boot_ci(stat_fn, n: int, b: int = BOOTSTRAP_B,
            seed: int = BOOTSTRAP_SEED) -> tuple[float, float] | None:
    """Percentile interval, resampling SAMPLE INDICES so every diagnostic in a replicate sees the
    same rows. That is what makes dAUROC a paired quantity."""
    rng = random.Random(seed)
    reps = []
    for _ in range(b):
        idx = [rng.randrange(n) for _ in range(n)]
        v = stat_fn(idx)
        if v is not None:
            reps.append(v)
    if len(reps) < b // 2:
        return None
    reps.sort()
    return reps[int(0.025 * (len(reps) - 1))], reps[int(0.975 * (len(reps) - 1))]


# --------------------------------------------------------------------------- data
def load(args: argparse.Namespace) -> list[dict]:
    if not args.latent.exists():
        raise SystemExit(
            f"missing {args.latent}\n"
            "E2's whole question is whether the plan beats the LATENT, so the latent diagnostic is\n"
            "not optional. Run scratch/e2_latent_cosine.py first (GPU, WSL, ai_dev)."
        )
    lat = {json.loads(l)["sample_id"]: json.loads(l)["lat_cos"]
           for l in args.latent.open(encoding="utf-8") if l.strip()}

    pm = json.load(args.plan_metrics.open(encoding="utf-8"))["per_sample"]
    plan = {r["sample_id"]: r for r in pm}

    geo: dict[str, dict] = {}
    for line in args.geometry.open(encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        cands = r.get("candidate_results") or []
        if not cands:
            geo[r["sample_id"]] = {"build_ok": False, "step_export_ok": False,
                                   "cd": None, "f_score_1pct": None}
            continue
        # N = 1 throughout this arm, so there is exactly one candidate; assert rather than assume,
        # because silently taking the best of several would be selection this protocol forbids.
        if len(cands) != 1:
            raise SystemExit(f"{r['sample_id']} has {len(cands)} candidates; E2 is single-shot")
        c = cands[0]
        geo[r["sample_id"]] = {
            "build_ok": bool(c.get("build_ok")),
            "step_export_ok": bool(c.get("step_export_ok")),
            "cd": c.get("cd"),
            "f_score_1pct": c.get("f_score_1pct"),
        }

    ids = sorted(set(lat) & set(plan) & set(geo))
    # A partial join is a wrong experiment, not a smaller one: the protocol fixes the arm as
    # B2-Pred's 500-row slice. The first run of this script printed a note and analysed the
    # 82-row overlap between two different 500-row draws, which is exactly the kind of silent
    # denominator substitution the rest of this paper spends its guards preventing.
    sizes = {"latent": len(lat), "plan metrics": len(plan), "geometry": len(geo)}
    if len(set(sizes.values())) != 1 or len(ids) != next(iter(sizes.values())):
        detail = ", ".join(f"{k}={v}" for k, v in sizes.items())
        raise SystemExit(
            f"join is {len(ids)} rows but the sources are {detail}.\n"
            "These are not the same sample set. Check that --plan-metrics is the arm's own\n"
            "plan file: outputs/ablation_prefix/score_step_prior.json carries the E1 rows,\n"
            "outputs/tab_ir_quality_step_C.json is a different draw with 82 ids in common.")
    rows = []
    for s in ids:
        rows.append({
            "sample_id": s,
            "lat_cos": lat[s],
            "plan_cos": plan[s]["ir_cosine"],
            "op_set_f1": plan[s]["op_set_f1"],
            "op_seq_lcs": plan[s]["op_seq_lcs"],
            **geo[s],
        })
    keys = [k for k, _, _ in DIAGNOSTICS]
    kept = [r for r in rows if all(r[k] is not None for k in keys)]
    if len(kept) != len(rows):
        print(f"  dropped {len(rows) - len(kept)} rows missing a diagnostic value")
    return kept


# --------------------------------------------------------------------------- report
def main() -> int:
    args = parse_args()
    rows = load(args)
    n = len(rows)
    print(f"E2: {n} rows joined on sample_id\n")
    print("Protocol: docs/E2_protocol_frozen.md. AUROC predicts SUCCESS; higher diagnostic means")
    print("better plan agreement. Lower CD is better, so negative rho is the useful direction.\n")

    results: dict = {"n_rows": n, "bootstrap_B": BOOTSTRAP_B, "seed": BOOTSTRAP_SEED,
                     "outcome1": {}, "outcome2": {}}

    # ---- Outcome 1: validity-failure localisation --------------------------
    print("=== Outcome 1 --- AUROC(diagnostic, success), all rows ===")
    for outcome in ("build_ok", "step_export_ok"):
        labels = [int(r[outcome]) for r in rows]
        base_rate = sum(labels) / n
        print(f"\n  {outcome}: {sum(labels)}/{n} successes ({base_rate:.1%})")
        if base_rate in (0.0, 1.0):
            print("    one class only; AUROC undefined, skipped")
            continue
        per: dict = {}
        for key, label, _ in DIAGNOSTICS:
            a = auroc([r[key] for r in rows], labels)
            ci = boot_ci(lambda idx, k=key: auroc([rows[i][k] for i in idx],
                                                  [int(rows[i][outcome]) for i in idx]), n)
            per[key] = {"auroc": a, "ci": ci}
            cis = f"[{ci[0]:.3f}, {ci[1]:.3f}]" if ci else "--"
            print(f"    {label:42s} {a:.3f}  95 % {cis}")
        print(f"    {'paired dAUROC against the latent':42s}")
        for key, label, needs_plan in DIAGNOSTICS:
            if not needs_plan:
                continue
            d = per[key]["auroc"] - per["lat_cos"]["auroc"]
            ci = boot_ci(lambda idx, k=key: (
                lambda ys: (lambda a1, a0: None if a1 is None or a0 is None else a1 - a0)(
                    auroc([rows[i][k] for i in idx], ys),
                    auroc([rows[i]["lat_cos"] for i in idx], ys))
            )([int(rows[i][outcome]) for i in idx]), n)
            cis = f"[{ci[0]:+.3f}, {ci[1]:+.3f}]" if ci else "--"
            excl = "excludes 0" if ci and (ci[0] > 0 or ci[1] < 0) else "contains 0"
            print(f"      {label:40s} {d:+.3f}  95 % {cis}  {excl}")
            per[key]["d_vs_latent"] = {"delta": d, "ci": ci}
        results["outcome1"][outcome] = {"n": n, "successes": sum(labels), "per_diagnostic": per}

    # ---- Outcome 2: geometric fidelity ------------------------------------
    print("\n=== Outcome 2 --- Spearman rho, each on its own scoreable subset ===")
    for metric, useful in (("cd", "negative"), ("f_score_1pct", "positive")):
        sub = [r for r in rows if r[metric] is not None]
        print(f"\n  {metric}: n = {len(sub)} scoreable of {n}   (useful direction: {useful})")
        per = {}
        for key, label, _ in DIAGNOSTICS:
            rho = spearman([r[key] for r in sub], [r[metric] for r in sub])
            ci = boot_ci(lambda idx, k=key, m=metric: spearman([sub[i][k] for i in idx],
                                                               [sub[i][m] for i in idx]),
                         len(sub))
            per[key] = {"rho": rho, "ci": ci}
            cis = f"[{ci[0]:+.3f}, {ci[1]:+.3f}]" if ci else "--"
            print(f"    {label:42s} {rho:+.3f}  95 % {cis}")
        results["outcome2"][metric] = {"n": len(sub), "useful_direction": useful,
                                       "per_diagnostic": per}

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(f"\nwrote {args.out}")
    print("\nInterpretation is fixed in docs/E2_protocol_frozen.md and is decided by the")
    print("intervals above. Plan metrics score against ONE reference construction, so a low")
    print("value is not evidence of wrong geometry.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
