from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from flluma.api.evaluation import extract_step_brep_features


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


def as_windows_path(path: str | Path) -> Path:
    text = str(path).replace("\\", "/")
    if text.startswith("/mnt/") and len(text) > 6:
        drive = text[5].upper()
        rest = text[7:]
        return Path(f"{drive}:/{rest}")
    return Path(path)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Extract real STEP/B-Rep features with Flluma/OpenCASCADE.")
    p.add_argument("--input-jsonl", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--index-jsonl", type=Path, required=True)
    p.add_argument("--summary-json", type=Path, required=True)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--resume", action="store_true")
    p.add_argument("--fail-fast", action="store_true")

    env_args = os.environ.get("MIRAGE_STEP_FEATURE_ARGS") or os.environ.get("KCADGEN_STEP_FEATURE_ARGS")
    if env_args:
        return p.parse_args(shlex.split(env_args))
    return p.parse_args()


def main() -> int:
    args = parse_args()
    input_jsonl = as_windows_path(args.input_jsonl)
    output_dir = as_windows_path(args.output_dir)
    index_jsonl = as_windows_path(args.index_jsonl)
    summary_json = as_windows_path(args.summary_json)

    rows = read_jsonl(input_jsonl)
    if args.limit is not None:
        rows = rows[: args.limit]

    output_dir.mkdir(parents=True, exist_ok=True)
    index_rows: list[dict[str, Any]] = []
    started = time.time()
    success = 0
    failed = 0
    skipped = 0

    for i, row in enumerate(rows, start=1):
        sample_id = row["sample_id"]
        relpath = row.get("relpath", "")
        step_path = as_windows_path(row["step_path"])
        out_path = output_dir / f"{sample_id}.json"

        if args.resume and out_path.exists():
            skipped += 1
            index_row = dict(row)
            index_row.update(
                {
                    "step_path": str(step_path),
                    "step_feature_path": str(out_path),
                    "success": True,
                    "skipped": True,
                }
            )
            index_rows.append(index_row)
            continue

        record = {
            "sample_id": sample_id,
            "relpath": relpath,
            "step_path": str(step_path),
            "backend": "Flluma/OpenCASCADE extract_step_brep_features",
        }
        try:
            features = extract_step_brep_features(step_path)
            record["features"] = features
            record["success"] = bool(features.get("success"))
            if record["success"]:
                success += 1
            else:
                failed += 1
                record["error"] = features.get("error", "STEP feature extraction failed")
        except Exception as exc:
            failed += 1
            record["success"] = False
            record["error"] = str(exc)
            if args.fail_fast:
                raise

        out_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        index_row = dict(row)
        index_row.update(
            {
                "step_path": str(step_path),
                "step_feature_path": str(out_path),
                "success": bool(record["success"]),
                "error": record.get("error", ""),
            }
        )
        index_rows.append(index_row)

        if i % 100 == 0 or i == len(rows):
            elapsed = time.time() - started
            print(
                f"{i}/{len(rows)} success={success} failed={failed} skipped={skipped} "
                f"elapsed={elapsed:.1f}s"
            )

    write_jsonl(index_jsonl, index_rows)
    summary = {
        "input_jsonl": str(input_jsonl),
        "output_dir": str(output_dir),
        "index_jsonl": str(index_jsonl),
        "rows": len(rows),
        "success": success,
        "failed": failed,
        "skipped": skipped,
        "runtime_seconds": round(time.time() - started, 3),
    }
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    main()
