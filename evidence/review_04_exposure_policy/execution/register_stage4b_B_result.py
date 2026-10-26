#!/usr/bin/env python3
"""Register the human-run B final and reverify the paired A/B training; never train."""
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
    destination = PACKAGE / "execution/stage4b_B_and_paired_training_completed_20261018.json"
    reject_existing(destination)
    print("Verifying both Stage4b finals and A's previously registered artifacts; CPU only", flush=True)
    ctx = FrozenInputs(PACKAGE, SOURCE).guard()
    preflight_path = PACKAGE / "execution/stage4b_execution_preflight_v1.json"
    preflight = read_json(preflight_path)
    dependencies, _ = s.checked_inputs(ctx)
    fingerprint = s.execution_fingerprint(dependencies)
    require(preflight["dependencies"] == dependencies
            and preflight["execution_fingerprint"] == fingerprint, "Execution source/input drift")
    verify_record(preflight["protected_inventory"])
    s.verify_protected(ctx, read_json(preflight["protected_inventory"]["path"]))
    a_registration_path = PACKAGE / "execution/stage4b_A_completed_20261018.json"
    a_registration = read_json(a_registration_path)
    require(a_registration["status"] == "STAGE4B_A_COMPLETE_VERIFIED_B_MANUAL_READY"
            and a_registration["execution_fingerprint"] == fingerprint,
            "Prior A result is missing or uses different execution")
    verify_record(a_registration["completion"])
    for item in a_registration["final_files"].values():
        verify_record(item)
    arms = {}
    for arm in ("A", "B"):
        completion = s.final_stage4b(ctx, arm, fingerprint)
        output = s.output_path(ctx, arm)
        state = read_json(output / "trainer_state.json")
        report = read_json(output / "training_report.json")
        complete = read_json(completion["path"])
        train = [row for row in state["log_history"] if "train_loss" in row][-1]
        evaluation = [row for row in state["log_history"] if "eval_loss" in row][-1]
        require(train["step"] == evaluation["step"] == state["global_step"] == 1182
                and state["epoch"] == train["epoch"] == evaluation["epoch"] == 3,
                f"{arm}: missing final native metrics")
        epochs = report["exposure_trace"]["epochs"]
        presentations = sum(row["presentations"] for row in epochs)
        targets = sum(row["supervised_target_tokens"] for row in epochs)
        require(presentations == 9450 and targets == 5696292, f"{arm}: actual full exposure mismatch")
        prediction_root = output.parent / "predictions"
        require(not any(prediction_root.glob("test_*")) and not any(prediction_root.glob("geom_input_*")),
                f"{arm}: unexpected evaluation prediction outputs; inspect before recording NOT_STARTED")
        arms[arm] = {"output": str(output), "completion": completion, "final_files": complete["files"],
                     "trainer_state": state, "training_report": report,
                     "native_final_train_metrics": train, "native_final_eval_metrics": evaluation,
                     "actual_presentations": presentations, "actual_full_supervised_target_tokens": targets,
                     "actual_input_tokens": sum(row["input_tokens"] for row in epochs),
                     "actual_padding_tokens": sum(row["padding_tokens"] for row in epochs)}
    require(arms["A"]["completion"] == a_registration["completion"]
            and arms["A"]["final_files"] == a_registration["final_files"]
            and arms["A"]["trainer_state"] == a_registration["trainer_state"]
            and arms["A"]["training_report"] == a_registration["training_report"],
            "A's registered final changed during or after B")
    require(arms["A"]["training_report"]["startup"] == arms["B"]["training_report"]["startup"]
            and arms["A"]["training_report"]["validation"] == arms["B"]["training_report"]["validation"],
            "Paired shared initialization/validation drift")
    actuals = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "BOTH_STAGE4B_COMPLETE_VERIFIED_NEEDS_FOUR_MODALITY_PREDICTION",
        "seed": 42, "execution_version": s.VERSION, "execution_fingerprint": fingerprint,
        "parent_fingerprint": s.PARENT, "amendment_fingerprint": s.AMENDMENT,
        "checks": {"original_frozen_seal": "PASS", "current_sources_and_dependencies": "PASS",
                   "both_final_artifacts_and_native_1182_steps": "PASS",
                   "same_shared_stage4_initialization_and_validation": "PASS",
                   "both_sampler_lr_and_full_target_traces": "PASS",
                   "protected_plan_branches_unchanged": "PASS", "A_registered_final_unchanged": "PASS",
                   "test_prediction_files_absent": "PASS"},
        "preflight": record(preflight_path), "A_prior_registration": record(a_registration_path),
        "dependencies": dependencies, "arms": arms,
        "code_checkout": str(IMPLEMENTATION.parent.parent), "source_data_checkout": str(SOURCE),
        "registration_script": record(Path(__file__)), "training_run_by": "human_operator",
        "training_started_by_this_audit": False, "prediction_or_evaluation_run_by_this_audit": False,
        "evaluation_status": "NOT_STARTED", "review04_status": "OPEN",
        "next_action": "Prepare and audit overlay-aware inference; original2500 IDs x4 modalities per arm, no retraining",
        "limitations": ["One seed exposure-policy diagnostic, not a multi-seed robustness claim",
                        "Teacher-forced losses do not establish generated CAD coverage or geometric superiority",
                        "No new model loading/forward/backward or full raw-resource/cache-tensor scan in this audit",
                        "A final-file identity checked independently; full A-subtree runtime checks were enforced by B's unchanged training wrapper"]}
    write_json_new(destination, actuals)
    print(f"PASS: A/B native1182 each, A final unchanged; no training/prediction/evaluation run. {destination}", flush=True)
    for arm, data in arms.items():
        print({"arm": arm, "train": data["native_final_train_metrics"],
               "validation": data["native_final_eval_metrics"],
               "actual_input_tokens": data["actual_input_tokens"],
               "actual_padding_tokens": data["actual_padding_tokens"],
               "final_adapter": data["final_files"]["adapter_model.safetensors"]}, flush=True)


if __name__ == "__main__":
    main()
