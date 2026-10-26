from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
        encoding="utf-8",
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--modality", default="step")
    ap.add_argument("--work", type=Path, default=Path("outputs/e1_observation_bypass"))
    ap.add_argument("--test-jsonl", type=Path, default=Path("data/25k/test.jsonl"))
    ap.add_argument("--expected-rows", type=int, default=500)
    args = ap.parse_args()

    targets = {r["sample_id"]: r for r in read_jsonl(args.test_jsonl)}
    manifest = {
        "purpose": "CAG frozen A1E/B2P seed-specific geometry input prep",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "modality": args.modality,
        "expected_rows": args.expected_rows,
        "test_jsonl": str(args.test_jsonl),
        "test_jsonl_sha256": sha256_file(args.test_jsonl),
        "arms": [],
    }

    for arm in ("A1E", "B2P"):
        src = args.work / f"gen_code_{args.modality}_{arm}_s{args.seed}.jsonl"
        dst = args.work / f"geom_input_{args.modality}_{arm}_s{args.seed}.jsonl"

        pred_rows = read_jsonl(src)
        if len(pred_rows) != args.expected_rows:
            raise RuntimeError(f"{src} has {len(pred_rows)} rows, expected {args.expected_rows}")

        out_rows = []
        empty_program = 0
        missing_target = 0
        no_point_path = 0

        for r in pred_rows:
            sample_id = r["sample_id"]
            t = targets.get(sample_id)
            if t is None:
                missing_target += 1
                continue

            code = r.get("prediction") or ""
            if not code.strip():
                empty_program += 1

            point_path = t.get("point_path", "")
            if not point_path:
                no_point_path += 1

            out_rows.append({
                "sample_id": sample_id,
                "modality": r.get("modality", args.modality),
                "point_path": point_path,
                "all_candidates": [code],
            })

        if len(out_rows) != args.expected_rows:
            raise RuntimeError(
                f"{arm}_s{args.seed}: wrote {len(out_rows)} rows, expected {args.expected_rows}; "
                f"missing_target={missing_target}"
            )
        if no_point_path:
            raise RuntimeError(f"{arm}_s{args.seed}: {no_point_path} rows lack point_path")

        write_jsonl(dst, out_rows)

        record = {
            "arm": arm,
            "prediction_file": str(src),
            "prediction_rows": len(pred_rows),
            "prediction_sha256": sha256_file(src),
            "geometry_input_file": str(dst),
            "geometry_input_rows": len(out_rows),
            "geometry_input_sha256": sha256_file(dst),
            "empty_program": empty_program,
            "missing_target": missing_target,
            "no_point_path": no_point_path,
        }
        manifest["arms"].append(record)

        print(f"{args.modality}_{arm}_s{args.seed}: {len(out_rows)} rows -> {dst}")

    manifest_path = args.work / f"cag_seed_{args.seed}_geometry_prep_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {manifest_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())