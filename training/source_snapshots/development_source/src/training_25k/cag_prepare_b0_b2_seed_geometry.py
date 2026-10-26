#!/usr/bin/env python3
"""Prepare N=1 geometry inputs for the Review/03 B0/B2 seed replication."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--modality", default="step")
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--test-jsonl", type=Path, default=Path("data/25k/test.jsonl"))
    p.add_argument("--expected-rows", type=int, default=2500)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    targets = {r["sample_id"]: r for r in read_jsonl(args.test_jsonl)}
    manifest: dict[str, Any] = {
        "purpose": "Review/03 B0/B2 full-stack seed geometry input prep",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "modality": args.modality,
        "expected_rows": args.expected_rows,
        "test_jsonl": str(args.test_jsonl),
        "test_jsonl_sha256": sha256_file(args.test_jsonl),
        "arms": [],
    }

    for arm in ("B0", "B2"):
        pred_path = args.work / f"gen_{args.modality}_{arm}_s{args.seed}.jsonl"
        geom_path = args.work / f"geom_input_{args.modality}_{arm}_s{args.seed}.jsonl"
        pred_rows = read_jsonl(pred_path)
        if len(pred_rows) != args.expected_rows:
            raise SystemExit(f"{pred_path} has {len(pred_rows)} rows, expected {args.expected_rows}")

        out_rows: list[dict[str, Any]] = []
        empty_program = 0
        missing_target = 0
        no_point_path = 0
        for row in pred_rows:
            sid = row["sample_id"]
            target = targets.get(sid)
            if target is None:
                missing_target += 1
                continue
            code = row.get("prediction") or ""
            if not code.strip():
                empty_program += 1
            point_path = target.get("point_path", "")
            if not point_path:
                no_point_path += 1
            out_rows.append({
                "sample_id": sid,
                "modality": row.get("modality", args.modality),
                "point_path": point_path,
                "all_candidates": [code],
            })

        if len(out_rows) != args.expected_rows:
            raise SystemExit(
                f"{arm}_s{args.seed}: wrote {len(out_rows)} rows, expected "
                f"{args.expected_rows}; missing_target={missing_target}"
            )
        if no_point_path:
            raise SystemExit(f"{arm}_s{args.seed}: {no_point_path} rows lack point_path")

        write_jsonl(geom_path, out_rows)
        record = {
            "arm": arm,
            "prediction_file": str(pred_path),
            "prediction_rows": len(pred_rows),
            "prediction_sha256": sha256_file(pred_path),
            "geometry_input_file": str(geom_path),
            "geometry_input_rows": len(out_rows),
            "geometry_input_sha256": sha256_file(geom_path),
            "empty_program": empty_program,
            "missing_target": missing_target,
            "no_point_path": no_point_path,
        }
        manifest["arms"].append(record)
        print(f"{args.modality}_{arm}_s{args.seed}: {len(out_rows)} rows -> {geom_path}")

    manifest_path = args.work / f"cag_b0_b2_seed_{args.seed}_geometry_prep_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
