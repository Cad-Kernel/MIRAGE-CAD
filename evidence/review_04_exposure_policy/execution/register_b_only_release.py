#!/usr/bin/env python3
"""Register the tested manual B-only command, without starting training."""
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

PACKAGE = Path(__file__).resolve().parents[1]
SOURCE = Path("__RUN_SOURCE_ROOT__")
IMPLEMENTATION = Path("__DEV_ROOT__/src/training_25k")
sys.path.insert(0, str(IMPLEMENTATION))
import cag_exposure_policy_b_only as b
from cag_exposure_policy_core import FrozenInputs, read_json, record, reject_existing, require, verify_record, write_json_new


def main():
    destination = PACKAGE / "execution/b_only_manual_release_v2.json"
    reject_existing(destination)
    ctx = FrozenInputs(PACKAGE, SOURCE).guard()
    path = PACKAGE / "execution/b_only_preflight_v2.json"
    report = read_json(path)
    require(report["status"] == "PASS_B_ONLY_CPU_DRY_RUN" and report["version"] == b.VERSION,
            "Final B-only CPU preflight is not current/PASS")
    require(report["inputs"] == b.checked_inputs(ctx), "Current inputs differ from final dry-run")
    require(report["policy_lock"] == b.policy_lock(ctx, b.policy_identity(ctx), create=False), "Policy lock drift")
    verify_record(report["A_read_only_inventory"])
    a_root, b_root = b.arm_roots(ctx)
    b.assert_tree_unchanged(a_root, read_json(report["A_read_only_inventory"]["path"]))
    require(b.verify_plan_branch(ctx, "A") == report["A_branch"], "A branch drift")
    b.output_guards(ctx)
    checkout = IMPLEMENTATION.parents[1]
    commit = subprocess.run(["git", "-c", f"safe.directory={checkout}", "-C", str(checkout), "rev-parse", "HEAD"],
                            check=True, capture_output=True, text=True).stdout.strip()
    command = "bash __DEV_ROOT__/src/training_25k/cag_run_exposure_policy_b_only.sh run --confirm-training"
    write_json_new(destination, {"created_utc": datetime.now(timezone.utc).isoformat(), "version": b.VERSION,
        "status": "B_ONLY_MANUAL_COMMAND_RELEASED_NOT_EXECUTED", "command": command,
        "working_directory": str(SOURCE), "environment": "WSL Ubuntu / ai_dev",
        "parent_fingerprint": b.PARENT, "amendment_fingerprint": b.AMENDMENT,
        "policy_lock": report["policy_lock"], "preflight": record(path),
        "contract_tests": report["inputs"]["tests"], "sources": b.own_sources(),
        "canonical_code_checkout": str(checkout), "checkout_base_commit": commit,
        "checkout_note": "New uncommitted execution files are identified by source SHA256, not by base commit alone",
        "registration_script": record(Path(__file__)), "allowed_sequence": list(b.SEQUENCE),
        "A_read_only_inventory": report["A_read_only_inventory"], "A_branch": report["A_branch"],
        "B_output": str(b_root), "B_state_at_release": "NOT_STARTED", "actual_B_steps": None,
        "Stage4b_A": "NOT_STARTED", "Stage4b_B": "NOT_STARTED", "stage4b_training_released": False,
        "GPU_training_started_by_assistant": False, "A_plans_regenerated": False,
        "shared_cache_regenerated": False, "superseded_initial_dry_run": "b_only_preflight_v1.json",
        "next_after_B": "Actual A/B Stage4b paired preflight, then separate manual release only if PASS"})
    print(f"B-only manual release recorded: {destination}; no training started", flush=True)


if __name__ == "__main__":
    main()
