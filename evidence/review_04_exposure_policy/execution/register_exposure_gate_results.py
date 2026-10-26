#!/usr/bin/env python3
"""Audit/register all eight human-run Review/04 gate evaluations; never execute CAD."""
import ast
import codecs
from collections import Counter, defaultdict
import hashlib
import math
import os
from pathlib import Path, PureWindowsPath
import re
import sys
import warnings

PACKAGE = Path(__file__).resolve().parents[1]
SOURCE = Path("__RUN_SOURCE_ROOT__")
IMPLEMENTATION = Path("__DEV_ROOT__/src/training_25k")
SCRATCH = IMPLEMENTATION.parent.parent / "scratch"
STAGING = Path("/mnt/c/tmp/MIRAGE/exec_eval")
sys.path.insert(0, str(IMPLEMENTATION))
import cag_exposure_inference as s
from cag_exposure_policy_core import FrozenInputs, read_json, read_rows, record, reject_existing, require, sha, verify_record, write_json_new

FLAGS = ("syntax_ok", "exec_ok", "build_ok", "solid_valid", "step_export_ok")


def read_cli_log(path):
    raw = Path(path).read_bytes()
    return raw.decode("utf-16" if raw.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)) else "utf-8-sig")


def code_sha(code):
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def audit_rows(rows, predictions, expected_ids, native_syntax_rows):
    require([row["sample_id"] for row in rows] == expected_ids
            and len(rows) == len({row["sample_id"] for row in rows}) == 2500,
            "Gate row count/uniqueness/frozen ID order mismatch")
    require([r["sample_id"] for r in native_syntax_rows] == expected_ids, "Native syntax ID/order mismatch")
    counts, failure_stages, errors = Counter(), Counter(), Counter()
    failure_ids = defaultdict(list)
    crash_count, syntax_checks = 0, 0
    default_parser_disagreement_ids = []
    for row, pred, native in zip(rows, predictions, native_syntax_rows):
        require(all(isinstance(row[k], bool) for k in FLAGS) and isinstance(row["error"], str), "Invalid gate row schema")
        require(all(not row[FLAGS[i]] or row[FLAGS[i - 1]] for i in range(1, len(FLAGS))), "Non-monotonic gate flags")
        require(native["code_sha256"] == code_sha(pred["prediction"]), "Native AST code hash mismatch")
        for flag in FLAGS:
            counts[flag] += row[flag]
        crashed = row["error"].startswith("kernel access")
        if crashed:
            crash_count += 1
            stage = "kernel_crash"
        else:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", SyntaxWarning)
                try:
                    ast.parse(pred["prediction"])
                    default_syntax = True
                except SyntaxError:
                    default_syntax = False
            require(native["syntax_ok"] == row["syntax_ok"], f"Actual native AST syntax mismatch: {row['sample_id']}")
            if default_syntax != row["syntax_ok"]:
                default_parser_disagreement_ids.append(row["sample_id"])
            syntax_checks += 1
            stage = next((flag + "_failure" for flag in FLAGS if not row[flag]), "all_gates_pass")
        failure_stages[stage] += 1
        if stage == "all_gates_pass":
            require(not row["error"], "Successful row has a failure message")
        else:
            require(bool(row["error"]), "Failed row lacks an error message")
            errors[row["error"]] += 1
            failure_ids[stage].append(row["sample_id"])
    return {"counts": dict(counts), "kernel_crashes": crash_count, "independent_AST_checks": syntax_checks,
            "native_AST_python_version": "3.11.11", "auxiliary_audit_python_version": sys.version,
            "default_parser_disagreement_count": len(default_parser_disagreement_ids),
            "default_parser_disagreement_sample_ids": default_parser_disagreement_ids,
            "first_failure_stage_counts": dict(failure_stages), "exact_error_counts": dict(errors.most_common()),
            "failure_sample_ids_by_stage": dict(failure_ids)}


