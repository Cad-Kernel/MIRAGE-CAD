"""Independent CSV/native/locator validation with no CAD or model operations."""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from audit_fusion360 import ROOT,resolve,sha,read,write_new,prior_seals


def check(value,message):
    if not value:
        raise AssertionError(message)


def main():
    source=read(ROOT/"audit/master_records_v1.json")
    corr=read(ROOT/"audit/correspondence_v1.json")
    files=read(ROOT/"audit/source_files_v1.json")["files"]
    with (ROOT/"fusion360_case_registry.csv").open(encoding="utf-8",newline="") as f:
        reader=csv.DictReader(f)
        headers=reader.fieldnames
        csvrows=list(reader)
    check(len(csvrows)==400 and headers==source["csv_columns"],"CSV count/header differs")
    ids=(ROOT/"audit/master_ids_v1.txt").read_text().splitlines()
    check([r["sample_id"] for r in csvrows]==ids,"CSV does not follow master order")
    check(len(set(ids))==400,"Duplicate master ID")
    for expected,actual in zip(source["csv_rows"],csvrows):
        for key,value in expected.items():
            if value is None:
                check(actual[key]=="","Missing value converted to zero/text")
            elif isinstance(value,bool):
                check(actual[key]==str(value).lower(),"Boolean changed")
            elif isinstance(value,float):
                check(float(actual[key])==value,"Historical metric changed")
            else:
                check(actual[key]==str(value),"Identifier/path/label changed")
        check(all(actual[c]=="" for c in ("verified_failure_class","failure_evidence","selection_bucket")),"Premature taxonomy or selection")
    checked_existing=0
    checked_absent=0
    hash_checks=0
    for entry in files.values():
        path=Path(entry["path"])
        check(path.is_file()==entry["exists"],"File existence changed during audit: "+str(path))
        if entry["exists"]:
            check(path.stat().st_size==entry["bytes"] and sha(path)==entry["sha256"],"Source bytes changed during audit: "+str(path))
            checked_existing+=1
        else:
            checked_absent+=1
            check(all("prediction_STEP" in role for role in entry["roles"]),"Unexpected absent non-prediction input")
        for historic in entry["historical_hash_checks"]:
            check(entry["sha256"]==historic["expected"] and historic["matches"],"Historical file hash mismatch")
            hash_checks+=1
    # Re-read physical source lines independently; do not rely on cached dictionary order.
    source_lines={}
    for typed in source["rows"]:
        sid=typed["sample_id"]
        for locator in typed["locators"].values():
            path=locator["path"]
            if path not in source_lines:
                source_lines[path]=Path(path).read_bytes().splitlines(keepends=True)
            line=source_lines[path][locator["line_1based"]-1]
            check(hashlib.sha256(line).hexdigest()==locator["line_bytes_sha256"],"Physical line drift")
            check(json.loads(line.decode("utf-8-sig"))["sample_id"]==sid,"Physical locator resolves wrong sample")
    for row in csvrows:
        for method in ("mirage","nn","cadr"):
            manifest=read(row[method+"_metric_manifest_path"])
            check(manifest["sample_id"]==row["sample_id"] and manifest["terminal"] is True,"Wrong or unfinished native result")
            evaluation=manifest.get("evaluation") or {}
            for column,field,status in (("CD","cd_x1000","cd_status"),("IoU","iou","iou_status")):
                value=evaluation.get(field) if manifest.get(status)=="ok" else None
                actual=row[method+"_"+column]
                check((actual=="") if value is None else float(actual)==value,"CSV metric differs from fresh native manifest")
    check(corr["critical_issues"]==0 and not corr["issues"],"Unresolved correspondence/integrity issue")
    check(len(corr["CADR_retained_input_array_checks"])==400 and all(r["matches"] for r in corr["CADR_retained_input_array_checks"]),"CADR model-input array binding fails")
    test=subprocess.run([sys.executable,str(Path(__file__).parent/"test_audit_contract.py")],capture_output=True,text=True,timeout=60)
    check(test.returncode==0,"CPU contract tests failed")
    report={"status":"PASS_INDEPENDENT_STEP1_VALIDATION","CSV_rows":400,"CSV_columns":len(headers),
        "master_order":"PASS","duplicate_ids":0,"all_physical_JSONL_locators":"PASS",
        "existing_source_file_rehashes":checked_existing,"expected_absent_prediction_STEP_files":checked_absent,
        "historical_file_hash_checks":hash_checks,"historical_file_hash_mismatches":0,
        "CADR_retained_input_array_hash_checks":400,"fresh_native_metric_records_compared":1200,
        "taxonomy_and_selection_fields_blank":True,"contract_tests":8,"contract_test_output":test.stdout+test.stderr,
        "previous_evidence_seals_unchanged":prior_seals(),"models_CAD_metrics_or_rendering_executed":False,
        "registry_sha256":sha(ROOT/"fusion360_case_registry.csv")}
    write_new(ROOT/"audit/independent_validation_v1.json",report)
    print(json.dumps({k:v for k,v in report.items() if k not in ("contract_test_output","previous_evidence_seals_unchanged")},indent=2))


if __name__=="__main__":
    main()
