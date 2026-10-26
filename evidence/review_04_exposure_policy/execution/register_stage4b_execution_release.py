#!/usr/bin/env python3
"""Register Stage4b manual commands after real CPU preflight; never train."""
from datetime import datetime, timezone
from pathlib import Path
import sys

PACKAGE = Path(__file__).resolve().parents[1]
SOURCE = Path("__RUN_SOURCE_ROOT__")
IMPLEMENTATION = Path("__DEV_ROOT__/src/training_25k")
sys.path.insert(0, str(IMPLEMENTATION))
import cag_stage4b_execution as s
from cag_exposure_policy_core import FrozenInputs, read_json, record, reject_existing, require, verify_record, write_json_new


def main():
    destination = PACKAGE / "execution/stage4b_manual_release_v1.json"
    reject_existing(destination)
    ctx = FrozenInputs(PACKAGE, SOURCE).guard()
    path = PACKAGE / "execution/stage4b_execution_preflight_v1.json"
    pre = read_json(path)
    require(pre["status"] == "PASS_STAGE4B_EXECUTION_CPU_PREFLIGHT" and pre["version"] == s.VERSION, "CPU preflight not PASS/current")
    dependencies, paired = s.checked_inputs(ctx)
    require(pre["dependencies"] == dependencies and pre["execution_fingerprint"] == s.execution_fingerprint(dependencies),
            "Source/input drift after CPU preflight")
    verify_record(pre["protected_inventory"])
    s.verify_protected(ctx, read_json(pre["protected_inventory"]["path"]))
    for arm in ("A", "B"):
        reject_existing(s.output_path(ctx, arm))
        require(pre["arms"][arm]["cpu_dataloader"]["planned_updates"] == 1182
                and pre["arms"][arm]["dataset"]["rows"] == 3150
                and pre["arms"][arm]["dataset"]["EOS_preserved"] == "all", "Invalid Stage4b dataset/budget acceptance")
    commands = {arm: "bash __DEV_ROOT__/src/training_25k/cag_run_stage4b_only.sh "
                    f"run --arm {arm} --confirm-training" for arm in ("A", "B")}
    write_json_new(destination, {"created_utc": datetime.now(timezone.utc).isoformat(), "version": s.VERSION,
        "status": "STAGE4B_A_MANUAL_RELEASED_B_GATED_ON_A_FINAL", "execution_fingerprint": pre["execution_fingerprint"],
        "parent_fingerprint": s.PARENT, "amendment_fingerprint": s.AMENDMENT, "preflight": record(path),
        "sources": s.own_sources(), "contract_tests": dependencies["tests"], "registration_script": record(Path(__file__)),
        "policy_lock": dependencies["policy_lock"], "commands": commands, "working_directory": str(SOURCE),
        "code_checkout": str(IMPLEMENTATION.parent.parent), "environment": "WSL Ubuntu / ai_dev",
        "outputs": {arm: str(s.output_path(ctx, arm)) for arm in ("A", "B")},
        "actual_stage4b_global_steps": {"A": None, "B": None}, "states_at_release": {"A": "NOT_STARTED", "B": "NOT_STARTED"},
        "A_release": "human-operated one-arm Stage4b run only",
        "B_release": "conditional: same-version/fingerprint A overlay final and actual1182 steps verified at startup",
        "training_started_by_assistant": False, "plan_branches_retrained": False, "plans_regenerated": False,
        "evaluation_predictions_generated": False, "GPU_forward_or_gradient_smoke_test": "NOT_RUN_OPERATOR_STARTS_REAL_TRAINING",
        "runtime_raw_source_resources": "Full frozen source-resource byte checks run before model loading in each manual run",
        "future_inference_boundary": "Use overlay-aware final validation; original final_path/generate intentionally reject the new completion fingerprint"})
    print(f"Stage4b A manual command registered; B gated on A final: {destination}. No training started.", flush=True)


if __name__ == "__main__":
    main()
