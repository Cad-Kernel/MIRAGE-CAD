#!/usr/bin/env python3
"""Read-only CPU audit of the eight human-run Review/04 geometry evaluations."""
from collections import Counter, defaultdict
import json
import math
import os
from pathlib import Path
import re
import sys

PACKAGE = Path(__file__).resolve().parents[1]
SOURCE = Path("__RUN_SOURCE_ROOT__")
IMPLEMENTATION = Path("__DEV_ROOT__/src/training_25k")
SCRATCH = IMPLEMENTATION.parent.parent / "scratch"
STAGING = Path("/mnt/c/tmp/MIRAGE/geometry_nbest")
sys.path.insert(0, str(IMPLEMENTATION))
import cag_exposure_inference as inference
import cag_summarize_b0_b2_fullstack_eval as prior_metrics
from cag_exposure_policy_core import (
    FrozenInputs, read_json, read_rows, record, reject_existing, require,
    sha, value_sha, verify_record, write_json_new,
)
from register_exposure_gate_results import read_cli_log

FLAGS = prior_metrics.FLAGS
METRICS = ("cd", "f_score_1pct", "bbox_err", "target_bbox_diag", "gen_bbox_diag", "bbox_ratio_to_gt")
describe = prior_metrics.describe
sign_p = prior_metrics.sign_p


def finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def scoreable(row):
    return (row.get("has_target") is True and all(row.get(k) is True for k in FLAGS)
            and finite_number(row.get("cd")) and finite_number(row.get("f_score_1pct")))


def ordered_rows(rows, expected_ids, label):
    require([r["sample_id"] for r in rows] == expected_ids
            and len(rows) == len(set(expected_ids)), f"{label}: ID/order/count/uniqueness mismatch")


def paired(a, b, lower):
    require(len(a) == len(b), "Unequal paired lengths")
    require(all(finite_number(x) for x in a + b), "Nonfinite paired metric")
    delta = [y - x for x, y in zip(a, b)]
    ties = sum(abs(x) <= 1e-12 for x in delta)
    wins = sum(x < -1e-12 if lower else x > 1e-12 for x in delta)
    losses = len(delta) - wins - ties
    return {"n": len(delta), "A": describe(a), "B": describe(b),
            "delta_B_minus_A": describe(delta), "B_wins": wins, "A_wins": losses,
            "ties": ties, "non_tied": wins + losses,
            "sign_test_p_two_sided": sign_p(wins, losses)}


