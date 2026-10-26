#!/usr/bin/env python3
"""Read-only revalidation and manual-command release record; never trains."""
from datetime import datetime, timezone
from pathlib import Path
import sys

PACKAGE = Path(__file__).resolve().parents[1]
SOURCE = Path("__RUN_SOURCE_ROOT__")
IMPLEMENTATION = Path("__DEV_ROOT__/src/training_25k")
sys.path.insert(0, str(IMPLEMENTATION))

from cag_exposure_policy_core import (
    FrozenInputs, QueryCache, execution_hashes, read_json, record, require, verify_record, write_json_new,
)
from cag_exposure_policy import all_output_guards


def main():
    ctx = FrozenInputs(PACKAGE, SOURCE).guard()
    all_output_guards(ctx)
    implementation = read_json(PACKAGE / "execution/implementation_status.json")
    require(implementation["execution_hashes"] == execution_hashes(), "Implementation changed")
    require(implementation["contract_tests"]["status"] == "PASS", "Contract tests did not pass")
    verify_record(implementation["contract_tests"]["report"])
    preflight_file = PACKAGE / "execution/real_cache_preflight.json"
    preflight = read_json(preflight_file)
    require(preflight["status"] == "PASS" and preflight["fingerprint"] == ctx.fingerprint
            and preflight["execution_hashes"] == execution_hashes(), "Real-cache preflight is stale/failed")
    require(preflight["training_started"] is False and preflight["actual_global_steps"] is None,
            "Preflight unexpectedly claims trained results")
    verify_record(preflight["cache_completion"])
    verify_record(preflight["cache_index"])
    cache = QueryCache(ctx)
    require(cache.complete["entries"] == 83997 and cache.complete["training_started"] is False,
            "Unexpected full-cache count or training state")
    for arm in ("A", "B"):
        for phase, rows, steps in (("phase1", 75024, 4689), ("phase2", 8000, 500)):
            result = preflight["stages"][f"{arm}_{phase}"]
            require(result["rows"] == rows and result["planned_updates"] == steps
                    and result["all_cases_retain_target_tokens"], f"Plan preflight mismatch: {arm}/{phase}")
        result = preflight["stages"][f"{arm}_stage4b_contract"]
        require(result["rows"] == 3150 and result["epochs"] == 3 and result["planned_updates"] == 1182
                and result["actual_predicted_plan_gate"] == "REQUIRED_AFTER_FINAL_PHASE2_GENERATION",
                "Stage4b future actual-plan gate is missing")
    result = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "scientific_protocol": "FROZEN_UNCHANGED", "full_shared_cache": "COMPLETE_REVERIFIED",
        "shared_cache_entries": cache.complete["entries"], "real_cache_cpu_preflight": "PASS_REVERIFIED",
        "frozen_source_runtime_and_initialization_hashes": "PASS", "training_output_paths": "ALL_ABSENT",
        "execution_hashes": execution_hashes(), "fingerprint": ctx.fingerprint,
        "cache_complete": record(cache.root / "COMPLETE.json"), "cache_index": record(cache.root / "index.jsonl"),
        "preflight_report": record(preflight_file),
        "manual_training_command": "RELEASED_NOT_EXECUTED_BY_ASSISTANT",
        "training": "NOT_STARTED_AT_RELEASE", "trained_results": None,
        "command": "bash __DEV_ROOT__/src/training_25k/cag_run_exposure_policy.sh run --confirm-training",
        "working_directory": str(SOURCE), "environment": "WSL Ubuntu / ai_dev",
        "remaining_runtime_gates": [
            "Actual final global_step 4689 / 500 / 1182 in each arm",
            "Same-arm final LoRA/prefix at phase boundary, fresh optimizer/scheduler/RNG",
            "Exactly 945 generated predicted-role plans with final Phase2 provenance",
            "Actual generated-plan Stage4b tokenization retains supervised targets without dropping rows",
            "All actual epoch sample-order/LR hashes and final trainable-weight finiteness",
            "Same 2500 ordered evaluation IDs per modality; gate/geometry evaluation remains separate",
        ],
        "operator_policy": "Human runs the command; stop on any failure, no automatic resume or protocol change",
    }
    output = PACKAGE / "execution/training_release_actuals.json"
    write_json_new(output, result)
    print(f"Release verification PASS: {cache.complete['entries']} cached entries; all future training paths absent")
    print(f"Manual training command recorded, not executed: {output}")


if __name__ == "__main__":
    main()
