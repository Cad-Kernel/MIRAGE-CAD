"""Independent stage oracle and exact source/CSV/evidence checks for Step 2."""
from collections import Counter
import csv
import json
from pathlib import Path
import subprocess
import sys
from classify_native_logs import ROOT,read,sha,write_new,verify_step1


def check(ok,message):
    if not ok:
        raise AssertionError(message)


def oracle(item,method):
    n=item["native_records"][method]
    ev=n.get("evaluation") or {}
    has_cd=n.get("cd_status")=="ok" and ev.get("cd_x1000") is not None
    if method=="cadr":
        if n["pipeline_status"]=="EXECUTION_FAILED":
            error=((n.get("execution") or {}).get("runner_result") or {}).get("error") or ""
            return "SYNTAX_FAILURE" if error.startswith("SyntaxError:") else "EXECUTION_FAILURE"
        check(has_cd and n["pipeline_status"]=="SUCCESS","Unhandled CADR source status")
        return "CD_SCOREABLE"
    g=item["source_records"][method+"_gate"]
    e=item["source_records"][method+"_export"]
    message=g.get("error") or e.get("error") or n.get("reason") or ""
    if e.get("status")=="KERNEL_CRASH" or "0xC0000005" in message or "kernel access violation" in message.lower():
        return "KERNEL_CRASH_STAGE_UNRESOLVED"
    flags=[g[k] for k in ("syntax_ok","exec_ok","build_ok","solid_valid","step_export_ok")]
    labels=["SYNTAX_FAILURE","EXECUTION_FAILURE","BUILD_FAILURE","SOLID_VALIDITY_FAILURE","STEP_EXPORT_FAILURE"]
    if False in flags:
        return labels[flags.index(False)]
    if n["pipeline_status"]=="EMPTY_PREDICTION_MESH":
        return "EMPTY_PREDICTION_MESH"
    if n["pipeline_status"]=="REMESH_FAILED":
        return "REMESH_FAILURE"
    check(has_cd and n["pipeline_status"]=="SUCCESS","Unhandled post-export source status")
    return "CD_SCOREABLE"


def compare_csv(path,expected,columns):
    with path.open(encoding="utf-8",newline="") as f:
        reader=csv.DictReader(f)
        check(reader.fieldnames==columns,"CSV headers differ: "+str(path))
        rows=list(reader)
    check(len(rows)==len(expected),"Logical CSV row count changed")
    for actual,original in zip(rows,expected):
        for key,value in original.items():
            if value is None:
                check(actual[key]=="","Null converted to nonblank")
            elif isinstance(value,bool):
                check(actual[key]==str(value).lower(),"Boolean changed")
            elif isinstance(value,float):
                check(float(actual[key])==value,"Metric changed")
            else:
                check(actual[key]==str(value),"Literal value changed: "+key)
    return len(rows)


