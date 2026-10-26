#!/usr/bin/env python3
"""Audit and summarize the four frozen Review/03 B0/B2 evaluation runs."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics as st
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


FLAGS = ("syntax_ok", "exec_ok", "build_ok", "solid_valid", "step_export_ok")
ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_rows(path: Path, expected_ids: list[str]) -> dict[str, dict]:
    with path.open(encoding="utf-8-sig") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    ids = [r["sample_id"] for r in rows]
    if ids != expected_ids or len(set(ids)) != len(ids):
        raise ValueError(f"Row count, uniqueness, or frozen ID/order mismatch: {path}")
    return dict(zip(ids, rows))


def sign_p(wins: int, losses: int) -> float:
    n = wins + losses
    if not n:
        return 1.0
    k = min(wins, losses)
    # Divide integer sums only at the end; no overflowing float combinations.
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / (1 << n))


def describe(values: list[float]) -> dict:
    if not values:
        return {"n": 0}
    ordered = sorted(values)

    def quantile(p: float) -> float:
        pos = (len(ordered) - 1) * p
        lo, hi = math.floor(pos), math.ceil(pos)
        return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)

    return {
        "n": len(values), "mean": st.fmean(values), "median": st.median(values),
        "sd_sample": st.stdev(values) if len(values) > 1 else None,
        "min": ordered[0], "max": ordered[-1],
        **{f"q{int(p * 100)}": quantile(p) for p in (.25, .75, .95, .99)},
    }


def scoreable(c: dict) -> bool:
    return all(c.get(k) is True for k in FLAGS) and all(
        isinstance(c.get(k), (int, float)) and math.isfinite(c[k])
        for k in ("cd", "f_score_1pct")
    )


def comparisons(a: list[float], b: list[float], lower: bool) -> dict:
    delta = [y - x for x, y in zip(a, b)]
    ties = sum(abs(d) <= 1e-12 for d in delta)
    wins = sum(d < -1e-12 if lower else d > 1e-12 for d in delta)
    losses = len(delta) - wins - ties
    return {
        "n": len(delta), "B0": describe(a), "B2": describe(b),
        "delta_B2_minus_B0": describe(delta), "B2_wins": wins,
        "B0_wins": losses, "ties": ties, "non_tied": wins + losses,
        "sign_test_p_two_sided": sign_p(wins, losses),
    }


def dump_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + "\n",
                    encoding="utf-8")


def audit_seed(seed: int, source: Path, scratch: Path, out: Path,
               expected_ids: list[str], created: str) -> dict:
    base = source / f"outputs/b0_b2_fullstack_s{seed}"
    actual_path = base / f"cag_b0_b2_seed_{seed}_actuals.json"
    actual = read_json(actual_path)
    if actual["seed"] != seed or actual["status"] != "GENERATION_COMPLETE_NEEDS_GATE_AND_GEOMETRY":
        raise ValueError(f"Generation actuals mismatch: {actual_path}")
    for record in actual["outputs"].values():
        if isinstance(record, dict) and "path" in record and "sha256" in record:
            if digest(source / record["path"]) != record["sha256"]:
                raise ValueError(f"Generation output changed: {record['path']}")
    n = len(expected_ids)
    result = {
        "seed": seed, "status": "EVALUATION_COMPLETE", "created_utc": created,
        "expected_rows": n, "generation_actuals_path": str(actual_path),
        "generation_actuals_sha256": digest(actual_path),
        "generation_actuals": actual, "arms": {}, "paired_gate": {},
        "evaluator_sources_at_analysis": {
            str(ROOT / rel): digest(ROOT / rel) for rel in (
                "scripts/evaluate_execution.ps1", "scripts/evaluate_geometry_nbest.ps1",
                "evaluate_geometry_nbest.py")
        },
    }
    exe, geom = {}, {}
    for arm in ("B0", "B2"):
        pred_record = actual["outputs"][arm.lower() + "_prediction"]
        geom_record = actual["outputs"][arm.lower() + "_geometry_input"]
        pred_path, input_path = source / pred_record["path"], source / geom_record["path"]
        preds = read_rows(pred_path, expected_ids)
        inputs = read_rows(input_path, expected_ids)
        for path, record in ((pred_path, pred_record), (input_path, geom_record)):
            if digest(path) != record["sha256"]:
                raise ValueError(f"Changed output hash: {path}")
        for sid in expected_ids:
            if inputs[sid]["all_candidates"] != [preds[sid]["prediction"]]:
                raise ValueError(f"Geometry code/prediction mismatch: {arm} {seed} {sid}")
        exec_dir = scratch / f"exec_b0b2_step_{arm}_s{seed}"
        geom_dir = scratch / f"geom_b0b2_step_{arm}_s{seed}"
        ep, gp, sp = (exec_dir / "execution_rows.jsonl",
                      geom_dir / "geometry_nbest_rows.jsonl", exec_dir / "execution_summary.json")
        e = read_rows(ep, expected_ids)
        raw_g = read_rows(gp, expected_ids)
        g = {}
        for sid, row in raw_g.items():
            if len(row.get("candidate_results", [])) != 1:
                raise ValueError(f"Expected N=1 candidate: {gp} {sid}")
            g[sid] = {**row["candidate_results"][0], "has_target": row.get("has_target")}
        summary = read_json(sp)
        if summary["rows"] != n:
            raise ValueError(f"Summary row mismatch: {sp}")
        e_counts = {k: sum(r[k] is True for r in e.values()) for k in FLAGS}
        for k in FLAGS:
            if e_counts[k] != summary[k + "_count"] or not math.isclose(
                e_counts[k] / n, summary[k + "_rate"], abs_tol=1e-12
            ):
                raise ValueError(f"Summary/rows mismatch: {sp} {k}")
        scored = {sid: c for sid, c in g.items() if scoreable(c)}
        if any(c.get("has_target") is not True for c in scored.values()):
            raise ValueError(f"Scoreable result without target: {gp}")
        if any(c["cd"] < 0 or not 0 <= c["f_score_1pct"] <= 1 for c in scored.values()):
            raise ValueError(f"Invalid geometry metric range: {gp}")
        u_f = [g[sid]["f_score_1pct"] if sid in scored else 0.0 for sid in expected_ids]
        failures = Counter(c.get("error") or "UNSPECIFIED" for sid, c in g.items() if sid not in scored)
        gg = {
            "rows": n, "scoreable": len(scored), "scoreable_pct": 100 * len(scored) / n,
            "gate_counts_from_geometry_run": {k: sum(c[k] is True for c in g.values()) for k in FLAGS},
            "missing_target_rows": sum(c.get("has_target") is not True for c in g.values()),
            "conditional": {k: describe([c[k] for c in scored.values() if isinstance(c.get(k), (int, float))
                                         and math.isfinite(c[k])])
                            for k in ("cd", "f_score_1pct", "bbox_err", "bbox_ratio_to_gt")},
            "unconditional_f_score_1pct": describe(u_f),
            "non_scoreable_error_counts": dict(failures.most_common()),
            "extreme_cd_cases_gt_1000": [dict(sample_id=sid, **c) for sid, c in scored.items() if c["cd"] > 1000],
            "export_but_unscoreable_ids": [sid for sid, c in g.items() if c["step_export_ok"] and sid not in scored],
        }
        result["arms"][arm] = {
            "files": {str(p): digest(p) for p in (ep, gp, sp, pred_path, input_path)},
            "execution_summary": summary, "execution_counts_recomputed": e_counts,
            "geometry": gg,
        }
        exe[arm], geom[arm] = e, g
    for k in FLAGS:
        both = sum(exe["B0"][sid][k] and exe["B2"][sid][k] for sid in expected_ids)
        b0 = sum(exe["B0"][sid][k] and not exe["B2"][sid][k] for sid in expected_ids)
        b2 = sum(not exe["B0"][sid][k] and exe["B2"][sid][k] for sid in expected_ids)
        result["paired_gate"][k] = {
            "both": both, "B0_only": b0, "B2_only": b2, "neither": n - both - b0 - b2,
            "delta_B2_minus_B0_pp": 100 * (b2 - b0) / n,
            "exact_McNemar_p_two_sided": sign_p(b2, b0),
        }
    joint = [sid for sid in expected_ids if scoreable(geom["B0"][sid]) and scoreable(geom["B2"][sid])]
    result["paired_geometry"] = {
        "jointly_scoreable_n": len(joint), "sample_ids": joint,
        **{k: comparisons([geom["B0"][sid][k] for sid in joint],
                          [geom["B2"][sid][k] for sid in joint], lower)
           for k, lower in (("cd", True), ("f_score_1pct", False), ("bbox_err", True))},
    }
    case_path = out / f"cag_b0_b2_seed_{seed}_paired_cases.jsonl"
    with case_path.open("w", encoding="utf-8", newline="\n") as f:
        for sid in expected_ids:
            row = {"sample_id": sid, "seed": seed, "modality": "step", "arms": {}}
            for arm in ("B0", "B2"):
                c = geom[arm][sid]
                row["arms"][arm] = {
                    "execution": exe[arm][sid], "geometry": c, "scoreable": scoreable(c),
                    "unconditional_f_score_1pct": c["f_score_1pct"] if scoreable(c) else 0.0,
                }
            f.write(json.dumps(row, ensure_ascii=True, allow_nan=False) + "\n")
    result["paired_cases_path"] = str(case_path)
    result["paired_cases_sha256"] = digest(case_path)
    result["audit_status"] = "PASS"
    dump_json(out / f"cag_b0_b2_seed_{seed}_eval_summary.json", result)
    return result


def metrics(r: dict, arm: str) -> dict[str, float]:
    a = r["arms"][arm]
    g = a["geometry"]
    p = r["paired_geometry"]
    return {
        **{k + "_pct": a["execution_summary"][k + "_rate"] * 100 for k in FLAGS},
        "scoreable_pct": g["scoreable_pct"],
        "conditional_mean_cd": g["conditional"]["cd"]["mean"],
        "conditional_median_cd": g["conditional"]["cd"]["median"],
        "conditional_mean_f1_pct": g["conditional"]["f_score_1pct"]["mean"] * 100,
        "conditional_median_f1_pct": g["conditional"]["f_score_1pct"]["median"] * 100,
        "unconditional_mean_f1_pct": g["unconditional_f_score_1pct"]["mean"] * 100,
        "unconditional_median_f1_pct": g["unconditional_f_score_1pct"]["median"] * 100,
        "paired_mean_cd": p["cd"][arm]["mean"],
        "paired_median_cd": p["cd"][arm]["median"],
        "paired_mean_f1_pct": p["f_score_1pct"][arm]["mean"] * 100,
        "paired_median_f1_pct": p["f_score_1pct"][arm]["median"] * 100,
        "conditional_mean_bbox_err": g["conditional"]["bbox_err"]["mean"],
        "conditional_median_bbox_err": g["conditional"]["bbox_err"]["median"],
    }


def aggregate(runs: list[dict], created: str) -> dict:
    m = {r["seed"]: {arm: metrics(r, arm) for arm in ("B0", "B2")} for r in runs}
    out = {
        "status": "CLOSED",
        "created_utc": created, "seeds": [r["seed"] for r in runs],
        "training_replicates": len(runs), "fixed_queries_per_seed": runs[0]["expected_rows"],
        "aggregation": "Equal-weight seed means; sample SD with ddof=1; no pooled model-level p-values",
        "metrics": {},
    }
    for key in next(iter(m.values()))["B0"]:
        a = [m[r["seed"]]["B0"][key] for r in runs]
        b = [m[r["seed"]]["B2"][key] for r in runs]
        lower = "cd" in key or "bbox" in key
        out["metrics"][key] = comparisons(a, b, lower)
        out["metrics"][key]["inference_note"] = "Sign test here uses training seeds, not individual queries"
    out["jointly_scoreable_cases_descriptive_total"] = sum(r["paired_geometry"]["jointly_scoreable_n"] for r in runs)
    return out


def gate_table(runs: list[dict]) -> list[str]:
    lines = ["| Seed | Arm | Syntax | Execute | Build | Solid | STEP export | Scoreable |",
             "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for r in runs:
        for arm in ("B0", "B2"):
            a = r["arms"][arm]
            n = r["expected_rows"]
            values = [f"{a['execution_counts_recomputed'][k]}/{n} ({100*a['execution_counts_recomputed'][k]/n:.2f}%)" for k in FLAGS]
            g = a["geometry"]
            lines.append(f"| {r['seed']} | {arm} | " + " | ".join(values) + f" | {g['scoreable']}/{n} ({g['scoreable_pct']:.2f}%) |")
    return lines


def seed_markdown(r: dict) -> str:
    seed = r["seed"]
    lines = [f"# Seed {seed} Evaluation Record", "", "Audit: PASS. Evaluation complete.", ""]
    lines += gate_table([r])
    lines += ["", "## Geometry", "", "| Metric | B0 | B2 | B2 - B0 |", "| --- | ---: | ---: | ---: |"]
    a, b = metrics(r, "B0"), metrics(r, "B2")
    for k in a:
        if k.endswith("_ok_pct") or k in ("solid_valid_pct", "scoreable_pct"):
            continue
        lines.append(f"| {k} | {a[k]:.10g} | {b[k]:.10g} | {b[k]-a[k]:.10g} |")
    lines += ["", "Percent metrics above use 0-100 units. CD/bbox remain in evaluator units. Conditional full-set and jointly scoreable metrics use different subsets.",
              "", "## Paired Tests", "", "Within-seed query-level tests below do not measure uncertainty across training seeds.", "",
              "| Gate | Both | B0 only | B2 only | Neither | Delta pp | Exact McNemar p |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for k, v in r["paired_gate"].items():
        lines.append(f"| {k} | {v['both']} | {v['B0_only']} | {v['B2_only']} | {v['neither']} | {v['delta_B2_minus_B0_pp']:.2f} | {v['exact_McNemar_p_two_sided']:.8g} |")
    p = r["paired_geometry"]
    lines += ["", f"Jointly scoreable: {p['jointly_scoreable_n']}.", "",
              "| Metric | B2 wins | B0 wins | Ties | Median paired difference B2 - B0 | Exact sign p |",
              "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for k in ("cd", "f_score_1pct", "bbox_err"):
        v = p[k]
        lines.append(f"| {k} | {v['B2_wins']} | {v['B0_wins']} | {v['ties']} | {v['delta_B2_minus_B0']['median']:.10g} | {v['sign_test_p_two_sided']:.8g} |")
    lines += ["", "F@1 paired differences in the last table use raw 0-1 units. Multiply by 100 for percentage points.",
              "", "## Distributions And Failures", "", "No CD values were removed, clipped, or winsorized. CD > 1000 is a retrospective audit flag, not an exclusion rule."]
    for arm in ("B0", "B2"):
        g = r["arms"][arm]["geometry"]
        lines += ["", f"### {arm}", "", "```json", json.dumps(g, indent=2, ensure_ascii=True), "```"]
    lines += ["", "## Provenance", "", f"Generation actuals: `{r['generation_actuals_path']}`.",
              f"Generation actuals SHA256: `{r['generation_actuals_sha256']}`.",
              f"All {r['expected_rows']} paired-case rows: `{r['paired_cases_path']}`."]
    for arm in ("B0", "B2"):
        lines += ["", f"{arm} files and SHA256:", "", "```json", json.dumps(r["arms"][arm]["files"], indent=2), "```"]
    lines += ["", "Evaluator-source hashes describe files present at analysis time; they are not a historical build attestation. See the frozen generation actuals and earlier run records for training-code provenance."]
    return "\n".join(lines) + "\n"


def full_markdown(runs: list[dict], agg: dict) -> str:
    lines = ["# B0 vs B2 Four-Seed Full Results", "", "Review/03; audited 2026-10-16. Seeds 1, 2, 3, 4; 2500 identical STEP queries per seed.",
             "", "Training, prediction, gate evaluation, and geometry scoring are complete for all four seeds.",
             "", "## Per-Seed Coverage", ""] + gate_table(runs)
    lines += ["", "## Equal-Weight Seed Aggregates", "", "All SD values use sample SD (ddof=1), with four training runs per arm. Percentages and F@1 are shown in 0-100 units.",
              "", "| Metric | B0 mean +/- SD | B2 mean +/- SD | Delta mean +/- SD | B2-favorable seeds | Seed-level sign p |",
              "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for key, v in agg["metrics"].items():
        a, b, d = v["B0"], v["B2"], v["delta_B2_minus_B0"]
        lines.append(f"| {key} | {a['mean']:.8g} +/- {a['sd_sample']:.8g} | {b['mean']:.8g} +/- {b['sd_sample']:.8g} | {d['mean']:.8g} +/- {d['sd_sample']:.8g} | {v['B2_wins']}/4 | {v['sign_test_p_two_sided']:.8g} |")
    lines += ["", "## Interpretation Boundaries", "",
              "- CD is the evaluator's symmetric mean squared nearest-neighbour distance, without rescaling in this analysis. F@1 is F-score at a threshold of 1% of the target bounding-box diagonal. Bounding-box error is mean absolute axis-extent error.",
              "- Report all endpoints, including syntax, raw mean CD, and bbox outcomes. A lower median CD does not imply better tails or a lower mean CD.",
              "- Raw means include catastrophic geometric outliers. Use medians and paired win counts alongside these means; do not retrospectively remove outliers or present robust metrics as proof of uniform superiority.",
              "- Full-set conditional metrics are calculated over each arm's own scoreable outputs. Paired metrics restrict both arms to the same jointly scoreable queries. Unconditional F@1 uses all 2500 queries, assigning zero to non-scoreable outputs.",
              "- Query-level sign/McNemar tests are within-run descriptive paired-case evidence. There are four training replicates, not 10000 independent model replications. Four same-direction seeds alone give a two-sided seed sign-test p of 0.125.",
              "- This is a replication of complete deployed conditions, not a fully compute-matched isolation of plan text. B2 has extra alignment/prior/plan stages and a code continuation. B0 trains with max_length 2048 while B2 code training uses 1536.",
              "- B2 Stage 4b mixes have seed-dependent row counts after grammar filtering. Preserve the actual counts and resulting update budgets. Do not claim identical total updates or total compute across B0/B2.",
              "- Program/code repair is disabled in both arms. B2 P1a plan canonicalization remains enabled and is logged. Do not describe all repair as disabled.",
              "- Scope is the fixed in-corpus STEP evaluation. These results do not establish broad external generalization or universal representation superiority.",
              "", "## Training And P1a Actuals", "",
              "| Seed | B2 Stage 4b rows | P1a ADD | P1a CUT | Touched samples |",
              "| --- | ---: | ---: | ---: | ---: |"]
    for r in runs:
        a = r["generation_actuals"]
        log = read_json(Path(r["generation_actuals_path"]).parent / f"predictions/repair_face_extrude_alias_log_step_s{r['seed']}.json")
        lines.append(f"| {r['seed']} | {a['outputs']['b2_stage4b_report']['train_rows']} | {log['counts']['ADD']} | {log['counts']['CUT']} | {len(log['touched_samples'])} |")
    lines += ["", "## Reproducibility", "", f"Source checkout: `{ROOT}`.",
              "WSL training checkout: `__RUN_SOURCE_ROOT__`.",
              "Train/generation wrapper: `training_25k/cag_run_b0_b2_fullstack_seed.sh` (frozen original hash retained in every generation actuals JSON).",
              f"Analysis script: `{Path(__file__).resolve()}`.", f"Analysis script SHA256: `{digest(Path(__file__))}`.",
              "Per-seed JSON includes all gate summaries, source-file hashes, metric distributions, exact error counts, extreme cases, paired subset IDs, and generation actuals. Paired-case JSONL preserves per-sample evaluation fields for all queries. Original raw outputs and CLI logs remain in their recorded scratch directories.",
              "", "## Full Per-Seed Detail", ""]
    for r in runs:
        lines.append(seed_markdown(r))
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-root", type=Path, required=True)
    ap.add_argument("--scratch-root", type=Path, default=ROOT.parent / "scratch")
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    test = args.source_root / "data/25k/test.jsonl"
    ids = [r["sample_id"] for r in (json.loads(line) for line in test.read_text(encoding="utf-8").splitlines() if line.strip())]
    if len(ids) != 2500 or len(set(ids)) != 2500:
        raise ValueError("Frozen test must contain 2500 unique IDs")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    created = datetime.now(timezone.utc).isoformat()
    runs = [audit_seed(seed, args.source_root, args.scratch_root, args.out_dir, ids, created)
            for seed in (1, 2, 3, 4)]
    script_hashes = [r["generation_actuals"]["scripts"] for r in runs]
    for rel in ("data/25k/train.jsonl", "data/25k/val.jsonl", "data/25k/test.jsonl"):
        hashes = {r["generation_actuals"]["data"][rel]["sha256"] for r in runs}
        if hashes != {digest(args.source_root / rel)}:
            raise ValueError(f"Across-seed frozen data hashes differ: {rel}")
    if any(s != script_hashes[0] for s in script_hashes[1:]):
        raise ValueError("Across-seed training-script hashes differ")
    agg = aggregate(runs, created)
    agg["audit_status"] = "PASS"
    agg["analysis_script_sha256"] = digest(Path(__file__))
    agg["per_seed_summary_paths"] = [str(args.out_dir / f"cag_b0_b2_seed_{r['seed']}_eval_summary.json") for r in runs]
    dump_json(args.out_dir / "cag_b0_b2_four_seed_eval_summary.json", agg)
    for r in runs:
        (args.out_dir / f"seed_{r['seed']}_full_results.md").write_text(seed_markdown(r), encoding="utf-8")
    (args.out_dir / "01_four_seed_full_results.md").write_text(full_markdown(runs, agg), encoding="utf-8")
    for r in runs:
        print(f"Seed {r['seed']}: audit PASS; jointly scoreable={r['paired_geometry']['jointly_scoreable_n']}")
        for arm in ("B0", "B2"):
            print(arm, json.dumps(metrics(r, arm), sort_keys=True))
        print("paired CD/F1:", json.dumps({k: {x: r["paired_geometry"][k][x] for x in ("B2_wins", "B0_wins", "ties", "sign_test_p_two_sided")} for k in ("cd", "f_score_1pct")}))
    print("Aggregate:", json.dumps(agg, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
