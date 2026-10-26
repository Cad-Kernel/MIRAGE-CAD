"""Table `tab:complexity`: join per-sample execution_rows.jsonl (build/step_export)
+ evaluation_rows.jsonl (syntax/op-F1/op-count-error) + manifest complexity_level,
cross-tabulate by L1-L4, for variant C (Generated IR only), Text and STEP queries.
No new generation/execution -- pure re-slicing of existing 500-sample results.
"""
import json
import statistics
import sys
from pathlib import Path


def read_jsonl(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def build(exec_path, eval_path, complexity_path):
    exec_rows = {r["sample_id"]: r for r in read_jsonl(exec_path)}
    eval_rows = {r["sample_id"]: r for r in read_jsonl(eval_path)}
    complexity = {r["sample_id"]: r["complexity_level"] for r in read_jsonl(complexity_path)}

    by_tier = {"L1": [], "L2": [], "L3": [], "L4": []}
    missing_complexity = 0
    for sid, e in exec_rows.items():
        tier = complexity.get(sid)
        if not tier:
            missing_complexity += 1
            continue
        ev = eval_rows.get(sid, {})
        by_tier.setdefault(tier, []).append({
            "syntax_ok": e.get("syntax_ok"),
            "build_ok": e.get("build_ok"),
            "syntax_valid": ev.get("syntax_valid"),
            "operation_f1": ev.get("operation_f1"),
            "operation_count_error": ev.get("operation_count_error"),
        })
    return by_tier, missing_complexity


def report(label, exec_path, eval_path, complexity_path):
    by_tier, missing = build(exec_path, eval_path, complexity_path)
    print(f"=== {label} ===")
    if missing:
        print(f"  WARNING: {missing} samples had no complexity_level match")
    for tier in ["L1", "L2", "L3", "L4"]:
        rows = by_tier.get(tier, [])
        n = len(rows)
        if n == 0:
            print(f"  {tier}: n=0 (no samples in this tier)")
            continue
        syntax_pct = 100 * sum(1 for r in rows if r["syntax_ok"]) / n
        build_pct = 100 * sum(1 for r in rows if r["build_ok"]) / n
        f1_vals = [r["operation_f1"] for r in rows if r["operation_f1"] is not None]
        cnt_err_vals = [r["operation_count_error"] for r in rows if r["operation_count_error"] is not None]
        mean_f1 = 100 * statistics.mean(f1_vals) if f1_vals else float("nan")
        mean_cnt_err = statistics.mean(cnt_err_vals) if cnt_err_vals else float("nan")
        print(f"  {tier}: n={n:3d}  Syntax={syntax_pct:5.1f}%  Op-F1={mean_f1:5.1f}%  "
              f"Build={build_pct:5.1f}%  Op-Cnt-Err={mean_cnt_err:5.2f}")


if __name__ == "__main__":
    report(
        "Text (variant C, 500-sample)",
        "scratch/exec_eval_text500/execution_rows.jsonl",
        "scratch/tab3_text_C_evaluation_rows.jsonl",
        "scratch/complexity_lookup.jsonl",
    )
    report(
        "STEP (variant C, 500-sample)",
        "scratch/exec_eval_stage4b_test500_p1a/execution_rows.jsonl",
        "scratch/tab3_step_C_evaluation_rows.jsonl",
        "scratch/complexity_lookup.jsonl",
    )
