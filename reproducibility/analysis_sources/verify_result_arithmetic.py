"""Independent arithmetic from saved native per-case gate/geometry files. CPU only."""
import hashlib
import json
import math
import statistics
from pathlib import Path

R = Path("__EVIDENCE_SOURCE_ROOT__")
S = R.parent / "MIRAGE-V2/scratch"
OUT = R / "09_cpu_preparation/result_arithmetic_v1"


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def rows(p):
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def close(a, b):
    return math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-9)


def check(a, b, label):
    if not close(a, b):
        raise ValueError(f"{label}: {a} != {b}")


def native(gate_path, geom_path, expected=2500):
    gate, geom = rows(gate_path), rows(geom_path)
    ids = [r["sample_id"] for r in gate]
    assert len(gate) == len(geom) == len(set(ids)) == expected
    assert ids == [r["sample_id"] for r in geom]
    result = {k + "_pct": 100 * sum(bool(r[k]) for r in gate) / expected for k in ("syntax_ok", "exec_ok", "build_ok", "solid_valid", "step_export_ok")}
    scored = {}
    for r in geom:
        assert len(r["candidate_results"]) == 1
        c = r["candidate_results"][0]
        if r.get("has_target") and all(isinstance(c.get(k), (int, float)) and math.isfinite(c[k]) for k in ("cd", "f_score_1pct")):
            assert c["cd"] >= 0 and 0 <= c["f_score_1pct"] <= 1
            scored[r["sample_id"]] = c
    result["scoreable_pct"] = 100 * len(scored) / expected
    for label, key, scale in (("cd", "cd", 1), ("f1_pct", "f_score_1pct", 100), ("bbox_err", "bbox_err", 1)):
        vals = [c[key] * scale for c in scored.values()]
        assert all(math.isfinite(x) for x in vals)
        result["conditional_mean_" + label] = statistics.mean(vals)
        result["conditional_median_" + label] = statistics.median(vals)
    uncond = [scored[sid]["f_score_1pct"] * 100 if sid in scored else 0 for sid in ids]
    result["unconditional_mean_f1_pct"] = statistics.mean(uncond)
    result["unconditional_median_f1_pct"] = statistics.median(uncond)
    return {"metrics": result, "scoreable": scored, "ids": ids,
            "files": [{"path": str(p), "sha256": sha(p)} for p in (gate_path, geom_path)]}


