#!/usr/bin/env python3
"""Verify and register the operator's completed Stage4b A; never train."""
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
    destination = PACKAGE / "execution/stage4b_A_completed_20261018.json"
    reject_existing(destination)
    print("Checking frozen inputs, current execution sources and completed plan branches; no training", flush=True)
    ctx = FrozenInputs(PACKAGE, SOURCE).guard()
    preflight_path = PACKAGE / "execution/stage4b_execution_preflight_v1.json"
    preflight = read_json(preflight_path)
    dependencies, _ = s.checked_inputs(ctx)
    fingerprint = s.execution_fingerprint(dependencies)
    require(preflight["dependencies"] == dependencies
            and preflight["execution_fingerprint"] == fingerprint,
            "Source/input drift after execution preflight")
    completion = s.final_stage4b(ctx, "A", fingerprint)
    verify_record(preflight["protected_inventory"])
    s.verify_protected(ctx, read_json(preflight["protected_inventory"]["path"]))
    b_output = s.run_guards(ctx, "B", fingerprint)
    output = s.output_path(ctx, "A")
    state = read_json(output / "trainer_state.json")
    report = read_json(output / "training_report.json")
    complete = read_json(completion["path"])
    history = state["log_history"]
    final_train = [row for row in history if "train_loss" in row][-1]
    final_eval = [row for row in history if "eval_loss" in row][-1]
    require(final_train["step"] == final_eval["step"] == state["global_step"] == 1182
            and state["epoch"] == final_train["epoch"] == final_eval["epoch"] == 3,
            "Missing final native training/evaluation metrics")
    epochs = report["exposure_trace"]["epochs"]
    require(sum(row["presentations"] for row in epochs) == 9450, "Actual presentation count mismatch")
    actuals = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "STAGE4B_A_COMPLETE_VERIFIED_B_MANUAL_READY",
        "arm": "A", "seed": 42, "execution_version": s.VERSION,
        "execution_fingerprint": fingerprint, "parent_fingerprint": s.PARENT,
        "amendment_fingerprint": s.AMENDMENT,
        "checks": {"original_frozen_seal": "PASS", "current_sources_and_dependencies": "PASS",
                   "final_artifacts_and_hashes": "PASS", "native_actual_1182_steps": "PASS",
                   "shared_stage4_initialization": "PASS", "paired_packing_identity": "PASS",
                   "actual_sampler_lr_and_full_target_trace": "PASS",
                   "protected_plan_branches_unchanged": "PASS", "B_stage4b_absent": "PASS",
                   "B_read_only_startup_guard": "PASS"},
        "preflight": record(preflight_path), "dependencies": dependencies,
        "completion": completion, "final_files": complete["files"],
        "trainer_state": state, "training_report": report,
        "native_final_train_metrics": final_train, "native_final_eval_metrics": final_eval,
        "actual_presentations": sum(row["presentations"] for row in epochs),
        "actual_full_supervised_target_tokens": sum(row["supervised_target_tokens"] for row in epochs),
        "actual_input_tokens": sum(row["input_tokens"] for row in epochs),
        "actual_padding_tokens": sum(row["padding_tokens"] for row in epochs),
        "code_checkout": str(IMPLEMENTATION.parent.parent), "source_data_checkout": str(SOURCE),
        "A_output": str(output), "B_output": str(b_output),
        "B_manual_command": "bash __DEV_ROOT__/src/training_25k/"
                            "cag_run_stage4b_only.sh run --arm B --confirm-training",
        "registration_script": record(Path(__file__)),
        "training_run_by": "human_operator", "training_started_by_this_audit": False,
        "B_training_started_by_this_audit": False, "evaluation_predictions_generated_by_this_audit": False,
        "audit_scope": "CPU file/lineage/native-trace verification; no model loading or forward/backward",
        "limitations": ["One seed exposure-policy diagnostic; B Stage4b remains not started at registration",
                        "Native teacher-forced losses are not free-generation CAD Build or geometry metrics",
                        "Raw resource files and all cache tensors are not rescanned by this result registration"]}
    write_json_new(destination, actuals)
    print(f"PASS: A final actual1182, 9450 presentations; B absent and manual startup gate valid. {destination}", flush=True)
    print({"train": final_train, "validation": final_eval,
           "actual_full_supervised_target_tokens": actuals["actual_full_supervised_target_tokens"],
           "actual_input_tokens": actuals["actual_input_tokens"],
           "actual_padding_tokens": actuals["actual_padding_tokens"],
           "final_adapter": complete["files"]["adapter_model.safetensors"]}, flush=True)


if __name__ == "__main__":
    main()
