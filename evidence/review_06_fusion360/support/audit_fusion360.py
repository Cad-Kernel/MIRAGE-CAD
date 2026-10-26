"""Inventory existing bytes and exact-ID correspondence, without executing source code."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
REPO=Path(r"__DEV_ROOT__")
WSL=Path(r"__RUN_SOURCE_ROOT__")
GATES=("syntax_ok","exec_ok","build_ok","solid_valid","step_export_ok")


def require(ok,message):
    if not ok:
        raise ValueError(message)


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):
            h.update(b)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_new(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as f:
        json.dump(value,f,indent=2,ensure_ascii=True,allow_nan=False)
        f.write("\n")


def resolve(value):
    value=str(value).replace("\\","/")
    if value.startswith("/mnt/c/"):
        return Path("C:/"+value[7:])
    if value.startswith("/home/"):
        return Path("//wsl.localhost/Ubuntu"+value)
    p=Path(value)
    return p if p.is_absolute() else REPO/p


def unique_index(items,label):
    index={}
    for item in items:
        sid=item["sample_id"]
        require(isinstance(sid,str) and sid,"Missing sample_id: "+label)
        require(sid not in index,"Duplicate sample_id in "+label+": "+sid)
        index[sid]=item
    return index


def metric(manifest,key,status):
    value=(manifest.get("evaluation") or {}).get(key)
    if manifest.get(status)!="ok":
        return None
    require(isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value),"Metric marked ok but missing/nonfinite: "+key)
    return value


class Audit:
    def __init__(self):
        self.files={}
        self.collections={}
        self.issues=[]

    def issue(self,kind,detail,severity="warning",sid=None):
        self.issues.append({"kind":kind,"detail":detail,"severity":severity,"sample_id":sid})

    def file(self,value,role,expected=None,required=True):
        p=resolve(value)
        key=str(p)
        if key not in self.files:
            exists=p.is_file()
            record={"path":key,"exists":exists,"bytes":p.stat().st_size if exists else None,
                    "sha256":sha(p) if exists else None,"roles":[],"historical_hash_checks":[]}
            self.files[key]=record
        record=self.files[key]
        if role not in record["roles"]:
            record["roles"].append(role)
        if required and not record["exists"]:
            self.issue("required_file_missing",key,"error")
        if expected:
            match=record["exists"] and record["sha256"]==expected
            record["historical_hash_checks"].append({"expected":expected,"matches":match,"role":role,"hash_kind":"file_bytes_sha256"})
            if not match:
                self.issue("historical_file_hash_mismatch",key,"error")
        return record

    def jsonl(self,path,label):
        info=self.file(path,label)
        require(info["exists"],"Cannot establish correspondence without "+label)
        items=[]
        locators={}
        with resolve(path).open("rb") as f:
            for line_no,line in enumerate(f,1):
                if not line.strip():
                    continue
                row=json.loads(line.decode("utf-8-sig"))
                items.append(row)
                locators.setdefault(row["sample_id"],{"path":info["path"],"line_1based":line_no,
                    "line_bytes_sha256":hashlib.sha256(line).hexdigest(),"file_sha256":info["sha256"]})
        index=unique_index(items,label)
        self.collections[label]={"path":info["path"],"rows":len(items),"ids":[x["sample_id"] for x in items],"locators":locators}
        return index

    def match_universe(self,label,ids):
        got=self.collections[label]["ids"]
        missing=sorted(set(ids)-set(got))
        extra=sorted(set(got)-set(ids))
        self.collections[label].update(missing_ids=missing,extra_ids=extra,same_id_set=not missing and not extra,
            matches_master_order=got==ids,order_differences=sum(a!=b for a,b in zip(ids,got)))
        require(not missing and not extra and len(got)==400,"ID-set mismatch in "+label)


def prior_seals():
    paths=[ROOT.parent/"05_qualitative/selection/path_lock_manifest_v1.json",
           ROOT.parent/"05_qualitative/rendering/cpu_v1/render_inventory_v1.json",
           ROOT.parent/"05_qualitative/raw_archive_v1/archive_manifest.json",
           ROOT.parent/"04/execution/final_evidence_inventory_20261022.json"]
    counts={}
    root05=ROOT.parent/"05_qualitative"
    for p in paths:
        data=read(p)
        for rel,item in data["files"].items():
            target=resolve(item["path"]) if "path" in item else root05/rel
            if "path" in item and not Path(item["path"]).is_absolute() and not item["path"].startswith("/"):
                target=root05/item["path"]
            require(sha(target)==item["sha256"],"Previous evidence drift: "+str(target))
        counts[str(p)]=len(data["files"])
    return counts


def main():
    require(not (ROOT/"audit/master_records_v1.json").exists(),"Do not overwrite an existing audit")
    audit=Audit()
    previous=prior_seals()
    definitions={"rows":WSL/"data/external/fusion360/rows.jsonl",
        "queries":WSL/"data/external/fusion360/queries.jsonl",
        "step_index":WSL/"data/external/fusion360/step_index.jsonl",
        "legacy_manifest":REPO/"scratch/external_manifest/manifest.jsonl",
        "plan":WSL/"outputs/external_fusion360/ir_point.jsonl"}
    for prefix,arm in (("mirage","point_genplan"),("nn","point_nnir")):
        definitions.update({prefix+"_raw":WSL/f"outputs/external_fusion360/gen_{arm}.jsonl",
            prefix+"_used":WSL/f"outputs/external_fusion360/gen_{arm}_repaired_p0.jsonl",
            prefix+"_gate":REPO/f"scratch/exec_ext_{arm}/execution_rows.jsonl",
            prefix+"_published_geom":REPO/f"scratch/geom_ext_{arm}/geometry_nbest_rows.jsonl",
            prefix+"_geom_input":WSL/f"outputs/external_geometry/geom_input_{arm}.jsonl",
            prefix+"_export":REPO/f"scratch/mirage_runs/{arm}/export_rows.jsonl"})
    data={name:audit.jsonl(path,name) for name,path in definitions.items()}
    ids=list(data["rows"])
    require(len(ids)==400,"Master input must contain 400 unique IDs")
    # Master IDs precede every method-specific coverage count or metric view.
    with (ROOT/"audit/master_ids_v1.txt").open("x",encoding="ascii",newline="\n") as f:
        f.write("\n".join(ids)+"\n")
    for label in definitions:
        audit.match_universe(label,ids)
    official_path=Path(r"__LOCAL_WORKSPACE__\Project\Dataset\Fusion360Gallery\r1.0.1\train_test.json")
    audit.file(official_path,"official_split")
    official=read(official_path)
    extids=[data["rows"][sid]["external_id"] for sid in ids]
    require(set(extids)<=set(official["test"]) and not set(extids)&set(official["train"]),"Master contains non-test external ID")
    train=audit.jsonl(WSL/"data/25k/train.jsonl","retrieval_training_ids")
    native={}
    for name,base,filename in (("cadr",REPO/"scratch/cadrecode_runs","run_manifest.json"),
        ("mirage",REPO/"scratch/mirage_runs/point_genplan","score_manifest.json"),
        ("nn",REPO/"scratch/mirage_runs/point_nnir","score_manifest.json")):
        records=[]
        paths={}
        for path in sorted(base.glob("*/"+filename)):
            audit.file(path,name+"_metric_manifest")
            m=read(path)
            require(m["sample_id"]==path.parent.name,"Directory/manifest ID mismatch")
            require(m.get("terminal") is True,"Unfinished native record")
            records.append(m)
            paths[m["sample_id"]]=str(path)
        native[name]=unique_index(records,name)
        audit.collections[name+"_native"]={"rows":len(records),"ids":[r["sample_id"] for r in records],"order_meaning":"lexicographic directory inventory, not execution order"}
        audit.match_universe(name+"_native",ids)
        native[name+"_paths"]=paths
    # Preserve source scripts as observations, never import them into this process.
    for filename in ("external_sample_manifest.py","external_paired_analysis.py","external_geometry_eval.py",
        "cadrecode_stage2.py","cadrecode_batch.py","cadrecode_generated_runner.py","probe_cadrecode_mesh.py",
        "mirage_step_export.py","mirage_score_one.py","mirage_score_batch.py"):
        audit.file(REPO/"src/scratch"/filename,"source_script")
    for p in (REPO/"scratch/external_paired_report.txt",REPO/"scratch/cadrecode_runs/batch_summary.txt",
        REPO/"scratch/mirage_runs/score_summary.txt",WSL/"data/external/fusion360/run_metadata.json",
        WSL/"outputs/external_geometry/run_metadata.json"):
        audit.file(p,"summary_or_metadata")
    output=[]
    typed=[]
    array_checks=[]
    missing_old_paths=Counter()
    for number,sid in enumerate(ids,1):
        row,q,idx=data["rows"][sid],data["queries"][sid],data["step_index"][sid]
        require(q["external_id"]==idx["external_id"]==row["external_id"] and sid=="f360_"+row["external_id"],"External/reference ID mismatch")
        require(q["split"]==row["split"]==idx["split"]=="test","Split mismatch")
        cadr=native["cadr"][sid]
        require(resolve(q["step_path_wsl"])==resolve(cadr["step_path"]),"CAD-Recode/reference STEP path mismatch")
        assets={"reference":audit.file(q["step_path_wsl"],"reference_step",(cadr.get("input") or {}).get("source_step_sha256")),
            "point":audit.file(row["point_path"],"MIRAGE_point_input"),
            "step_descriptor":audit.file(row["step_feature_path"],"MIRAGE_step_descriptor"),
            "step_descriptor_index_copy":audit.file(idx["step_feature_path"],"index_step_descriptor_copy")}
        require(resolve(row["point_path"])==resolve(q["point_path_wsl"]),"Input point path mismatch")
        if assets["step_descriptor"]["sha256"]!=assets["step_descriptor_index_copy"]["sha256"]:
            audit.issue("descriptor_copy_difference","Rows and step_index descriptor copies differ","warning",sid)
        notes=[]
        crbase=Path(native["cadr_paths"][sid]).parent
        for filename,key in (("raw_generation.txt","raw_sha256"),("extracted_code.py","extracted_code_sha256")):
            expected=(cadr.get("generation") or {}).get(key) if key=="raw_sha256" else cadr.get(key)
            assets["cadr_"+filename]=audit.file(crbase/filename,"CADR_"+filename,expected)
        for filename in ("execution_result.json","execution_stdout.txt","execution_stderr.txt","cloud_256.npy"):
            assets["cadr_"+filename]=audit.file(crbase/filename,"CADR_"+filename)
        execution=read(crbase/"execution_result.json")
        if execution!=(cadr.get("execution") or {}).get("runner_result"):
            audit.issue("execution_result_differs_from_manifest","Separate execution JSON and embedded runner_result disagree","error",sid)
        array=np.load(crbase/"cloud_256.npy",allow_pickle=False)
        digest=hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()
        expected=(cadr.get("input") or {}).get("cloud_256_sha256")
        array_checks.append({"sample_id":sid,"path":str(crbase/"cloud_256.npy"),"shape":list(array.shape),"array_bytes_sha256":digest,"expected":expected,"matches":digest==expected})
        if digest!=expected:
            audit.issue("CADR_input_array_hash_mismatch","Retained cloud differs from manifest array hash","error",sid)
        cp=(cadr.get("artifacts") or {}).get("prediction_step") or str(crbase/"prediction.step")
        assets["cadr_step"]=audit.file(cp,"CADR_prediction_STEP",(cadr.get("artifacts") or {}).get("prediction_step_sha256"),required=bool((cadr.get("artifacts") or {}).get("prediction_step_sha256")))
        view={"master_index":number,"sample_id":sid,"external_id":row["external_id"],"source_split":"test",
            "reference_path":assets["reference"]["path"],"reference_sha256":assets["reference"]["sha256"],
            "point_input_path":assets["point"]["path"],"point_input_sha256":assets["point"]["sha256"]}
        for prefix in ("mirage","nn"):
            m=native[prefix][sid]
            exp=data[prefix+"_export"][sid]
            gate=data[prefix+"_gate"][sid]
            source=data[prefix+"_used"][sid]
            code=source.get("prediction")
            gi=data[prefix+"_geom_input"][sid]
            require(gi.get("modality")==source.get("modality")=="point","Wrong input modality")
            require(isinstance(code,str) and gi.get("all_candidates")==[code.strip()],"Export-input and used prediction code mismatch")
            if prefix=="mirage":
                require(source.get("predicted_ir")==data["plan"][sid].get("predicted_ir"),"Generated-plan record mismatch")
            else:
                require(source.get("nn_sample_id") in train,"NN retrieval ID is not a registered training sample")
                view["nn_retrieved_training_sample_id"]=source["nn_sample_id"]
            candidates=data[prefix+"_published_geom"][sid].get("candidate_results") or []
            native_gates=m.get("gates")
            exp_gates=exp.get("gates")
            for origin,flags in (("score_manifest",native_gates),("export_rows",exp_gates),("published_geometry",candidates[0] if candidates else None)):
                if flags is not None:
                    if any(flags.get(k)!=gate.get(k) for k in GATES):
                        audit.issue("native_gate_disagreement",prefix+":"+origin+" differs from standalone gate","warning",sid)
                        notes.append(prefix+" gate disagreement: "+origin)
            if exp.get("gate_check") not in ("match","published_crash",None):
                notes.append(prefix+" original gate_check="+str(exp.get("gate_check")))
            base=Path(native[prefix+"_paths"][sid]).parent
            declared=exp.get("step_path") or m.get("prediction_step") or str(base/"candidate.step")
            assets[prefix+"_step"]=audit.file(declared,prefix+"_prediction_STEP",exp.get("step_sha256"),required=bool(exp.get("step_path")))
            if exp.get("step_path") and m.get("prediction_step"):
                require(resolve(exp["step_path"])==resolve(m["prediction_step"]),"Export/score STEP path mismatch")
            assets[prefix+"_original_geometry_target_cloud"]=audit.file(gi["point_path"],prefix+"_original_geometry_target_cloud")
            if assets[prefix+"_original_geometry_target_cloud"]["sha256"]!=assets["point"]["sha256"]:
                audit.issue("reference_cloud_copy_difference",prefix+" original scorer cloud differs from input NPZ","warning",sid)
            cd=metric(m,"cd_x1000","cd_status")
            iou=metric(m,"iou","iou_status")
            loc=audit.collections[prefix+"_used"]["locators"][sid]
            gate_loc=audit.collections[prefix+"_gate"]["locators"][sid]
            view.update({prefix+"_prediction_path":loc["path"],prefix+"_prediction_line_1based":loc["line_1based"],
                prefix+"_prediction_line_sha256":loc["line_bytes_sha256"],
                prefix+"_step_path":assets[prefix+"_step"]["path"] if assets[prefix+"_step"]["exists"] else None,
                prefix+"_step_sha256":assets[prefix+"_step"]["sha256"],prefix+"_log_path":gate_loc["path"],
                prefix+"_gate_line_1based":gate_loc["line_1based"],prefix+"_metric_manifest_path":native[prefix+"_paths"][sid],
                prefix+"_export_ok":gate.get("step_export_ok"),prefix+"_step_exists_current":assets[prefix+"_step"]["exists"],
                prefix+"_scoreable":cd is not None,prefix+"_iou_scoreable":iou is not None,
                prefix+"_CD":cd,prefix+"_IoU":iou,prefix+"_pipeline_status":m.get("pipeline_status"),
                prefix+"_cd_status":m.get("cd_status"),prefix+"_iou_status":m.get("iou_status"),
                prefix+"_native_error":gate.get("error"),prefix+"_score_reason":m.get("reason")})
        for key in ("gt_mesh_path","mirage_mesh_path","cadrecode_mesh_path"):
            old=data["legacy_manifest"][sid].get(key)
            if old and not resolve(old).is_file():
                missing_old_paths[key]+=1
        ccd=metric(cadr,"cd_x1000","cd_status")
        ciou=metric(cadr,"iou","iou_status")
        view.update(cadr_prediction_path=assets["cadr_extracted_code.py"]["path"],
            cadr_prediction_sha256=assets["cadr_extracted_code.py"]["sha256"],
            cadr_raw_generation_path=assets["cadr_raw_generation.txt"]["path"],
            cadr_step_or_mesh_path=assets["cadr_step"]["path"] if assets["cadr_step"]["exists"] else None,
            cadr_step_sha256=assets["cadr_step"]["sha256"],cadr_log_path=str(crbase/"execution_result.json"),
            cadr_metric_manifest_path=native["cadr_paths"][sid],cadr_export_ok=bool((cadr.get("artifacts") or {}).get("prediction_step_sha256")),
            cadr_step_exists_current=assets["cadr_step"]["exists"],cadr_scoreable=ccd is not None,cadr_iou_scoreable=ciou is not None,
            cadr_CD=ccd,cadr_IoU=ciou,cadr_pipeline_status=cadr.get("pipeline_status"),cadr_cd_status=cadr.get("cd_status"),cadr_iou_status=cadr.get("iou_status"),
            verified_failure_class=None,failure_evidence=None,selection_bucket=None,
            notes="; ".join(notes) or "Step 1 only; taxonomy and case selection not started")
        output.append(view)
        typed.append({"sample_id":sid,"view":view,"locators":{name:c["locators"][sid] for name,c in audit.collections.items() if "locators" in c and sid in c["locators"]},
            "assets":{key:value["path"] for key,value in assets.items()},"native_records":{name:native[name][sid] for name in ("mirage","nn","cadr")},
            "source_records":{name:index[sid] for name,index in data.items()}})
        if number%50==0:
            print(f"master correspondence and file hashes {number}/400",flush=True)
    counts={}
    for name in ("mirage","nn","cadr"):
        counts[name]={"rows":400,"historical_export_ok":sum(r[name+"_export_ok"] is True for r in output),
            "STEP_exists_current":sum(r[name+"_step_exists_current"] for r in output),
            "CD_scoreable":sum(r[name+"_scoreable"] for r in output),"IoU_scoreable":sum(r[name+"_iou_scoreable"] for r in output)}
    paired={}
    for a,b in (("mirage","cadr"),("nn","cadr"),("mirage","nn")):
        paired[a+"_vs_"+b]={"universe":400,"CD":sum(r[a+"_scoreable"] and r[b+"_scoreable"] for r in output),
            "IoU":sum(r[a+"_iou_scoreable"] and r[b+"_iou_scoreable"] for r in output)}
    critical=[x for x in audit.issues if x["severity"]=="error"]
    correspondence={"status":"PASS_MASTER_CORRESPONDENCE_WITH_RECORDED_LIMITATIONS" if not critical else "NEEDS_REVIEW_INTEGRITY_ISSUES",
        "created_utc":utc(),"scope":"Step 1 existing-file audit only; no new model/CAD/metrics/rendering/selection",
        "master_authority":str(definitions["rows"]),"master_rows":400,"master_ids_sha256":sha(ROOT/"audit/master_ids_v1.txt"),
        "official_split":{"test":len(official["test"]),"train":len(official["train"]),"selected_test_members":400,"selected_train_members":0},
        "collections":audit.collections,"coverage_inventory":counts,"paired_metric_availability":paired,
        "CADR_retained_input_array_checks":array_checks,"historical_native_pipeline_status_counts":{name:dict(Counter(m.get("pipeline_status") for m in native[name].values())) for name in ("mirage","nn","cadr")},
        "missing_legacy_placeholder_mesh_paths":dict(missing_old_paths),"issues":audit.issues,"critical_issues":len(critical),
        "file_counts":{"existing":sum(v["exists"] for v in audit.files.values()),"absent":sum(not v["exists"] for v in audit.files.values())},
        "prior_seals_unchanged":previous,"CD_definition":"existing evaluation.cd_x1000; dimensionless normalized squared symmetric CD times1000, not internal native-mm CD",
        "gt_mesh_verification":"Historical canonical mesh fingerprints and MIRAGE gt_verified flags retained; no mesh tessellation or fingerprint recomputation performed",
        "retrieval_condition":"NN-IR is training-index retrieval assisted, not autonomous point-to-plan",
        "source_code_observations":"Current source bytes retained by hash; not an invented attestation of historical executed checkout/model seed",
        "CADR_training_overlap":"This audit verifies Fusion360 official test membership only; overlap with upstream CAD-Recode training is not established",
        "reserved_taxonomy_and_selection":"all null"}
    write_new(ROOT/"audit/master_records_v1.json",{"rows":typed,"csv_columns":list(output[0]),"csv_rows":output})
    write_new(ROOT/"audit/source_files_v1.json",{"created_utc":utc(),"files":audit.files})
    write_new(ROOT/"audit/correspondence_v1.json",correspondence)
    print(json.dumps({k:correspondence[k] for k in ("status","master_rows","coverage_inventory","paired_metric_availability","missing_legacy_placeholder_mesh_paths","critical_issues","file_counts")},indent=2),flush=True)


if __name__=="__main__":
    main()
