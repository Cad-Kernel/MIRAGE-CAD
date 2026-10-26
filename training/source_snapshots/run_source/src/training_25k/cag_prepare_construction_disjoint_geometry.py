#!/usr/bin/env python3
"""Prepare N=1 geometry input for construction-disjoint predictions."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--predictions", type=Path, required=True)
    p.add_argument("--test-jsonl", type=Path, default=Path("data/construction_disjoint_step_v1/test.jsonl"))
    p.add_argument("--output-jsonl", type=Path, required=True)
    p.add_argument("--manifest-json", type=Path, required=True)
    p.add_argument("--arm", required=True)
    p.add_argument("--expected-rows", type=int, default=500)
    return p.parse_args()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> int:
    args = parse_args()
    pred_rows = read_jsonl(args.predictions)
    test_by_id = {r["sample_id"]: r for r in read_jsonl(args.test_jsonl)}
    if len(pred_rows) != args.expected_rows:
        raise SystemExit(f"{args.predictions} has {len(pred_rows)} rows, expected {args.expected_rows}")

    out_rows = []
    missing_target = 0
    empty_program = 0
    no_point_path = 0
    for row in pred_rows:
        sid = row["sample_id"]
        target = test_by_id.get(sid)
        if target is None:
            missing_target += 1
            continue
        code = row.get("prediction") or ""
        if not code.strip():
            empty_program += 1
        point_path = row.get("point_path") or target.get("point_path", "")
        if not point_path:
            no_point_path += 1
        out_rows.append({
            "sample_id": sid,
            "modality": row.get("modality", "step"),
            "point_path": point_path,
            "all_candidates": [code],
        })

    if len(out_rows) != args.expected_rows:
        raise SystemExit(f"wrote {len(out_rows)} rows, expected {args.expected_rows}; missing_target={missing_target}")
    if no_point_path:
        raise SystemExit(f"{no_point_path} rows lack point_path")

    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with args.output_jsonl.open("w", encoding="utf-8", newline="\n") as f:
        for row in out_rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    manifest = {
        "purpose": "construction-disjoint geometry input prep",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "arm": args.arm,
        "expected_rows": args.expected_rows,
        "prediction_file": str(args.predictions),
        "prediction_rows": len(pred_rows),
        "prediction_sha256": sha256_file(args.predictions),
        "test_jsonl": str(args.test_jsonl),
        "test_jsonl_sha256": sha256_file(args.test_jsonl),
        "output_jsonl": str(args.output_jsonl),
        "output_rows": len(out_rows),
        "output_sha256": sha256_file(args.output_jsonl),
        "empty_program": empty_program,
        "missing_target": missing_target,
        "no_point_path": no_point_path,
    }
    args.manifest_json.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_json.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
