#!/usr/bin/env python3
"""Independent NumPy/SciPy recomputation directly from the native per-case files."""
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.stats import binomtest

PACKAGE = Path(__file__).resolve().parents[1]
FLAGS = ("syntax_ok", "exec_ok", "build_ok", "solid_valid", "step_export_ok")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def item(path):
    p = Path(path)
    return {"path": str(p), "bytes":p.stat().st_size, "sha256":hashlib.sha256(p.read_bytes()).hexdigest()}


def same(actual, expected):
    assert math.isclose(actual, expected, rel_tol=1e-11, abs_tol=1e-14), (actual, expected)


def distribution(values, stored):
    a = np.asarray(values, dtype=float)
    assert len(a) == stored["n"]
    if not len(a):
        return
    same(float(np.mean(a)), stored["mean"])
    same(float(np.median(a)), stored["median"])
    same(float(np.min(a)), stored["min"])
    same(float(np.max(a)), stored["max"])
    if len(a)>1:
        same(float(np.std(a,ddof=1)),stored["sd_sample"])
    else:
        assert stored["sd_sample"] is None
    for q in (25,75,95,99):
        same(float(np.quantile(a,q/100,method="linear")),stored[f"q{q}"])


def main():
    destination = PACKAGE / "execution/exposure_final_independent_verification_20261022.json"
    assert not destination.exists()
    path = PACKAGE / "result/cag_exposure_policy_eval_summary.json"
    r = read(path)
    assert r["status"] == "CLOSED" and r["audit_status"] == "PASS"
    groups, n_cases, native_records = {}, 0, {}
    for m, case_item in r["paired_cases"].items():
        assert item(case_item["path"]) == case_item
        cases = rows(case_item["path"])
        assert len(cases) == 2500 and len({c["sample_id"] for c in cases}) == 2500
        groups[m] = {}
        for arm in ("A","B"):
            g = r["groups"][arm][m]
            for artifact in (*g["files"].values(), *g["gate"]["files"].values()):
                assert item(artifact["path"]) == artifact
                native_records[artifact["path"]] = artifact
            geom = rows(g["files"]["geometry_nbest_rows.jsonl"]["path"])
            gate = rows(g["gate"]["files"]["execution_rows.jsonl"]["path"])
            ids = [c["sample_id"] for c in cases]
            assert [x["sample_id"] for x in geom] == [x["sample_id"] for x in gate] == ids
            c = [x["candidate_results"][0] for x in geom]
            selected = [x["has_target"] is True and all(y[k] is True for k in FLAGS)
                        and all(type(y.get(k)) in (int,float) and math.isfinite(y[k]) for k in ("cd","f_score_1pct"))
                        for x,y in zip(geom,c)]
            groups[m][arm] = (c, selected, gate)
            assert sum(selected) == g["geometry"]["scoreable"]
            assert all(x["has_target"] is True and len(x["candidate_results"]) == 1 for x in geom)
            for k in FLAGS:
                assert sum(x[k] for x in gate) == g["gate"]["native_summary"][k+"_count"]
                assert sum(x[k] for x in c) == g["geometry"]["gate_counts_from_geometry_run"][k]
            for k, stored in g["geometry"]["conditional"].items():
                vals = [x[k] for x,yes in zip(c,selected) if yes and type(x.get(k)) in (int,float) and math.isfinite(x[k])]
                distribution(vals,stored)
            u = [x["f_score_1pct"] if yes else 0. for x,yes in zip(c,selected)]
            distribution(u,g["geometry"]["unconditional_f_score_1pct"])
            for i,case in enumerate(cases):
                payload = case["arms"][arm]
                assert case["row_1based"] == i+1 and case["modality"] == m
                assert payload["native_gate"] == gate[i] and payload["native_geometry"] == geom[i]
                assert payload["scoreable"] == selected[i] and payload["unconditional_f_score_1pct"] == u[i]
            n_cases += len(c)
        a, b = groups[m]["A"], groups[m]["B"]
        joint = [i for i in range(2500) if a[1][i] and b[1][i]]
        p = r["paired_geometry"][m]
        assert p["sample_ids"] == [ids[i] for i in joint] and p["jointly_scoreable_n"] == len(joint)
        for k, stored in p["metrics"].items():
            valid = [i for i in joint if all(type(t[0][i].get(k)) in (int,float) and math.isfinite(t[0][i][k]) for t in (a,b))]
            aa,bb = ([t[0][i][k] for i in valid] for t in (a,b))
            delta = np.asarray(bb)-np.asarray(aa)
            assert stored["sample_ids"] == [ids[i] for i in valid]
            distribution(aa,stored["A"])
            distribution(bb,stored["B"])
            distribution(delta.tolist(),stored["delta_B_minus_A"])
            wins = int(np.sum(delta>1e-12 if k=="f_score_1pct" else delta < -1e-12))
            ties = int(np.sum(np.abs(delta)<=1e-12))
            losses = len(delta)-wins-ties
            assert (wins,losses,ties) == (stored["B_wins"],stored["A_wins"],stored["ties"])
            same(float(binomtest(wins,wins+losses,p=0.5).pvalue) if wins+losses else 1., stored["sign_test_p_two_sided"])
        for k,stored in r["paired_gate"][m].items():
            both=sum(x[k] and y[k] for x,y in zip(a[2],b[2]))
            ao=sum(x[k] and not y[k] for x,y in zip(a[2],b[2]))
            bo=sum(not x[k] and y[k] for x,y in zip(a[2],b[2]))
            assert (both,ao,bo,2500-both-ao-bo)==tuple(stored[x] for x in ("both_pass","A_only","B_only","both_fail"))
            same(float(binomtest(bo,bo+ao,p=.5).pvalue) if bo+ao else 1., stored["exact_McNemar_p_two_sided"])
        print(f"Independent NumPy/SciPy PASS {m}: native rows, paired-case archive, all distributions and exact tests",flush=True)
    assert n_cases == 20000
    report = {"created_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS", "rows_verified":n_cases,
        "audit_source":item(__file__), "summary":item(path), "full_markdown":item(PACKAGE/"result/01_complete_evaluation_results.md"),
        "paired_cases":r["paired_cases"],"native_result_files":native_records,
        "numpy_version":np.__version__,"training_or_model_or_CAD_execution":False,
        "checks":["Every native row equals archived per-case raw record","Every coverage count/scoreable decision",
            "All conditional/unconditional/paired mean/median/sampleSD/min/max/quantiles via independent NumPy",
            "Every paired ID and win/loss/tie count", "Every sign/McNemar p-value via independent scipy.stats.binomtest"]}
    with destination.open("x",encoding="utf-8") as stream:
        json.dump(report,stream,indent=2,allow_nan=False)
        stream.write("\n")
    print(f"Independent final verification PASS: {destination}",flush=True)


if __name__ == "__main__":
    main()
