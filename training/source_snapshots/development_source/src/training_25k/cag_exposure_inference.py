#!/usr/bin/env python3
"""Review/04 evaluation-only overlay. Default CPU preflight never loads a model."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import gc
import os
from pathlib import Path
import sys

import numpy as np
import torch

import cag_stage4b_execution as training
from cag_exposure_policy_core import (
    FrozenInputs, QueryCache, array_sha, encoded, load_module, read_json, read_rows,
    record, reject_existing, require, sha, value_sha, verify_record, write_json_new,
)

original = training.original
lineage = training.lineage
VERSION = "review04_evaluation_only_v1"
MODALITIES = ("step", "point", "text", "image")
EXPECTED_GENERATION = {
    "evaluation_manifest": "manifests/evaluation_shared.jsonl", "rows_per_modality": 2500,
    "modalities": list(MODALITIES), "batch_size": 8, "num_return_sequences": 1,
    "num_beams": 1, "do_sample": False, "max_length": 1536, "max_new_tokens": 1536,
    "point_plan_evidence": "off", "preserve_query_evidence_in_code_prompt": True,
    "program_code_repair": False, "P1a_plan_canonicalization": True, "retrieval": False,
}


def own_sources():
    root = Path(__file__).resolve().parent
    return {n: record(root / n) for n in ("cag_exposure_inference.py", "cag_run_exposure_inference.sh")}


def output_path(ctx, arm):
    require(arm in ("A", "B"), "Only inference arm A or B is supported")
    parent = ctx.source / ctx.spec["training_output_root"]
    root = parent / "evaluation_v1"
    require(not parent.is_symlink() and not root.is_symlink(), "Linked inference output parent")
    result = root / f"arm_{arm}"
    require(not result.is_symlink(), "Linked inference output")
    return result


def validate_cases(ctx):
    require(ctx.spec["generation"] == EXPECTED_GENERATION and ctx.spec["seed"] == 42,
            "Frozen decoding/evidence/repair policy drift")
    require(ctx.spec["point_sampling"]["seed"] == 42
            and ctx.spec["point_sampling"]["validation_and_test_mode"] == "fps", "Point policy drift")
    cases = ctx.manifests["evaluation_shared"]
    ids = [row["sample_id"] for row in ctx.splits["test"]]
    require(len(ids) == len(set(ids)) == 2500 and len(cases) == 10000, "Fixed test count/uniqueness mismatch")
    for i, case in enumerate(cases):
        source_row = i % 2500
        require(case == {"case_index": i, "source_row": source_row, "source_split": "test",
                         "sample_id": ids[source_row], "modality": MODALITIES[i // 2500]},
                f"Test IDs/order/modality mismatch at {i}")
        ctx.resolve(case)
    return cases


def checked_inputs(ctx):
    validate_cases(ctx)
    dependencies, _ = training.checked_inputs(ctx)
    fingerprint = training.execution_fingerprint(dependencies)
    registration_path = ctx.package / "execution/stage4b_B_and_paired_training_completed_20261018.json"
    registered = read_json(registration_path)
    require(registered["status"] == "BOTH_STAGE4B_COMPLETE_VERIFIED_NEEDS_FOUR_MODALITY_PREDICTION"
            and registered["execution_fingerprint"] == fingerprint
            and registered["dependencies"] == dependencies, "Paired trained-final registration drift")
    finals = {}
    for arm in ("A", "B"):
        finals[arm] = training.final_stage4b(ctx, arm, fingerprint)
        require(finals[arm] == registered["arms"][arm]["completion"], "Registered code final changed")
    tests_path = ctx.package / "execution/exposure_inference_contract_tests_v1.json"
    tests = read_json(tests_path)
    require(tests["status"] == "PASS" and tests["sources"] == own_sources(), "Current inference CPU tests required")
    verify_record(tests["test_source"])
    return {"training_dependencies": dependencies, "stage4b_finals": finals,
            "paired_training_registration": record(registration_path),
            "prompt_source": record(ctx.source / "miragecad/gen_prompts.py"),
            "prefix_source": record(ctx.source / "miragecad/soft_prefix.py"),
            "canonicalizer": record(ctx.source / "scratch/repair_face_extrude_alias.py"),
            "sources": own_sources(), "tests": record(tests_path),
            "generation": ctx.spec["generation"], "seed": 42}


def inference_fingerprint(dependencies):
    return value_sha({"version": VERSION, "dependencies": dependencies})


def protected_snapshot(ctx):
    return {arm: lineage.tree_snapshot(root) for arm, root in zip(("A", "B"), lineage.arm_roots(ctx))}


def verify_protected(ctx, expected):
    require(protected_snapshot(ctx) == expected, "Read-only training weights/plan predictions changed")


@dataclass(frozen=True)
class QueryInput:
    modality: str
    plan_prompt: str
    evidence: str
    latent: np.ndarray
    latent_sha256: str
    points_sha256: str


def query_input(ctx, cache, case):
    # Cache integrity includes stored references, but only query fields cross
    # this boundary. Reference text/length never reaches either model prompt.
    from miragecad.gen_prompts import build_ir_prompt, get_query_evidence

    meta, latent, points = cache.load(case)
    row, modality = ctx.resolve(case), case["modality"]
    evidence = get_query_evidence(row, modality, point_xyz=points if modality == "point" else None)
    require(meta["evidence"] == evidence, "Cached query evidence differs from the frozen source")
    planner_evidence = get_query_evidence({}, "point") if modality == "point" else evidence
    prompt = build_ir_prompt({}, modality, evidence_text=planner_evidence)
    require(meta["infer_prompt"] == prompt, "Cached plan prompt drift or hidden target dependence")
    return QueryInput(modality, prompt, evidence, latent, array_sha(latent), array_sha(points))


def code_prompt(query, predicted_plan):
    from miragecad.gen_prompts import build_program_prompt

    require(isinstance(predicted_plan, str), "Missing plan is not an empty prediction")
    return build_program_prompt({}, query.modality, predicted_plan, evidence_text=query.evidence)


def generation_kwargs(ctx, tok):
    g = ctx.spec["generation"]
    return {"max_new_tokens": g["max_new_tokens"], "do_sample": g["do_sample"],
            "num_beams": g["num_beams"], "num_return_sequences": g["num_return_sequences"],
            "pad_token_id": tok.eos_token_id}


def tokenize_batch(tok, prompts):
    require(tok.padding_side == "left" and tok.truncation_side == "right", "Inference padding/truncation drift")
    inputs = tok(prompts, truncation=True, max_length=1536, padding=True, return_tensors="pt")
    require(inputs["input_ids"].shape == inputs["attention_mask"].shape
            and inputs["input_ids"].shape[1] <= 1536, "Invalid inference batch")
    return inputs


def input_audit(tok, prompts, inputs, cases, queries):
    original_ids = tok(prompts, add_special_tokens=True, truncation=False)["input_ids"]
    rows = []
    for i, (case, query, ids) in enumerate(zip(cases, queries, original_ids)):
        actual = inputs["input_ids"][i][inputs["attention_mask"][i].bool()].tolist()
        require(actual == ids[:1536], "Whole-prompt inference truncation differs from the historical policy")
        rows.append({"case_index": case["case_index"], "sample_id": case["sample_id"], "modality": case["modality"],
                     "prompt_sha256": value_sha(prompts[i]), "original_prompt_tokens": len(ids),
                     "retained_prompt_tokens": len(actual), "prompt_truncated": len(ids) > 1536,
                     "input_ids_sha256": value_sha(inputs["input_ids"][i].tolist()),
                     "attention_mask_sha256": value_sha(inputs["attention_mask"][i].tolist()),
                     "latent_sha256": query.latent_sha256, "points_sha256": query.points_sha256})
    return rows


def validate_rows(rows, cases, arm):
    require(len(rows) == len(cases), "Prediction count mismatch; never drop failures")
    for row, case in zip(rows, cases):
        require(row["sample_id"] == case["sample_id"] and row["modality"] == case["modality"]
                and row["source_split"] == "test" and row["arm"] == arm, "Prediction IDs/order/arm mismatch")


def verify_generation(ctx, arm, fingerprint):
    root = output_path(ctx, arm)
    complete = read_json(root / "COMPLETE.json")
    require(complete["version"] == VERSION and complete["inference_fingerprint"] == fingerprint
            and complete["arm"] == arm and complete["rows"] == 10000
            and complete["program_code_repair"] is False, "Wrong inference completion")
    expected = {"STARTED.json", "test_plans.jsonl", "test_plans.p1a_log.json", "test_code.jsonl",
                "plan_input_audit.jsonl", "code_input_audit.jsonl"}
    expected.update(f"{prefix}_{m}.jsonl" for prefix in ("test_code", "geom_input") for m in MODALITIES)
    require(set(complete["files"]) == expected, "Missing or unexpected generated-file inventory")
    for name, item in complete["files"].items():
        require(Path(item["path"]).resolve() == (root / name).resolve(), "Generated file outside selected output")
        verify_record(item)
    cases = validate_cases(ctx)
    validate_rows(read_rows(root / "test_plans.jsonl"), cases, arm)
    validate_rows(read_rows(root / "test_code.jsonl"), cases, arm)
    for m in MODALITIES:
        subset = [case for case in cases if case["modality"] == m]
        predictions, geometry = read_rows(root / f"test_code_{m}.jsonl"), read_rows(root / f"geom_input_{m}.jsonl")
        validate_rows(predictions, subset, arm)
        require(len(geometry) == 2500 and all(
            geom == geometry_row(ctx, case, row) for geom, case, row in zip(geometry, subset, predictions)),
            "Geometry inputs differ from the fixed predictions/targets")
    return record(root / "COMPLETE.json")


def run_guards(ctx, arm, fingerprint):
    target = output_path(ctx, arm)
    reject_existing(target)
    if arm == "A":
        reject_existing(output_path(ctx, "B"))
    else:
        verify_generation(ctx, "A", fingerprint)
    return target


def tokenizer_for(ctx):
    tok = original.tokenizer_for(ctx)
    tok.padding_side = "left"
    require(tok.truncation_side == "right", "Historical inference uses right truncation")
    return tok


def preflight(ctx, report_path):
    report_path = lineage.audit_report_path(ctx, report_path)
    rows_path, weights_path = report_path.with_suffix(".rows.jsonl"), report_path.with_suffix(".weights.json")
    for path in (report_path, rows_path, weights_path, output_path(ctx, "A"), output_path(ctx, "B")):
        reject_existing(path)
    dependencies = checked_inputs(ctx)
    protected = protected_snapshot(ctx)
    cache, tok, cases = QueryCache(ctx, verify=False), tokenizer_for(ctx), validate_cases(ctx)
    rows, batch_counts = [], Counter()
    with rows_path.open("xb") as stream:
        for start, batch in original.modality_batches(cases, size=8):
            queries = [query_input(ctx, cache, c) for c in batch]
            prompts = [q.plan_prompt for q in queries]
            inputs = tokenize_batch(tok, prompts)
            audits = input_audit(tok, prompts, inputs, batch, queries)
            for row in audits:
                stream.write(encoded(row))
            rows.extend(audits)
            batch_counts[batch[0]["modality"]] += 1
            if start // 1000 != (start + len(batch)) // 1000:
                print(f"CPU query/cache/prompt preflight {start + len(batch)}/10000; no model forward", flush=True)
    # No generated test plans exist yet. Exercise the code-prompt tokenizer with
    # disclosed synthetic plans only; actual code prompts are audited at run time.
    probes = []
    for m in MODALITIES:
        q = query_input(ctx, cache, next(c for c in cases if c["modality"] == m))
        plans = ("", "INVALID PLAN", "FEATURE EXTRUDE\n" * 2000)
        prompts = [code_prompt(q, plan) for plan in plans]
        inputs = tokenize_batch(tok, prompts)
        probe_cases = [{"case_index": i, "sample_id": "SYNTHETIC_PROMPT_PROBE", "modality": m} for i in range(3)]
        probes.extend(input_audit(tok, prompts, inputs, probe_cases, [q] * 3))
    verify_protected(ctx, protected)
    write_json_new(weights_path, protected)
    write_json_new(report_path, {"version": VERSION, "created_utc": original.now(),
        "status": "PASS_EVALUATION_ONLY_CPU_PREFLIGHT", "inference_fingerprint": inference_fingerprint(dependencies),
        "dependencies": dependencies, "protected_training_inventory": record(weights_path), "query_row_audit": record(rows_path),
        "evaluation_manifest": record(ctx.package / "manifests/evaluation_shared.jsonl"),
        "rows": len(rows), "rows_per_modality": dict(Counter(r["modality"] for r in rows)),
        "batches_per_modality": dict(batch_counts), "ordered_plan_input_audit_sha256": value_sha(rows),
        "test_id_order_sha256": value_sha([r["sample_id"] for r in ctx.splits["test"]]),
        "plan_prompt_truncated_rows": sum(r["prompt_truncated"] for r in rows),
        "generation_kwargs": generation_kwargs(ctx, tok), "padding_side": tok.padding_side,
        "truncation_side": tok.truncation_side, "synthetic_code_prompt_probes": probes,
        "cache_index": record(cache.root / "index.jsonl"), "cache_complete": record(cache.root / "COMPLETE.json"),
        "consumed_test_cache_entries_verified": 10000, "point_sampling": ctx.spec["point_sampling"],
        "training_started": False, "gpu_model_loaded": False, "test_predictions_generated": False,
        "raw_resource_check": "Frozen resource inventory checked; all raw resources rehashed at manual run startup",
        "scope": "All test cache bytes/tensors/query evidence and plan prompts; synthetic code prompts, no model forward",
        "pending_runtime_gates": ["GPU model loading and generation", "Actual generated code-prompt audit",
                                  "10000 outputs per arm and final model/source immutability"]})
    print(f"Evaluation-only CPU preflight PASS: {report_path}; no training or prediction", flush=True)


def plan_row(case, arm, raw, canonicalizer, repairs, model_hash, prefix_hash):
    from miragecad.gen_prompts import validate_ir_grammar

    plan = canonicalizer.repair_ir_text(case["sample_id"], raw, repairs)
    return {"sample_id": case["sample_id"], "source_split": "test", "modality": case["modality"],
            "arm": arm, "predicted_ir": plan, "raw_predicted_ir": raw, "empty": not bool(plan.strip()),
            "grammar": validate_ir_grammar(plan), "canonicalization": "P1a",
            "plan_model_sha256": model_hash, "plan_prefix_sha256": prefix_hash}


def output_row(cache, case, plan, code, code_model_hash):
    # Evaluation references are attached only after generation, never to prompts.
    meta, _, _ = cache.load(case)
    return {**plan, "prediction": code, "reference": meta["reference_code"], "reference_ir": meta["reference_ir"],
            "code_model_sha256": code_model_hash, "program_code_repair": False}


def geometry_row(ctx, case, prediction):
    target = ctx.resolve(case)
    return {"sample_id": case["sample_id"], "modality": case["modality"], "point_path": target["point_path"],
            "all_candidates": [prediction["prediction"]]}


def export_modality_files(ctx, arm, root, cases):
    generated = read_rows(root / "test_code.jsonl")
    validate_rows(generated, cases, arm)
    files = {}
    for modality in MODALITIES:
        selected = [(case, row) for case, row in zip(cases, generated) if case["modality"] == modality]
        require(len(selected) == 2500, "Per-modality export must retain all cases")
        for prefix in ("test_code", "geom_input"):
            path = root / f"{prefix}_{modality}.jsonl"
            with path.open("xb") as stream:
                for case, row in selected:
                    stream.write(encoded(row if prefix == "test_code" else geometry_row(ctx, case, row)))
            files[path.name] = record(path)
    return files


def load_inference_model(ctx, directory):
    from transformers import AutoModelForCausalLM
    from peft import PeftModel

    base = AutoModelForCausalLM.from_pretrained(ctx.spec["model"]["id"], revision=ctx.spec["model"]["revision"],
        local_files_only=True, dtype=torch.bfloat16, device_map={"": 0})
    model = PeftModel.from_pretrained(base, directory, local_files_only=True, is_trainable=False).eval().requires_grad_(False)
    require(not model.training and not any(p.requires_grad for p in model.parameters()), "Inference model not frozen")
    return model


def plan_model_inputs(model, prefix, inputs, queries):
    embeddings = model.get_input_embeddings()(inputs["input_ids"])
    soft = prefix(torch.tensor(np.stack([q.latent for q in queries]), device=inputs["input_ids"].device)).to(embeddings.dtype)
    require(soft.shape == (len(queries), 4, embeddings.shape[-1]), "Frozen four-token soft-prefix shape mismatch")
    mask = torch.cat([torch.ones(len(queries), 4, dtype=inputs["attention_mask"].dtype,
                                device=inputs["attention_mask"].device), inputs["attention_mask"]], dim=1)
    return {"inputs_embeds": torch.cat([soft, embeddings], dim=1), "attention_mask": mask}


def generate_plans(ctx, arm, root, cache, tok, cases, expected_audits, verify_readonly):
    from miragecad.soft_prefix import load_soft_prefix_adapter

    plan_dir = original.final_path(ctx, arm, "phase2")
    model = load_inference_model(ctx, plan_dir)
    prefix = load_soft_prefix_adapter(plan_dir / "soft_prefix.pt", device="cuda").eval().requires_grad_(False)
    require(not any(p.requires_grad for p in prefix.parameters()), "Inference prefix not frozen")
    model_hash, prefix_hash = sha(plan_dir / "adapter_model.safetensors"), sha(plan_dir / "soft_prefix.pt")
    canonicalizer = load_module(ctx.source / "scratch/repair_face_extrude_alias.py", "review04_eval_p1a")
    repairs, outputs = [], []
    with torch.inference_mode(), (root / "test_plans.building").open("xb") as stream, \
            (root / "plan_input_audit.jsonl").open("xb") as audit_stream:
        for start, batch in original.modality_batches(cases, size=8):
            queries = [query_input(ctx, cache, c) for c in batch]
            prompts = [q.plan_prompt for q in queries]
            inputs = tokenize_batch(tok, prompts)
            audits = input_audit(tok, prompts, inputs, batch, queries)
            require(audits == expected_audits[start:start + len(batch)], "Run plan input differs from CPU preflight")
            for audit in audits:
                audit_stream.write(encoded(audit))
            inputs = inputs.to("cuda")
            sequences = model.generate(**plan_model_inputs(model, prefix, inputs, queries), **generation_kwargs(ctx, tok))
            require(len(sequences) == len(batch), "Plan generation dropped rows")
            for case, sequence in zip(batch, sequences):
                raw = tok.decode(sequence, skip_special_tokens=True).strip()
                row = plan_row(case, arm, raw, canonicalizer, repairs, model_hash, prefix_hash)
                outputs.append(row)
                stream.write(encoded(row))
            print(f"Arm {arm} {batch[0]['modality']} test plans {start + len(batch)}/10000", flush=True)
    validate_rows(outputs, cases, arm)
    (root / "test_plans.building").rename(root / "test_plans.jsonl")
    write_json_new(root / "test_plans.p1a_log.json", {"changes": repairs, "rows": len(outputs),
        "empty_retained": sum(row["empty"] for row in outputs),
        "invalid_retained": sum(not row["grammar"]["valid"] for row in outputs)})
    del model, prefix
    gc.collect()
    torch.cuda.empty_cache()
    verify_readonly()
    return outputs


def generate_codes(ctx, arm, root, cache, tok, cases, plans, verify_readonly):
    directory = training.output_path(ctx, arm)
    model_hash = sha(directory / "adapter_model.safetensors")
    model = load_inference_model(ctx, directory)
    counts = Counter()
    with torch.inference_mode(), (root / "test_code.building").open("xb") as stream, \
            (root / "code_input_audit.jsonl").open("xb") as audit_stream:
        for start, batch in original.modality_batches(cases, size=8):
            queries = [query_input(ctx, cache, c) for c in batch]
            current = plans[start:start + len(batch)]
            prompts = [code_prompt(q, p["predicted_ir"]) for q, p in zip(queries, current)]
            inputs = tokenize_batch(tok, prompts)
            for audit in input_audit(tok, prompts, inputs, batch, queries):
                audit_stream.write(encoded(audit))
                counts[audit["modality"]] += int(audit["prompt_truncated"])
            inputs = inputs.to("cuda")
            sequences = model.generate(**inputs, **generation_kwargs(ctx, tok))
            require(len(sequences) == len(batch), "Code generation dropped rows")
            for case, plan, sequence in zip(batch, current, sequences):
                code = tok.decode(sequence[inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
                stream.write(encoded(output_row(cache, case, plan, code, model_hash)))
            print(f"Arm {arm} {batch[0]['modality']} test code {start + len(batch)}/10000", flush=True)
    (root / "test_code.building").rename(root / "test_code.jsonl")
    del model
    gc.collect()
    torch.cuda.empty_cache()
    verify_readonly()
    return dict(counts)


def print_evaluation_commands(arm):
    print("\nGeneration only COMPLETE. Gate/geometry NOT RUN. Later run in Windows PowerShell:", flush=True)
    print('$Root = "__RUN_SOURCE_ROOT__"')
    print(f'$Pred = "$Root\\outputs\\exposure_policy_s42\\evaluation_v1\\arm_{arm}"')
    print('foreach ($m in @("step", "point", "text", "image")) {')
    print('  & "__DEV_ROOT__\\src\\scripts\\evaluate_execution.ps1" `')
    print('    -InputJsonl "$Pred\\test_code_$m.jsonl" `')
    print(f'    -OutputDir "__DEV_ROOT__\\scratch\\exec_r04_${{m}}_{arm}" -CodeField prediction')
    print('  & "__DEV_ROOT__\\src\\scripts\\evaluate_geometry_nbest.ps1" `')
    print('    -InputJsonl "$Pred\\geom_input_$m.jsonl" `')
    print(f'    -OutputDir "__DEV_ROOT__\\scratch\\geom_r04_${{m}}_{arm}"')
    print('}')


def run(ctx, arm, report_path, *, confirmed):
    require(confirmed and arm in ("A", "B"), "Prediction NOT AUTHORIZED: --arm and --confirm-generation required")
    report_path = lineage.audit_report_path(ctx, report_path)
    pre = read_json(report_path)
    dependencies = checked_inputs(ctx)
    fingerprint = inference_fingerprint(dependencies)
    require(pre["status"] == "PASS_EVALUATION_ONLY_CPU_PREFLIGHT" and pre["version"] == VERSION
            and pre["dependencies"] == dependencies and pre["inference_fingerprint"] == fingerprint, "Stale inference preflight")
    verify_record(pre["protected_training_inventory"])
    protected = read_json(pre["protected_training_inventory"]["path"])
    verify_protected(ctx, protected)
    verify_record(pre["query_row_audit"])
    audits = read_rows(pre["query_row_audit"]["path"])
    require(len(audits) == 10000 and value_sha(audits) == pre["ordered_plan_input_audit_sha256"], "Input audit drift")
    run_guards(ctx, arm, fingerprint)
    require(torch.cuda.is_available(), "Explicit prediction requires CUDA")
    ctx.guard(resources=True)
    peer = lineage.tree_snapshot(output_path(ctx, "A")) if arm == "B" else None

    def verify_readonly():
        verify_protected(ctx, protected)
        require(own_sources() == dependencies["sources"], "Inference source changed during generation")
        for key in ("prompt_source", "prefix_source", "canonicalizer"):
            verify_record(dependencies[key])
        for key in ("cache_index", "cache_complete"):
            verify_record(pre[key])
        if peer is not None:
            lineage.assert_tree_unchanged(output_path(ctx, "A"), peer)

    cache, tok = QueryCache(ctx, verify=False), tokenizer_for(ctx)
    require(generation_kwargs(ctx, tok) == pre["generation_kwargs"], "Generation token/special-ID policy drift")
    cases = validate_cases(ctx)
    root = run_guards(ctx, arm, fingerprint)
    root.parent.mkdir(parents=True, exist_ok=True)
    root.mkdir(exist_ok=False)
    write_json_new(root / "STARTED.json", {"version": VERSION, "created_utc": original.now(), "arm": arm,
        "inference_fingerprint": fingerprint, "preflight": record(report_path), "sources": own_sources(),
        "code_model_completion": dependencies["stage4b_finals"][arm], "implicit_resume": False,
        "training_allowed": False, "reference_dependent_packing": False})
    from transformers import set_seed
    set_seed(42)
    torch.backends.cuda.matmul.allow_tf32 = True
    try:
        plans = generate_plans(ctx, arm, root, cache, tok, cases, audits, verify_readonly)
        crops = generate_codes(ctx, arm, root, cache, tok, cases, plans, verify_readonly)
        files = export_modality_files(ctx, arm, root, cases)
        for name in ("STARTED.json", "test_plans.jsonl", "test_plans.p1a_log.json", "test_code.jsonl",
                     "plan_input_audit.jsonl", "code_input_audit.jsonl"):
            files[name] = record(root / name)
        verify_readonly()
        write_json_new(root / "COMPLETE.json", {"version": VERSION, "created_utc": original.now(), "arm": arm,
            "status": "GENERATION_COMPLETE_NEEDS_GATE_AND_GEOMETRY", "inference_fingerprint": fingerprint,
            "preflight": record(report_path), "files": files, "rows": 10000, "rows_per_modality": 2500,
            "program_code_repair": False, "plan_canonicalization": "P1a", "code_prompt_truncations": crops,
            "training_run": False, "evaluation_run": False})
        verify_generation(ctx, arm, fingerprint)
    finally:
        verify_readonly()
    print_evaluation_commands(arm)


def parser():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("action", choices=("preflight", "run"), nargs="?", default="preflight")
    ap.add_argument("--arm", choices=("A", "B"))
    ap.add_argument("--confirm-generation", action="store_true")
    ap.add_argument("--source-root", type=Path, default=Path("__RUN_SOURCE_ROOT__"))
    ap.add_argument("--package-root", type=Path, default=Path("__EVIDENCE_SOURCE_ROOT__/04"))
    ap.add_argument("--report", type=Path)
    return ap


def main():
    args = parser().parse_args()
    require(args.action != "run" or (args.arm and args.confirm_generation), "Prediction NOT AUTHORIZED: --arm and --confirm-generation required")
    require(args.action != "preflight" or (not args.arm and not args.confirm_generation), "Preflight checks both arms; no generation flag")
    os.chdir(args.source_root)
    torch.set_num_threads(2)
    ctx = FrozenInputs(args.package_root, args.source_root).guard()
    report = args.report or ctx.package / "execution/exposure_inference_preflight_v1.json"
    if args.action == "preflight":
        preflight(ctx, report)
    else:
        run(ctx, args.arm, report, confirmed=args.confirm_generation)


if __name__ == "__main__":
    main()
