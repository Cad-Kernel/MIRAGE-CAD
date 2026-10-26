#!/usr/bin/env python3
"""Read-only model/cache checks plus CPU tokenization audit; no training entrypoint."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
import sys

from cag_exposure_policy_core import (
    FrozenInputs, QueryCache, collate, encoded, execution_hashes, final_component, plan_role_rows,
    read_json, read_rows, record, reject_existing, require, sha, value_sha, verify_record, write_json_new,
)
from cag_exposure_policy import count_loader, tokenizer_for
from cag_stage4b_packing_v1 import POLICY, Stage4bPackedDataset


def audit_dataset(dataset, label, directory, tok):
    from torch.utils.data import DataLoader, Subset
    import torch

    rows, failures = [], []
    with (directory / f"{label}_rows.jsonl").open("xb") as stream:
        for i in range(len(dataset)):
            try:
                feature, row = dataset.audited_item(i)
                require(len(feature["input_ids"]) <= 1536, "Input overflow")
                require(int((feature["labels"] != -100).sum()) == row["full_target_tokens_including_eos"],
                        "Incomplete target labels")
                row["set"] = label
                rows.append(row)
                stream.write(encoded(row))
            except (ValueError, KeyError, OSError) as exc:
                failure = {"set": label, "case": dataset.cases[i], "error": str(exc)}
                failures.append(failure)
                stream.write(encoded(failure))
            if (i + 1) % 500 == 0:
                print(f"{label}: {i + 1}/{len(dataset)} packed on CPU; no training", flush=True)
    probes = []
    if not failures:
        indices = sorted({0, len(dataset) - 1} | {
            next((i for i, r in enumerate(rows) if r["role"] == role and r["plan_truncated"]), 0)
            for role in ("gt", "predicted")})
        loader = DataLoader(Subset(dataset, indices), batch_size=2, shuffle=False,
                            collate_fn=partial(collate, pad_id=tok.pad_token_id))
        for batch in loader:
            for mask, labels in zip(batch["attention_mask"], batch["labels"]):
                require(torch.all(labels[mask == 0] == -100).item(), "Padding labels are not masked")
                require(torch.any(labels != -100).item(), "Zero supervision in collated batch")
            probes.append({"input_shape": list(batch["input_ids"].shape),
                           "supervised_tokens": (batch["labels"] != -100).sum(1).tolist()})
    report = {
        "status": "PASS" if not failures else "FAIL", "total_rows": len(dataset), "packed_rows": len(rows),
        "roles": dict(Counter(c.get("role", "gt") for c in dataset.cases)),
        "rows_requiring_plan_truncation": sum(r["plan_truncated"] for r in rows),
        "predicted_rows_truncated": sum(r["plan_truncated"] and r["role"] == "predicted" for r in rows),
        "gt_rows_truncated": sum(r["plan_truncated"] and r["role"] == "gt" for r in rows),
        "validation_rows_truncated": sum(r["plan_truncated"] for r in rows) if label == "validation" else 0,
        "max_original_plan_tokens": max((r["original_plan_tokens"] for r in rows), default=None),
        "max_retained_plan_tokens": max((r["retained_plan_tokens"] for r in rows), default=None),
        "max_final_sequence_tokens": max((r["final_sequence_tokens"] for r in rows), default=None),
        "zero_supervision_rows": sum(r["zero_supervision"] for r in rows),
        "instruction_target_overflow_rows": sum("instruction+target overflow" in f["error"] for f in failures),
        "failure_rows": len(failures), "failures": failures,
        "legacy_zero_supervision_rows": sum(r["legacy_zero_supervision"] for r in rows),
        "plan_emptied_by_budget_rows": sum(r["plan_emptied_by_budget"] for r in rows),
        "full_supervised_tokens_one_pass": sum(r["supervised_tokens"] for r in rows),
        "ordered_ids_roles_sha256": value_sha([[c["sample_id"], c.get("role", "gt")] for c in dataset.cases]),
        "row_audit": record(directory / f"{label}_rows.jsonl"), "collated_batch_probes": probes,
    }
    return report, rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--package", type=Path, default=Path("__EVIDENCE_SOURCE_ROOT__/04"))
    ap.add_argument("--source", type=Path, default=Path("__RUN_SOURCE_ROOT__"))
    ap.add_argument("--output", type=Path, required=True, help="New audit directory; never overwritten")
    args = ap.parse_args()
    reject_existing(args.output)
    ctx = FrozenInputs(args.package, args.source).guard()
    require(ctx.fingerprint == "905782583273b437e9e82d11882583d81167738baa4d988712c2263a2e643d73",
            "Original parent fingerprint changed; do not rewrite existing provenance")
    cache, tok = QueryCache(ctx, verify=False), tokenizer_for(ctx)
    root = ctx.source / ctx.spec["training_output_root"]
    for arm in ("A", "B"):
        reject_existing(root / f"arm_{arm}/stage4b")
    args.output.mkdir(parents=True)
    provenance, reports, arm_rows = {}, {}, {}
    import inspect
    from miragecad.gen_prompts import build_program_prompt
    policy_record = record(Path(__file__).with_name("cag_stage4b_packing_v1.py"))
    tokenizer_dir = ctx.package / ctx.spec["plan_adapter"]["initialization_A"]
    tokenizer_records = {p.name: record(p) for p in sorted(tokenizer_dir.iterdir())
                         if p.is_file() and ("token" in p.name or p.name in ("vocab.json", "merges.txt"))}
    identity = {"policy": POLICY, "parent_fingerprint": ctx.fingerprint, "implementation": policy_record,
                "tokenizer_files": tokenizer_records, "prompt_builder": record(inspect.getsourcefile(build_program_prompt))}
    for arm in ("A", "B"):
        arm_root = root / f"arm_{arm}"
        if not arm_root.exists():
            reports[arm] = {"status": "PENDING_PLAN_BRANCH", "actual_plans_available": False}
            continue
        for phase, steps in (("phase1", 4689), ("phase2", 500)):
            final_component(arm_root / f"plan_{phase}", steps, arm=arm, phase=phase, fingerprint=ctx.fingerprint)
        path = arm_root / "predictions/train_roles_plans.jsonl"
        completion = read_json(path.with_suffix(".complete.json"))
        require(Path(completion["prediction_file"]["path"]).resolve() == path.resolve(), "Wrong prediction artifact path")
        verify_record(completion["prediction_file"])
        predictions = read_rows(path)
        model2 = arm_root / "plan_phase2"
        by_id = plan_role_rows(ctx.manifests["stage4b_roles"], predictions, arm=arm,
                              phase2_hash=sha(model2 / "adapter_model.safetensors"))
        require(all(r["plan_prefix_sha256"] == sha(model2 / "soft_prefix.pt") for r in predictions),
                "Wrong prediction prefix provenance")
        provenance[arm] = {"predictions": record(path), "completion": record(path.with_suffix(".complete.json")),
                           "phase1": record(arm_root / "plan_phase1/COMPLETE.json"),
                           "phase2": record(model2 / "COMPLETE.json")}
        dataset = Stage4bPackedDataset(ctx.manifests["stage4b_roles"], cache, tok, by_id)
        reports[arm], arm_rows[arm] = audit_dataset(dataset, arm, args.output, tok)
        require(reports[arm]["roles"] == {"predicted": 945, "gt": 2205}, "Role count drift")
    require("A" in arm_rows, "Actual Arm A predictions are required for this audit")
    val_cases = [{"case_index": i, "source_row": i, "sample_id": r["sample_id"], "source_split": "val",
                  "modality": "step", "role": "gt"} for i, r in enumerate(ctx.splits["val"])]
    require(len(val_cases) == 2500, "Validation count drift")
    reports["validation"], _ = audit_dataset(Stage4bPackedDataset(val_cases, cache, tok, {}), "validation", args.output, tok)
    budget = count_loader(ctx, "stage4b", 3150)
    require(budget["planned_updates"] == 1182, "Stage4b planned budget drift")
    failed = any(r["status"] == "FAIL" for r in reports.values())
    paired = "PENDING_B_ACTUAL_PLANS"
    if "B" in arm_rows and not failed:
        require(len(arm_rows["A"]) == len(arm_rows["B"]) == 3150, "Paired row count drift")
        for a, b in zip(arm_rows["A"], arm_rows["B"]):
            for key in ("case_index", "sample_id", "role", "full_target_ids_sha256", "reference_code_sha256",
                        "protected_scaffold_sha256", "evidence_sha256", "supervised_tokens"):
                require(a[key] == b[key], f"Paired identity mismatch: {key}/{a['sample_id']}")
            if a["role"] == "gt":
                require(a["input_ids_sha256"] == b["input_ids_sha256"], "Paired GT packing differs")
        paired = "PASS"
    result = {"created_utc": datetime.now(timezone.utc).isoformat(),
              "status": "FAIL" if failed else ("PASS_PAIRED" if paired == "PASS" else "PASS_A_AND_VALIDATION_B_PENDING"),
              "training_authorized": False, "training_started": False, "model_forward_called": False,
              "policy_identity": identity, "amendment_fingerprint": value_sha(identity),
              "original_execution_hashes": execution_hashes(), "audit_script": record(Path(__file__)),
              "cache_complete": record(cache.root / "COMPLETE.json"), "cache_index": record(cache.root / "index.jsonl"),
              "cache_verification_scope": "full index/identity coverage; bytes/tensors verified for every consumed train/validation entry",
              "provenance": provenance, "datasets": reports, "paired_actual_plan_preflight": paired,
              "dataloader_budget": budget, "actual_stage4b_global_step": None,
              "notes": "CPU-only audit; no continuation entrypoint or training authorization. Original three execution sources unchanged."}
    write_json_new(args.output / "preflight_actuals.json", result)
    print(__import__("json").dumps({k: v for k, v in result.items() if k in (
        "status", "training_started", "paired_actual_plan_preflight", "amendment_fingerprint", "dataloader_budget")}, indent=2))
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
