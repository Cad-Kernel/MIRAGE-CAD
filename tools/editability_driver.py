"""B7 driver: run editability_worker.py once per input row, tolerate hard crashes.

Runs under ORDINARY WINDOWS PYTHON (it needs only json/subprocess), not FllumaCLI.
Only the worker needs the kernel.

The reason for the split is in editability_worker.py's docstring: perturbing a
declared parameter can abort the process instead of raising, so a single in-process
loop loses the whole run. Here each row is a separate FllumaCLI invocation. If one
dies, the row is recorded as `hard_crash`, the parent moves on, and the partial
results the worker already flushed are kept.

`hard_crash` is a real outcome, not lost data: a dimension edit that takes the kernel
down is a stronger brittleness finding than one that merely fails to build, and it
belongs in the table.

Usage:
    python src/editability_driver.py \
        --input-jsonl   <programs> \
        --output-jsonl  <per-perturbation records> \
        --summary-json  <aggregate> \
        --flluma-cli    "C:\\...\\FllumaCLI.exe" \
        --worker        "\\\\wsl.localhost\\...\\src\\editability_worker.py" \
        [--deltas -0.25,-0.1,0.1,0.25] [--limit N] [--timeout 300]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

CATEGORIES = ["rebuilt_and_moved", "rebuilt_no_change", "rebuilt_change_unknown",
              "hard_crash"]


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--input-jsonl", type=Path, required=True)
    p.add_argument("--output-jsonl", type=Path, required=True)
    p.add_argument("--summary-json", type=Path, required=True)
    p.add_argument("--flluma-cli", required=True)
    p.add_argument("--worker", required=True)
    p.add_argument("--deltas", default="-0.25,-0.1,0.1,0.25")
    p.add_argument("--fingerprint-points", type=int, default=512)
    p.add_argument("--program-field", default="prediction")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--timeout", type=int, default=300, help="seconds per row")
    return p.parse_args(sys.argv[1:])


def main() -> int:
    args = parse_args()
    rows = read_jsonl(args.input_jsonl)
    if args.limit > 0:
        rows = rows[: args.limit]
    print(f"[driver] {len(rows)} rows, deltas {args.deltas}", flush=True)

    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    if args.output_jsonl.exists():
        args.output_jsonl.unlink()

    outcomes: Counter = Counter()
    per_delta: dict[str, Counter] = {}
    cov_vals, noise_vals = [], []
    n_valid = n_crashed_rows = n_skipped = 0
    total_declared = total_dead = 0
    clamped = 0

    tmpdir = Path(tempfile.mkdtemp(prefix="editprobe_"))
    try:
        for i, row in enumerate(rows, 1):
            sid = row.get("sample_id", f"row{i}")
            row_file = tmpdir / "row.json"
            row_out = tmpdir / "row_out.jsonl"
            row_file.write_text(json.dumps(row, ensure_ascii=False), encoding="utf-8")
            if row_out.exists():
                row_out.unlink()

            env = dict(os.environ)
            # `--deltas=` (equals form) is required, not optional: the value starts
            # with a minus sign, and shlex.split hands the worker's argparse a
            # leading-dash token which it reads as an option instead of a value.
            env["MIRAGE_STEP_FEATURE_ARGS"] = (
                f'--row-json "{row_file}" --output-jsonl "{row_out}" '
                f'--deltas="{args.deltas}" '
                f'--fingerprint-points {args.fingerprint_points} '
                f'--program-field "{args.program_field}"'
            )
            crashed = False
            try:
                proc = subprocess.run([args.flluma_cli, args.worker], env=env,
                                      capture_output=True, timeout=args.timeout)
                rc = proc.returncode
            except subprocess.TimeoutExpired:
                rc, crashed = -1, True
                print(f"[driver] {i}/{len(rows)} {sid}: TIMEOUT", flush=True)

            recs = read_jsonl(row_out) if row_out.exists() else []
            saw_done = any(r.get("kind") == "done" for r in recs)
            if not saw_done:
                crashed = True

            # Reconstruct this row's results from the worker's flushed stream.
            attempts = {}
            noise = None
            for r in recs:
                k = r.get("kind")
                if k == "row":
                    if r["baseline"].get("step_export_ok"):
                        n_valid += 1
                        cov_vals.append(r["coverage"]["parametric_coverage"])
                        total_declared += r["coverage"]["n_declared"]
                        total_dead += r["coverage"]["n_declared_unreferenced"]
                    with open(args.output_jsonl, "a", encoding="utf-8", newline="\n") as fh:
                        fh.write(json.dumps(r, ensure_ascii=False) + "\n")
                elif k == "noise":
                    noise = r["value"]
                    noise_vals.append(noise)
                elif k == "attempt":
                    attempts[(r["param"], r["delta"])] = r
                elif k == "result":
                    attempts.pop((r["param"], r["delta"]), None)
                    outcomes[r["outcome"]] += 1
                    clamped += int(bool(r.get("clamped_to_bound")))
                    per_delta.setdefault(f'{r["delta"]:+.2f}', Counter())[r["outcome"]] += 1
                    with open(args.output_jsonl, "a", encoding="utf-8", newline="\n") as fh:
                        fh.write(json.dumps(r, ensure_ascii=False) + "\n")
                elif k == "done" and r.get("skipped"):
                    n_skipped += 1

            # An announced attempt with no matching result is the perturbation that
            # killed the process. Record it rather than losing it.
            for (param, delta), a in attempts.items():
                outcomes["hard_crash"] += 1
                per_delta.setdefault(f"{delta:+.2f}", Counter())["hard_crash"] += 1
                rec = {"kind": "result", "sample_id": sid, "param": param,
                       "delta": delta, "from": a["from"], "to": a["to"],
                       "outcome": "hard_crash",
                       "error": "worker process died during this perturbation"}
                with open(args.output_jsonl, "a", encoding="utf-8", newline="\n") as fh:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

            if crashed:
                n_crashed_rows += 1
            done = sum(outcomes.values())
            print(f"[driver] {i}/{len(rows)} {sid}: rc={rc} "
                  f"{'CRASHED ' if crashed else ''}records={len(recs)} "
                  f"perturbations so far={done}", flush=True)
    finally:
        for f in tmpdir.glob("*"):
            try:
                f.unlink()
            except OSError:
                pass
        try:
            tmpdir.rmdir()
        except OSError:
            pass

    n = sum(outcomes.values())
    pct = lambda k: round(100.0 * outcomes.get(k, 0) / n, 2) if n else 0.0  # noqa: E731
    broke = sum(v for k, v in outcomes.items() if k.startswith("broke_"))
    summary = {
        "n_rows": len(rows),
        "n_baseline_kernel_valid": n_valid,
        "n_rows_skipped_baseline_invalid": n_skipped,
        "n_worker_processes_crashed": n_crashed_rows,
        "n_perturbations": n,
        "n_clamped_to_declared_bound": clamped,
        "outcomes": dict(outcomes),
        "outcomes_pct": {k: pct(k) for k in outcomes},
        "per_delta": {k: dict(v) for k, v in per_delta.items()},
        "editable_pct": pct("rebuilt_and_moved"),
        "silently_ignored_pct": pct("rebuilt_no_change"),
        "hard_crash_pct": pct("hard_crash"),
        "broke_pct": round(100.0 * broke / n, 2) if n else 0.0,
        "mean_parametric_coverage": round(sum(cov_vals) / len(cov_vals), 4) if cov_vals else 0.0,
        "mean_resample_noise_floor": round(sum(noise_vals) / len(noise_vals), 9) if noise_vals else 0.0,
        "max_resample_noise_floor": round(max(noise_vals), 9) if noise_vals else 0.0,
        "declared_params_total": total_declared,
        "declared_params_never_referenced": total_dead,
    }
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