def main():
    if OUT.exists():
        raise ValueError("Do not overwrite arithmetic audit")
    OUT.mkdir()
    checked_seeds = []
    collected = {arm: {} for arm in ("B0", "B2")}
    agg = load(R / "03/result/cag_b0_b2_four_seed_eval_summary.json")
    native_rows = 0
    for seed in range(1, 5):
        recorded = load(R / f"03/result/cag_b0_b2_seed_{seed}_eval_summary.json")
        groups = {arm: native(S / f"exec_b0b2_step_{arm}_s{seed}/execution_rows.jsonl", S / f"geom_b0b2_step_{arm}_s{seed}/geometry_nbest_rows.jsonl") for arm in ("B0", "B2")}
        native_rows += 5000
        assert groups["B0"]["ids"] == groups["B2"]["ids"]
        joint = [sid for sid in groups["B0"]["ids"] if sid in groups["B0"]["scoreable"] and sid in groups["B2"]["scoreable"]]
        assert len(joint) == recorded["paired_geometry"]["jointly_scoreable_n"]
        for arm, group in groups.items():
            v = group["metrics"]
            for k in ("syntax_ok", "exec_ok", "build_ok", "solid_valid", "step_export_ok"):
                check(v[k + "_pct"], recorded["arms"][arm]["execution_summary"][k + "_rate"] * 100, f"{seed}/{arm}/{k}")
            gr = recorded["arms"][arm]["geometry"]
            check(v["scoreable_pct"], gr["scoreable_pct"], "scoreable")
            for label, key, scale in (("cd", "cd", 1), ("f1_pct", "f_score_1pct", 100), ("bbox_err", "bbox_err", 1)):
                for stat in ("mean", "median"):
                    check(v[f"conditional_{stat}_{label}"], gr["conditional"][key][stat] * scale, f"conditional/{key}/{stat}")
            for stat in ("mean", "median"):
                check(v[f"unconditional_{stat}_f1_pct"], gr["unconditional_f_score_1pct"][stat] * 100, "unconditional")
            for label, key, scale in (("cd", "cd", 1), ("f1_pct", "f_score_1pct", 100)):
                vals = [group["scoreable"][sid][key] * scale for sid in joint]
                for stat, fn in (("mean", statistics.mean), ("median", statistics.median)):
                    v[f"paired_{stat}_{label}"] = fn(vals)
                    check(fn(vals), recorded["paired_geometry"][key][arm][stat] * scale, "paired")
            for endpoint, value in v.items():
                collected[arm].setdefault(endpoint, []).append(value)
        checked_seeds.append({"seed": seed, "joint_n": len(joint), "arms": {arm: {"metrics": g["metrics"], "files": g["files"]} for arm, g in groups.items()}})
    aggregate_checks = []
    for endpoint, item in agg["metrics"].items():
        vals = {arm: collected[arm][endpoint] for arm in ("B0", "B2")}
        vals["delta_B2_minus_B0"] = [b - a for a, b in zip(vals["B0"], vals["B2"])]
        for arm, numbers in vals.items():
            check(statistics.mean(numbers), item[arm]["mean"], f"aggregate/{endpoint}/{arm}/mean")
            check(statistics.stdev(numbers), item[arm]["sd_sample"], f"aggregate/{endpoint}/{arm}/sd")
            aggregate_checks.append({"endpoint": endpoint, "arm": arm, "per_seed_values": numbers, "mean": statistics.mean(numbers), "sample_sd": statistics.stdev(numbers), "status": "PASS"})
    exposure = load(R / "04/result/cag_exposure_policy_eval_summary.json")
    exposure_checks = []
    for mod in ("step", "point", "text", "image"):
        groups = {}
        for arm in ("A", "B"):
            group = native(S / f"exec_r04_{mod}_{arm}/execution_rows.jsonl", S / f"geom_r04_{mod}_{arm}/geometry_nbest_rows.jsonl")
            groups[arm] = group
            g = exposure["groups"][arm][mod]
            for key in ("syntax_ok", "exec_ok", "build_ok", "solid_valid", "step_export_ok"):
                check(group["metrics"][key + "_pct"], g["gate"]["native_summary"][key + "_rate"] * 100, f"R04/{mod}/{arm}/{key}")
            check(group["metrics"]["scoreable_pct"], g["geometry"]["scoreable_pct"], "R04 scoreable")
            for key, stat in (("cd", "median"), ("f_score_1pct", "median")):
                label, scale = ("cd", 1) if key == "cd" else ("f1_pct", 100)
                check(group["metrics"][f"conditional_{stat}_{label}"], g["geometry"]["conditional"][key][stat] * scale, "R04 conditional")
            check(group["metrics"]["unconditional_mean_f1_pct"], g["geometry"]["unconditional_f_score_1pct"]["mean"] * 100, "R04 unconditional")
        assert groups["A"]["ids"] == groups["B"]["ids"]
        exposure_checks.append({"modality": mod, "arms": {arm: {"metrics": g["metrics"], "files": g["files"]} for arm, g in groups.items()}, "status": "PASS"})
    output = {"status": "PASS_NATIVE_ROW_AND_SEED_ARITHMETIC", "review03_native_gate_rows": native_rows,
              "review03_native_geometry_rows": native_rows, "review04_native_gate_rows": 20000, "review04_native_geometry_rows": 20000,
              "review03_seed_checks": checked_seeds, "review03_aggregate_checks": aggregate_checks,
              "review04_checks": exposure_checks, "no_CAD_execution_or_model_run": True,
              "limitations": ["Does not establish historical checkpoint binding", "Review01 raw metrics not re-audited in this script", "Does not convert four seeds into population-level significance"]}
    (OUT / "summary.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in output.items() if not isinstance(v, list)}, indent=2), flush=True)


if __name__ == "__main__":
    main()