def main():
    preserved=verify_step1()
    payload=read(ROOT/"taxonomy/failure_taxonomy_v1.json")
    master=read(ROOT/"audit/master_records_v1.json")
    check(payload["source_master_sha256"]==sha(ROOT/"audit/master_records_v1.json"),"Wrong master hash")
    check(payload["policy_sha256"]==sha(ROOT/"02_failure_taxonomy_protocol.md"),"Policy drift")
    check(payload["classifier_sha256"]==sha(Path(__file__).parent/"classify_native_logs.py"),"Classifier drift")
    long_count=compare_csv(ROOT/"fusion360_failure_taxonomy_v1.csv",payload["rows"],payload["long_csv_columns"])
    wide_count=compare_csv(ROOT/"fusion360_case_registry_step2_v1.csv",payload["wide_registry_rows"],payload["wide_registry_columns"])
    index={r["sample_id"]:r for r in master["rows"]}
    pairs=set()
    for row in payload["rows"]:
        pair=(row["sample_id"],row["method"])
        check(pair not in pairs,"Duplicate method/sample")
        pairs.add(pair)
        source=index[row["sample_id"]]
        native=source["native_records"][row["method"]]
        check(row["primary_outcome"]==oracle(source,row["method"]),"Independent first-stage oracle differs")
        expected_failure=None if row["primary_outcome"]=="CD_SCOREABLE" else row["primary_outcome"]
        check(row["verified_failure_class"]==expected_failure,"Scoreable incorrectly tagged as primary failure")
        check(row["selection_bucket"] is None and row["verified_semantic_failure"] is None,"Premature case/semantic label")
        check(row["geometry_review_status"]=="NOT_VISUALLY_REVIEWED","Invented visual review")
        for field,native_field,status in (("CD","cd_x1000","cd_status"),("IoU","iou","iou_status")):
            value=(native.get("evaluation") or {}).get(native_field) if native.get(status)=="ok" else None
            check(row[field]==value,"Original metric not preserved")
        ev=read(row["failure_evidence"])
        check(ev["sample_id"]==row["sample_id"] and ev["method"]==row["method"],"Wrong evidence record")
        check(ev["original_native_record"]==native,"Native evidence not literal")
        for key,value in ev["classification"].items():
            check(row[key]==value,"Evidence/classification mismatch")
        check(ev["sealed_step1_master"]["row_index_zero_based"]==row["master_index"]-1,"Master pointer offset wrong")
        subtype=row["reason_subtype"]
        message=row["reported_error"] or ""
        if subtype=="MISSING_API_ATTRIBUTE":
            check("object has no attribute" in message,"Missing-API label without native message")
        if subtype=="UNEXPECTED_KEYWORD_ARGUMENT":
            check("unexpected keyword argument" in message,"Keyword label without native message")
        if subtype=="ZERO_TRIANGLE_TESSELLATION_REPORTED":
            check(native.get("pred_mesh_triangles_on_failure")==0,"Invented zero triangles")
        if subtype=="ZERO_FACE_PREDICTION_REPORTED":
            check((native.get("prediction_step_diagnostics") or {}).get("n_faces")==0,"Invented zero faces")
        if subtype=="CADQUERY_LINE_EDGE_CONSTRUCTION_REPORTED":
            trace=row["native_traceback"] or ""
            check("BRep_API: command not done" in message and ("Edge.makeLine" in trace or "BRepBuilderAPI_MakeEdge" in trace),"Line construction label unsupported")
        if subtype=="CADQUERY_THREE_POINT_ARC_CONSTRUCTION_REPORTED":
            check("GC_MakeArcOfCircle" in message and "makeThreePointArc" in (row["native_traceback"] or ""),"Arc construction label unsupported")
        if row["iou_failure_class"]=="IOU_BOOLEAN_FAILURE":
            check(row["cd_scoreable"] and row["IoU"] is None and native.get("iou_status")=="boolean_failed","Boolean failure substituted for zero/non-scoreable")
    for before,after in zip(master["csv_rows"],payload["wide_registry_rows"]):
        check(all(before[k]==after[k] for k in master["csv_columns"]),"An original 67-column value changed")
    for method in ("mirage","nn","cadr"):
        group=[r for r in payload["rows"] if r["method"]==method]
        check(len(group)==400,"Method lost sample IDs")
        check(dict(Counter(r["primary_outcome"] for r in group))==payload["counts"][method]["primary_outcomes"],"Primary totals mismatch")
        check(dict(Counter(r["iou_outcome"] for r in group))==payload["counts"][method]["iou_outcomes"],"IoU totals mismatch")
    for ref in payload["source_files_verified"]:
        check(sha(ref["path"])==ref["sha256"],"Underlying native log changed")
    test=subprocess.run([sys.executable,str(Path(__file__).parent/"test_native_taxonomy.py")],capture_output=True,text=True,timeout=30)
    check(test.returncode==0,"Contract tests failed")
    sys.path.insert(0,str(ROOT/"support"))
    from audit_fusion360 import prior_seals
    prior=prior_seals()
    result={"status":"PASS_INDEPENDENT_NATIVE_LOG_TAXONOMY_VALIDATION","long_rows":long_count,"long_columns":len(payload["long_csv_columns"]),
        "wide_rows":wide_count,"wide_columns":len(payload["wide_registry_columns"]),"unique_method_sample_pairs":len(pairs),
        "evidence_files_checked":1200,"independent_stage_oracle_matches":1200,"original_67_columns_unchanged":True,
        "native_source_files_rehashed":len(payload["source_files_verified"]),"native_source_drift":0,
        "step1_sealed_files_unchanged":preserved,"prior_04_05_seals_unchanged":prior,
        "unit_tests":20,"unit_test_output":test.stdout+test.stderr,
        "measured_zero_IoU_preserved":sum(r["IoU"]==0 for r in payload["rows"] if r["IoU"] is not None),
        "all_semantic_and_selection_labels_null":True,"training_prediction_CAD_scoring_or_CAD_rendering":False}
    write_new(ROOT/"taxonomy/independent_validation_v1.json",result)
    print(json.dumps({k:v for k,v in result.items() if k not in ("unit_test_output","prior_04_05_seals_unchanged")},indent=2))


if __name__=="__main__":
    main()
