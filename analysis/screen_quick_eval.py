"""Diff a new checkpoint's quick-eval execution results against the frozen
baseline (Stage4b + P0 + P1a) and apply the pass/fail screening criteria
agreed for Stage 4c-mini before committing to a full 500-sample run:

  - rescued > regressed
  - regressed <= 5 (out of the ~135-sample quick-eval set)
  - target-family rescued >= 3 (out of 40 target-family samples, baseline 4/40)
  - normal-sample regressed <= 3 (out of 80 normal samples)
  - (stretch goal, not required to pass) rescued >= regressed + 5

Any config that fails these should be discarded WITHOUT running the full
500-sample cycle.

Usage:
  python scratch/screen_quick_eval.py --new-exec-rows <FllumaCLI execution_rows.jsonl for the quick-eval subset>
"""
import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick-eval-set", type=Path, default=Path("data/smoke5k/quick_eval_rareop_set.jsonl"))
    ap.add_argument("--new-exec-rows", type=Path, required=True, help="execution_rows.jsonl from FllumaCLI, quick-eval subset only")
    args = ap.parse_args()

    baseline = {}
    for l in open(args.quick_eval_set, encoding="utf-8"):
        if not l.strip():
            continue
        row = json.loads(l)
        baseline[row["sample_id"]] = row

    new = {}
    for l in open(args.new_exec_rows, encoding="utf-8"):
        if not l.strip():
            continue
        row = json.loads(l)
        new[row["sample_id"]] = row

    missing = set(baseline) - set(new)
    if missing:
        print(f"WARNING: {len(missing)} quick-eval samples missing from new results: {sorted(missing)[:5]}...")

    rescued, regressed, unchanged_ok, unchanged_fail = [], [], [], []
    for sid, b in baseline.items():
        n = new.get(sid, {})
        b_ok, n_ok = b["baseline_success"], bool(n.get("exec_ok"))
        if not b_ok and n_ok:
            rescued.append(sid)
        elif b_ok and not n_ok:
            regressed.append(sid)
        elif b_ok and n_ok:
            unchanged_ok.append(sid)
        else:
            unchanged_fail.append(sid)

    target_ids = {sid for sid, b in baseline.items() if b["is_target_family"]}
    normal_ids = {sid for sid, b in baseline.items() if not b["rare_op_types"]}

    target_rescued = [s for s in rescued if s in target_ids]
    target_regressed = [s for s in regressed if s in target_ids]
    normal_rescued = [s for s in rescued if s in normal_ids]
    normal_regressed = [s for s in regressed if s in normal_ids]

    print(f"total quick-eval samples: {len(baseline)}")
    print(f"rescued: {len(rescued)}  {rescued}")
    print(f"regressed: {len(regressed)}  {regressed}")
    print(f"unchanged_ok: {len(unchanged_ok)}, unchanged_fail: {len(unchanged_fail)}")
    print()
    print(f"target-family (n={len(target_ids)}): rescued={len(target_rescued)} regressed={len(target_regressed)}")
    print(f"normal (n={len(normal_ids)}): rescued={len(normal_rescued)} regressed={len(normal_regressed)}")
    print()

    checks = {
        "rescued > regressed": len(rescued) > len(regressed),
        "regressed <= 5": len(regressed) <= 5,
        "target-family rescued >= 3": len(target_rescued) >= 3,
        "normal regressed <= 3": len(normal_regressed) <= 3,
    }
    stretch = len(rescued) >= len(regressed) + 5

    print("--- pass/fail screen ---")
    all_pass = True
    for name, ok in checks.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        all_pass = all_pass and ok
    print(f"  [{'YES' if stretch else 'no'}] stretch goal: rescued >= regressed + 5")
    print()
    if all_pass:
        print("VERDICT: PASS screen -- worth running the full 500-sample confirmation.")
    else:
        print("VERDICT: FAIL screen -- discard this config, do NOT run the full 500-sample cycle.")


if __name__ == "__main__":
    main()
