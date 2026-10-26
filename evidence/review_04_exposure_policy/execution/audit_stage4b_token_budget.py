#!/usr/bin/env python3
"""Audit actual Stage4b token budgets on CPU; no training or tokenization changes."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import sys

PACKAGE = Path(__file__).resolve().parents[1]
SOURCE = Path("__RUN_SOURCE_ROOT__")
IMPLEMENTATION = Path("__DEV_ROOT__/src/training_25k")
sys.path.insert(0, str(IMPLEMENTATION))

from cag_exposure_policy_core import (
    FrozenInputs, QueryCache, final_component, plan_role_rows, read_json, read_rows,
    record, reject_existing, require, sha, value_sha, verify_record, write_json_new,
)
from cag_exposure_policy import tokenizer_for


def summary(values):
    import numpy as np
    if not values:
        return {"n": 0, "min": None, "median": None, "q95": None, "max": None}
    a = np.asarray(values)
    return {"n": len(values), "min": int(a.min()), "median": float(np.median(a)),
            "q95": float(np.quantile(a, 0.95)), "max": int(a.max())}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", choices=["A", "B"], default="A")
    ap.add_argument("--validation-only", action="store_true")
    args = ap.parse_args()
    ctx = FrozenInputs(PACKAGE, SOURCE).guard()
    from miragecad.gen_prompts import build_program_prompt
    root = ctx.source / ctx.spec["training_output_root"]
    arm_root = root / f"arm_{args.arm}"
    model1, model2 = arm_root / "plan_phase1", arm_root / "plan_phase2"
    for name, path, steps in (("phase1", model1, 4689), ("phase2", model2, 500)):
        final_component(path, steps, arm=args.arm, phase=name, fingerprint=ctx.fingerprint)
    prediction_path = arm_root / "predictions/train_roles_plans.jsonl"
    provenance = read_json(prediction_path.with_suffix(".complete.json"))
    verify_record(provenance["prediction_file"])
    predictions = read_rows(prediction_path)
    roles = ctx.manifests["stage4b_roles"]
    by_id = plan_role_rows(roles, predictions, arm=args.arm, phase2_hash=sha(model2 / "adapter_model.safetensors"))
    prefix_sha = sha(model2 / "soft_prefix.pt")
    require(all(r["plan_prefix_sha256"] == prefix_sha for r in predictions), "Wrong prefix provenance")
    if args.validation_only:
        roles = [{"case_index": i, "source_row": i, "sample_id": r["sample_id"], "source_split": "val",
                  "modality": "step", "role": "gt"} for i, r in enumerate(ctx.splits["val"])]
    cache, tok = QueryCache(ctx, verify=False), tokenizer_for(ctx)
    rows = []
    for case in roles:
        meta, _, _ = cache.load(case)
        plan = by_id[case["sample_id"]]["predicted_ir"] if case["role"] == "predicted" else meta["reference_ir"]
        prompt = build_program_prompt({}, "step", plan, evidence_text=meta["evidence"])
        scaffold = build_program_prompt({}, "step", "", evidence_text=meta["evidence"])
        n_prompt = len(tok(prompt, add_special_tokens=True)["input_ids"])
        n_empty = len(tok(scaffold, add_special_tokens=True)["input_ids"])
        n_target = len(tok(meta["reference_code"] + tok.eos_token, add_special_tokens=False)["input_ids"])
        retained = min(n_target, max(0, 1536 - n_prompt))
        rows.append({"case_index": case["case_index"], "sample_id": case["sample_id"], "role": case["role"],
                     "prompt_tokens": n_prompt, "plan_tokens": len(tok(plan, add_special_tokens=False)["input_ids"]),
                     "target_tokens_including_eos": n_target, "full_sequence_tokens": n_prompt + n_target,
                     "empty_plan_scaffold_tokens": n_empty, "empty_plan_plus_target_tokens": n_empty + n_target,
                     "legacy_supervised_tokens_retained": retained, "legacy_zero_supervision": retained == 0,
                     "legacy_target_partially_or_fully_truncated": retained < n_target,
                     "complete_target_exceeds_1536_alone": n_target > 1536,
                     "complete_target_plus_empty_scaffold_exceeds_1536": n_empty + n_target > 1536,
                     "full_target_requires_shorter_prompt": n_prompt + n_target > 1536,
                     "gt_fixed_prompt_plus_full_target_does_not_fit": case["role"] == "gt" and n_prompt + n_target > 1536,
                     "grammar": by_id[case["sample_id"]].get("grammar") if case["role"] == "predicted" else None})
    counts = {}
    flags = ("legacy_zero_supervision", "legacy_target_partially_or_fully_truncated",
             "complete_target_exceeds_1536_alone", "complete_target_plus_empty_scaffold_exceeds_1536",
             "full_target_requires_shorter_prompt", "gt_fixed_prompt_plus_full_target_does_not_fit")
    for role in ("predicted", "gt", "all"):
        selected = [r for r in rows if role == "all" or r["role"] == role]
        counts[role] = {"rows": len(selected), **{f: sum(r[f] for r in selected) for f in flags},
                        "prompt_tokens": summary([r["prompt_tokens"] for r in selected]),
                        "target_tokens_including_eos": summary([r["target_tokens_including_eos"] for r in selected])}
    label = "validation" if args.validation_only else args.arm
    paths = {"actuals": PACKAGE / f"execution/stage4b_{label}_token_budget_actuals.json",
             "rows": PACKAGE / f"execution/stage4b_{label}_token_budget_rows.jsonl"}
    for p in paths.values():
        reject_existing(p)
    with paths["rows"].open("xb") as f:
        from cag_exposure_policy_core import encoded
        for row in rows:
            f.write(encoded(row))
    result = {"created_utc": datetime.now(timezone.utc).isoformat(), "arm": "SHARED_VALIDATION" if args.validation_only else args.arm,
              "scope": "CPU feasibility audit, original tokenization unchanged; no model training",
              "fingerprint": ctx.fingerprint, "arm_phase1_final_actual_step": 4689,
              "arm_phase2_final_actual_step": 500, "stage4b_output_exists": (arm_root / "stage4b").exists(),
              "arm_B_exists": (root / "arm_B").exists(),
              "source_definition": record(ctx.source / "data/25k/val.jsonl") if args.validation_only else record(PACKAGE / "manifests/stage4b_roles.jsonl"),
              "prediction_file": None if args.validation_only else record(prediction_path),
              "audit_script": record(Path(__file__)), "row_audit": record(paths["rows"]), "counts": counts,
              "counting_contract": "existing prompt encoding with add_special_tokens=True plus reference_code+EOS encoded separately",
              "empty_plan_scaffold_note": "exact existing serialized prompt with empty plan; BPE boundaries require exact candidate re-counting in any future packer",
              "proposed_full_target_predicted_only_rule": "INFEASIBLE_AS_STATED" if (
                  counts["all"]["complete_target_plus_empty_scaffold_exceeds_1536"] or
                  counts["gt"]["gt_fixed_prompt_plus_full_target_does_not_fit"]) else "ARM_A_FEASIBLE_B_PENDING",
              "training_started_by_audit": False, "production_code_changed": False}
    write_json_new(paths["actuals"], result)
    print(__import__("json").dumps(result, indent=2))


if __name__ == "__main__":
    main()
