"""N-best execution-selection evaluation via Flluma/OpenCASCADE.

For each sample, evaluates every candidate in `all_candidates` through the
same 5 gates as evaluate_execution.py, then selects the candidate with the
highest validity level (ties broken by earliest index, matching
run_miragecad.py::select_best_candidate's partial-validity fallback).
Reports both the selected candidate's outcome and candidate-0's outcome
(the N=1/greedy baseline) so the lift from N-best selection is directly
comparable.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import shlex
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

_GATE_NAMES = ["syntax_ok", "exec_ok", "build_ok", "solid_valid", "step_export_ok"]


def as_windows_path(path: str | Path) -> Path:
    text = str(path).replace("\\", "/")
    if text.startswith("/mnt/") and len(text) > 6:
        drive = text[5].upper()
        rest = text[7:]
        return Path(f"{drive}:/{rest}")
    return Path(path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def flluma_exec_namespace() -> dict[str, Any]:
    import flluma  # type: ignore

    return {name: getattr(flluma, name) for name in dir(flluma) if not name.startswith("_")}


def evaluate_one(code: str) -> dict[str, Any]:
    result: dict[str, Any] = {k: False for k in _GATE_NAMES}
    result["validity"] = 0
    result["error"] = ""

    try:
        ast.parse(code)
    except SyntaxError as exc:
        result["error"] = f"SyntaxError: {exc}"
        return result
    result["syntax_ok"] = True
    result["validity"] = 1

    ns = flluma_exec_namespace()
    try:
        exec(compile(code, "<candidate>", "exec"), ns)  # noqa: S102
        part = ns.get("part")
        if part is None:
            result["error"] = "no `part` variable after execution"
            return result
    except Exception as exc:
        result["error"] = f"exec error: {exc}"
        return result
    result["exec_ok"] = True
    result["validity"] = 2

    try:
        part.build()
    except Exception as exc:
        result["error"] = f"build error: {exc}"
        return result
    result["build_ok"] = True
    result["validity"] = 3

    try:
        if part.validate() is False:
            result["error"] = "part failed geometric validity check"
            return result
    except Exception as exc:
        result["error"] = f"validity check error: {exc}"
        return result
    result["solid_valid"] = True
    result["validity"] = 4

    with tempfile.TemporaryDirectory() as tmpdir:
        step_out = os.path.join(tmpdir, "candidate.step")
        try:
            part.export_step(step_out)
        except Exception as exc:
            result["error"] = f"STEP export error: {exc}"
            return result
    result["step_export_ok"] = True
    result["validity"] = 5
    return result


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="N-best execution-selection evaluation.")
    p.add_argument("--input-jsonl", type=Path, required=True)
    p.add_argument("--output-jsonl", type=Path, required=True)
    p.add_argument("--summary-json", type=Path, required=True)
    p.add_argument("--limit", type=int, default=None)

    env_args = os.environ.get("MIRAGE_STEP_FEATURE_ARGS") or os.environ.get("KCADGEN_STEP_FEATURE_ARGS")
    if env_args:
        return p.parse_args(shlex.split(env_args))
    return p.parse_args()


def main() -> int:
    args = parse_args()
    input_jsonl = as_windows_path(args.input_jsonl)
    output_jsonl = as_windows_path(args.output_jsonl)
    summary_json = as_windows_path(args.summary_json)

    rows = read_jsonl(input_jsonl)
    if args.limit is not None:
        rows = rows[: args.limit]

    out_rows: list[dict[str, Any]] = []
    started = time.time()
    n_candidate0_exec_ok = 0
    n_selected_exec_ok = 0
    n_improved = 0  # candidate 0 failed but selection found a working candidate

    for i, row in enumerate(rows, start=1):
        candidates = row["all_candidates"]
        cand_results = [evaluate_one(c) for c in candidates]
        best_idx = max(range(len(cand_results)), key=lambda k: cand_results[k]["validity"])

        cand0_ok = cand_results[0]["exec_ok"]
        best_ok = cand_results[best_idx]["exec_ok"]
        n_candidate0_exec_ok += int(cand0_ok)
        n_selected_exec_ok += int(best_ok)
        if best_ok and not cand0_ok:
            n_improved += 1

        out_rows.append({
            "sample_id": row.get("sample_id", ""),
            "n_candidates": len(candidates),
            "candidate0_exec_ok": cand0_ok,
            "selected_idx": best_idx,
            "selected_exec_ok": best_ok,
            "candidate_results": cand_results,
        })
        if i % 10 == 0 or i == len(rows):
            print(f"{i}/{len(rows)} cand0_ok={n_candidate0_exec_ok} selected_ok={n_selected_exec_ok}", flush=True)

    write_jsonl(output_jsonl, out_rows)
    n = max(len(rows), 1)
    summary = {
        "input_jsonl": str(input_jsonl),
        "rows": len(rows),
        "runtime_seconds": round(time.time() - started, 3),
        "candidate0_exec_ok_rate": n_candidate0_exec_ok / n,
        "selected_exec_ok_rate": n_selected_exec_ok / n,
        "candidate0_exec_ok_count": n_candidate0_exec_ok,
        "selected_exec_ok_count": n_selected_exec_ok,
        "n_improved_by_selection": n_improved,
    }
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    main()
