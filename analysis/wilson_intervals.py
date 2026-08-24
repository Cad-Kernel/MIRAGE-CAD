"""B11: Wilson score intervals for the reported build/export rates.

Every rate in this paper is a binomial proportion over a known denominator, so an
interval is available without any re-run -- the paper simply never reported one, which
Section 9 lists as an evidence gap. Wilson rather than normal-approximation because
several rates sit near 100% where the normal interval overshoots 1.

Reads the execution summaries directly so the counts cannot drift from the tables.

    python src/scratch/wilson_intervals.py [--latex]
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

SCRATCH = Path(r"C:\Workspace\Project\Paper\MIRAGE-V2\scratch")
Z = 1.959963985  # 95%


def wilson(k: int, n: int, z: float = Z) -> tuple[float, float, float]:
    """Return (point, lo, hi) as percentages."""
    if n == 0:
        return (float("nan"),) * 3
    p = k / n
    d = 1.0 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * p, 100 * max(0.0, c - h), 100 * min(1.0, c + h)


def load(d: Path) -> dict | None:
    f = d / "execution_summary.json"
    if not f.is_file():
        return None
    return json.loads(f.read_text(encoding="utf-8"))


def rate(s: dict, key: str) -> tuple[int, int] | None:
    """Pull (successes, total) for a gate from a summary, tolerating key variants."""
    n = s.get("rows") or s.get("total") or s.get("n") or s.get("count")
    if n is None:
        return None
    for k in (key, f"{key}_count", f"n_{key}"):
        if k in s and isinstance(s[k], int):
            return s[k], n
    # stored as a fraction
    for k in (f"{key}_rate", key):
        if k in s and isinstance(s[k], float):
            v = s[k]
            return int(round(v * n if v <= 1.0 else v * n / 100.0)), n
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--latex", action="store_true")
    args = ap.parse_args()

    groups = [
        ("tab:main_25k / tab:stage3b_ablation (Stage 3b, n=2500)",
         [(m, SCRATCH / f"exec_eval_25k_stage3b_{m}") for m in
          ("step", "point", "text", "image")]),
        ("tab:stage3b_ablation (original Stage 3, n=2500)",
         [(m, SCRATCH / f"exec_eval_25k_{m}") for m in
          ("step", "point", "text", "image")]),
        ("tab:compositional, variant C (n=2923)",
         [(m, SCRATCH / f"exec_ours_comp_{m}") for m in
          ("step", "point", "text", "image")]),
    ]

    for title, items in groups:
        print(f"\n=== {title} ===")
        print(f"  {'modality':<8} {'build':>22}   {'step export':>22}")
        for m, d in items:
            s = load(d)
            if s is None:
                print(f"  {m:<8} (no summary at {d.name})")
                continue
            out = []
            for key in ("build_ok", "exec_ok", "step_export_ok"):
                r = rate(s, key)
                if r is None:
                    continue
                k, n = r
                p, lo, hi = wilson(k, n)
                out.append((key, p, lo, hi, k, n))
            b = next((o for o in out if o[0] in ("build_ok", "exec_ok")), None)
            e = next((o for o in out if o[0] == "step_export_ok"), None)
            fb = f"{b[1]:.1f} [{b[2]:.1f},{b[3]:.1f}] n={b[5]}" if b else "--"
            fe = f"{e[1]:.1f} [{e[2]:.1f},{e[3]:.1f}]" if e else "--"
            print(f"  {m:<8} {fb:>22}   {fe:>22}")

    # The 100-part tables, where the interval matters most.
    print("\n=== n=100 tables: the interval is the point ===")
    for label, k, n in [("tab:geometry STEP N=1 build", 67, 100),
                        ("tab:geometry STEP N=10 build", 82, 100),
                        ("tab:geometry point N=1 build", 51, 100),
                        ("tab:geometry point N=10 build", 68, 100),
                        ("tab:ablation_stage4b GT-IR, Stage4", 95, 100),
                        ("tab:ablation_stage4b GT-IR, Stage4b", 89, 100),
                        ("tab:ablation_stage4b pred-IR, Stage4", 28, 100),
                        ("tab:ablation_stage4b pred-IR, Stage4b", 67, 100)]:
        p, lo, hi = wilson(k, n)
        print(f"  {label:<40} {p:5.1f} [{lo:.1f}, {hi:.1f}]  width {hi-lo:.1f}pp")

    print("\n=== does Stage 4b's predicted-IR gain survive its interval? ===")
    _, lo4, hi4 = wilson(28, 100)
    _, lo4b, hi4b = wilson(67, 100)
    print(f"  Stage 4 [{lo4:.1f},{hi4:.1f}] vs Stage 4b [{lo4b:.1f},{hi4b:.1f}] -> "
          f"{'DISJOINT, gain is real' if hi4 < lo4b else 'OVERLAP'}")
    print("\n=== does the Stage 3b STEP cost (-4.4pp) survive? ===")
    _, lo3, hi3 = wilson(int(round(0.743 * 2500)), 2500)
    _, lo3b, hi3b = wilson(int(round(0.700 * 2500)), 2500)
    print(f"  Stage 3 [{lo3:.1f},{hi3:.1f}] vs Stage 3b [{lo3b:.1f},{hi3b:.1f}] -> "
          f"{'DISJOINT, cost is real' if lo3 > hi3b else 'OVERLAP, not separable'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
