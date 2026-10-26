#!/usr/bin/env python3
"""Register manual inference commands after CPU preflight; never load a model."""
from pathlib import Path
import sys

PACKAGE = Path(__file__).resolve().parents[1]
SOURCE = Path("__RUN_SOURCE_ROOT__")
IMPLEMENTATION = Path("__DEV_ROOT__/src/training_25k")
sys.path.insert(0, str(IMPLEMENTATION))
import cag_exposure_inference as s
from cag_exposure_policy_core import FrozenInputs, read_json, read_rows, record, reject_existing, require, value_sha, verify_record, write_json_new


def main():
    destination = PACKAGE / "execution/exposure_inference_manual_release_v1.json"
    reject_existing(destination)
    ctx = FrozenInputs(PACKAGE, SOURCE).guard()
    path = PACKAGE / "execution/exposure_inference_preflight_v1.json"
    pre = read_json(path)
    dependencies = s.checked_inputs(ctx)
    require(pre["version"] == s.VERSION and pre["status"] == "PASS_EVALUATION_ONLY_CPU_PREFLIGHT"
            and pre["dependencies"] == dependencies
            and pre["inference_fingerprint"] == s.inference_fingerprint(dependencies), "Stale/failed inference preflight")
    verify_record(pre["protected_training_inventory"])
    s.verify_protected(ctx, read_json(pre["protected_training_inventory"]["path"]))
    verify_record(pre["query_row_audit"])
    rows = read_rows(pre["query_row_audit"]["path"])
    require(len(rows) == pre["consumed_test_cache_entries_verified"] == 10000
            and value_sha(rows) == pre["ordered_plan_input_audit_sha256"]
            and pre["rows_per_modality"] == {m: 2500 for m in s.MODALITIES}, "Input preflight count/hash drift")
    for arm in ("A", "B"):
        reject_existing(s.output_path(ctx, arm))
    commands = {arm: "bash __DEV_ROOT__/src/training_25k/"
                     f"cag_run_exposure_inference.sh run --arm {arm} --confirm-generation" for arm in ("A", "B")}
    write_json_new(destination, {"version": s.VERSION, "created_utc": s.original.now(),
        "status": "A_INFERENCE_MANUAL_READY_B_GATED_ON_A_GENERATION_COMPLETE",
        "inference_fingerprint": pre["inference_fingerprint"], "preflight": record(path),
        "sources": s.own_sources(), "tests": dependencies["tests"], "registration_script": record(Path(__file__)),
        "working_directory": str(SOURCE), "code_checkout": str(IMPLEMENTATION.parent.parent),
        "checkout_head_inspected_from_Windows_git": "052392b6c7dc0305d04033b1f56d19b12fffb0a2",
        "source_commit_note": "New inference sources are uncommitted; source SHA256, not HEAD alone, identifies this execution",
        "commands": commands, "outputs": {a: str(s.output_path(ctx, a)) for a in ("A", "B")},
        "training_status": "COMPLETE_READ_ONLY", "prediction_status": "NOT_STARTED_BOTH_ARMS",
        "evaluation_status": "NOT_STARTED", "states_at_release": {"A": "NOT_STARTED", "B": "NOT_STARTED"},
        "scope": "One-arm greedy plan/code inference only; original2500 IDs x4 modalities; no training/gate/geometry",
        "A_release": "human-operated inference only; model/source/ID/cache guards rerun at startup",
        "B_release": "conditional on same-fingerprint A generation complete and all output hashes/IDs validated",
        "training_or_prediction_run_by_assistant": False, "GPU_model_loading_or_generation_smoke_test": "NOT_RUN",
        "runtime_code_prompt_gate": "Actual generated-plan prompts audited during inference without reference-aware packing",
        "on_partial_output": "Preserve outputs; no overwrite/deletion/implicit resume; inspect before a separate recovery decision"})
    print(f"A manual inference READY; B conditional; no training/prediction run: {destination}", flush=True)


if __name__ == "__main__":
    main()
