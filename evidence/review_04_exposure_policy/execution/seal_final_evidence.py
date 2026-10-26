#!/usr/bin/env python3
"""Inventory completed evidence and verify tiny exact-test tails with zero absolute tolerance."""
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import scipy
from scipy.stats import binomtest

PACKAGE=Path(__file__).resolve().parents[1]


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def record(path):
    path=Path(path)
    return {"path":str(path),"bytes":path.stat().st_size,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}


def check(item):
    assert record(item["path"]) == item, item["path"]


def main():
    destination=PACKAGE/"execution/final_evidence_inventory_20261022.json"
    assert not destination.exists()
    summary_path=PACKAGE/"result/cag_exposure_policy_eval_summary.json"
    summary=load(summary_path)
    independent_path=PACKAGE/"execution/exposure_final_independent_verification_20261022.json"
    independent=load(independent_path)
    assert summary["status"] == "CLOSED" and summary["audit_status"] == "PASS"
    assert independent["status"] == "PASS" and independent["rows_verified"] == 20000
    for item in (independent["summary"],independent["full_markdown"],independent["audit_source"],
                 summary["registration_script"],summary["test_report"],summary["metric_helper_source"],
                 summary["gate_registration"],summary["prediction_registration"],
                 *summary["paired_cases"].values(),*independent["native_result_files"].values()):
        check(item)
    tests=load(summary["test_report"]["path"])
    assert tests["status"] == "PASS" and tests["tests_run"] == 20
    for key in ("audit_source","test_source","metric_helper_source"):
        check(tests[key])
    n=0
    for group in summary["paired_geometry"].values():
        for metric in group["metrics"].values():
            total=metric["B_wins"]+metric["A_wins"]
            p=float(binomtest(metric["B_wins"],total,p=.5).pvalue) if total else 1.
            assert math.isclose(p,metric["sign_test_p_two_sided"],rel_tol=1e-10,abs_tol=0), (p,metric)
            n+=1
    for group in summary["paired_gate"].values():
        for flag in group.values():
            total=flag["B_only"]+flag["A_only"]
            p=float(binomtest(flag["B_only"],total,p=.5).pvalue) if total else 1.
            assert math.isclose(p,flag["exact_McNemar_p_two_sided"],rel_tol=1e-10,abs_tol=0), (p,flag)
            n+=1
    assert n==32
    result_paths=list((PACKAGE/"result").iterdir())
    assert len(result_paths)==6 and all(path.is_file() for path in result_paths)
    files=[PACKAGE/"README.md",PACKAGE/"11_stage4b_validation_checklist.md",
           PACKAGE/"20_gate_results_and_geometry_release.md",PACKAGE/"21_final_results_and_closed_summary.md",
           PACKAGE.parent/"training_experiments_roadmap.md",Path(__file__),
           PACKAGE/"execution/register_exposure_final_results.py",PACKAGE/"execution/test_exposure_final_audit.py",
           PACKAGE/"execution/verify_exposure_final_summary.py",independent_path,
           PACKAGE/"execution/exposure_final_audit_tests_20261022.json",*result_paths]
    text=(PACKAGE/"README.md").read_text(encoding="utf-8")
    assert "Review/04: CLOSED" in text and "Geometry evaluation: COMPLETE_VERIFIED_ALL8_GROUPS_2500_ROWS_EACH" in text
    report={"created_utc":datetime.now(timezone.utc).isoformat(),"status":"CLOSED_EVIDENCE_VERIFIED",
        "files":{str(path.relative_to(PACKAGE.parent)) if path.is_relative_to(PACKAGE.parent) else str(path):record(path) for path in files},
        "strict_exact_test_tail_checks":n,"tail_comparison_absolute_tolerance":0,
        "tail_comparison_relative_tolerance":1e-10,"scipy_version":scipy.__version__,
        "record_scope":"Post-result evidence inventory; does not rewrite or replace the original frozen scientific protocol/seal",
        "training_model_or_CAD_execution":False}
    with destination.open("x",encoding="utf-8") as stream:
        json.dump(report,stream,indent=2,allow_nan=False)
        stream.write("\n")
    print(f"CLOSED evidence inventory PASS: {len(files)} artifacts; all32 exact-test tails verified with abs_tol=0",flush=True)
    print(destination,flush=True)


if __name__=="__main__":
    main()
