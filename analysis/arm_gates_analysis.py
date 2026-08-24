"""Paired gate comparison across arbitrary arms, on the same 500 rows.

WHY THIS EXISTS. A1E's gate numbers went into the paper -- Build 86.2 %, export 85.6 %, and the
paired 124 : 50 and 140 : 49 against the deployed arm -- computed ad hoc, with no script that
regenerates them. That is a reproducibility hole in figures already written down, and the
exposure-matched arm needs exactly the same treatment. So: one script, arms named on the command
line, and a self-check against the published counts before anything new is reported.

e1_analysis.py deliberately covers only E1's four observation conditions (C3/C2/C1/C0) and is
left alone; this handles the arms that sit outside that grid -- A1, A1E, B2P -- which are compared
against C3 and against each other rather than crossed.

EVERYTHING IS PAIRED ON sample_id. The arms decode the same rows, so a difference of rates
understates the evidence: exact McNemar on the discordant pairs is the test, and the marginal
rates are reported only for orientation.

GATE CHOICE. Build and STEP export are reported separately and neither is a proxy for the other.
Build says the kernel produced a solid; export says the solid survived being written out. They
came apart on this very arm -- A1E built 431 and exported 428 -- and a paper whose method section
warns against reading fidelity off a validity gate should not quietly collapse two gates either.
"""
from __future__ import annotations

import argparse
import json
from math import comb
from pathlib import Path

# Published counts, asserted before any new number is printed. If the pipeline drifts, this fails
# loudly on a known arm instead of silently re-baselining the comparison. Counts, not rates:
# a rate can round to the same value from a different denominator.
KNOWN = {
    "C3": {"build_ok": 357, "step_export_ok": 337},
    "A1E": {"build_ok": 431, "step_export_ok": 428},
    "A1": {"build_ok": 468, "step_export_ok": 468},
}

GATES = ("syntax_ok", "build_ok", "step_export_ok")


def load(root: Path, arm: str, modality: str) -> dict[str, dict]:
    p = root / f"exec_e1_{modality}_{arm}" / "execution_rows.jsonl"
    if not p.exists():
        return {}
    out: dict[str, dict] = {}
    with p.open(encoding="utf-8") as f:
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=r"C:\Workspace\Project\Paper\MIRAGE-V2\scratch")
    ap.add_argument("--modality", default="step")
    ap.add_argument("--arms", nargs="+", default=["C3", "A1E", "A1", "B2P"])
    ap.add_argument("--baseline", default="C3",
                    help="arm every other arm is paired against")
    ap.add_argument("--also-pair", nargs="*", default=["A1E:B2P"],
                    help="extra pairs as A:B; A1E:B2P is the budget- and exposure-matched one")
    args = ap.parse_args()
    root = Path(args.root)

    data = {a: load(root, a, args.modality) for a in args.arms}
    present = [a for a in args.arms if data[a]]
    for a in args.arms:
        if not data[a]:
            print(f"note: no gate rows for {a} -- skipped "
                  f"({root / f'exec_e1_{args.modality}_{a}'})")
    if not present:
        print("nothing to analyse")
        return 1

    # ---- the self-check, before anything new is reported --------------------------
    print("=== regression check against published counts ===")
    bad = 0
    for a in present:
        if a not in KNOWN:
            continue
        for g, want in KNOWN[a].items():
            got = sum(1 for r in data[a].values() if r.get(g))
            flag = "ok  " if got == want else "FAIL"
            bad += got != want
            print(f"  {flag} {a} {g}: {got} (published {want})")
    if bad:
        print(f"\n{bad} published count(s) did not reproduce. Something upstream changed; the")
        print("comparisons below would be against a different pipeline than the paper reports.")
        return 1
    print("  all published counts reproduce" if any(a in KNOWN for a in present)
          else "  no published arm among those requested")

    # ---- the row set must be identical, not merely the same size -----------------
    ids = {a: set(data[a]) for a in present}
    base = ids[present[0]]
    for a in present[1:]:
        if ids[a] != base:
            print(f"\nFAIL {a} scores a different row set than {present[0]} "
                  f"({len(ids[a] - base)} extra, {len(base - ids[a])} missing). Paired tests "
                  f"would silently compare different questions.")
            return 1
    common = sorted(base)
    print(f"\nall arms share the same {len(common)} rows, verified by sample_id")

    # ---- marginals ---------------------------------------------------------------
    print("\n=== marginal rates (orientation only; the paired tests below are the evidence) ===")
    head = "  arm    " + "".join(f"{g:>22s}" for g in GATES)
    print(head)
    for a in present:
        cells = []
        for g in GATES:
            k = sum(1 for s in common if data[a][s].get(g))
            lo, hi = wilson(k, len(common))
            cells.append(f"{100 * k / len(common):6.1f} [{lo:.1f},{hi:.1f}]")
        print(f"  {a:6s} " + "".join(f"{c:>22s}" for c in cells))

    # ---- paired -------------------------------------------------------------------
    pairs = [(args.baseline, a) for a in present if a != args.baseline]
    for spec in args.also_pair or []:
        if ":" not in spec:
            continue
        x, y = spec.split(":", 1)
        if x in data and y in data and data[x] and data[y] and (x, y) not in pairs:
            pairs.append((x, y))

    print("\n=== paired, exact McNemar on discordant pairs ===")
    for x, y in pairs:
        print(f"\n  {y} against {x}")
        for g in GATES:
            b01 = sum(1 for s in common if data[y][s].get(g) and not data[x][s].get(g))
            b10 = sum(1 for s in common if data[x][s].get(g) and not data[y][s].get(g))
            kx = sum(1 for s in common if data[x][s].get(g))
            ky = sum(1 for s in common if data[y][s].get(g))
            d = 100 * (ky - kx) / len(common)
            p = mcnemar_exact(b01, b10)
            verdict = "  (not distinguishable)" if p > 0.05 else ""
            print(f"    {g:16s} {d:+6.1f} pp   {y}-only {b01:3d} : {b10:3d} {x}-only   "
                  f"p = {p:.3g}{verdict}")

    print("\nNo repair, batched greedy, N = 1. Comparable to the arms in this directory, not to")
    print("the main tables. Rows are the FIRST 500 of the 2,500-row split, identical across arms.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
