"""N1: analyse the prefix-source ablation at both the IR level and the Build level.

The experiment decodes the same test rows five ways, changing only what is fed to the
soft-prefix adapter Psi:

    prior        pi_m(z_m)                 -- the deployed path
    oracle_ir    f_ir(reference IR)        -- upper bound on the prefix path
    zero_prefix  K all-zero embeddings     -- Psi bypassed entirely
    zero_latent  Psi(0)                    -- learned constant prefix
    shuffled     another row's Psi(pi_m(z_m))

Everything downstream (LoRA-IR, LoRA-Code, decoding config, checkpoints) is held fixed,
so any difference is attributable to the prefix.

Two levels are reported because they answer different questions and -- as it turns out --
disagree:

  IR level     does the prefix determine WHICH construction plan is produced?
  Build level  does the prefix determine WHETHER the resulting program runs?

Pairing is exploited wherever it exists: every mode sees the same sample_ids, so the
correct tests are paired ones (McNemar's exact test for the binary Build outcome, a
paired bootstrap for the continuous IR metrics), not comparisons of marginal intervals.

    python src/scratch/n1_prefix_analysis.py [--latex]
"""
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _roots import OUTPUTS, SCRATCH  # noqa: E402
WSL = OUTPUTS / "ablation_prefix"


