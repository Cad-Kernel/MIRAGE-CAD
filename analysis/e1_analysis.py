"""E1: paired comparison of the four observation-bypass conditions.

Reads the gate booleans that run_e1_execution.ps1 produced and answers the one question
the experiment exists for: does suppressing the query-derived evidence block change what
the code decoder can build?

Everything here is PAIRED on sample_id. The four conditions decode the same rows, so an
unpaired comparison would throw away the only thing that makes 500 rows enough.

McNemar is computed exactly, from the discordant pairs, with no normal approximation and
no continuity correction -- at these counts the exact test is cheap and the approximation
has no excuse. scipy is not assumed; the two-sided binomial tail is four lines.

Run:  python src/scratch/e1_analysis.py
      python src/scratch/e1_analysis.py --root <dir> --modalities step point
"""
from __future__ import annotations

import argparse
import json
from math import comb
from pathlib import Path

CONDITIONS = ["C3", "C2", "C1", "C0"]
LABEL = {
    "C3": "plan + observation   (deployed)",
    "C2": "plan only            (observation suppressed in both prompts)",
    "C1": "observation only     (plan suppressed)",
    "C0": "neither",
}
# The contrasts worth testing, and what each one licenses. Order matters: C3 vs C2 is the
# experiment; the rest bound it.
CONTRASTS = [
    ("C3", "C2", "what the observation adds on top of the plan"),
    ("C3", "C1", "what the plan adds on top of the observation"),
    ("C2", "C0", "the plan's worth with no observation present"),
    ("C1", "C0", "the observation's worth with no plan present"),
]


def load(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    out = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            sid = r.get("sample_id")
            if sid is not None:
                out[sid] = r
    return out


def mcnemar_exact(b01: int, b10: int) -> float:
    """Two-sided exact McNemar. b01 favours the first arm, b10 the second."""
    n = b01 + b10
    if n == 0:
        return 1.0
    k = min(b01, b10)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def wilson(k: int, n: int) -> tuple[float, float]:
    """Wilson score interval, the same one the paper's tables use."""
    if n == 0:
        return (0.0, 0.0)
    z = 1.959963984540054
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (100 * max(0.0, c - h), 100 * min(1.0, c + h))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path,
                    default=Path(r"C:\Workspace\Project\Paper\MIRAGE-V2\scratch"))
    ap.add_argument("--modalities", nargs="+", default=["step", "point", "text", "image"])
    ap.add_argument("--gate", default="build_ok",
                    choices=["syntax_ok", "exec_ok", "build_ok", "solid_valid", "step_export_ok"])
    args = ap.parse_args()

    for m in args.modalities:
        arms = {c: load(args.root / f"exec_e1_{m}_{c}" / "execution_rows.jsonl")
                for c in CONDITIONS}
        present = [c for c in CONDITIONS if arms[c]]
        if not present:
            print(f"\n{m}: nothing scored yet\n")
            continue

        # One row set for the whole modality, so every rate and every test below is over
        # the same parts. Reporting each arm on its own row set would let a missing row
        # move a rate without anything having changed.
        shared = set.intersection(*(set(arms[c]) for c in present))
        print(f"\n{'=' * 78}\n{m}   ({len(shared)} rows scored in all {len(present)} available arms)"
              f"   gate = {args.gate}\n{'=' * 78}")

        rates = {}
        for c in present:
            k = sum(1 for s in shared if arms[c][s].get(args.gate))
            rates[c] = k
            lo, hi = wilson(k, len(shared))
            print(f"  {c}  {100 * k / max(len(shared), 1):5.1f} %  [{lo:4.1f}, {hi:4.1f}]"
                  f"   {LABEL[c]}")

        print()
        for hi_c, lo_c, why in CONTRASTS:
            if hi_c not in present or lo_c not in present:
                continue
            b01 = sum(1 for s in shared
                      if arms[hi_c][s].get(args.gate) and not arms[lo_c][s].get(args.gate))
            b10 = sum(1 for s in shared
                      if not arms[hi_c][s].get(args.gate) and arms[lo_c][s].get(args.gate))
            p = mcnemar_exact(b01, b10)
            delta = 100 * (rates[hi_c] - rates[lo_c]) / max(len(shared), 1)
            verdict = "separable" if p < 0.05 else "NOT separable"
            print(f"  {hi_c} vs {lo_c}   {delta:+6.1f} pp   {b01:>4} : {b10:<4}"
                  f"  p = {p:.4g}   {verdict}")
            print(f"                {why}")

        print()
        print("  C2 is a LOWER bound: the code decoder was trained with the evidence block")
        print("  present, so suppressing it at inference is a distribution shift. C1 and C0")
        print("  carry the same caveat in the other direction and are not equivalent to a")
        print("  trained observation-only or plan-free model.")
        if m == "point":
            print()
            print("  point: the PLAN prompt carried only the constant 'Point cloud query.' to")
            print("  begin with, so C2's plan-side suppression removed no information. Its")
            print("  code-side suppression is the real manipulation here.")

    print()
    print("Repair was not applied, so none of these line up with the main tables.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
