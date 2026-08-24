"""MIRAGE-CAD program execution validation via Flluma/OpenCASCADE.

Runs generated Flluma programs through the real CAD kernel to check:
  - syntax: ast.parse succeeds
  - exec: exec() runs and defines a `part` variable
  - build: `flluma.build(part)` (or `part.build()`) succeeds
  - solid_valid: `flluma.is_valid(solid)` passes
  - step_export: `flluma.export_step(solid, path)` succeeds

Must be run through FllumaCLI.exe (embedded Python with the native `flluma`
module) — the plain WSL/conda environment cannot import `flluma`.
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


def _flluma_namespace() -> dict[str, Any]:
    # `Parameters`/`Part`/primitives (box, cylinder, ...) are top-level attributes
    # of the native `flluma` module, not something generated programs import —
    # the Flluma harness injects them into the exec namespace instead.
    import flluma  # type: ignore

    return {name: getattr(flluma, name) for name in dir(flluma) if not name.startswith("_")}


def evaluate_one(code: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "syntax_ok": False,
        "exec_ok": False,
        "build_ok": False,
        "solid_valid": False,
        "step_export_ok": False,
        "error": "",
    }

    try:
        ast.parse(code)
    except SyntaxError as exc:
        result["error"] = f"SyntaxError: {exc}"
        return result
    result["syntax_ok"] = True

    part = None
    try:
        ns = _flluma_namespace()
        exec(compile(code, "<candidate>", "exec"), ns)  # noqa: S102
        part = ns.get("part")
        if part is None:
            result["error"] = "no `part` variable after execution"
            return result
    except Exception as exc:
        result["error"] = f"exec error: {exc}"
        return result
    result["exec_ok"] = True

    try:
        part.build()
    except Exception as exc:
        result["error"] = f"build error: {exc}"
        return result
    result["build_ok"] = True

    try:
        valid = part.validate()
        if valid is False:
            result["error"] = "part failed geometric validity check"
            return result
    except Exception as exc:
        result["error"] = f"validity check error: {exc}"
        return result
    result["solid_valid"] = True

    with tempfile.TemporaryDirectory() as tmpdir:
        step_out = os.path.join(tmpdir, "candidate.step")
        try:
            part.export_step(step_out)
        except Exception as exc:
            result["error"] = f"STEP export error: {exc}"
            return result
        result["step_export_ok"] = True

    return result


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Execute generated Flluma programs and validate build/export success.")
    p.add_argument("--input-jsonl", type=Path, required=True)
    p.add_argument("--output-jsonl", type=Path, required=True)
    p.add_argument("--summary-json", type=Path, required=True)
    p.add_argument("--code-field", default="prediction")
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

    # Incremental and resumable, because a generated program can take the whole process down
    # with it. One point-modality candidate raised an access violation (0xC0000005) inside
    # the kernel, and since results were held in memory and written once at the end, all 400
    # rows were lost -- and a plain re-run would walk into the same candidate and die again.
    #
    # So: append each row as it is scored, remember which sample_ids are already done, and
    # leave an in-flight marker before executing. A sample_id that appears in the marker file
    # but not in the results is one that killed the process, which is a legitimate outcome to
    # record for a paper whose primary metric is whether generated code runs -- not a reason
    # to lose the arm.
    inflight_path = output_jsonl.with_suffix(".inflight")
    done: dict[str, dict[str, Any]] = {}
    if output_jsonl.is_file():
        for line in output_jsonl.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                done[r.get("sample_id", "")] = r
    crashed = set()
    if inflight_path.is_file():
        for sid in inflight_path.read_text(encoding="utf-8").split():
            if sid and sid not in done:
                crashed.add(sid)
    if done or crashed:
        print(f"resuming: {len(done)} already scored, {len(crashed)} previously crashed the "
              f"kernel and will be recorded as such", flush=True)

    CRASH = {"syntax_ok": False, "exec_ok": False, "build_ok": False, "solid_valid": False,
             "step_export_ok": False,
             "error": "kernel access violation (0xC0000005) -- the process died on this "
                      "candidate; recorded on resume rather than re-attempted"}

    started = time.time()
    counts = {"syntax_ok": 0, "exec_ok": 0, "build_ok": 0, "solid_valid": 0, "step_export_ok": 0}
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with open(output_jsonl, "a", encoding="utf-8", newline="\n") as out:
        for i, row in enumerate(rows, start=1):
            sid = row.get("sample_id", "")
            if sid in done:
                res = done[sid]
            elif sid in crashed:
                res = dict(CRASH)
                out.write(json.dumps({"sample_id": sid, **res}, ensure_ascii=False) + "\n")
                out.flush()
                done[sid] = res
            else:
                with open(inflight_path, "a", encoding="utf-8", newline="\n") as fl:
                    fl.write(sid + "\n")
                    fl.flush()
                    os.fsync(fl.fileno())
                res = evaluate_one(row.get(args.code_field, ""))
                out.write(json.dumps({"sample_id": sid, **res}, ensure_ascii=False) + "\n")
                out.flush()
                done[sid] = res
            for k in counts:
                if res.get(k):
                    counts[k] += 1
            if i % 20 == 0 or i == len(rows):
                print(f"{i}/{len(rows)} " + " ".join(f"{k}={v}" for k, v in counts.items()),
                      flush=True)

    n_crash = sum(1 for r in done.values() if str(r.get("error", "")).startswith("kernel access"))
    if n_crash:
        print(f"NOTE: {n_crash} candidate(s) crashed the kernel outright", flush=True)
    n = max(len(rows), 1)
    summary = {
        "input_jsonl": str(input_jsonl),
        "rows": len(rows),
        "runtime_seconds": round(time.time() - started, 3),
        **{f"{k}_rate": v / n for k, v in counts.items()},
        **{f"{k}_count": v for k, v in counts.items()},
        "kernel_crash_count": n_crash,
    }
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    main()