MODES = ["zero_prefix", "zero_latent", "shuffled", "prior", "oracle_ir"]
BUILD_MODES = ["prior", "oracle_ir", "shuffled"]
Z = 1.959963985  # 95%
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
    """Two-sided exact McNemar on discordant counts b (only A) and c (only B)."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def load_ir() -> dict:
    """{(modality, mode): {sample_id: per_sample_dict}} plus summaries."""
    per, summ = {}, {}
    for mode in MODES:
        for m in ("step", "point"):
            f = WSL / f"score_{m}_{mode}.json"
            if not f.is_file():
                continue
            d = json.loads(f.read_text(encoding="utf-8"))
            summ[(m, mode)] = d.get("summary", {})
            per[(m, mode)] = {r["sample_id"]: r for r in d.get("per_sample", [])}
    return {"per": per, "summary": summ}


def load_build() -> dict:
    out = {}
    for mode in BUILD_MODES:
        f = SCRATCH / f"exec_n1_step_{mode}" / "execution_rows.jsonl"
        if not f.is_file():
            continue
        rows = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
        out[mode] = {r["sample_id"]: r for r in rows}
    return out


def paired_boot(a: list[float], b: list[float]) -> tuple[float, float, float]:
    """Bootstrap CI for mean(a) - mean(b) over paired observations."""
    rng = random.Random(SEED)
    n = len(a)
    d = [x - y for x, y in zip(a, b)]
    point = sum(d) / n
    means = []
    for _ in range(BOOT):
        s = 0.0
        for _ in range(n):
            s += d[rng.randrange(n)]
        means.append(s / n)
    means.sort()
    return point, means[int(0.025 * BOOT)], means[int(0.975 * BOOT) - 1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--latex", action="store_true")
    args = ap.parse_args()

    ir = load_ir()
    build = load_build()

    meta = WSL / "run_metadata.json"
    if meta.is_file():
        print("=== run metadata ===")
        print(meta.read_text(encoding="utf-8").strip())

    # ---------------------------------------------------------------- IR level
    print("\n=== IR level (n=500 per cell, greedy, batch 16) ===")
    print(f"  {'mode':<12}{'modality':<9}{'IR cos':>9}{'Op-Set F1':>11}"
          f"{'Op-Seq LCS':>12}{'F1 median':>11}")
    for mode in MODES:
        for m in ("step", "point"):
            s = ir["summary"].get((m, mode))
            if not s:
                print(f"  {mode:<12}{m:<9}{'(missing)':>9}")
                continue
            print(f"  {mode:<12}{m:<9}{s['ir_cosine_mean']:>9.3f}"
                  f"{100*s['op_set_f1_mean']:>10.1f}%{100*s['op_seq_lcs_mean']:>11.1f}%"
                  f"{100*s['op_set_f1_median']:>10.1f}%")

    print("\n=== IR level, paired contrasts (bootstrap CI on the mean difference) ===")
    for m in ("step", "point"):
        for hi, lo in [("prior", "shuffled"), ("oracle_ir", "prior"),
                       ("zero_latent", "zero_prefix"), ("shuffled", "zero_prefix")]:
            A, B = ir["per"].get((m, hi)), ir["per"].get((m, lo))
            if not A or not B:
                continue
            ids = sorted(set(A) & set(B))
            for key, label in [("op_set_f1", "Op-Set F1"), ("ir_cosine", "IR cos")]:
                a = [A[i][key] for i in ids]
                b = [B[i][key] for i in ids]
                p, l, h = paired_boot(a, b)
                sig = "" if (l <= 0 <= h) else "  *"
                sc = 100 if key == "op_set_f1" else 1
                print(f"  {m:<6}{hi:>10} - {lo:<12}{label:<11}"
                      f"{sc*p:>+8.2f} [{sc*l:>+7.2f},{sc*h:>+7.2f}]  n={len(ids)}{sig}")

    # ------------------------------------------------------------- Build level
    if build:
        print("\n=== Build level, STEP only (n=500, no repair rules applied) ===")
        print(f"  {'mode':<12}{'syntax':>22}{'build':>22}{'STEP export':>22}")
        for mode in BUILD_MODES:
            rows = build.get(mode)
            if not rows:
                print(f"  {mode:<12}(missing)")
                continue
            n = len(rows)
            cells = []
            for key in ("syntax_ok", "build_ok", "step_export_ok"):
                k = sum(1 for r in rows.values() if r.get(key))
                p, lo, hi = wilson(k, n)
                cells.append(f"{p:.1f} [{lo:.1f},{hi:.1f}]")
            print(f"  {mode:<12}{cells[0]:>22}{cells[1]:>22}{cells[2]:>22}")

        print("\n=== Build level, paired McNemar (exact, two-sided) ===")
        for hi, lo in [("prior", "shuffled"), ("prior", "oracle_ir"),
                       ("oracle_ir", "shuffled")]:
            A, B = build.get(hi), build.get(lo)
            if not A or not B:
                continue
            ids = sorted(set(A) & set(B))
            b = sum(1 for i in ids if A[i]["build_ok"] and not B[i]["build_ok"])
            c = sum(1 for i in ids if B[i]["build_ok"] and not A[i]["build_ok"])
            both = sum(1 for i in ids if A[i]["build_ok"] and B[i]["build_ok"])
            neither = len(ids) - both - b - c
            p = mcnemar_exact(b, c)
            verdict = "DIFFERENT" if p < 0.05 else "not separable"
            print(f"  {hi:>10} vs {lo:<12} n={len(ids)}  both={both} neither={neither} "
                  f"only-{hi[:5]}={b} only-{lo[:5]}={c}  p={p:.4f}  {verdict}")

        # The disagreement between the two levels is the finding, so quantify it
        # directly: among rows every mode builds, how often is the plan even right?
        print("\n=== the two levels disagree: Build is blind to plan content ===")
        ids = sorted(set.intersection(*(set(build[m]) for m in BUILD_MODES)))
        pri, shu = ir["per"].get(("step", "prior"), {}), ir["per"].get(("step", "shuffled"), {})
        both_build = [i for i in ids
                      if build["prior"][i]["build_ok"] and build["shuffled"][i]["build_ok"]]
        if pri and shu and both_build:
            bi = [i for i in both_build if i in pri and i in shu]
            fp = sum(pri[i]["op_set_f1"] for i in bi) / len(bi)
            fs = sum(shu[i]["op_set_f1"] for i in bi) / len(bi)
            exact_p = sum(1 for i in bi if pri[i]["op_set_f1"] > 0.999)
            exact_s = sum(1 for i in bi if shu[i]["op_set_f1"] > 0.999)
            print(f"  rows that build under BOTH prior and shuffled: {len(bi)}")
            print(f"    mean Op-Set F1   prior {100*fp:.1f}%   shuffled {100*fs:.1f}%")
            print(f"    exact op-set match  prior {exact_p}/{len(bi)} "
                  f"({100*exact_p/len(bi):.1f}%)   shuffled {exact_s}/{len(bi)} "
                  f"({100*exact_s/len(bi):.1f}%)")
            print("  => a program can build perfectly while encoding the wrong part.")

    if args.latex:
        print("\n% ---- tab:ablation_prefix, generation level ----")
        rows_out = []
        for mode, disp in [("zero_prefix", "Zero prefix (bypass $\\Psi$)"),
                           ("zero_latent", "$\\Psi(\\mathbf{0})$"),
                           ("shuffled", "Shuffled prefix"),
                           ("prior", "Prior $\\pi_m$ (deployed)"),
                           ("oracle_ir", "Oracle IR encoder")]:
            cells = [disp]
            for m in ("step", "point"):
                s = ir["summary"].get((m, mode), {})
                cells += ["--" if not s else f"{s['ir_cosine_mean']:.3f}",
                          "--" if not s else f"{100*s['op_set_f1_mean']:.1f}",
                          "--" if not s else f"{100*s['op_seq_lcs_mean']:.1f}"]
            rows_out.append(" & ".join(cells) + r" \\")
        print("\n".join(rows_out))
        print("\n% ---- Build column, STEP ----")
        for mode in BUILD_MODES:
            rows = build.get(mode, {})
            if not rows:
                continue
            k = sum(1 for r in rows.values() if r.get("build_ok"))
            p, lo, hi = wilson(k, len(rows))
            print(f"% {mode}: {p:.1f} [{lo:.1f}, {hi:.1f}] (n={len(rows)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
