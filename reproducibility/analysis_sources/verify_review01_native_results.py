"""Preserve and independently recount the four existing Review01 native evaluations."""
import hashlib
import json
import shutil
import statistics
from pathlib import Path
from verify_result_arithmetic import native, check

R = Path("__EVIDENCE_SOURCE_ROOT__")
S = R.parent / "MIRAGE-V2/scratch"
OUT = R / "09_cpu_preparation/review01_native_results_v1"


def main():
    if OUT.exists():
        raise ValueError("Do not overwrite native archive")
    OUT.mkdir()
    records, errors = [], []
    for seed in range(1, 5):
        source = S / f"cag_seed_{seed}_a1e_b2p_eval_summary.json"
        rec = json.loads(source.read_text(encoding="utf-8"))
        shutil.copyfile(source, OUT / source.name)
        arms = {}
        for arm in ("A1E", "B2P"):
            original = rec["arms"][arm]
            gate = Path(original["execution"]["path"])
            geom = Path(original["geometry"]["path"])
            hashes = {"execution": hashlib.sha256(gate.read_bytes()).hexdigest(), "geometry": hashlib.sha256(geom.read_bytes()).hexdigest()}
            assert all(hashes[k] == original[k]["sha256"] for k in hashes), "Native result bytes changed"
            n = native(gate, geom, expected=500)
            for p in (gate, geom):
                shutil.copyfile(p, OUT / f"seed{seed}_{arm}_{p.name}")
            for key in ("syntax_ok", "exec_ok", "build_ok", "solid_valid", "step_export_ok"):
                check(n["metrics"][key + "_pct"], original["execution"][key + "_pct"], key)
            gr = original["geometry"]
            check(n["metrics"]["scoreable_pct"], gr["pointcloud_scored_pct"], "scoreable")
            check(n["metrics"]["conditional_median_cd"], gr["median_cd"], "median CD")
            check(n["metrics"]["conditional_median_f1_pct"], gr["median_f1"] * 100, "median F1")
            check(n["metrics"]["unconditional_mean_f1_pct"], gr["unconditional_f1_mean"] * 100, "uncond F1")
            arms[arm] = n
        ids = arms["A1E"]["ids"]
        assert ids == arms["B2P"]["ids"]
        joint = [sid for sid in ids if all(sid in arms[a]["scoreable"] for a in arms)]
        assert len(joint) == rec["paired"]["jointly_scoreable_n"]
        paired = {}
        for arm in arms:
            for key, stat_name in (("cd", "median_cd"), ("f_score_1pct", "median_f1")):
                value = statistics.median(arms[arm]["scoreable"][sid][key] for sid in joint)
                check(value, rec["paired"][f"{arm}_paired_{stat_name}"], "paired")
                paired[f"{arm}_{stat_name}"] = value
        records.append({"seed": seed, "source_summary_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "arms": {a: v["metrics"] for a,v in arms.items()}, "joint_n": len(joint), "paired": paired})
    aggregate = {}
    for endpoint in ("build_ok_pct", "step_export_ok_pct", "unconditional_mean_f1_pct"):
        aggregate[endpoint] = {arm: {"mean": statistics.mean(r["arms"][arm][endpoint] for r in records), "sample_sd": statistics.stdev(r["arms"][arm][endpoint] for r in records)} for arm in ("A1E", "B2P")}
    report = {"status": "PASS_RECORDED_NATIVE_BYTES_AND_ARITHMETIC", "gate_rows_checked": 4000, "geometry_rows_checked": 4000,
              "per_seed": records, "aggregate": aggregate, "comparison_control_status": "HOLD_STRICT_MATCH_CLAIM_UNCHANGED",
              "historical_prediction_weight_binding": "NOT_ESTABLISHED_BY_THIS_RECOUNT"}
    (OUT / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (OUT / "artifact_manifest.json").write_text(json.dumps([{"name": p.name,"sha256": hashlib.sha256(p.read_bytes()).hexdigest(),"bytes": p.stat().st_size} for p in OUT.iterdir() if p.is_file()], indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "aggregate": aggregate}, indent=2))


if __name__ == "__main__":
    main()
