#!/usr/bin/env python3
"""Register human-run B and paired prediction completion; CPU-only verification."""
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
    destination = PACKAGE / "execution/exposure_prediction_B_and_paired_completed_20261021.json"
    inventory_path = PACKAGE / "execution/exposure_predictions_read_only_20261021.json"
    reject_existing(destination)
    reject_existing(inventory_path)
    os.chdir(SOURCE)
    print("Checking both generation completions, prior A output hashes and read-only training; CPU only", flush=True)
    ctx = FrozenInputs(PACKAGE, SOURCE).guard()
    preflight_path = PACKAGE / "execution/exposure_inference_preflight_v1.json"
    pre = read_json(preflight_path)
    dependencies = s.checked_inputs(ctx)
    fingerprint = s.inference_fingerprint(dependencies)
    require(pre["status"] == "PASS_EVALUATION_ONLY_CPU_PREFLIGHT"
            and pre["dependencies"] == dependencies and pre["inference_fingerprint"] == fingerprint,
            "Inference source/input/model drift")
    verify_record(pre["protected_training_inventory"])
    training_inventory = read_json(pre["protected_training_inventory"]["path"])
    s.verify_protected(ctx, training_inventory)
    completions = {arm: s.verify_generation(ctx, arm, fingerprint) for arm in ("A", "B")}
    a_path = PACKAGE / "execution/exposure_prediction_A_completed_20261019.json"
    a_result = read_json(a_path)
    require(a_result["status"] == "A_PREDICTION_COMPLETE_VERIFIED_B_MANUAL_READY"
            and a_result["inference_fingerprint"] == fingerprint and a_result["dependencies"] == dependencies
            and a_result["completion"] == completions["A"], "Prior A completion/provenance changed")
    verify_record(a_result["completion"])
    require(a_result["native_completion"] == read_json(completions["A"]["path"]), "A native completion changed")
    for item in a_result["native_completion"]["files"].values():
        verify_record(item)
    roots = {arm: s.output_path(ctx, arm) for arm in ("A", "B")}
    predictions_inventory = {arm: s.lineage.tree_snapshot(root) for arm, root in roots.items()}
    root, cases = roots["B"], s.validate_cases(ctx)
    complete, started = read_json(completions["B"]["path"]), read_json(root / "STARTED.json")
    require(started["inference_fingerprint"] == fingerprint and started["arm"] == "B"
            and started["preflight"] == record(preflight_path)
            and started["code_model_completion"] == dependencies["stage4b_finals"]["B"]
            and started["sources"] == s.own_sources() and started["training_allowed"] is False
            and started["reference_dependent_packing"] is False and started["implicit_resume"] is False,
            "Wrong B inference startup/provenance")
    plans, codes = read_rows(root / "test_plans.jsonl"), read_rows(root / "test_code.jsonl")
    plan_audits, code_audits = read_rows(root / "plan_input_audit.jsonl"), read_rows(root / "code_input_audit.jsonl")
    verify_record(pre["query_row_audit"])
    expected_audits = read_rows(pre["query_row_audit"]["path"])
    require(plan_audits == expected_audits == read_rows(roots["A"] / "plan_input_audit.jsonl")
            and len(plan_audits) == len(code_audits) == 10000, "Paired plan-input identity/count drift")
    model_dir = s.original.final_path(ctx, "B", "phase2")
    plan_hash, prefix_hash = sha(model_dir / "adapter_model.safetensors"), sha(model_dir / "soft_prefix.pt")
    code_hash = sha(s.training.output_path(ctx, "B") / "adapter_model.safetensors")
    for plan, code in zip(plans, codes):
        require(plan["plan_model_sha256"] == plan_hash and plan["plan_prefix_sha256"] == prefix_hash
                and plan["canonicalization"] == "P1a", "Not B's final same-arm plan model/prefix/P1a")
        require(all(code[k] == v for k, v in plan.items()) and code["code_model_sha256"] == code_hash
                and code["program_code_repair"] is False and isinstance(code["prediction"], str),
                "B code/plan/model/repair provenance mismatch")
    cache, tok = QueryCache(ctx, verify=False), s.tokenizer_for(ctx)
    for start, batch in s.original.modality_batches(cases, size=8):
        queries = [s.query_input(ctx, cache, case) for case in batch]
        prompts = [s.code_prompt(q, plan["predicted_ir"]) for q, plan in zip(queries, plans[start:start + len(batch)])]
        inputs = s.tokenize_batch(tok, prompts)
        require(s.input_audit(tok, prompts, inputs, batch, queries) == code_audits[start:start + len(batch)],
                f"B code input differs from independent query-only reconstruction at {start}")
        for offset, case in enumerate(batch):
            meta, _, _ = cache.load(case)
            code = codes[start + offset]
            require(code["reference"] == meta["reference_code"] and code["reference_ir"] == meta["reference_ir"],
                    "B evaluation reference mismatch")
        if start // 1000 != (start + len(batch)) // 1000:
            print(f"B actual code-prompt reconstruction {start + len(batch)}/10000; no model forward", flush=True)
    summaries = {}
    for modality in s.MODALITIES:
        selected = [i for i, case in enumerate(cases) if case["modality"] == modality]
        subset = [codes[i] for i in selected]
        require(read_rows(root / f"test_code_{modality}.jsonl") == subset, "B split export differs from full code")
        require(read_rows(roots["A"] / f"test_code_{modality}.jsonl")
                == [row for row in read_rows(roots["A"] / "test_code.jsonl") if row["modality"] == modality],
                "A split export mismatch")
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
        require(summaries[modality]["id_order_sha256"] == a_result["summaries"][modality]["id_order_sha256"],
                "Paired A/B evaluation order differs")
    require(complete["code_prompt_truncations"] == {m: row["code_prompt_truncations"] for m, row in summaries.items()},
            "B completion truncation counts mismatch")
    s.verify_protected(ctx, training_inventory)
    for arm, root in roots.items():
        s.lineage.assert_tree_unchanged(root, predictions_inventory[arm])
    write_json_new(inventory_path, predictions_inventory)
    evaluator_files = {name: record(IMPLEMENTATION.parent / "scripts" / name)
                       for name in ("evaluate_execution.ps1", "evaluate_geometry_nbest.ps1")}
    evaluator_files.update({name: record(SOURCE / name)
                            for name in ("evaluate_execution.py", "evaluate_geometry_nbest.py")})
    result = {
        "created_utc": s.original.now(), "status": "BOTH_PREDICTIONS_COMPLETE_VERIFIED_NEEDS_GATE_AND_GEOMETRY",
        "seed": 42, "inference_fingerprint": fingerprint,
        "checks": {"original_frozen_seal": "PASS", "inference_sources_models_dependencies": "PASS",
                   "both14_file_output_inventories_ids_geometry_inputs": "PASS", "prior_A_registered_files_unchanged": "PASS",
                   "both_complete_training_arm_snapshots_unchanged": "PASS", "paired_plan_input_audits_identical": "PASS",
                   "B_final_same_arm_model_and_exact_plan_code_linkage": "PASS",
                   "B10000_actual_code_inputs_reconstructed_without_reference_targets": "PASS",
                   "paired_per_modality_exports_and_order": "PASS"},
        "preflight": record(preflight_path), "dependencies": dependencies,
        "A_prior_registration": record(a_path), "completions": completions,
        "B_native_completion": complete, "B_startup": started, "registration_script": record(Path(__file__)),
        "predictions_read_only_inventory": record(inventory_path), "manual_evaluator_sources_at_release": evaluator_files,
        "summaries": {"A": a_result["summaries"], "B": summaries}, "rows_per_arm": 10000,
        "rows_per_modality_per_arm": 2500, "evaluation_cases_across_arms": 20000,
        "code_checkout": str(IMPLEMENTATION.parent.parent), "source_data_checkout": str(SOURCE),
        "prediction_roots": {arm: str(root) for arm, root in roots.items()},
        "B_model_hashes": {"plan_adapter": plan_hash, "plan_prefix": prefix_hash, "code_adapter": code_hash},
        "training_status": "COMPLETE_READ_ONLY", "prediction_status": "COMPLETE_BOTH_ARMS_VERIFIED",
        "gate_geometry_status": "NOT_RUN_BY_GENERATION_OR_THIS_AUDIT", "review04_status": "OPEN",
        "real_prediction_run_by": "human_operator", "training_prediction_or_evaluation_run_by_audit": False,
        "audit_scope": "CPU hash/file/input reconstruction with tokenizer; no model loading/forward",
        "limitations": ["Plan grammar/empty-output diagnostics are not CAD Syntax/Build/Scoreable/geometry metrics",
                        "A retrospective immutability check binds its prior registered completion and14 file hashes; B's unchanged wrapper additionally enforced the full A prediction-tree runtime snapshot",
                        "20,000 evaluation cases are not20,000 independent training replicates; one paired seed only",
                        "Evaluator files are recorded at pre-evaluation release, not executed or modified by this audit"]}
    write_json_new(destination, result)
    print(f"BOTH predictions VERIFIED; training and prior A files unchanged; no GPU/evaluation run: {destination}", flush=True)
    for modality, row in summaries.items():
        print({"arm": "B", "modality": modality, **{k: v for k, v in row.items() if not isinstance(v, dict)}}, flush=True)


if __name__ == "__main__":
    main()