def main():
    destination = PACKAGE / "execution/exposure_gate_completed_20261021.json"
    reject_existing(destination)
    os.chdir(SOURCE)
    print("Checking prediction/model immutability and all eight gate results; CPU only, no CAD execution", flush=True)
    ctx = FrozenInputs(PACKAGE, SOURCE).guard()
    registration_path = PACKAGE / "execution/exposure_prediction_B_and_paired_completed_20261021.json"
    registration = read_json(registration_path)
    dependencies = s.checked_inputs(ctx)
    fingerprint = s.inference_fingerprint(dependencies)
    require(registration["status"] == "BOTH_PREDICTIONS_COMPLETE_VERIFIED_NEEDS_GATE_AND_GEOMETRY"
            and registration["dependencies"] == dependencies and registration["inference_fingerprint"] == fingerprint,
            "Prediction source/model registration drift")
    pre = read_json(PACKAGE / "execution/exposure_inference_preflight_v1.json")
    verify_record(pre["protected_training_inventory"])
    s.verify_protected(ctx, read_json(pre["protected_training_inventory"]["path"]))
    inventory_record = registration["predictions_read_only_inventory"]
    verify_record(inventory_record)
    inventory = read_json(inventory_record["path"])
    for arm in ("A", "B"):
        require(s.verify_generation(ctx, arm, fingerprint) == registration["completions"][arm], "Prediction completion changed")
        s.lineage.assert_tree_unchanged(s.output_path(ctx, arm), inventory[arm])
    for item in registration["manual_evaluator_sources_at_release"].values():
        verify_record(item)
    native_path = PACKAGE / "execution/exposure_gate_native311_syntax_20261021.json"
    native = read_json(native_path)
    require(native["status"] == "PASS_NATIVE311_AST_ONLY" and native["python_version"] == [3, 11, 11]
            and native["program_or_CAD_execution"] is False, "Matching native AST audit missing")
    verify_record(native["audit_source"])
    verify_record(native["executable"])
    ids = [row["sample_id"] for row in ctx.splits["test"]]
    groups = {}
    for arm in ("A", "B"):
        groups[arm] = {}
        for modality in s.MODALITIES:
            run_id = f"exec_r04_{modality}_{arm}"
            output, staging = SCRATCH / run_id, STAGING / run_id
            prediction = s.output_path(ctx, arm) / f"test_code_{modality}.jsonl"
            predictions = read_rows(prediction)
            require([p["sample_id"] for p in predictions] == ids, "Gate prediction order mismatch")
            summary_path, rows_path = output / "execution_summary.json", output / "execution_rows.jsonl"
            summary, rows = read_json(summary_path), read_rows(rows_path)
            require(summary["rows"] == 2500 and PureWindowsPath(summary["input_jsonl"])
                    == PureWindowsPath(f"__TEMP_RUN_ROOT__/exec_eval/{run_id}/input.jsonl"), "Wrong summary count/input staging path")
            require(sha(staging / "input.jsonl") == sha(prediction), "Staged evaluator input differs from frozen prediction")
            require(sha(staging / "output.jsonl") == sha(rows_path)
                    and sha(staging / "summary.json") == sha(summary_path), "Staged/exported result mismatch")
            require(sha(staging / "evaluate_execution.py")
                    == registration["manual_evaluator_sources_at_release"]["evaluate_execution.py"]["sha256"],
                    "Staged evaluator source drift")
            log = read_cli_log(output / "cli.log")
            runtime = re.search(r"Python runtime:\s*(\d+)\.(\d+)\.(\d+)", log)
            require(runtime is not None, "Embedded Python version absent from CLI log")
            native_python = tuple(int(part) for part in runtime.groups())
            require(list(native_python) == native["python_version"], "Native CLI/parser version mismatch")
            native_group = native["groups"][arm][modality]
            verify_record(native_group["input"])
            verify_record(native_group["gate_rows"])
            require(native_group["input"]["sha256"] == sha(prediction)
                    and native_group["gate_rows"]["sha256"] == sha(rows_path), "Native AST artifact/input mismatch")
            recomputed = audit_rows(rows, predictions, ids, native_group["rows"])
            for flag in FLAGS:
                require(summary[flag + "_count"] == recomputed["counts"][flag]
                        and math.isclose(summary[flag + "_rate"], recomputed["counts"][flag] / 2500,
                                         rel_tol=0, abs_tol=1e-12), f"Native summary/row mismatch: {run_id}/{flag}")
            require(summary["kernel_crash_count"] == recomputed["kernel_crashes"], "Crash count mismatch")
            resume_lines = [line for line in log.splitlines() if "already scored" in line and "resuming:" in line]
            groups[arm][modality] = {"native_summary": summary, "row_audit": recomputed,
                "files": {name: record(output / name) for name in ("execution_summary.json", "execution_rows.jsonl", "cli.log")},
                "prediction": record(prediction), "staged_input": record(staging / "input.jsonl"),
                "staged_evaluator": record(staging / "evaluate_execution.py"),
                "native_python_version": ".".join(str(p) for p in native_python),
                "resume_log_lines": resume_lines, "resume_history_note": "Recorded from the retained last-attempt CLI log; not an independent full attempt history"}
            print(f"PASS {arm}/{modality}:2500 ordered rows, staged input byte-identical, counts and AST verified", flush=True)
    deltas, paired = {}, {}
    for modality in s.MODALITIES:
        deltas[modality] = {flag: 100 * (groups["B"][modality]["row_audit"]["counts"][flag]
            - groups["A"][modality]["row_audit"]["counts"][flag]) / 2500 for flag in FLAGS}
        a = read_rows(groups["A"][modality]["files"]["execution_rows.jsonl"]["path"])
        b = read_rows(groups["B"][modality]["files"]["execution_rows.jsonl"]["path"])
        paired[modality] = {flag: {"both_pass": sum(x[flag] and y[flag] for x, y in zip(a, b)),
            "A_only": sum(x[flag] and not y[flag] for x, y in zip(a, b)),
            "B_only": sum(not x[flag] and y[flag] for x, y in zip(a, b)),
            "both_fail": sum(not x[flag] and not y[flag] for x, y in zip(a, b))} for flag in FLAGS}
    s.verify_protected(ctx, read_json(pre["protected_training_inventory"]["path"]))
    for arm in ("A", "B"):
        s.lineage.assert_tree_unchanged(s.output_path(ctx, arm), inventory[arm])
    write_json_new(destination, {"created_utc": s.original.now(), "status": "ALL8_GATE_COMPLETE_VERIFIED_GEOMETRY_PENDING",
        "seed": 42, "rows_per_group": 2500, "gate_groups": 8, "total_gate_rows": 20000,
        "prediction_registration": record(registration_path), "predictions_read_only_inventory": inventory_record,
        "inference_fingerprint": fingerprint, "dependencies": dependencies, "registration_script": record(Path(__file__)),
        "checks": {"original_seal_and_source_models": "PASS", "predictions_and_training_trees_unchanged": "PASS",
                   "all8_frozen_ID_order_and_uniqueness": "PASS", "staged_input_bytes_match_predictions": "PASS",
                   "native_exported_rows_summaries_match_staging": "PASS", "evaluator_sources_match_release": "PASS",
                   "counts_rates_crashes_recomputed": "PASS", "matching_native311_AST_syntax": "PASS"},
        "native_syntax_audit": record(native_path),
        "groups": groups, "delta_B_minus_A_pp": deltas, "paired_gate_tables": paired,
        "equal_modality_descriptive_mean_pct": {arm: {flag: sum(groups[arm][m]["row_audit"]["counts"][flag]
            for m in s.MODALITIES) / 100 for flag in FLAGS} for arm in ("A", "B")},
        "gate_run_by": "human_operator", "training_model_prediction_or_CAD_execution_by_audit": False,
        "audit_implementation_note": "Initial WSL3.12 AST check stopped on flluma_0090798; feature_version also cannot fully emulate native3.11 f-strings. Replaced this auxiliary comparison with standalone native3.11.11 AST parsing, matching UTF16 CLI runtime logs. No gate output/model/prediction artifact changed",
        "geometry_status": "PENDING_NOT_RUN_BY_THIS_AUDIT", "review04_status": "OPEN",
        "limitations": ["Scoreable/CD/F@1 require geometry and are not inferred from gate",
                        "One paired seed, shared2500 source IDs across modalities; no multi-seed claim",
                        "Runtime is native per-attempt summary time and need not be total wall time if evaluation resumed",
                        "Independent syntax audit uses the matching standalone3.11.11 parser; this is not re-execution through the embedded CAD environment",
                        "AST parsing is CPU-only syntax verification, not re-execution of CAD programs"]})
    print(f"ALL8 gate results VERIFIED; geometry next. {destination}", flush=True)
    print({"delta_B_minus_A_pp": deltas}, flush=True)


if __name__ == "__main__":
    main()
