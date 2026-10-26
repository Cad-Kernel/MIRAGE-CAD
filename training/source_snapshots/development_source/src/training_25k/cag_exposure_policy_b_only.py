#!/usr/bin/env python3
"""Versioned B-plan-only continuation. Default is a CPU dry-run, never training."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import sys

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import torch
import cag_exposure_policy as original
from cag_exposure_policy_core import (
    FrozenInputs, PlanDataset, QueryCache, execution_hashes, final_component, plan_role_rows,
    read_json, read_rows, record, reject_existing, require, sha, value_sha, verify_record, write_json_new,
)

PARENT = "905782583273b437e9e82d11882583d81167738baa4d988712c2263a2e643d73"
AMENDMENT = "efc5ea52d9ab2b9b3aa46661a0a4f46805e09c0b466b9162f3962d9dee335fd1"
VERSION = "review04_b_plan_only_v2"
SEQUENCE = ("B_phase1", "B_phase2", "B_train_roles_945")


def now():
    return datetime.now(timezone.utc).isoformat()


def own_sources():
    root = Path(__file__).resolve().parent
    return {n: record(root / n) for n in ("cag_exposure_policy_b_only.py", "cag_run_exposure_policy_b_only.sh")}


def nested_records(value):
    if isinstance(value, dict):
        if {"path", "sha256", "bytes"} <= value.keys():
            yield value
        else:
            for item in value.values():
                yield from nested_records(item)
    elif isinstance(value, list):
        for item in value:
            yield from nested_records(item)


def verify_records(value):
    unique = {r["path"]: r for r in nested_records(value)}
    for r in unique.values():
        verify_record(r)
    return len(unique)


def arm_roots(ctx):
    base = ctx.source / ctx.spec["training_output_root"]
    return base / "arm_A", base / "arm_B"


def output_guards(ctx):
    a, b = arm_roots(ctx)
    require(a.is_dir() and not a.is_symlink(), "Completed A output must exist and may not be a symlink")
    for root in (a, b):
        reject_existing(root / "stage4b")
    require(not b.is_symlink(), "B output may not be a symlink")
    if b.exists():
        require(b.is_dir() and not any(b.iterdir()), "B output is nonempty: no overwrite or silent resume")
    for phase in ("phase1", "phase2"):
        _, _, path = original.stage_spec(ctx, "B", phase)
        require(path.parent.resolve() == b.resolve(), "B phase output is outside the B root")
        reject_existing(path)
    require(original.predicted_train_path(ctx, "B").resolve() == (b / "predictions/train_roles_plans.jsonl").resolve(),
            "B prediction output path changed")


def tree_snapshot(root):
    root = Path(root)
    require(root.is_dir() and not root.is_symlink(), f"Missing or linked protected tree: {root}")
    files, directories = {}, []
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), f"Symlink inside protected A tree: {path}")
        relative = path.relative_to(root).as_posix()
        if path.is_dir():
            directories.append(relative)
        elif path.is_file():
            files[relative] = {"sha256": sha(path), "bytes": path.stat().st_size,
                               "mtime_ns": path.stat().st_mtime_ns}
        else:
            raise ValueError(f"Unsupported protected A asset: {path}")
    return {"root": str(root.resolve()), "files": files, "directories": directories}


def assert_tree_unchanged(root, expected):
    require(tree_snapshot(root) == expected, "Protected A output tree changed; stop without modifying/retraining A")


def audit_report_path(ctx, path):
    path = Path(path)
    directory = ctx.package / "execution"
    require(not directory.is_symlink() and not path.is_symlink() and path.suffix == ".json"
            and path.parent.resolve() == directory.resolve(),
            "Audit reports must be non-symlink JSON files directly inside Review/04/execution; never write into A/B")
    return path.resolve()


def verify_model_startup(ctx, arm, phase):
    require(phase in ("phase1", "phase2"), "Only plan-phase startup lineage is valid here")
    root = arm_roots(ctx)[0 if arm == "A" else 1]
    initial = (ctx.package / ctx.spec["plan_adapter"][f"initialization_{arm}"]
               if phase == "phase1" else root / "plan_phase1")
    report = read_json(root / f"plan_{phase}/training_report.json")
    require(report["fingerprint"] == PARENT and report["arm"] == arm and report["stage"] == phase,
            "Wrong startup-report arm/phase/parent")
    expected = {n: record(initial / n) for n in ("adapter_model.safetensors", "adapter_config.json", "soft_prefix.pt")}
    require(report["startup"] == expected, "Actual loaded startup LoRA/prefix does not match the frozen initialization/phase1 final")
    require(report["fresh_optimizer_and_scheduler"], "Phase optimizer/scheduler was not reset")


def verify_plan_branch(ctx, arm):
    root = arm_roots(ctx)[0 if arm == "A" else 1]
    finals = {}
    for phase, steps in (("phase1", 4689), ("phase2", 500)):
        final_component(root / f"plan_{phase}", steps, arm=arm, phase=phase, fingerprint=ctx.fingerprint)
        verify_model_startup(ctx, arm, phase)
        finals[phase] = record(root / f"plan_{phase}/COMPLETE.json")
    path = original.predicted_train_path(ctx, arm)
    complete_path = path.with_suffix(".complete.json")
    complete = read_json(complete_path)
    require(complete["fingerprint"] == ctx.fingerprint and complete["arm"] == arm, "Wrong plan completion provenance")
    require(Path(complete["prediction_file"]["path"]).resolve() == path.resolve(), "Wrong plan completion path")
    verify_record(complete["prediction_file"])
    model = root / "plan_phase2"
    model_hash, prefix_hash = sha(model / "adapter_model.safetensors"), sha(model / "soft_prefix.pt")
    predictions = read_rows(path)
    plan_role_rows(ctx.manifests["stage4b_roles"], predictions, arm=arm, phase2_hash=model_hash)
    require(complete["rows"] == len(predictions) == 945, "Plan branch must contain exactly 945 predictions")
    require(complete["plan_model_sha256"] == model_hash and complete["plan_prefix_sha256"] == prefix_hash,
            "Completion is not bound to final same-arm LoRA/prefix")
    require(all(r["plan_prefix_sha256"] == prefix_hash and r["canonicalization"] == "P1a" for r in predictions),
            "Wrong plan prefix/canonicalization provenance")
    require(complete["id_sequence_sha256"] == value_sha([r["sample_id"] for r in predictions]), "Plan ID hash drift")
    log = read_json(path.with_suffix(".p1a_log.json"))
    require(log["rows"] == 945, "Missing/incomplete P1a log")
    return {"finals": finals, "predictions": record(path), "completion": record(complete_path),
            "p1a_log": record(path.with_suffix(".p1a_log.json")), "actual_steps": [4689, 500], "rows": 945}


def policy_identity(ctx):
    path = ctx.package / "execution/stage4b_packing_v1_preflight/preflight_actuals.json"
    report = read_json(path)
    require(report["status"] == "PASS_A_AND_VALIDATION_B_PENDING" and not report["training_started"],
            "Missing A/validation packing acceptance")
    identity = report["policy_identity"]
    require(identity["parent_fingerprint"] == PARENT and value_sha(identity) == report["amendment_fingerprint"] == AMENDMENT,
            "Stage4b packing policy identity drift")
    verify_records(identity)
    return {"amendment_id": "R04-S4B-PACK-01", "amendment_fingerprint": AMENDMENT,
            "parent_fingerprint": PARENT, "identity": identity, "acceptance_report": record(path),
            "scope": "all Stage4b construction-plan fields, GT/predicted, train/validation",
            "scope_confirmation": "operator confirmed before B-only implementation",
            "stage4b_training_authorized": False}


def policy_lock(ctx, expected, *, create):
    path = ctx.package / "execution/stage4b_policy_lock_v1.json"
    if not path.exists():
        require(create, "Packing policy lock absent; run CPU preflight first")
        write_json_new(path, {"created_utc": now(), "policy": expected})
    require(read_json(path)["policy"] == expected, "Locked packing policy changed; no automatic amendment")
    return record(path)


def checked_inputs(ctx):
    require(ctx.fingerprint == PARENT, "Original parent fingerprint drift")
    require(ctx.package == Path(ctx.spec["package_root"]).resolve(), "Use the canonical frozen package root")
    historical = read_json(ctx.package / "execution/training_release_actuals.json")
    require(historical["fingerprint"] == PARENT and historical["execution_hashes"] == execution_hashes(),
            "Original execution source drift")
    verify_record(historical["preflight_report"])
    verify_record(historical["cache_complete"])
    verify_record(historical["cache_index"])
    initial = ctx.actuals["checks"]["initialization"]
    a, b = initial["arm_files"]["A"], initial["arm_files"]["B"]
    require(set(a) == set(b) and all(a[n]["sha256"] == b[n]["sha256"] for n in a), "Common initialization mismatch")
    count = verify_records({"upstreams": ctx.actuals["checks"]["checkpoints"]["components"],
                            "initializations": initial["arm_files"], "base": initial["base_files"]})
    test_path = ctx.package / "execution/b_only_contract_tests_v2.json"
    tests = read_json(test_path)
    require(tests["status"] == "PASS" and tests["sources"] == own_sources(), "B-only code lacks current passing CPU tests")
    verify_record(tests["test_source"])
    return {"checked_component_and_initialization_files": count, "tests": record(test_path),
            "original_execution": execution_hashes(), "continuation_sources": own_sources(),
            "cache_index": historical["cache_index"], "cache_complete": historical["cache_complete"],
            "initialization_files": initial["arm_files"],
            "manifests": {n: record(ctx.package / f"manifests/{n}.jsonl") for n in ctx.manifests}}


def preflight(ctx, report_path):
    report_path = audit_report_path(ctx, report_path)
    reject_existing(report_path)
    output_guards(ctx)
    inputs = checked_inputs(ctx)
    packing = policy_identity(ctx)
    a_root, b_root = arm_roots(ctx)
    a_branch = verify_plan_branch(ctx, "A")
    a_tree = tree_snapshot(a_root)
    print(f"A protected tree: {len(a_tree['files'])} files, snapshot/hash only; no chmod or writes", flush=True)
    cache = QueryCache(ctx)
    tok = original.tokenizer_for(ctx)
    stages = {}
    for phase, rows, steps in (("phase1", 75024, 4689), ("phase2", 8000, 500)):
        _, cases, _ = original.stage_spec(ctx, "B", phase)
        dataset = PlanDataset(cases, cache, tok)
        require(len(dataset) == rows, "B manifest row budget changed")
        stages[phase] = {**original.dataset_check(dataset, tok), **original.count_loader(ctx, phase, rows)}
        require(stages[phase]["planned_updates"] == steps, "B plan budget drift")
        print(f"B-only {phase}: {rows} rows -> {steps} planned updates; no training", flush=True)
    validation = original.dataset_check(PlanDataset(ctx.manifests["validation_shared"], cache, tok), tok)
    predicted_roles = [c for c in ctx.manifests["stage4b_roles"] if c["role"] == "predicted"]
    require(len(predicted_roles) == 945 and all(c["source_split"] == "train" and c["modality"] == "step"
            for c in predicted_roles), "B generation must use exactly 945 train-only STEP roles")
    assert_tree_unchanged(a_root, a_tree)
    output_guards(ctx)
    inventory_path = report_path.with_suffix(".a_inventory.json")
    reject_existing(inventory_path)
    write_json_new(inventory_path, a_tree)
    lock = policy_lock(ctx, packing, create=True)
    result = {"version": VERSION, "created_utc": now(), "status": "PASS_B_ONLY_CPU_DRY_RUN",
              "parent_fingerprint": PARENT, "amendment_fingerprint": AMENDMENT, "policy_lock": lock,
              "training_started": False, "gpu_model_loaded": False, "actual_B_steps": None,
              "allowed_sequence": list(SEQUENCE), "stage4b_allowed": False, "evaluation_generation_allowed": False,
              "inputs": inputs, "A_branch": a_branch, "A_read_only_inventory": record(inventory_path),
              "A_tree_unchanged": True, "B_output_unstarted": True, "B_output": str(b_root),
              "B_phases": stages, "plan_validation": validation,
              "generation": {"rows": 945, "id_sequence_sha256": value_sha([c["sample_id"] for c in predicted_roles]),
                             "training_roles": True, "canonicalization": "P1a", "empty_invalid_retained": True},
              "cache_entries_reverified": len(cache.entries), "cache_regenerated": False,
              "scope": "Full cache byte/tensor check plus actual B plan tokenization and CPU sampler traversal; no model forward/backward/optimizer step"}
    write_json_new(report_path, result)
    print(f"B-only CPU dry-run PASS: {report_path}; Stage4b is forbidden; no training", flush=True)


def train_b_phase(ctx, phase, cache, report_path):
    require(phase in ("phase1", "phase2"), "B-only entrypoint forbids Stage4b or any other stage")
    original.train_stage(ctx, "B", phase, cache, report_path)


def execute_b_sequence(ctx, cache, report_path, boundary):
    # Literal calls only: there is no CLI arm/stage selector, A call, or test-code generation.
    for phase in ("phase1", "phase2"):
        train_b_phase(ctx, phase, cache, report_path)
        boundary(phase)
    original.generate(ctx, "B", cache, training_roles=True)
    boundary("train_roles_945")


def run(ctx, report_path, *, confirmed):
    require(confirmed, "B-only training NOT AUTHORIZED: human --confirm-training required")
    report_path = audit_report_path(ctx, report_path)
    require(torch.cuda.is_available(), "B-only training requires CUDA")
    output_guards(ctx)
    report = read_json(report_path)
    require(report["status"] == "PASS_B_ONLY_CPU_DRY_RUN" and report["version"] == VERSION,
            "Current B-only CPU dry-run required")
    require(report["parent_fingerprint"] == ctx.fingerprint == PARENT and report["amendment_fingerprint"] == AMENDMENT,
            "Preflight lineage drift")
    inputs = checked_inputs(ctx)
    require(report["inputs"] == inputs, "B-only inputs/source hashes changed after dry-run")
    require(report["allowed_sequence"] == list(SEQUENCE) and not report["stage4b_allowed"], "B-only scope drift")
    require(policy_lock(ctx, policy_identity(ctx), create=False) == report["policy_lock"], "Policy lock drift")
    verify_record(report["A_read_only_inventory"])
    expected_a = read_json(report["A_read_only_inventory"]["path"])
    a_root, b_root = arm_roots(ctx)
    assert_tree_unchanged(a_root, expected_a)
    require(verify_plan_branch(ctx, "A") == report["A_branch"], "A branch changed after dry-run")
    cache = QueryCache(ctx)
    # Exclusive claim makes a second invocation fail, including after a partial run.
    output_guards(ctx)
    b_root.mkdir(parents=True, exist_ok=True)
    write_json_new(b_root / "B_ONLY_STARTED.json", {"version": VERSION, "created_utc": now(),
        "parent_fingerprint": PARENT, "amendment_fingerprint": AMENDMENT, "policy_lock": report["policy_lock"],
        "preflight": record(report_path), "sources": own_sources(), "sequence": list(SEQUENCE),
        "implicit_resume": False, "A_writes_allowed": False, "stage4b_allowed": False})
    require({p.name for p in b_root.iterdir()} == {"B_ONLY_STARTED.json"}, "Concurrent/unexpected B output detected")
    torch.backends.cuda.matmul.allow_tf32 = True

    def boundary(phase):
        assert_tree_unchanged(a_root, expected_a)
        for root in (a_root, b_root):
            reject_existing(root / "stage4b")
        require(own_sources() == report["inputs"]["continuation_sources"]
                and execution_hashes() == report["inputs"]["original_execution"], "Execution source changed during run")
        verify_record(report["policy_lock"])
        verify_records(report["inputs"]["manifests"])
        verify_record(report["inputs"]["cache_index"])
        verify_record(report["inputs"]["cache_complete"])
        if phase in ("phase1", "phase2"):
            final_component(b_root / f"plan_{phase}", 4689 if phase == "phase1" else 500,
                            arm="B", phase=phase, fingerprint=PARENT)
            verify_model_startup(ctx, "B", phase)
        else:
            verify_plan_branch(ctx, "B")
        write_json_new(b_root / f"B_ONLY_AFTER_{phase}.json", {"created_utc": now(), "completed": phase,
            "A_tree_unchanged": True, "Stage4b_A": "NOT_STARTED", "Stage4b_B": "NOT_STARTED"})

    try:
        execute_b_sequence(ctx, cache, report_path, boundary)
    finally:
        assert_tree_unchanged(a_root, expected_a)
    b_branch = verify_plan_branch(ctx, "B")
    write_json_new(b_root / "B_ONLY_COMPLETE.json", {"version": VERSION, "created_utc": now(),
        "status": "PLAN_BRANCHES_COMPLETE_STAGE4B_NOT_STARTED", "parent_fingerprint": PARENT,
        "amendment_fingerprint": AMENDMENT, "policy_lock": report["policy_lock"], "sources": own_sources(),
        "preflight": record(report_path), "A": report["A_branch"], "B": b_branch, "A_tree_unchanged": True,
        "Stage4b_A": "NOT_STARTED", "Stage4b_B": "NOT_STARTED",
        "next": "Run immutable actual A/B Stage4b paired preflight; do not train Stage4b until separately released"})
    print("A plan branch COMPLETE (unchanged); B plan branch COMPLETE (4689 + 500, 945 plans).", flush=True)
    print("Stage4b A/B NOT STARTED. STOP: paired actual-plan preflight is required next.", flush=True)


def parser():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("action", choices=("preflight", "run"), nargs="?", default="preflight")
    ap.add_argument("--source-root", type=Path, default=Path("__RUN_SOURCE_ROOT__"))
    ap.add_argument("--package-root", type=Path, default=Path("__EVIDENCE_SOURCE_ROOT__/04"))
    ap.add_argument("--report", type=Path)
    ap.add_argument("--confirm-training", action="store_true")
    return ap


def main():
    args = parser().parse_args()
    require(args.action != "run" or args.confirm_training, "B-only training NOT AUTHORIZED: --confirm-training required")
    require(args.action == "run" or not args.confirm_training, "Confirmation cannot be passed to preflight")
    os.chdir(args.source_root)
    torch.set_num_threads(2)
    ctx = FrozenInputs(args.package_root, args.source_root).guard()
    report_path = args.report or ctx.package / "execution/b_only_preflight_v2.json"
    try:
        if args.action == "preflight":
            preflight(ctx, report_path)
        else:
            run(ctx, report_path, confirmed=args.confirm_training)
    except Exception as exc:
        write_json_new(ctx.package / f"execution/b_only_{args.action}_failed_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}.json",
                       {"version": VERSION, "created_utc": now(), "status": "FAILED_NO_AUTOMATIC_RESUME",
                        "action": args.action, "error": str(exc), "type": type(exc).__name__,
                        "human_training_confirmation": args.confirm_training})
        raise


if __name__ == "__main__":
    main()
