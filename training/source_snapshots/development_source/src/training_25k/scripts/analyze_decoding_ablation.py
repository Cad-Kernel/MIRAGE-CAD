"""Pre-execution diagnostic for the repetition_penalty decoding ablation
(docs/MIRAGE-CAD_experiment_results.md SS8.8): flags whether a generated
program is a degenerate repeated-literal generation (no real Flluma program
structure -- no part.xxx(...) call, no __all__ marker) vs. genuine code,
without needing a real FllumaCLI execution pass. Not a substitute for real
execution -- exec_ok/step_export_ok still require the evaluate_execution.ps1
step; this is just a fast first look at whether repetition_penalty reduced
the degenerate-generation rate before spending kernel-execution time on it.
"""
import argparse
import json
from pathlib import Path


def is_degenerate(prediction: str) -> bool:
    has_call = "(" in prediction and ")" in prediction and "part" in prediction.lower()
    has_all_marker = "__all__" in prediction
    return not (has_call and has_all_marker)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--files", nargs="+", required=True, type=Path)
    args = ap.parse_args()
    for path in args.files:
        if not path.exists():
            print(f"{path.name}: MISSING")
            continue
        rows = [json.loads(l) for l in open(path, encoding="utf-8")]
        n = len(rows)
        if n == 0:
            print(f"{path.name}: n=0 (empty)")
            continue
        degenerate = sum(1 for r in rows if is_degenerate(r["prediction"]))
        mean_len = sum(len(r["prediction"]) for r in rows) / n
        print(f"{path.name}: n={n} degenerate={degenerate} ({degenerate/n:.1%}) mean_len={mean_len:.0f}")


if __name__ == "__main__":
    main()