def audit_geometry(rows, gate_rows, inputs, predictions, expected_ids, modality):
    for label, data in (("geometry", rows), ("gate", gate_rows), ("input", inputs), ("prediction", predictions)):
        ordered_rows(data, expected_ids, label)
    flat, errors, stages = {}, Counter(), Counter()
    mismatches, failure_ids = [], defaultdict(list)
    for row, gate, inp, pred in zip(rows, gate_rows, inputs, predictions):
        sid = row["sample_id"]
        require(row.get("modality") == inp.get("modality") == pred.get("modality") == modality,
                f"Wrong modality: {sid}")
        require(inp.get("all_candidates") == [pred["prediction"]], f"N=1 prediction/input mismatch: {sid}")
        candidates = row.get("candidate_results")
        # A native kernel-crash record has no candidate; preserve it as an unscoreable case.
        crashed = str(row.get("error", "")).startswith("kernel access")
        if crashed:
            require(candidates == [] and row.get("has_target") is None, "Invalid native crash record")
            c = {k: False for k in FLAGS}
            c.update({k: None for k in METRICS})
            c.update(error=row["error"], has_target=None)
        else:
            require(isinstance(candidates, list) and len(candidates) == 1, f"Expected one candidate: {sid}")
            c = {**candidates[0], "has_target": row.get("has_target")}
            require(type(c["has_target"]) is bool, "Invalid target status")
            require(all(type(c.get(k)) is bool for k in FLAGS), "Invalid gate flag type")
            require(all(not c[FLAGS[i]] or c[FLAGS[i - 1]] for i in range(1, len(FLAGS))), "Non-monotonic gates")
            require(isinstance(c.get("error"), str), "Missing native error field")
            require(all(c.get(k) is None or finite_number(c[k]) for k in METRICS), "Nonfinite/bool native metric")
            if c.get("cd") is not None:
                require(c["cd"] >= 0, "Negative CD")
            if c.get("f_score_1pct") is not None:
                require(0 <= c["f_score_1pct"] <= 1, "F@1 outside [0,1]")
            if c.get("cd") is not None or c.get("f_score_1pct") is not None:
                require(scoreable(c), "Metric exists without valid target/all gates/complete metrics")
        differing = [k for k in FLAGS if gate[k] != c[k]]
        if differing:
            mismatches.append({"sample_id": sid, "flags": differing,
                               "standalone_gate": gate, "geometry_run": c})
        if crashed:
            stage = "kernel_crash"
        elif not all(c[k] for k in FLAGS):
            stage = next(k + "_failure" for k in FLAGS if not c[k])
        elif not c["has_target"]:
            stage = "missing_target"
        elif not scoreable(c):
            stage = "post_export_geometry_failure"
        else:
            stage = "scoreable"
        if stage == "scoreable":
            require(not c["error"], "Scored result has a failure message")
        else:
            require(bool(c["error"]) or stage == "missing_target", "Unscoreable case lacks error")
            errors[c["error"] or "MISSING_TARGET_NO_NATIVE_ERROR"] += 1
            failure_ids[stage].append(sid)
        stages[stage] += 1
        flat[sid] = c
    scored = {sid: c for sid, c in flat.items() if scoreable(c)}
    result = {"rows": len(rows), "scoreable": len(scored), "scoreable_pct": 100 * len(scored) / len(rows),
        "gate_counts_from_geometry_run": {k: sum(c[k] for c in flat.values()) for k in FLAGS},
        "rows_with_target": sum(c["has_target"] is True for c in flat.values()),
        "missing_target_ids": [sid for sid, c in flat.items() if c["has_target"] is False],
        "kernel_crash_ids": [sid for sid, c in flat.items() if c["has_target"] is None],
        "first_failure_stage_counts": dict(stages), "failure_ids_by_stage": dict(failure_ids),
        "non_scoreable_exact_error_counts": dict(errors.most_common()),
        "scoreable_ids": list(scored),
        "export_but_unscoreable_ids": [sid for sid, c in flat.items() if c["step_export_ok"] and not scoreable(c)],
        "conditional": {k: describe([c[k] for c in scored.values() if finite_number(c.get(k))]) for k in METRICS},
        "unconditional_f_score_1pct": describe([c["f_score_1pct"] if scoreable(c) else 0.0 for c in flat.values()]),
        "standalone_vs_geometry_gate_mismatches": mismatches,
        "extreme_cd_cases_gt_1000": [dict(sample_id=sid, **c) for sid, c in scored.items() if c["cd"] > 1000],
        "cd_zero_ids": [sid for sid, c in scored.items() if c["cd"] == 0],
        "f1_zero_ids": [sid for sid, c in scored.items() if c["f_score_1pct"] == 0],
        "f1_one_ids": [sid for sid, c in scored.items() if c["f_score_1pct"] == 1]}
    return result, flat


