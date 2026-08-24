"""Aggregate editability_probe.py output into the paper table (B7).

Usage:
    python3 src/scratch/aggregate_editability.py \
        --dirs  .../editability_25k_step_c .../editability_25k_step_direct \
        --labels "C: Generated IR" "A: Direct-NN-IR" \
        [--latex]

Reads `editability_summary.json` from each directory (falling back to recomputing
from `editability_rows.jsonl` if the summary is absent) and prints one row per
variant. `--latex` emits a tabular body ready to paste.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def load(d: Path) -> dict:
    s = d / "editability_summary.json"
    if s.is_file():
        return json.loads(s.read_text(encoding="utf-8"))
    rows_path = d / "editability_rows.jsonl"
    if not rows_path.is_file():
        raise SystemExit(f"neither summary nor rows found in {d}")
    outcomes: Counter = Counter()
    cov, n_valid = [], 0
    for line in rows_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("skipped"):
            continue
        n_valid += 1
        cov.append(r["coverage"]["parametric_coverage"])
        for p in r.get("perturbations", []):
            outcomes[p["outcome"]] += 1
    n = sum(outcomes.values())
    pct = lambda k: round(100.0 * outcomes.get(k, 0) / n, 2) if n else 0.0  # noqa: E731
    return {
        "n_baseline_kernel_valid": n_valid,
        "n_perturbations": n,
        "outcomes": dict(outcomes),
        "editable_pct": pct("rebuilt_and_moved"),
        "silently_ignored_pct": pct("rebuilt_no_change"),
        "broke_pct": round(sum(100.0 * v / n for k, v in outcomes.items()
                               if k.startswith("broke_")), 2) if n else 0.0,
        "mean_parametric_coverage": round(sum(cov) / len(cov), 4) if cov else 0.0,
    }


# Directory-name suffix -> paper label. Having this here rather than passed on the
# command line is deliberate: the labels contain spaces and colons, and the overnight
# orchestrator drives this through `wsl -e bash -lc`, where PowerShell will not pass
# quoted arguments through intact. Deriving them removes the need to quote anything.
LABEL_BY_SUFFIX = {
    "_c": "C: Generated IR",
    "_direct": "A: Direct-NN-IR",
    "_prior": "B: Prior-NN-IR",
}


def label_for(d: Path) -> str:
    name = d.name
    for suffix, label in LABEL_BY_SUFFIX.items():
        if name.endswith(suffix):
            return label
    return name


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="+", type=Path, required=True)
    ap.add_argument("--labels", nargs="+", default=None,
                    help="override the labels derived from directory names")
    ap.add_argument("--latex", action="store_true")
    args = ap.parse_args()

    labels = args.labels or [label_for(d) for d in args.dirs]
    if len(labels) != len(args.dirs):
        raise SystemExit("--labels must match --dirs in length")

    data = [(lab, load(d)) for lab, d in zip(labels, args.dirs)]

    if args.latex:
        print("% Editable / Ignored / Broke are percentages of perturbations;")
        print("% Coverage is the mean fraction of numeric literals reaching the")
        print("% kernel through a params[...] reference.")
        for lab, s in data:
            print(f"{lab:<20} & {s['n_baseline_kernel_valid']:>4} & "
                  f"{s['n_perturbations']:>5} & {s['editable_pct']:>5.1f} & "
                  f"{s['silently_ignored_pct']:>5.1f} & {s['broke_pct']:>5.1f} & "
                  f"{100*s['mean_parametric_coverage']:>5.1f} \\\\")
        return 0

    hdr = (f"{'Variant':<20} {'valid':>6} {'perturb':>8} {'Editable%':>10} "
           f"{'Ignored%':>9} {'Broke%':>8} {'Coverage%':>10}")
    print(hdr)
    print("-" * len(hdr))
    for lab, s in data:
        print(f"{lab:<20} {s['n_baseline_kernel_valid']:>6} {s['n_perturbations']:>8} "
              f"{s['editable_pct']:>9.1f}% {s['silently_ignored_pct']:>8.1f}% "
              f"{s['broke_pct']:>7.1f}% {100*s['mean_parametric_coverage']:>9.1f}%")
    print()
    print("outcome detail:")
    for lab, s in data:
        print(f"  {lab}: {s['outcomes']}")
    print()
    print("Reminder: 'Ignored' means the program rebuilt but its geometry did not")
    print("change -- a declared parameter that nothing consumes. Do not fold it into")
    print("the editable column; an edit that silently does nothing is its own failure.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
