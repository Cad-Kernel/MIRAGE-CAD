"""Pure log taxonomy, separate program/CD outcome from IoU evaluator availability."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
METHODS=("mirage","nn","cadr")
POLICY=ROOT/"02_failure_taxonomy_protocol.md"


def require(ok,message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_new(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as f:
        json.dump(value,f,indent=2,ensure_ascii=True,allow_nan=False)
        f.write("\n")


def verify_step1():
    seal=read(ROOT/"audit/step1_package_seal_v1.json")
    for rel,item in seal["files"].items():
        require(sha(ROOT/rel)==item["sha256"],"Sealed Step-1 bytes changed: "+rel)
    return len(seal["files"])


def metric(native,key,status):
    value=(native.get("evaluation") or {}).get(key)
    if native.get(status)!="ok":
        return None
    require(isinstance(value,(float,int)) and not isinstance(value,bool) and math.isfinite(value),"Invalid metric marked ok")
    return value


def subtype(outcome,message,traceback="",native=None):
    native=native or {}
    if outcome=="CD_SCOREABLE":
        return "NOT_APPLICABLE",None
    if outcome=="KERNEL_CRASH_STAGE_UNRESOLVED":
        return "NATIVE_ACCESS_VIOLATION_REPORTED",None
    if outcome=="SYNTAX_FAILURE":
        return "NATIVE_SYNTAX_ERROR_REPORTED",None
    if outcome=="EMPTY_PREDICTION_MESH":
        return ("ZERO_TRIANGLE_TESSELLATION_REPORTED" if native.get("pred_mesh_triangles_on_failure")==0 else "EMPTY_TESSELLATION_REPORTED"),None
    if outcome=="REMESH_FAILURE":
        return ("ZERO_FACE_PREDICTION_REPORTED" if (native.get("prediction_step_diagnostics") or {}).get("n_faces")==0 else "REMESH_ERROR_REPORTED"),None
    patterns=[
        ("UNRESOLVED_TOPOLOGY_REFERENCE",r"topology reference .* did not resolve"),
        ("HANDLE_TYPE_CONTRACT",r"target must be (?:a FeatureHandle|a TopologyReference)"),
        ("MISSING_API_ATTRIBUTE",r"'([^']+)' object has no attribute '([^']+)'"),
        ("UNEXPECTED_KEYWORD_ARGUMENT",r"([\w.]+)\(\) got an unexpected keyword argument '([^']+)'"),
        ("MISSING_REQUIRED_ARGUMENT",r"missing .*required .*argument"),
        ("POSITIONAL_ARGUMENT_ARITY",r"takes .*positional arguments? but .* (?:was|were) given"),
        ("DUPLICATE_PARAMETER_NAME",r"parameter '[^']+' already exists"),
        ("UNDEFINED_NAME",r"name '[^']+' is not defined"),
        ("UNSUPPORTED_OPERAND_TYPES",r"unsupported operand type\(s\)"),
        ("ARGUMENT_VALUE_OR_SHAPE_CONTRACT",r"must be a [23]D sequence|hole depth must be a number or 'through'|extrude_on_face .*requires"),
        ("OCCT_BUILD_ERROR_DURING_STEP_EXPORT",r"STEP export error: OCCT build failed")]
    for label,pattern in patterns:
        match=re.search(pattern,message)
        if match:
            detail=" / ".join(match.groups()) if match.groups() else None
            return label,detail
    if "BRep_API: command not done" in message and ("Edge.makeLine" in traceback or "BRepBuilderAPI_MakeEdge" in traceback):
        return "CADQUERY_LINE_EDGE_CONSTRUCTION_REPORTED",None
    if "GC_MakeArcOfCircle::Value() - no result" in message and "makeThreePointArc" in traceback:
        return "CADQUERY_THREE_POINT_ARC_CONSTRUCTION_REPORTED",None
    if "StdFail_NotDone" in message:
        return "KERNEL_OPERATION_ERROR_REPORTED",None
    return outcome+"_REASON_UNSPECIFIED",None


def classify(method,native,gate=None,export=None):
    gate=gate or {}
    export=export or {}
    evaluation=native.get("evaluation") or {}
    cd=metric(native,"cd_x1000","cd_status")
    iou=metric(native,"iou","iou_status")
    traceback=""
    rule=None
    if method=="cadr":
        execution=native.get("execution") or {}
        result=execution.get("runner_result") or {}
        message=result.get("error") or native.get("reason") or ""
        traceback=result.get("traceback") or ""
        if native.get("pipeline_status")=="EXECUTION_FAILED":
            outcome="SYNTAX_FAILURE" if message.startswith("SyntaxError:") else "EXECUTION_FAILURE"
            rule="CADR_NATIVE_EXECUTION_RESULT"
        elif native.get("pipeline_status")=="SUCCESS" and cd is not None:
            outcome="CD_SCOREABLE"
            rule="CADR_NATIVE_CD_OK"
        else:
            outcome="OTHER_NATIVE_UNSCOREABLE"
            rule="CADR_OTHER_TERMINAL_STATUS"
    else:
        message=gate.get("error") or export.get("error") or native.get("reason") or ""
        crash=export.get("status")=="KERNEL_CRASH" or "0xC0000005" in message or "kernel access violation" in message.lower()
        if crash:
            outcome="KERNEL_CRASH_STAGE_UNRESOLVED"
            rule="EXPLICIT_NATIVE_CRASH_OVERRIDES_INCOMPLETE_FLAGS"
        else:
            outcome=None
            for field,label in (("syntax_ok","SYNTAX_FAILURE"),("exec_ok","EXECUTION_FAILURE"),("build_ok","BUILD_FAILURE"),
                                ("solid_valid","SOLID_VALIDITY_FAILURE"),("step_export_ok","STEP_EXPORT_FAILURE")):
                require(type(gate.get(field)) is bool,"Gate flag missing or not boolean: "+field)
                if gate[field] is False:
                    outcome=label
                    rule="FIRST_FALSE_NATIVE_GATE:"+field
                    break
            if outcome is None:
                status=native.get("pipeline_status")
                if status=="EMPTY_PREDICTION_MESH":
                    outcome="EMPTY_PREDICTION_MESH"
                elif status=="REMESH_FAILED":
                    outcome="REMESH_FAILURE"
                elif cd is not None:
                    outcome="CD_SCOREABLE"
                elif status in ("GT_UNVERIFIED","GT_OOM","NO_GT_RECORD"):
                    outcome="GT_VERIFICATION_OR_RESOURCE_FAILURE"
                elif status in ("EVAL_OOM","EVAL_TIMEOUT","EVAL_KILLED","EVAL_NO_MANIFEST"):
                    outcome="EVALUATOR_RESOURCE_OR_PROCESS_FAILURE"
                elif evaluation.get("cd_status") or native.get("cd_status"):
                    outcome="CD_EVALUATION_FAILURE"
                else:
                    outcome="OTHER_NATIVE_UNSCOREABLE"
                rule="POST_EXPORT_NATIVE_STATUS:"+str(status)
                message=native.get("reason") or evaluation.get("remesh_status") or ""
    require((outcome=="CD_SCOREABLE")== (cd is not None),"Primary failure contradicts recorded CD availability")
    if outcome=="CD_SCOREABLE":
        message=""
    reason,detail=subtype(outcome,message,traceback,native)
    if iou is not None:
        iou_outcome="IOU_AVAILABLE"
        iou_failure=None
    elif outcome!="CD_SCOREABLE":
        iou_outcome="UNAVAILABLE_AFTER_PRIMARY_FAILURE"
        iou_failure=None
    elif native.get("iou_status")=="boolean_failed" or evaluation.get("iou_status")=="boolean_failed":
        iou_outcome="IOU_BOOLEAN_FAILURE"
        iou_failure="IOU_BOOLEAN_FAILURE"
    elif native.get("iou_status")=="ineligible" or evaluation.get("iou_eligible") is False:
        iou_outcome="IOU_INELIGIBLE_OR_EVALUATOR_FAILURE"
        iou_failure=iou_outcome
    else:
        iou_outcome="IOU_UNAVAILABLE_OTHER_REPORTED"
        iou_failure=iou_outcome
    return {"primary_outcome":outcome,"verified_failure_class":outcome if outcome!="CD_SCOREABLE" else None,
        "reason_subtype":reason,"reason_detail":detail,"classification_rule":rule,
        "reported_error":message or None,"native_traceback":traceback or None,
        "cd_scoreable":cd is not None,"iou_scoreable":iou is not None,"CD":cd,"IoU":iou,
        "iou_outcome":iou_outcome,"iou_failure_class":iou_failure,
        "geometry_review_status":"NOT_VISUALLY_REVIEWED","verified_semantic_failure":None,"selection_bucket":None}


def main():
    preserved=verify_step1()
    require(not (ROOT/"taxonomy/failure_taxonomy_v1.json").exists(),"Taxonomy version exists; do not overwrite")
    require(not (ROOT/"taxonomy/evidence_v1").exists(),"Partial/existing evidence requires explicit review")
    master=read(ROOT/"audit/master_records_v1.json")
    inventory=read(ROOT/"audit/source_files_v1.json")["files"]
    master_hash=sha(ROOT/"audit/master_records_v1.json")
    policy_hash=sha(POLICY)
    classifier_hash=sha(__file__)
    originals={}
    loc_cache={}
    def verify_source(path):
        path=str(path)
        if path not in originals:
            expected=inventory[path]
            require(expected["exists"] and sha(Path(path))==expected["sha256"],"Source changed since Step 1: "+path)
            originals[path]={"path":path,"sha256":expected["sha256"],"bytes":expected["bytes"]}
        return originals[path]
    rows=[]
    wide=[]
    evidence=[]
    for position,item in enumerate(master["rows"]):
        sid=item["sample_id"]
        require(re.fullmatch(r"f360_[0-9]+_[0-9a-f]+_[0-9]+",sid),"Unsafe/unexpected sample ID")
        wide_row=dict(item["view"])
        for method in METHODS:
            native=item["native_records"][method]
            native_path=item["view"][method+"_metric_manifest_path"]
            manifest_ref=verify_source(native_path)
            require(read(native_path)==native,"Native snapshot no longer matches source")
            gate=None
            export=None
            refs=[manifest_ref]
            locators={}
            log_texts={}
            if method!="cadr":
                gate=item["source_records"][method+"_gate"]
                export=item["source_records"][method+"_export"]
                for label in (method+"_gate",method+"_export"):
                    locator=item["locators"][label]
                    refs.append(verify_source(locator["path"]))
                    locators[label]=locator
                    if locator["path"] not in loc_cache:
                        loc_cache[locator["path"]]=Path(locator["path"]).read_bytes().splitlines(keepends=True)
                    line=loc_cache[locator["path"]][locator["line_1based"]-1]
                    require(hashlib.sha256(line).hexdigest()==locator["line_bytes_sha256"],"Physical source row drift")
                    require(json.loads(line.decode("utf-8-sig"))==item["source_records"][label],"Physical row/source mismatch")
            else:
                for filename in ("execution_result.json","execution_stdout.txt","execution_stderr.txt"):
                    path=Path(native_path).parent/filename
                    refs.append(verify_source(path))
                    if filename.endswith(".txt"):
                        log_texts[filename]=path.read_bytes().decode("utf-8-sig")
                    else:
                        require(read(path)==(native.get("execution") or {}).get("runner_result"),"CADR runner result changed")
            result=classify(method,native,gate,export)
            require(result["cd_scoreable"]==item["view"][method+"_scoreable"] and result["iou_scoreable"]==item["view"][method+"_iou_scoreable"],"Classification changed metric availability")
            evidence_path=ROOT/"taxonomy/evidence_v1"/method/(sid+".json")
            ev={"sample_id":sid,"method":method,"classification":result,
                "policy_sha256":policy_hash,"classifier_sha256":classifier_hash,
                "sealed_step1_master":{"path":str(ROOT/"audit/master_records_v1.json"),"sha256":master_hash,
                    "row_index_zero_based":position,"json_pointer":f"/rows/{position}/native_records/{method}"},
                "source_files":refs,"physical_JSONL_locators":locators,"original_native_record":native,
                "original_gate":gate,"original_export_record":export,"original_CADR_execution_texts":log_texts,
                "scope":"Native error/evaluator evidence only; no figure or semantic inspection"}
            evidence.append((evidence_path,ev))
            record={"master_index":position+1,"sample_id":sid,"method":method,**result,
                "historical_export_ok":item["view"][method+"_export_ok"],
                "prediction_step_exists":item["view"][method+"_step_exists_current"],
                "native_pipeline_status":native.get("pipeline_status"),"native_cd_status":native.get("cd_status"),"native_iou_status":native.get("iou_status"),
                "failure_evidence":str(evidence_path),"native_manifest_path":native_path,
                "input_sample_id_unchanged":True,"classification_version":"native-log-taxonomy-v1"}
            rows.append(record)
            for key in ("primary_outcome","verified_failure_class","reason_subtype","reason_detail","iou_outcome","iou_failure_class","geometry_review_status","verified_semantic_failure"):
                wide_row[method+"_"+key]=result[key]
            wide_row[method+"_failure_evidence"]=str(evidence_path)
        wide.append(wide_row)
    require(len(rows)==1200 and len(wide)==400,"Incomplete taxonomy universe")
    require(len({(r["sample_id"],r["method"]) for r in rows})==1200,"Duplicate taxonomy key")
    counts={}
    for method in METHODS:
        group=[r for r in rows if r["method"]==method]
        counts[method]={"total":len(group),"primary_outcomes":dict(Counter(r["primary_outcome"] for r in group)),
            "primary_failure_count":sum(r["verified_failure_class"] is not None for r in group),
            "primary_failure_reason_subtypes":dict(Counter(r["reason_subtype"] for r in group if r["verified_failure_class"] is not None)),
            "iou_outcomes":dict(Counter(r["iou_outcome"] for r in group)),
            "IoU_boolean_failures_among_CD_scoreable":sum(r["iou_failure_class"]=="IOU_BOOLEAN_FAILURE" for r in group),
            "measured_zero_IoU_preserved":sum(r["IoU"]==0 for r in group if r["IoU"] is not None),
            "reason_unspecified_primary_failures":sum(r["reason_subtype"].endswith("REASON_UNSPECIFIED") for r in group)}
    payload={"created_utc":datetime.now(timezone.utc).isoformat(),"status":"NATIVE_LOG_TAXONOMY_COMPLETE_NO_VISUAL_SEMANTIC_LABELS",
        "policy_sha256":policy_hash,"classifier_sha256":classifier_hash,"source_master_sha256":master_hash,
        "prior_step1_files_unchanged":preserved,"source_files_verified":list(originals.values()),
        "rows":rows,"counts":counts,"wide_registry_rows":wide,"wide_registry_columns":list(wide[0]),
        "long_csv_columns":list(rows[0]),"all_selection_buckets_null":True,"all_semantic_labels_null":True,
        "Step3_rendering_or_selection":"NOT_STARTED","Step4_raw_asset_archive":"NOT_STARTED"}
    for path,ev in evidence:
        write_new(path,ev)
    write_new(ROOT/"taxonomy/failure_taxonomy_v1.json",payload)
    print(json.dumps({"status":payload["status"],"long_rows":1200,"wide_rows":400,"counts":counts,"source_files_verified":len(originals)},indent=2))


if __name__=="__main__":
    main()