def write_text_new(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(content)


def fmt(x):
    return "NA" if x is None else f"{x:.12g}"


def full_markdown(result):
    lines = ["# Review/04 Full Evaluation Results", "", "Closure record: 2026-10-22. Status: CLOSED. Audit: PASS.", "",
        "One paired training seed (42); 2500 fixed source IDs, four modalities, two arms. All eight gate and eight geometry runs were performed manually by the operator. This registrar only read artifacts and calculated CPU statistics; it did not run models or CAD programs.", "",
        "## Definitions And Scope", "",
        "A = STEP-first then balanced continuation; B = balanced from the start. Both plan branches ran actual4689+500 optimizer updates, with the same optimizer/scheduler reset and LR boundary. Each Stage4b ran actual1182 updates,3150 fixed-role rows x3 epochs. Shared upstreams/initialization/GT-plan Stage4 are unchanged. This changes cumulative modality exposure as well as its order; it is not a pure order-only ablation or a full-stack architecture comparison.", "",
        "Syntax/Execute/Build/Solid/STEP export below come from standalone gate evaluation. Scoreable requires a readable reference, all five geometry-run gates, finite CD and F@1. Conditional metrics use each arm's own scoreable set. Paired geometry uses only the same jointly scoreable IDs. Unconditional F@1 uses all2500 cases, assigning zero to non-scoreable cases. F@1 is shown in percent in the main table; full distributions preserve raw0-1 fractions.", "",
        "CD is0.5*mean(d(P,Q)^2)+0.5*mean(d(Q,P)^2), with no post-hoc rescaling/alignment/normalization. F@1 uses a distance threshold of1% of the target sampled-cloud bbox diagonal. Target NPZ clouds are downsampled to1024 with RandomState42 when needed; generated clouds are sampled by the native part API at1024 points, with no sampling seed exposed by this evaluator. Bbox error is mean absolute axis-extent error. Bbox ratio is generated/target sampled-cloud bbox diagonal. Preserve native units and distinguish this evaluation sampling from the fixed inference input cache.", "",
        "No clipping, winsorization, outlier exclusion, target repair or row filtering was performed. CD>1000 is a retrospective inventory flag inherited from earlier revision summaries, not a threshold used for scoring, selection or significance. Exact case-level sign/McNemar tests below are descriptive, unadjusted for multiple comparisons, and do not measure training-seed uncertainty. Four modalities are not four independent training seeds.", "",
        "## Complete Coverage And Primary Geometry", "",
        "All coverage denominators are2500. CD/F@1 medians use the arm-specific scoreable subset.", "",
        "| Modality | Arm | Syntax count (%) | Execute count (%) | Build count (%) | Solid count (%) | Export count (%) | Scoreable count (%) | Median CD | Median F@1 (%) | Unconditional mean F@1 (%) |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for modality in inference.MODALITIES:
        for arm in ("A", "B"):
            g = result["groups"][arm][modality]
            n = g["geometry"]["rows"]
            counts = g["gate"]["native_summary"]
            values = [f"{counts[k+'_count']} ({100*counts[k+'_count']/n:.2f})" for k in FLAGS]
            v = g["geometry"]
            lines.append(f"| {modality} | {arm} | " + " | ".join(values)
                + f" | {v['scoreable']} ({v['scoreable_pct']:.2f}) | {fmt(v['conditional']['cd'].get('median'))}"
                + f" | {fmt(100*v['conditional']['f_score_1pct'].get('median',0))} | {fmt(100*v['unconditional_f_score_1pct'].get('mean',0))} |")
    lines += ["", "## Deltas B Minus A", "",
        "Coverage/F@1 differences are percentage points; CD stays in native squared-distance units. Full-set conditional differences compare different arm-specific successful subsets; do not confuse them with paired differences.", "",
        "| Modality | Syntax pp | Build pp | Export pp | Scoreable pp | Conditional median CD | Conditional median F@1 pp | Unconditional mean F@1 pp |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for modality, d in result["delta_B_minus_A"].items():
        lines.append(f"| {modality} | " + " | ".join(fmt(d[k]) for k in
            ("syntax_ok_pp", "build_ok_pp", "step_export_ok_pp", "scoreable_pp", "conditional_median_cd", "conditional_median_f1_pp", "unconditional_mean_f1_pp")) + " |")
    lines += ["", "## Jointly Scoreable Paired Geometry", "",
        "All distributions are raw evaluator units (F@1 fractions, not percent). A/B medians in this table use identical IDs. Median(B-A) is not generally median(B)-median(A). Ties use absolute difference<=1e-12.", "",
        "| Modality | Metric | N | A median | B median | Median paired B-A | B wins | A wins | Ties | Two-sided exact sign p |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for modality, p in result["paired_geometry"].items():
        for k, v in p["metrics"].items():
            lines.append(f"| {modality} | {k} | {v['n']} | {fmt(v['A'].get('median'))} | {fmt(v['B'].get('median'))} | {fmt(v['delta_B_minus_A'].get('median'))} | {v['B_wins']} | {v['A_wins']} | {v['ties']} | {fmt(v['sign_test_p_two_sided'])} |")
    lines += ["", "## All Metric Distributions", "",
        "Sample SD describes variation between scored cases, not training-run uncertainty. Quantiles use linear interpolation at(n-1)*p. F@1 values here are fractions.", "",
        "| Modality | Arm | Set/metric | N | Mean | Median | Sample SD | Min | Q25 | Q75 | Q95 | Q99 | Max |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for modality in inference.MODALITIES:
        for arm in ("A", "B"):
            geom = result["groups"][arm][modality]["geometry"]
            dist = {"conditional/"+k: v for k, v in geom["conditional"].items()}
            dist["unconditional/f_score_1pct"] = geom["unconditional_f_score_1pct"]
            dist.update({"paired/"+k: v[arm] for k, v in result["paired_geometry"][modality]["metrics"].items()})
            for k, v in dist.items():
                lines.append(f"| {modality} | {arm} | {k} | {v['n']} | " + " | ".join(fmt(v.get(x)) for x in ("mean","median","sd_sample","min","q25","q75","q95","q99","max")) + " |")
    lines += ["", "## Paired Gate Tables", "",
        "| Modality | Flag | Both pass | A only | B only | Both fail | Exact McNemar p |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |"]
    for m, gates in result["paired_gate"].items():
        for k, v in gates.items():
            lines.append(f"| {m} | {k} | {v['both_pass']} | {v['A_only']} | {v['B_only']} | {v['both_fail']} | {fmt(v['exact_McNemar_p_two_sided'])} |")
    lines += ["", "## Failure Inventories And Native Run Metadata", "",
        "Every exact native error string/count follows. All failure IDs, scored IDs, export-but-unscoreable IDs, zero/one-F@1 IDs, extreme-CD cases and every raw gate/geometry record are retained in the summary/per-case JSON files; no case is omitted. Native error text is an evaluator outcome, not an independently validated causal taxonomy."]
    for m in inference.MODALITIES:
        for arm in ("A", "B"):
            group = result["groups"][arm][m]
            g = group["geometry"]
            lines += ["", f"### {m} / {arm}", "",
                f"Scoreable={g['scoreable']}; target-present={g['rows_with_target']}; missing-target={len(g['missing_target_ids'])}; kernel-crashes={len(g['kernel_crash_ids'])}; export-but-unscoreable={len(g['export_but_unscoreable_ids'])}; gate/geometry flag-mismatch cases={len(g['standalone_vs_geometry_gate_mismatches'])}; CD>1000 scored cases={len(g['extreme_cd_cases_gt_1000'])}.",
                f"First failure stages: `{json.dumps(g['first_failure_stage_counts'],sort_keys=True)}`.",
                f"Geometry-run gate counts: `{json.dumps(g['gate_counts_from_geometry_run'],sort_keys=True)}`.",
                f"Native gate runtime seconds={group['gate']['native_summary']['runtime_seconds']}; native geometry Python={group['native_python_version']}. Geometry runtime is not separately measured by this script; no wall-time estimate is invented.",
                f"Retained last-attempt geometry resume messages: `{json.dumps(group['resume_log_lines'])}`. The last log is not a complete independent retry history.", "",
                "| Count | Exact error |", "| ---: | --- |"]
            for error, count in g["non_scoreable_exact_error_counts"].items():
                lines.append(f"| {count} | " + error.replace("|", "\\|").replace("\n", " ").replace("\r", " ") + " |")
    lines += ["", "## Full Paths And SHA256", "",
        "WSL source checkout: `__RUN_SOURCE_ROOT__`; Windows source checkout: `__DEV_ROOT__`; evidence package: `__EVIDENCE_SOURCE_ROOT__\\04`. Release records retain historical Git/dirty-tree/source inventories; hashes, not an assumed clean commit, identify the executed sources. Do not substitute another checkout when publishing.", "",
        "Training implementation: `src/training_25k/cag_exposure_policy.py`, B-only continuation `cag_exposure_policy_b_only.py`, isolated Stage4b `cag_stage4b_execution.py`, training packer `cag_stage4b_packing_v1.py`; inference `cag_exposure_inference.py`. Exact source hashes are bound through `dependencies` and the immutable training/prediction records, not newly inferred from file names.", "",
        "| Artifact | Path | SHA256 |", "| --- | --- | --- |"]
    authorities = {"gate_registration": result["gate_registration"], "prediction_registration": result["prediction_registration"],
        "final_registrar": result["registration_script"], "final_tests": result["test_report"],
        "prior_metric_helpers": result["metric_helper_source"], **result["evaluator_sources"]}
    for k, item in authorities.items():
        lines.append(f"| {k} | `{item['path']}` | `{item['sha256']}` |")
    for arm in ("A", "B"):
        for m in inference.MODALITIES:
            g = result["groups"][arm][m]
            for k, item in {**g["files"], "geometry_input":g["geometry_input"],"prediction":g["prediction"],"staged_input":g["staged_input"],"staged_evaluator":g["staged_evaluator"]}.items():
                lines.append(f"| {arm}/{m}/{k} | `{item['path']}` | `{item['sha256']}` |")
            for k, item in g["gate"]["files"].items():
                lines.append(f"| {arm}/{m}/gate/{k} | `{item['path']}` | `{item['sha256']}` |")
    for k, item in result["paired_cases"].items():
        lines.append(f"| paired_cases/{k} | `{item['path']}` | `{item['sha256']}` |")
    lines += ["", "## Claim Boundaries", "",
        "This result answers whether the predeclared exposure policies change the modality profile in this single matched diagnostic. It cannot establish seed-level robustness, equivalence, broad external generalization, or that shared architecture alone caused the observed differences. Report every modality and retain syntax/export/scoreable/fidelity trade-offs even when Build increases. Whole-prompt test cropping differed between arms; this is a measured downstream behavior under the same decoding rule, not an arm-specific test-time packing change. The Stage4b post-freeze target-preserving training amendment and its timing remain disclosed in records10-16; it is not a test-time target-aware procedure.", "",
        "Original frozen62-file package remains unchanged. Both trained arm trees and both prediction trees were verified against their prior read-only inventories before and after this audit. Native evaluator sources and every previously registered gate artifact remain unchanged. No additional seed, new training, weight selection or evaluation retry was performed by this registrar.", ""]
    return "\n".join(lines)


def main():
    out = PACKAGE / "result"
    summary_path = out / "cag_exposure_policy_eval_summary.json"
    human_path = out / "01_complete_evaluation_results.md"
    test_path = PACKAGE / "execution/exposure_final_audit_tests_20261022.json"
    for path in (summary_path, human_path, *(out / f"paired_cases_{m}.jsonl" for m in inference.MODALITIES)):
        reject_existing(path)
    tests = read_json(test_path)
    require(tests["status"] == "PASS" and tests["failures"] == tests["errors"] == 0, "Final audit tests missing/failing")
    require(tests["audit_source"] == record(Path(__file__)), "Tests do not cover current audit source")
    verify_record(tests["test_source"])
    verify_record(tests["metric_helper_source"])
    os.chdir(SOURCE)
    print("CPU-only final audit: checking original seal, trained weights, predictions and eight geometry groups", flush=True)
    ctx = FrozenInputs(PACKAGE, SOURCE).guard()
    pred_path = PACKAGE / "execution/exposure_prediction_B_and_paired_completed_20261021.json"
    pred_reg = read_json(pred_path)
    gate_path = PACKAGE / "execution/exposure_gate_completed_20261021.json"
    gate_reg = read_json(gate_path)
    require(gate_reg["status"] == "ALL8_GATE_COMPLETE_VERIFIED_GEOMETRY_PENDING", "Wrong gate authority")
    verify_record(gate_reg["prediction_registration"])
    require(gate_reg["prediction_registration"] == record(pred_path), "Wrong prediction registration")
    deps = inference.checked_inputs(ctx)
    fp = inference.inference_fingerprint(deps)
    require(deps == pred_reg["dependencies"] == gate_reg["dependencies"]
            and fp == pred_reg["inference_fingerprint"] == gate_reg["inference_fingerprint"], "Source/model dependency drift")
    pre = read_json(PACKAGE / "execution/exposure_inference_preflight_v1.json")
    weights = pre["protected_training_inventory"]
    verify_record(weights)
    pred_inventory = pred_reg["predictions_read_only_inventory"]
    verify_record(pred_inventory)
    inventory = read_json(pred_inventory["path"])

    def verify_immutable():
        inference.verify_protected(ctx, read_json(weights["path"]))
        for arm in ("A", "B"):
            require(inference.verify_generation(ctx, arm, fp) == pred_reg["completions"][arm], "Prediction completion drift")
            inference.lineage.assert_tree_unchanged(inference.output_path(ctx, arm), inventory[arm])
        for item in pred_reg["manual_evaluator_sources_at_release"].values():
            verify_record(item)
        verify_record(gate_reg["registration_script"])
        verify_record(gate_reg["native_syntax_audit"])
        for by_modality in gate_reg["groups"].values():
            for group in by_modality.values():
                for item in group["files"].values():
                    verify_record(item)
                for key in ("prediction", "staged_input", "staged_evaluator"):
                    verify_record(group[key])

    verify_immutable()
    ids = [r["sample_id"] for r in ctx.splits["test"]]
    require(len(ids) == len(set(ids)) == 2500, "Wrong frozen test IDs")
    groups, raw, inputs_by_arm, flat = {}, {}, {}, {}
    geometry_snapshots = {}
    for arm in ("A", "B"):
        groups[arm], raw[arm], inputs_by_arm[arm], flat[arm] = {}, {}, {}, {}
        for m in inference.MODALITIES:
            output, staging = SCRATCH / f"geom_r04_{m}_{arm}", STAGING / f"geom_r04_{m}_{arm}"
            geometry_snapshots[str(output)] = inference.lineage.tree_snapshot(output)
            prediction = inference.output_path(ctx, arm) / f"test_code_{m}.jsonl"
            geom_input = inference.output_path(ctx, arm) / f"geom_input_{m}.jsonl"
            require(sha(staging / "input.jsonl") == sha(geom_input), "Geometry staged input differs from frozen export")
            require(sha(staging / "output.jsonl") == sha(output / "geometry_nbest_rows.jsonl"), "Geometry staged/exported rows differ")
            require(sha(staging / "evaluate_geometry_nbest.py")
                    == pred_reg["manual_evaluator_sources_at_release"]["evaluate_geometry_nbest.py"]["sha256"], "Geometry source drift")
            require(sha(staging / "cli.log") == sha(output / "cli.log"), "Staged/exported geometry logs differ")
            log = read_cli_log(output / "cli.log")
            runtime = re.search(r"Python runtime:\s*(\d+)\.(\d+)\.(\d+)", log)
            require(runtime is not None and runtime.groups() == ("3", "11", "11"), "Wrong native geometry interpreter")
            require("Done. Script executed successfully." in log, "Geometry success marker missing")
            gate_group = gate_reg["groups"][arm][m]
            gate_rows = read_rows(gate_group["files"]["execution_rows.jsonl"]["path"])
            rows, inp, preds = read_rows(output / "geometry_nbest_rows.jsonl"), read_rows(geom_input), read_rows(prediction)
            audit, flattened = audit_geometry(rows, gate_rows, inp, preds, ids, m)
            require(audit["rows_with_target"] == 2500 and not audit["kernel_crash_ids"], "Incomplete target/geometry coverage; investigate before closing")
            inflight = staging / "output.inflight"
            visited = inflight.read_text(encoding="utf-8").splitlines()
            require(set(visited) == set(ids), "Native inflight trace misses frozen IDs or includes unknown IDs")
            groups[arm][m] = {"gate": gate_group, "geometry": audit,
                "files": {name: record(output / name) for name in ("geometry_nbest_rows.jsonl", "cli.log")},
                "prediction": record(prediction), "geometry_input": record(geom_input),
                "staged_input": record(staging / "input.jsonl"), "staged_output": record(staging / "output.jsonl"),
                "staged_evaluator": record(staging / "evaluate_geometry_nbest.py"),
                "inflight_trace": record(inflight), "inflight_count": len(visited), "inflight_repeat_count": len(visited)-len(set(visited)),
                "native_python_version": ".".join(runtime.groups()),
                "resume_log_lines": [line for line in log.splitlines() if "already scored" in line and "resuming:" in line]}
            raw[arm][m], inputs_by_arm[arm][m], flat[arm][m] = rows, inp, flattened
            print(f"PASS {arm}/{m}:2500 ordered rows; target-present2500; scoreable{audit['scoreable']}; gate differences{len(audit['standalone_vs_geometry_gate_mismatches'])}", flush=True)
    pairs, deltas, paired_gate = {}, {}, {}
    for m in inference.MODALITIES:
        a, b = flat["A"][m], flat["B"][m]
        joint = [sid for sid in ids if scoreable(a[sid]) and scoreable(b[sid])]
        metrics = {}
        for k, lower in (("cd", True), ("f_score_1pct", False), ("bbox_err", True)):
            valid = [sid for sid in joint if finite_number(a[sid].get(k)) and finite_number(b[sid].get(k))]
            metrics[k] = {**paired([a[sid][k] for sid in valid], [b[sid][k] for sid in valid], lower), "sample_ids": valid}
        pairs[m] = {"jointly_scoreable_n": len(joint), "sample_ids": joint, "metrics": metrics}
        ga, gb = groups["A"][m], groups["B"][m]
        deltas[m] = {k+"_pp": 100*(gb["gate"]["native_summary"][k+"_count"]-ga["gate"]["native_summary"][k+"_count"])/2500 for k in FLAGS}
        deltas[m].update(scoreable_pp=gb["geometry"]["scoreable_pct"]-ga["geometry"]["scoreable_pct"],
            conditional_median_cd=gb["geometry"]["conditional"]["cd"]["median"]-ga["geometry"]["conditional"]["cd"]["median"],
            conditional_median_f1_pp=100*(gb["geometry"]["conditional"]["f_score_1pct"]["median"]-ga["geometry"]["conditional"]["f_score_1pct"]["median"]),
            unconditional_mean_f1_pp=100*(gb["geometry"]["unconditional_f_score_1pct"]["mean"]-ga["geometry"]["unconditional_f_score_1pct"]["mean"]))
        paired_gate[m] = {k: {**v, "exact_McNemar_p_two_sided": sign_p(v["B_only"],v["A_only"])} for k, v in gate_reg["paired_gate_tables"][m].items()}
    verify_immutable()
    for root, snapshot in geometry_snapshots.items():
        inference.lineage.assert_tree_unchanged(Path(root), snapshot)
    out.mkdir(parents=True, exist_ok=True)
    cases = {}
    for m in inference.MODALITIES:
        path = out / f"paired_cases_{m}.jsonl"
        gate_rows = {arm: read_rows(groups[arm][m]["gate"]["files"]["execution_rows.jsonl"]["path"]) for arm in ("A","B")}
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            for i, sid in enumerate(ids):
                row = {"sample_id": sid, "modality": m, "seed": 42, "row_1based": i+1, "arms": {}}
                for arm in ("A", "B"):
                    g, c = groups[arm][m], flat[arm][m][sid]
                    row["arms"][arm] = {"native_gate": gate_rows[arm][i], "native_geometry": raw[arm][m][i],
                        "scoreable": scoreable(c), "unconditional_f_score_1pct": c["f_score_1pct"] if scoreable(c) else 0.0,
                        "prediction_path": g["prediction"]["path"], "geometry_input_path": g["geometry_input"]["path"],
                        "reference_point_path": inputs_by_arm[arm][m][i].get("point_path"),
                        "native_gate_path": g["gate"]["files"]["execution_rows.jsonl"]["path"],
                        "native_geometry_path": g["files"]["geometry_nbest_rows.jsonl"]["path"]}
                stream.write(json.dumps(row, ensure_ascii=True, allow_nan=False, separators=(",", ":"))+"\n")
        cases[m] = record(path)
    result = {"created_utc": inference.original.now(), "status": "CLOSED", "audit_status": "PASS",
        "seed":42, "training_seed_pairs":1, "source_ids":2500, "rows_per_group":2500,
        "gate_groups":8, "geometry_groups":8, "total_gate_rows":20000, "total_geometry_rows":20000,
        "frozen_id_order_sha256": value_sha(ids), "inference_fingerprint":fp, "dependencies":deps,
        "gate_registration":record(gate_path), "prediction_registration":record(pred_path),
        "protected_training_inventory":weights, "predictions_read_only_inventory":pred_inventory,
        "registration_script":record(Path(__file__)), "test_report":record(test_path),
        "metric_helper_source":record(Path(prior_metrics.__file__)),
        "evaluator_sources":pred_reg["manual_evaluator_sources_at_release"],
        "groups":groups, "paired_geometry":pairs, "paired_gate":paired_gate, "delta_B_minus_A":deltas,
        "paired_cases":cases, "geometry_output_snapshots":geometry_snapshots,
        "checks": {key:"PASS" for key in ("original_seal_sources_and_model_lineage", "training_predictions_unchanged_before_after",
            "previous_gate_artifacts_unchanged", "all8_geometry_2500_ordered_unique_frozen_IDs", "all20000_references_readable",
            "all20000_N1_prediction_associations", "all_staged_inputs_match_frozen_geometry_exports", "native_staged_exported_rows_logs_match",
            "native_geometry_sources_match_release", "native_python31111_and_success_markers", "metric_schema_ranges_finiteness",
            "all_rows_retained_no_outlier_filtering", "geometry_outputs_unchanged_during_audit")},
        "human_run_training_inference_gate_geometry":True, "model_forward_training_or_CAD_execution_by_registrar":False,
        "metric_definitions": {"scoreable":"reference + all5 geometry gates + finite CD/F@1",
            "CD":"0.5*mean(dPQ**2)+0.5*mean(dQP**2); native units; no rescaling",
            "F@1":"distance < 0.01*target sampled-cloud bbox diagonal; raw fraction",
            "unconditional_F@1":"all2500 frozen cases; zero for non-scoreable",
            "bbox_err":"mean absolute axis-extent error", "point_count":1024, "target_downsampling_seed":42,
            "generated_point_sampling_seed":"not exposed by native evaluator",
            "quantiles":"linear interpolation at(n-1)*p", "sample_SD":"ddof1 across cases, not seeds",
            "paired_tie_tolerance":1e-12, "tests":"exact two-sided sign/McNemar; descriptive/unadjusted query-level only"},
        "limitations":["One paired seed, not seed robustness or equivalence", "Four modalities share source IDs and trained models",
            "Exposure policy changes cumulative modality proportions as well as order", "Different arm-specific scoreable subsets for full conditional metrics",
            "Post-freeze Stage4b training packing amendment applies to both arms/roles/validation, not test inference",
            "Same whole-prompt test truncation rule; arm-specific crop counts are recorded in prediction authority",
            "No broad external-generalization claim", "No generated STEP/render assets retained by native temporary-directory scorer; use original code/IDs for later controlled gallery rendering"]}
    write_json_new(summary_path, result)
    write_text_new(human_path, full_markdown(result))
    print(f"CLOSED: {summary_path}", flush=True)
    print(json.dumps({"delta_B_minus_A":deltas, "paired_geometry":{m:{k:{f:v[f] for f in ('n','A_wins','B_wins','ties','sign_test_p_two_sided')} for k,v in p['metrics'].items()} for m,p in pairs.items()}},indent=2),flush=True)


if __name__ == "__main__":
    main()
