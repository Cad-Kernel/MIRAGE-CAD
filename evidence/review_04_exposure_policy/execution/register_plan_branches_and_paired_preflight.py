#!/usr/bin/env python3
"""Register completed plan branches and paired CPU packing evidence. Never train."""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

PACKAGE = Path(__file__).resolve().parents[1]
SOURCE = Path("__RUN_SOURCE_ROOT__")
IMPLEMENTATION = Path("__DEV_ROOT__/src/training_25k")
sys.path.insert(0, str(IMPLEMENTATION))
import cag_exposure_policy_b_only as b
from cag_exposure_policy import tokenizer_for
from cag_exposure_policy_core import (
    FrozenInputs, QueryCache, encoded, read_json, read_rows, record, reject_existing, require,
    sha, value_sha, verify_record, write_json_new,
)
from cag_stage4b_packing_v1 import Stage4bPackedDataset, digest


def training_history(root):
    report = read_json(root / "training_report.json")
    state = read_json(root / "trainer_state.json")
    logs = state.get("log_history", [])
    last = lambda key: next((item for item in reversed(logs) if key in item), None)
    return {"actual_global_step": state["global_step"], "checkpoint_selection": report["checkpoint_selection"],
            "fresh_optimizer_and_scheduler": report["fresh_optimizer_and_scheduler"],
            "startup": report["startup"], "dataset": report["dataset"], "exposure_trace": report["exposure_trace"],
            "last_logged_training_loss": last("loss"), "last_logged_validation_loss": last("eval_loss"),
            "aggregate_training_metrics": last("train_loss"), "native_log_history": logs,
            "files": {n: record(root / n) for n in ("trainer_state.json", "training_report.json", "COMPLETE.json",
                     "adapter_model.safetensors", "adapter_config.json", "soft_prefix.pt")}}


def standard_counts(summary, rows):
    return {"rows_total": summary["total_rows"], "predicted_role_rows": summary["roles"].get("predicted", 0),
            "gt_role_rows": summary["roles"].get("gt", 0),
            "rows_plan_truncated": summary["rows_requiring_plan_truncation"],
            "predicted_rows_plan_truncated": summary["predicted_rows_truncated"],
            "gt_rows_plan_truncated": summary["gt_rows_truncated"],
            "rows_target_truncated": sum(r["supervised_tokens"] != r["full_target_tokens_including_eos"] for r in rows),
            "rows_zero_supervision": sum(r["supervised_tokens"] == 0 for r in rows),
            "hard_overflow": summary["instruction_target_overflow_rows"],
            "packing_failures": summary["failure_rows"], "max_sequence_tokens": summary["max_final_sequence_tokens"],
            "full_supervised_tokens_one_pass": summary["full_supervised_tokens_one_pass"],
            "full_supervised_tokens_three_train_epochs": summary["full_supervised_tokens_one_pass"] * 3,
            "ordered_ids_roles_sha256": summary["ordered_ids_roles_sha256"]}


def plan_statistics(predictions, audit_rows):
    by_id = {r["sample_id"]: r for r in audit_rows if r["role"] == "predicted"}
    diagnostics = []
    for p in predictions:
        require(isinstance(p["grammar"]["valid"], bool), "Invalid grammar-status type")
        row = by_id[p["sample_id"]]
        empty = not p["predicted_ir"].strip()
        require(p["empty"] == empty, "Empty-plan flag mismatch")
        diagnostics.append({"sample_id": p["sample_id"], "arm": p["arm"], "source_split": p["source_split"],
            "modality": p["modality"], "model_plan_empty": empty, "grammar": p["grammar"],
            "raw_characters": len(p["raw_predicted_ir"]), "p1a_characters": len(p["predicted_ir"]),
            "p1a_changed_text": p["raw_predicted_ir"] != p["predicted_ir"],
            "plan_tokens": row["original_plan_tokens"], "packed_plan_tokens": row["retained_plan_tokens"],
            "plan_truncated": row["plan_truncated"], "full_target_ids_sha256": row["full_target_ids_sha256"]})
    return {"rows": len(predictions), "empty": sum(d["model_plan_empty"] for d in diagnostics),
            "grammar_valid": sum(d["grammar"]["valid"] for d in diagnostics),
            "grammar_invalid": sum(not d["grammar"]["valid"] for d in diagnostics),
            "p1a_changed_rows": sum(d["p1a_changed_text"] for d in diagnostics),
            "max_generated_plan_tokens": max(d["plan_tokens"] for d in diagnostics),
            "interpretation": "945 fixed train-role STEP plans only; not held-out accuracy or four-modality CAD quality"}, diagnostics


