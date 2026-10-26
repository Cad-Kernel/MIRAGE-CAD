#!/usr/bin/env python3
"""Preflight and provenance records for Review/03 B0/B2 full-stack seeds."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_DATA = {
    "data/25k/train.jsonl": {
        "rows": 25000,
        "sha256": "991e0a6d811b5927d9316fed50c7cc09472719af1726b8c92017c3fbb86906ca",
    },
    "data/25k/val.jsonl": {
        "rows": 2500,
        "sha256": "4b76f8fec86f8fac7fbb9635542a924ccf3b91893115639d13ed79ada374a021",
    },
    "data/25k/test.jsonl": {
        "rows": 2500,
        "sha256": "248a032248d0d9e20b4474ee8adb705d74968a443b534cf51d96601eba0a019e",
    },
}

SCRIPT_PATHS = [
    "training_25k/cag_run_b0_b2_fullstack_seed.sh",
    "training_25k/cag_b0_b2_fullstack_actuals.py",
    "training_25k/cag_prepare_b0_b2_seed_geometry.py",
    "train_alignment.py",
    "train_latent_prior.py",
    "gen_scripts/train_soft_prefix_ir.py",
    "train_program_lora.py",
    "training_25k/scripts/gen_predicted_ir.py",
    "training_25k/scripts/gen_code_from_predicted_ir.py",
    "training_25k/scripts/build_stage4b_mix.py",
    "scratch/repair_face_extrude_alias.py",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def row_count(path: Path) -> int:
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def check_jsonl(path: Path, expected_rows: int | None = None) -> dict[str, Any]:
    exists = path.exists()
    rows = row_count(path) if exists else None
    record = {
        "path": str(path),
        "exists": exists,
        "rows": rows,
        "sha256": sha256_file(path) if exists else None,
    }
    if expected_rows is not None and rows != expected_rows:
        raise SystemExit(f"{path} has {rows} rows, expected {expected_rows}")
    return record


def data_records() -> dict[str, Any]:
    records: dict[str, Any] = {}
    for rel, expected in EXPECTED_DATA.items():
        path = Path(rel)
        if not path.exists():
            raise SystemExit(f"missing required data file: {rel}")
        rows = row_count(path)
        digest = sha256_file(path)
        if rows != expected["rows"]:
            raise SystemExit(f"{rel} has {rows} rows, expected {expected['rows']}")
        if digest != expected["sha256"]:
            raise SystemExit(f"{rel} sha256 mismatch: {digest} != {expected['sha256']}")
        records[rel] = {"rows": rows, "sha256": digest}
    return records


def script_records() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for rel in SCRIPT_PATHS:
        path = Path(rel)
        out[rel] = {
            "exists": path.exists(),
            "sha256": sha256_file(path) if path.exists() else None,
        }
    return out


def common_record(args: argparse.Namespace) -> dict[str, Any]:
    if args.seed not in {1, 2, 3, 4}:
        raise SystemExit(f"Review/03 frozen seeds are 1,2,3,4; got {args.seed}")
    if args.seed == 42:
        raise SystemExit("Seed 42 is the historical reference seed and is refused")
    return {
        "experiment": "Review/03 B0 vs B2 full-stack multi-seed replication",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "modality": args.modality,
        "limit": args.limit,
        "protocol": {
            "b0_scope": "full retrain of direct query->code no-plan condition",
            "b2_scope": "full retrain of deployed generated-plan pathway components",
            "b2_plan_canonicalization": "P1a face/extrude alias canonicalization before code generation",
            "program_code_repair": False,
            "checkpoint_selection": "final",
            "evaluation_slice": "data/25k/test.jsonl, first 2500 STEP rows",
            "run_policy": "one seed fully closed before the next",
        },
        "paths": {
            "base": args.base,
            "data_dir": args.data_dir,
            "work": args.work,
        },
        "data": data_records(),
        "scripts": script_records(),
    }


def write_record(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


def preflight(args: argparse.Namespace) -> None:
    payload = common_record(args)
    payload["status"] = "PREFLIGHT_PASS"
    payload["checks"] = {
        "seed_in_frozen_set": True,
        "data_hashes_match_frozen_25k": True,
        "output_paths_are_seed_scoped": all(f"s{args.seed}" in p for p in [args.base, args.data_dir, args.work]),
        "dry_run": args.dry_run,
    }
    write_record(Path(args.base) / f"cag_b0_b2_seed_{args.seed}_preflight.json", payload)


def post(args: argparse.Namespace) -> None:
    payload = common_record(args)
    base = Path(args.base)
    data_dir = Path(args.data_dir)
    work = Path(args.work)
    seed = args.seed
    modality = args.modality
    payload["status"] = "GENERATION_COMPLETE_NEEDS_GATE_AND_GEOMETRY"
    payload["outputs"] = {
        "b0_training_report": read_json(base / "b0_lora_code_noplan_25k" / "training_report.json"),
        "b2_stage3_report": read_json(base / "lora_ir_25k" / "soft_prefix_training_report.json"),
        "b2_stage3b_report": read_json(base / "lora_ir_25k_stage3b" / "soft_prefix_training_report.json"),
        "b2_stage4_report": read_json(base / "qwen25_coder_1_5b_program_25k" / "training_report.json"),
        "b2_stage4b_report": read_json(base / "qwen25_coder_1_5b_program_25k_stage4b" / "training_report.json"),
        "stage4b_mix": check_jsonl(data_dir / "train_stage4b_mix.jsonl"),
        "b0_prediction": check_jsonl(work / f"gen_{modality}_B0_s{seed}.jsonl", args.limit),
        "b2_predicted_ir_raw": check_jsonl(work / f"predicted_ir_test_{modality}_raw_s{seed}.jsonl", args.limit),
        "b2_predicted_ir_p1a": check_jsonl(work / f"predicted_ir_test_{modality}_p1a_s{seed}.jsonl", args.limit),
        "b2_prediction": check_jsonl(work / f"gen_{modality}_B2_s{seed}.jsonl", args.limit),
        "b0_geometry_input": check_jsonl(work / f"geom_input_{modality}_B0_s{seed}.jsonl", args.limit),
        "b2_geometry_input": check_jsonl(work / f"geom_input_{modality}_B2_s{seed}.jsonl", args.limit),
    }
    write_record(base / f"cag_b0_b2_seed_{seed}_actuals.json", payload)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=["preflight", "post"])
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--modality", default="step")
    p.add_argument("--limit", type=int, default=2500)
    p.add_argument("--base", required=True)
    p.add_argument("--data-dir", required=True)
    p.add_argument("--work", required=True)
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if args.mode == "preflight":
        preflight(args)
    else:
        post(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
