#!/usr/bin/env python3
"""Create/verify the Review/04 preparation seal, without running training."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path

from prepare_exposure_policy import digest, file_record, json_bytes, read_rows, require


def referenced_files(value):
    if isinstance(value, dict):
        if {"path", "sha256", "bytes"} <= value.keys():
            yield value
        for child in value.values():
            yield from referenced_files(child)
    elif isinstance(value, list):
        for child in value:
            yield from referenced_files(child)


def verify_records(records):
    for record in records:
        path = Path(record["path"])
        require(path.is_file(), f"Sealed file missing: {path}")
        require(path.stat().st_size == record["bytes"] and digest(path) == record["sha256"],
                f"Sealed content changed: {path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--verify-resources", action="store_true", help="Also rehash all 150000 external resource files")
    ap.add_argument("--package-root", type=Path, default=Path(__file__).resolve().parent)
    args = ap.parse_args()
    root = args.package_root.resolve()
    seal_path = root / "07_frozen_package_seal.json"
    if args.verify:
        seal = json.loads(seal_path.read_text())
        verify_records(seal["files"])
        if args.verify_resources:
            inventory = read_rows(root / "manifests/resource_inventory.jsonl")
            records = [r for row in inventory for r in row["files"].values()]
            with ThreadPoolExecutor(max_workers=16) as pool:
                list(pool.map(lambda r: verify_records([r]), records))
            print(f"External resource verification PASS: {len(records)} file hashes")
        print(f"Frozen preparation seal PASS: {len(seal['files'])} files; no files changed; no training")
        return
    require(not args.verify_resources, "--verify-resources requires --verify")
    require(not seal_path.exists(), "Refusing to overwrite an existing preparation seal; use --verify")
    actuals = json.loads((root / "04_preflight_actuals.json").read_text())
    spec = json.loads((root / "05_execution_spec.json").read_text())
    require(actuals["preflight_status"] == "PASS_PREPARATION_ONLY", "Preparation has not passed")
    require(not actuals["training_started"] and spec["status"] == "FROZEN" and not spec["training_authorized"],
            "Invalid freeze/training state")
    script_hash = digest(root / "prepare_exposure_policy.py")
    for check in ("manifests", "resources", "checkpoints", "budget", "initialization", "spec"):
        record = actuals["checks"][check]
        require(record["status"] == "PASS" and record["verified_by_script_sha256"] == script_hash,
                f"Stale or failed check: {check}")
    require(digest(root / "05_execution_spec.json") == actuals["checks"]["spec"]["execution_spec"]["sha256"],
            "Execution spec not verified at its final frozen hash")
    paths = {Path(r["path"]) for r in referenced_files(actuals)}
    paths.update(root / name for name in (
        "01_frozen_protocol.md", "02_stage3_stage3b_mapping.md", "03_stage_mapping_actuals.json",
        "04_preflight_actuals.json", "05_execution_spec.json", "06_preflight_record.md",
        "collect_stage_mapping.py", "prepare_exposure_policy.py", "test_prepare_exposure_policy.py",
        "seal_preparation.py", "artifacts/initialization/initialization_actuals.json"))
    paths.update(p for p in (root / "manifests").iterdir() if p.is_file())
    require(not any(p.suffix == ".pending" for p in paths), "Incomplete pending manifest exists")
    verify_records(list(referenced_files(actuals)))
    record = {
        "purpose": "Immutable Review/04 preparation snapshot; not training authorization",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": "FROZEN", "training": "NOT_STARTED", "training_release": "NOT_READY",
        "preparation": "PASS", "files": [file_record(p) for p in sorted(paths)],
        "fast_verify_scope": "sealed package and referenced source/checkpoint/base files; resource inventory itself",
        "full_resource_revalidation": "--verify --verify-resources additionally checks all inventory file contents",
        "live_progress_files_excluded": ["README.md", "../training_experiments_roadmap.md"],
    }
    with seal_path.open("xb") as f:
        f.write(json_bytes(record))
    print(f"Frozen preparation seal created: {seal_path}; {len(record['files'])} files; no training")


if __name__ == "__main__":
    main()
