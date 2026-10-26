#!/usr/bin/env python3
"""Record implementation readiness without authorizing or starting training."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import sys

PACKAGE = Path(__file__).resolve().parents[1]
SOURCE = Path("__RUN_SOURCE_ROOT__")
IMPLEMENTATION = Path("__DEV_ROOT__/src/training_25k")
sys.path.insert(0, str(IMPLEMENTATION))

from cag_exposure_policy_core import FrozenInputs, execution_hashes, read_json, record, require, write_json_new
from cag_exposure_policy import all_output_guards


def main():
    ctx = FrozenInputs(PACKAGE, SOURCE).guard()
    all_output_guards(ctx)
    candidates = sorted((PACKAGE / "execution").glob("test_result_*.json"))
    require(candidates, "No machine-readable contract test result")
    test_file = candidates[-1]
    tests = read_json(test_file)
    require(tests["status"] == "PASS" and tests["execution_hashes"] == execution_hashes(), "Tests are stale/failed")
    smokes = sorted((PACKAGE / "execution").glob("real_cpu_cache_smoke*.json"), key=lambda p: p.stat().st_mtime_ns)
    matching = [p for p in smokes if read_json(p)["fingerprint"] == ctx.fingerprint]
    require(matching, "No current real CPU encoding smoke result")
    smoke = matching[-1]
    require(read_json(smoke)["status"] == "PASS_SMOKE_ONLY", "Smoke failed")
    cases = ctx.required_cases()
    result = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "scientific_protocol": "FROZEN_UNCHANGED", "exposure_manifests": "FROZEN_UNCHANGED",
        "stage4b_roles": "FROZEN_UNCHANGED", "training_implementation": "IMPLEMENTED_CPU_CONTRACTS_PASS",
        "shared_cache": "NOT_BUILT", "final_real_cache_preflight": "BLOCKED_SHARED_CACHE_NOT_BUILT",
        "gpu_training": "NOT_AUTHORIZED_NOT_STARTED", "training_command_released": False,
        "execution_hashes": execution_hashes(), "fingerprint": ctx.fingerprint,
        "contract_tests": {"status": "PASS", "count": tests["tests_run"], "report": record(test_file)},
        "real_cpu_encoding_smoke": record(smoke),
        "full_cache_required_entries": len(cases),
        "cache_entries_by_split_modality": dict(Counter(f"{c['source_split']}/{c['modality']}" for c in cases)),
        "cache_output": str(ctx.cache_root), "all_future_training_paths_absent": True,
        "implementation_checkout": str(IMPLEMENTATION), "data_and_frozen_import_checkout": str(SOURCE),
        "runtime_claim_boundary": "No CUDA training tested; cache smoke and adapter-only save are CPU checks, not training",
        "next_operator_actions": ["cache --device cuda: frozen inference only", "preflight: real-cache CPU checks only"],
    }
    require(not ctx.cache_root.exists(), "This initial readiness record expects the full cache still absent")
    output = PACKAGE / "execution/implementation_status.json"
    write_json_new(output, result)
    print(f"Implementation recorded: {tests['tests_run']} tests PASS; {len(cases)} cache entries required; GPU training NOT AUTHORIZED")


if __name__ == "__main__":
    main()