def main():
    output = PACKAGE / "execution/plan_branches_and_paired_preflight_20261018"
    reject_existing(output)
    ctx = FrozenInputs(PACKAGE, SOURCE).guard()
    require(ctx.fingerprint == b.PARENT, "Parent fingerprint drift")
    a_root, b_root = b.arm_roots(ctx)
    for root in (a_root, b_root):
        reject_existing(root / "stage4b")
    completion = read_json(b_root / "B_ONLY_COMPLETE.json")
    require(completion["status"] == "PLAN_BRANCHES_COMPLETE_STAGE4B_NOT_STARTED" and completion["version"] == b.VERSION,
            "B-only completion absent/wrong version")
    require(completion["parent_fingerprint"] == b.PARENT and completion["amendment_fingerprint"] == b.AMENDMENT,
            "B completion lineage mismatch")
    require(completion["sources"] == b.own_sources(), "B-only source drift")
    b.verify_records(completion)
    branches = {arm: b.verify_plan_branch(ctx, arm) for arm in ("A", "B")}
    require(completion["A"] == branches["A"] and completion["B"] == branches["B"], "Branch completion content changed")
    for name in ("B_ONLY_STARTED.json", "B_ONLY_AFTER_phase1.json", "B_ONLY_AFTER_phase2.json", "B_ONLY_AFTER_train_roles_945.json"):
        require((b_root / name).is_file(), f"Missing B-only boundary record: {name}")
    dry_run = read_json(completion["preflight"]["path"])
    verify_record(dry_run["A_read_only_inventory"])
    a_inventory = read_json(dry_run["A_read_only_inventory"]["path"])
    b.assert_tree_unchanged(a_root, a_inventory)
    lock = b.policy_lock(ctx, b.policy_identity(ctx), create=False)
    require(completion["policy_lock"] == lock, "Packing lock changed since B ran")
    paired_path = PACKAGE / "execution/stage4b_packing_v1_preflight_after_B/preflight_actuals.json"
    paired = read_json(paired_path)
    require(paired["status"] == "PASS_PAIRED" and paired["paired_actual_plan_preflight"] == "PASS", "Paired packing not PASS")
    require(paired["amendment_fingerprint"] == b.AMENDMENT, "Paired preflight did not use the locked policy")
    require(paired["policy_identity"] == read_json(lock["path"])["policy"]["identity"], "Paired policy identity mismatch")
    b.verify_records({k: paired[k] for k in ("policy_identity", "audit_script", "cache_complete", "cache_index", "provenance")})
    require(paired["original_execution_hashes"] == b.execution_hashes(), "Original execution source drift")
    rows = {}
    for label in ("A", "B", "validation"):
        summary = paired["datasets"][label]
        verify_record(summary["row_audit"])
        rows[label] = read_rows(summary["row_audit"]["path"])
        require(summary["status"] == "PASS" and summary["failure_rows"] == 0, "Packing failure")
        require(len(rows[label]) == summary["total_rows"] == (2500 if label == "validation" else 3150), "Packed row count mismatch")
    cache, tok = QueryCache(ctx, verify=False), tokenizer_for(ctx)
    counts, plan_stats, diagnostics = {}, {}, {}
    for arm, root in (("A", a_root), ("B", b_root)):
        predictions = read_rows(root / "predictions/train_roles_plans.jsonl")
        by_id = {p["sample_id"]: p for p in predictions}
        dataset = Stage4bPackedDataset(ctx.manifests["stage4b_roles"], cache, tok, by_id)
        eos_checks = []
        for i, audited in enumerate(rows[arm]):
            feature, actual = dataset.audited_item(i)
            target_ids = feature["labels"][feature["labels"] != -100].tolist()
            eos_checks.append(bool(target_ids) and target_ids[-1] == tok.eos_token_id
                              and digest(target_ids) == audited["full_target_ids_sha256"])
            require(actual["input_ids_sha256"] == audited["input_ids_sha256"]
                    and actual["labels_sha256"] == audited["labels_sha256"], "Packed row changed during registration")
        require(all(eos_checks), "EOS or full target-ID sequence lost")
        counts[arm] = {**standard_counts(paired["datasets"][arm], rows[arm]), "EOS_preserved": "all", "EOS_rows_checked": len(eos_checks)}
        plan_stats[arm], diagnostics[arm] = plan_statistics(predictions, rows[arm])
    val_cases = [{"case_index": i, "source_row": i, "sample_id": r["sample_id"], "source_split": "val",
                  "modality": "step", "role": "gt"} for i, r in enumerate(ctx.splits["val"])]
    validation = Stage4bPackedDataset(val_cases, cache, tok, {})
    for i, audited in enumerate(rows["validation"]):
        feature, actual = validation.audited_item(i)
        target_ids = feature["labels"][feature["labels"] != -100].tolist()
        require(target_ids[-1] == tok.eos_token_id and digest(target_ids) == audited["full_target_ids_sha256"]
                and actual["labels_sha256"] == audited["labels_sha256"], "Validation target/EOS changed")
    counts["validation"] = {**standard_counts(paired["datasets"]["validation"], rows["validation"]),
                            "full_supervised_tokens_three_train_epochs": None, "EOS_preserved": "all", "EOS_rows_checked": 2500}
    histories = {arm: {phase: training_history(root / f"plan_{phase}") for phase in ("phase1", "phase2")}
                 for arm, root in (("A", a_root), ("B", b_root))}
    b.assert_tree_unchanged(a_root, a_inventory)
    output.mkdir()
    for arm in ("A", "B"):
        path = output / f"{arm}_train_role_plan_diagnostics.jsonl"
        with path.open("xb") as stream:
            for row in diagnostics[arm]:
                stream.write(encoded(row))
        plan_stats[arm]["diagnostics"] = record(path)
    manifest_paths = list((PACKAGE / "manifests").glob("*ids*"))
    actuals = {"created_utc": datetime.now(timezone.utc).isoformat(), "status": "B_PLAN_BRANCH_COMPLETE_PAIRED_CPU_PREFLIGHT_PASS",
        "registration_script": record(Path(__file__)), "parent_fingerprint": b.PARENT, "amendment_fingerprint": b.AMENDMENT,
        "policy_lock": lock, "policy_sha256": paired["policy_identity"]["implementation"]["sha256"],
        "tokenizer_files": paired["policy_identity"]["tokenizer_files"],
        "role_manifest": record(PACKAGE / "manifests/stage4b_roles.jsonl"),
        "source_id_manifests": {p.name: record(p) for p in manifest_paths if p.is_file()},
        "paired_preflight": record(paired_path), "B_only_completion": record(b_root / "B_ONLY_COMPLETE.json"),
        "B_boundary_records": {p.name: record(p) for p in b_root.glob("B_ONLY_AFTER_*.json")},
        "A_output_files_unchanged": len(a_inventory["files"]), "branches": branches,
        "training_histories": histories, "train_role_plan_diagnostics": plan_stats, "packing_counts": counts,
        "dataloader_budget": paired["dataloader_budget"],
        "current_state": {"A_plan_branch": "COMPLETE", "B_plan_branch": "COMPLETE",
                          "Stage4b_A": "NOT_STARTED", "Stage4b_B": "NOT_STARTED", "gate_geometry": "NOT_STARTED"},
        "training_started_by_registration": False, "stage4b_manual_command_released": False,
        "canonical_execution_checkout": "__DEV_ROOT__/src/training_25k",
        "training_data_output_checkout": str(SOURCE), "next": "Implement and audit Stage4b-only training entrypoint; release manually after guards/tests",
        "interpretation": "Readiness and train-role plan diagnostics only; no final Build/export/geometry or curriculum-effect conclusion yet"}
    write_json_new(output / "actuals.json", actuals)
    print(json.dumps({"status": actuals["status"], "plan_diagnostics": plan_stats, "packing_counts": counts,
                      "state": actuals["current_state"]}, indent=2))


if __name__ == "__main__":
    main()
