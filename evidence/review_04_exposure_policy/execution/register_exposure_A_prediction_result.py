#!/usr/bin/env python3
"""Independently verify/register human-run A test predictions; CPU audit only."""
from collections import Counter
import os
from pathlib import Path
import sys

PACKAGE = Path(__file__).resolve().parents[1]
SOURCE = Path("__RUN_SOURCE_ROOT__")
IMPLEMENTATION = Path("__DEV_ROOT__/src/training_25k")
sys.path.insert(0, str(IMPLEMENTATION))
import cag_exposure_inference as s
from cag_exposure_policy_core import FrozenInputs, QueryCache, read_json, read_rows, record, reject_existing, require, sha, value_sha, verify_record, write_json_new


def main():
    destination = PACKAGE / "execution/exposure_prediction_A_completed_20261019.json"
    reject_existing(destination)
    # Source JSONL resource paths are relative to the frozen data checkout,
    # matching the official generation wrapper and its main().
    os.chdir(SOURCE)
    print("Verifying A generation, final models and protected training snapshots; CPU only", flush=True)
    ctx = FrozenInputs(PACKAGE, SOURCE).guard()
    preflight_path = PACKAGE / "execution/exposure_inference_preflight_v1.json"
    pre = read_json(preflight_path)
    dependencies = s.checked_inputs(ctx)
    fingerprint = s.inference_fingerprint(dependencies)
    require(pre["status"] == "PASS_EVALUATION_ONLY_CPU_PREFLIGHT"
            and pre["dependencies"] == dependencies and pre["inference_fingerprint"] == fingerprint,
            "Source/input/model drift after inference preflight")
    verify_record(pre["protected_training_inventory"])
    s.verify_protected(ctx, read_json(pre["protected_training_inventory"]["path"]))
    completion = s.verify_generation(ctx, "A", fingerprint)
    b_output = s.run_guards(ctx, "B", fingerprint)
    root, cases = s.output_path(ctx, "A"), s.validate_cases(ctx)
    complete, started = read_json(completion["path"]), read_json(root / "STARTED.json")
    require(started["inference_fingerprint"] == fingerprint and started["arm"] == "A"
            and started["preflight"] == record(preflight_path)
            and started["code_model_completion"] == dependencies["stage4b_finals"]["A"]
            and started["sources"] == s.own_sources() and started["training_allowed"] is False
            and started["reference_dependent_packing"] is False and started["implicit_resume"] is False,
            "Wrong inference startup/provenance")
    plans, codes = read_rows(root / "test_plans.jsonl"), read_rows(root / "test_code.jsonl")
    plan_audits, code_audits = read_rows(root / "plan_input_audit.jsonl"), read_rows(root / "code_input_audit.jsonl")
    verify_record(pre["query_row_audit"])
    require(plan_audits == read_rows(pre["query_row_audit"]["path"])
            and len(plan_audits) == len(code_audits) == 10000, "Plan-input preflight identity/count drift")
    model_dir = s.original.final_path(ctx, "A", "phase2")
    plan_hash, prefix_hash = sha(model_dir / "adapter_model.safetensors"), sha(model_dir / "soft_prefix.pt")
    code_hash = sha(s.training.output_path(ctx, "A") / "adapter_model.safetensors")
    for plan, code in zip(plans, codes):
        require(plan["plan_model_sha256"] == plan_hash and plan["plan_prefix_sha256"] == prefix_hash
                and plan["canonicalization"] == "P1a", "Not the final same-arm plan model/prefix/P1a")
        require(all(code[k] == v for k, v in plan.items()) and code["code_model_sha256"] == code_hash
                and code["program_code_repair"] is False and isinstance(code["prediction"], str),
                "Code row does not retain its exact same-case generated plan/model/repair provenance")
    cache, tok = QueryCache(ctx, verify=False), s.tokenizer_for(ctx)
    # Reconstruct actual code prompts from generated plans, never reference code,
    # and compare every input-ID/mask hash with the recorded GPU-run inputs.
    for start, batch in s.original.modality_batches(cases, size=8):
        queries = [s.query_input(ctx, cache, case) for case in batch]
        prompts = [s.code_prompt(q, plan["predicted_ir"]) for q, plan in zip(queries, plans[start:start + len(batch)])]
        inputs = s.tokenize_batch(tok, prompts)
        require(s.input_audit(tok, prompts, inputs, batch, queries) == code_audits[start:start + len(batch)],
                f"Actual code prompt differs from query-only reconstruction at {start}")
        for offset, case in enumerate(batch):
            meta, _, _ = cache.load(case)
            code = codes[start + offset]
            require(code["reference"] == meta["reference_code"] and code["reference_ir"] == meta["reference_ir"],
                    "Evaluation reference mismatch")
        if start // 1000 != (start + len(batch)) // 1000:
            print(f"A actual code-prompt reconstruction {start + len(batch)}/10000; no model forward", flush=True)
    summaries = {}
    for modality in s.MODALITIES:
        selected = [i for i, case in enumerate(cases) if case["modality"] == modality]
        subset = [codes[i] for i in selected]
        require(read_rows(root / f"test_code_{modality}.jsonl") == subset, "Split export differs from full code output")
        summaries[modality] = {
            "rows": len(selected), "unique_sample_ids": len({codes[i]["sample_id"] for i in selected}),
            "id_order_sha256": value_sha([codes[i]["sample_id"] for i in selected]),
            "plan_grammar_valid": sum(bool(plans[i]["grammar"]["valid"]) for i in selected),
            "empty_plan": sum(not plans[i]["predicted_ir"].strip() for i in selected),
            "empty_code": sum(not codes[i]["prediction"].strip() for i in selected),
            "plan_text_changed_by_P1a": sum(plans[i]["predicted_ir"] != plans[i]["raw_predicted_ir"] for i in selected),
            "plan_prompt_truncations": sum(plan_audits[i]["prompt_truncated"] for i in selected),
            "code_prompt_truncations": sum(code_audits[i]["prompt_truncated"] for i in selected),
            "max_original_code_prompt_tokens": max(code_audits[i]["original_prompt_tokens"] for i in selected),
            "prediction_file": record(root / f"test_code_{modality}.jsonl"),
            "geometry_input": record(root / f"geom_input_{modality}.jsonl")}
    require(complete["code_prompt_truncations"] == {m: r["code_prompt_truncations"] for m, r in summaries.items()},
            "Completion truncation counts mismatch")
    s.verify_protected(ctx, read_json(pre["protected_training_inventory"]["path"]))
    result = {
        "created_utc": s.original.now(), "status": "A_PREDICTION_COMPLETE_VERIFIED_B_MANUAL_READY",
        "arm": "A", "seed": 42, "inference_fingerprint": fingerprint,
        "checks": {"original_frozen_seal": "PASS", "current_inference_sources_models_dependencies": "PASS",
                   "all14_output_hashes_and_fixed_ids": "PASS", "both_training_arm_snapshots_unchanged": "PASS",
                   "final_same_arm_plan_prefix_code_models": "PASS", "exact_plan_code_linkage": "PASS",
                   "full_and_per_modality_exports_match": "PASS", "geometry_inputs_match": "PASS",
                   "all10000_actual_code_inputs_reconstructed_without_reference_targets": "PASS",
                   "B_output_absent_and_generation_startup_gate": "PASS"},
        "preflight": record(preflight_path), "dependencies": dependencies, "completion": completion,
        "native_completion": complete, "startup": started, "registration_script": record(Path(__file__)),
        "summaries": summaries, "rows": len(codes), "predictions_by_modality": dict(Counter(c["modality"] for c in cases)),
        "code_checkout": str(IMPLEMENTATION.parent.parent), "source_data_checkout": str(SOURCE),
        "A_prediction_root": str(root), "B_prediction_root": str(b_output),
        "model_hashes": {"plan_adapter": plan_hash, "plan_prefix": prefix_hash, "code_adapter": code_hash},
        "B_manual_command": "bash __DEV_ROOT__/src/training_25k/"
                            "cag_run_exposure_inference.sh run --arm B --confirm-generation",
        "training_status": "COMPLETE_READ_ONLY", "B_prediction_status_at_audit": "NOT_STARTED",
        "gate_geometry_status": "NOT_RUN_BY_GENERATION_OR_THIS_AUDIT", "review04_status": "OPEN",
        "real_prediction_run_by": "human_operator", "training_prediction_or_evaluation_run_by_audit": False,
        "audit_scope": "CPU file/hash/native-input verification with actual tokenizer; no model loading/forward",
        "audit_working_directory": str(Path.cwd()),
        "audit_implementation_note": "Initial CPU prompt reconstruction was invoked outside SOURCE and stopped on relative STEP-resource evidence; corrected the registrar cwd only, without modifying generation/model artifacts",
        "limitations": ["Plan grammar and empty-output counts are not CAD Syntax/Build/Scoreable/geometry results",
                        "Code prompt truncation follows the frozen whole-prompt policy; no target-aware packing or row filtering",
                        "Single paired seed exposure-policy diagnostic; downstream evaluation pending"]}
    write_json_new(destination, result)
    print(f"A generation VERIFIED; B startup gate PASS; no GPU work run: {destination}", flush=True)
    for modality, row in summaries.items():
        print({"modality": modality, **{k: v for k, v in row.items() if not isinstance(v, dict)}}, flush=True)


if __name__ == "__main__":
    main()
