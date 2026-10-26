#!/usr/bin/env python3
"""CPU-only legacy B2 candidate audit and literal-field extraction. Never executes CAD."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess

PACKAGE=Path(__file__).resolve().parents[1]
SOURCE=Path("__RUN_SOURCE_ROOT__")
WINDOWS=Path("__DEV_ROOT__")
POLICY=PACKAGE/"03_candidate_selection_policy.md"
MODALITIES=("text","image","point","step")
FLAGS=("syntax_ok","exec_ok","build_ok","solid_valid","step_export_ok")
STAGES=("syntax_failure","execution_failure","build_failure","solid_invalid","step_export_failure")
PUBLISHED={"text":(98.3,57.2,53.1),"image":(94.3,57.8,52.3),"point":(89.5,55.4,52.6),"step":(94.5,70.,66.2)}


def require(ok,message):
    if not ok: raise ValueError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def file_record(path):
    path=Path(path)
    require(path.is_file() and path.stat().st_size>0,f"Missing/empty source: {path}")
    digest=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""): digest.update(block)
    return {"path":str(path),"bytes":path.stat().st_size,"sha256":digest.hexdigest()}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_text(path,text):
    path=Path(path)
    require(path.is_relative_to(PACKAGE),"Write escapes qualitative package")
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8",newline="\n") as stream: stream.write(text)
    return file_record(path)


def write_json(path,value):
    return write_text(path,json.dumps(value,ensure_ascii=True,indent=2,allow_nan=False)+"\n")


def read_index(path,expected_ids=None):
    entries,physical={},[]
    with Path(path).open("rb") as stream:
        for line_number,line in enumerate(stream,1):
            if not line.strip(): continue
            row=json.loads(line.decode("utf-8-sig"))
            sid=row["sample_id"]
            require(sid not in entries,f"Duplicate sample ID: {path}/{sid}")
            entries[sid]={"row":row,"line_1based":line_number,
                "line_bytes_sha256":hashlib.sha256(line.rstrip(b"\r\n")).hexdigest()}
            physical.append(sid)
    if expected_ids is not None:
        require(physical==expected_ids,f"ID/order/count mismatch: {path}")
    return entries


def finite(value):
    return type(value) in (int,float) and math.isfinite(value)


def scoreable(row,candidate):
    return (row.get("has_target") is True and all(candidate.get(k) is True for k in FLAGS)
            and finite(candidate.get("cd")) and finite(candidate.get("f_score_1pct")))


def reference_features(text,sid):
    family=None
    ops=[]
    for line in text.splitlines():
        tokens=line.split()
        if not tokens: continue
        if tokens[0]=="PART":
            require(tokens[1]==sid,f"Reference IR identity mismatch: {sid}")
            require("UNITS" in tokens and tokens[tokens.index("UNITS")+1]=="mm",f"Unexpected reference units: {sid}")
            if "CAT" in tokens: family=tokens[tokens.index("CAT")+1]
        if tokens[0]=="F":
            require(len(tokens)>=3 and tokens[2].startswith("OP_"),f"Unrecognized reference feature record: {sid}/{line}")
            ops.append(tokens[2])
    require(family is not None and ops,f"Missing reference PART/features: {sid}")
    return {"template_family":family,"operation_count":len(ops),"operation_set":sorted(set(ops))}


def percentiles(items,key):
    groups=defaultdict(list)
    for row in items: groups[row[key]].append(row)
    offset,n=0,len(items)
    for value,group in sorted(groups.items()):
        rank=.5 if n==1 else (offset+(len(group)-1)/2)/(n-1)
        for row in group: row[key+"_percentile"]=rank
        offset+=len(group)


def first_stage(gate):
    return next((stage for flag,stage in zip(FLAGS,STAGES) if not gate[flag]),"pass")


def tier_key(label):
    require(isinstance(label,str) and label.startswith("L") and label[1:].isdigit(),f"Unknown tier definition: {label}")
    return int(label[1:])


def observe_checkout(path):
    command=["git","--no-optional-locks","-C",str(path)]
    revision=subprocess.run(command+["rev-parse","HEAD"],text=True,capture_output=True)
    if revision.returncode:
        return {"path":str(path),"commit":None,"status_porcelain":None,"git_status":"UNAVAILABLE_OR_NOT_A_REPOSITORY",
            "git_error":revision.stderr.strip()}
    status=subprocess.run(command+["status","--short"],text=True,capture_output=True)
    return {"path":str(path),"commit":revision.stdout.strip(),"status_porcelain":status.stdout if not status.returncode else None,
        "git_status":"OBSERVED_CURRENT_CHECKOUT","git_error":status.stderr.strip() if status.returncode else None}


def central(rows,metric,target,secondary,secondary_target):
    return min(rows,key=lambda x:(abs(x[metric+"_percentile"]-target),abs(x[secondary+"_percentile"]-secondary_target),x["sample_id"]))


def common_failure(rows):
    stages=Counter(x["gate_status"] for x in rows)
    stage=min(stages,key=lambda x:(-stages[x],x))
    in_stage=[x for x in rows if x["gate_status"]==stage]
    errors=Counter(x["gate_error"] for x in in_stage)
    error=min(errors,key=lambda x:(-errors[x],x))
    group=[x for x in in_stage if x["gate_error"]==error]
    median=statistics.median(x["operation_count"] for x in group)
    chosen=min(group,key=lambda x:(abs(x["operation_count"]-median),x["sample_id"]))
    return chosen,{"stage":stage,"stage_count":stages[stage],"exact_error":error,"exact_error_count":errors[error],"reference_operation_count_median":median}


def select_cases(rows):
    eligible=[x for x in rows if x["eligible"]]
    picked,used,shortages=[],set(),[]

    def add(row,kind,placement,reason,extra=None):
        require(row["sample_id"] not in used,"Duplicate selected ID within modality")
        used.add(row["sample_id"])
        picked.append({"sample_id":row["sample_id"],"case_type":kind,"placement":placement,"reason":reason,"detail":extra or {}})

    success=[x for x in eligible if x["scoreable"]]
    if success:
        add(central(success,"f1",.5,"cd",.5),"representative_success","main",
            "Executable/scoreable case nearest complete-cohort F@1 percentile0.50, then CD percentile0.50; semantic accuracy not asserted")
    else: shortages.append("main representative_success: no eligible scoreable case")
    failures=[x for x in eligible if x["gate_status"]!="pass"]
    if failures:
        row,detail=common_failure(failures)
        add(row,"hard_failure","main","Dominant first-failure stage and exact native error; median reference feature count; sample-ID tie break",detail)
    else: shortages.append("main hard_failure: no eligible gate failure")
    for kind,metric,target,other,other_target in (("near_median","cd",.5,"f1",.5),("low_tail","f1",.1,"cd",.9)):
        pool=[x for x in success if x["sample_id"] not in used]
        if pool:
            add(central(pool,metric,target,other,other_target),kind,"appendix",
                f"Nearest complete-scoreable-cohort {metric} percentile{target}, then {other} percentile{other_target}; already registered IDs excluded")
        else: shortages.append(f"appendix {kind}: no eligible unused scoreable case")
    frequencies=Counter(op for row in rows for op in row["operation_set"])
    pool=[x for x in eligible if x["sample_id"] not in used and x["operation_set"]]
    if pool:
        row=min(pool,key=lambda x:(min(frequencies[o] for o in x["operation_set"]),not x["scoreable"],abs(x.get("f1_percentile",.5)-.5),x["sample_id"]))
        min_frequency=min(frequencies[o] for o in row["operation_set"])
        rare_ops=[o for o in row["operation_set"] if frequencies[o]==min_frequency]
        add(row,"rare_operation","appendix","Rarest reference OP_* by object frequency in all2500 test objects; scoreable/median-F@1 preference then sample ID",
            {"rarest_operations":rare_ops,"objects_with_each_rarest_operation":min_frequency,"rarity_denominator":len(rows),"rarity_scope":"current IID test cohort, not global corpus"})
    else: shortages.append("appendix rare_operation: no unused eligible reference operation")
    pool=[x for x in eligible if x["sample_id"] not in used]
    if pool:
        row=min(pool,key=lambda x:(-tier_key(x["complexity_tier"]),-x["operation_count"],not x["scoreable"],abs(x.get("f1_percentile",.5)-.5),x["sample_id"]))
        add(row,"high_complexity","appendix","Highest documented tier, largest reference feature count, then scoreable/median-F@1 preference and sample ID")
    else: shortages.append("appendix high_complexity: no eligible unused case")
    tiers=sorted({x["complexity_tier"] for x in rows},key=tier_key)
    indexed={x["sample_id"]:x for x in rows}
    for tier in tiers:
        if any(indexed[x["sample_id"]]["complexity_tier"]==tier for x in picked): continue
        pool=[x for x in eligible if x["sample_id"] not in used and x["complexity_tier"]==tier]
        scored=[x for x in pool if x["scoreable"]]
        if scored:
            median=statistics.median(x["f1"] for x in scored)
            row=min(scored,key=lambda x:(abs(x["f1"]-median),x["sample_id"]))
            add(row,"near_median","appendix_tier_coverage",f"Missing-tier coverage for {tier}: nearest available tier-specific F@1 median",{"tier":tier,"tier_scoreable_pool_n":len(scored),"tier_pool_f1_median":median})
        elif pool:
            row,detail=common_failure([x for x in pool if x["gate_status"]!="pass"]) if any(x["gate_status"]!="pass" for x in pool) else (min(pool,key=lambda x:x["sample_id"]),{})
            add(row,"hard_failure","appendix_tier_coverage",f"Missing-tier coverage for {tier}; no unused eligible scoreable case",detail)
        else: shortages.append(f"tier {tier}: no unused eligible case")
    return picked,shortages


def scan():
    files={}
    def source(path):
        path=Path(path)
        files[str(path)]=file_record(path)
        return path
    test_path=source(SOURCE/"data/25k/test.jsonl")
    test=read_index(test_path)
    ids=list(test)
    require(len(ids)==2500,"Expected2500 IID test source IDs")
    split_sets={"test":set(ids)}
    for split in ("train","val"):
        split_sets[split]=set(read_index(source(SOURCE/f"data/25k/{split}.jsonl")))
    require(not split_sets["train"]&split_sets["test"] and not split_sets["val"]&split_sets["test"]
            and not split_sets["train"]&split_sets["val"],"Source ID leakage")
    lookup=read_index(source(WINDOWS/"scratch/complexity_lookup.jsonl"))
    run_meta=read_json(source(SOURCE/"outputs/stage3b_geometry/run_metadata.json"))
    require(run_meta["repair_applied"] is True and run_meta["n_per_arm"]==2500,"Historical repair/cohort metadata mismatch")
    for relative in ("final/ComputersGraphics_version2/main.tex","src/training_25k/scripts/run_full_stage3b_pipeline.sh",
        "src/training_25k/32_stage3b_geometry.sh","src/training_25k/23_exec_norepair_all.ps1"):
        source(WINDOWS/relative)
    for relative in ("training_25k/scripts/gen_predicted_ir.py","training_25k/scripts/gen_code_from_predicted_ir.py",
        "miragecad/gen_prompts.py","miragecad/point_sampling.py","evaluate_geometry_nbest.py"):
        source(SOURCE/relative)
    checkpoint_sources={}
    for label,relative in {"plan_adapter":"outputs/lora_ir_25k_stage3b/adapter_model.safetensors",
        "plan_prefix":"outputs/lora_ir_25k_stage3b/soft_prefix.pt","code_adapter":"outputs/qwen25_coder_1_5b_program_25k_stage4b/adapter_model.safetensors",
        "plan_report":"outputs/lora_ir_25k_stage3b/soft_prefix_training_report.json","code_report":"outputs/qwen25_coder_1_5b_program_25k_stage4b/training_report.json"}.items():
        checkpoint_sources[label]=file_record(source(SOURCE/relative))
    cohorts,raw,summaries={},{},{}
    for m in MODALITIES:
        paths={"test":test_path,
            "raw_plan":SOURCE/f"outputs/lora_ir_25k_stage3b/predicted_ir_test_{m}.jsonl",
            "used_plan":SOURCE/f"outputs/lora_ir_25k_stage3b/predicted_ir_test_{m}_p1a.jsonl",
            "raw_code":SOURCE/f"outputs/qwen25_coder_1_5b_program_25k_stage4b/gen_test_{m}_stage3b.jsonl",
            "intermediate_code":SOURCE/f"outputs/qwen25_coder_1_5b_program_25k_stage4b/gen_test_{m}_stage3b_repaired.jsonl",
            "prediction":SOURCE/f"outputs/qwen25_coder_1_5b_program_25k_stage4b/gen_test_{m}_stage3b_repaired_p0.jsonl",
            "geometry_input":SOURCE/f"outputs/stage3b_geometry/geom_input_{m}_stage3b.jsonl",
            "gate":WINDOWS/f"scratch/exec_eval_25k_stage3b_{m}/execution_rows.jsonl",
            "geometry":WINDOWS/f"scratch/geom_stage3b_{m}_stage3b/geometry_nbest_rows.jsonl"}
        entries={role:(test if role=="test" else read_index(source(path),ids)) for role,path in paths.items()}
        gate_summary=read_json(source(WINDOWS/f"scratch/exec_eval_25k_stage3b_{m}/execution_summary.json"))
        require(gate_summary["rows"]==2500,"Wrong legacy gate denominator")
        counts={flag:sum(x["row"][flag] is True for x in entries["gate"].values()) for flag in FLAGS}
        for flag in FLAGS:
            require(counts[flag]==gate_summary[flag+"_count"] and math.isclose(counts[flag]/2500,gate_summary[flag+"_rate"],abs_tol=1e-12),"Legacy gate rows/summary mismatch")
        for flag,want in zip(("syntax_ok","build_ok","step_export_ok"),PUBLISHED[m]):
            require(abs(counts[flag]/25-want)<=.051,f"Wrong paper condition: {m}/{flag}")
        rows=[]
        for sid in ids:
            t=test[sid]["row"]
            p=entries["prediction"][sid]["row"]
            plan=entries["used_plan"][sid]["row"]
            inp=entries["geometry_input"][sid]["row"]
            g=entries["gate"][sid]["row"]
            geom=entries["geometry"][sid]["row"]
            require(all(x["row"].get("modality")==m for key in ("raw_plan","used_plan","raw_code","intermediate_code","prediction","geometry_input") for x in (entries[key][sid],)),"Source modality mismatch")
            require(p["predicted_ir"]==plan["predicted_ir"],"Used-plan/code association mismatch")
            require(inp["all_candidates"]==[p["prediction"]] and inp["point_path"]==t["point_path"],"Geometry prediction/reference association mismatch")
            require(p["reference_ir"]==plan["reference_ir"],"Reference plan association mismatch")
            require(all(type(g[k]) is bool for k in FLAGS),"Wrong gate flag type")
            candidates=geom.get("candidate_results",[])
            c=candidates[0] if len(candidates)==1 else {}
            agree=all(g[k]==c.get(k) for k in FLAGS)
            scored=scoreable(geom,c)
            if scored: require(c["cd"]>=0 and 0<=c["f_score_1pct"]<=1,"Invalid measured metric")
            features=reference_features(p["reference_ir"],sid)
            tier=t.get("complexity_level") or lookup.get(sid,{}).get("row",{}).get("complexity_level")
            if sid in lookup and t.get("complexity_level"):
                require(tier==lookup[sid]["row"]["complexity_level"],"Complexity source conflict")
            tier_key(tier)
            reasons=[]
            if not agree: reasons.append("standalone_geometry_gate_disagreement")
            if len(candidates)!=1: reasons.append("not_exactly_one_geometry_candidate")
            if geom.get("has_target") is not True: reasons.append("reference_not_present_in_native_geometry_run")
            rows.append({"sample_id":sid,"modality":m,"source_split":"test","scoreable":scored,
                "cd":c.get("cd") if scored else None,"f1":c.get("f_score_1pct") if scored else None,
                "complexity_tier":tier,**features,"gate_status":first_stage(g),"gate_error":g["error"],
                "geometry_error":c.get("error") or geom.get("error", ""),"gate_flags":{k:g[k] for k in FLAGS},
                "geometry_gate_flags":{k:c.get(k) for k in FLAGS},"eligible":not reasons,"ineligible_reasons":reasons,
                "prediction_line_1based":entries["prediction"][sid]["line_1based"]})
        scored=[r for r in rows if r["scoreable"]]
        percentiles(scored,"cd")
        percentiles(scored,"f1")
        cohorts[m]=rows
        raw[m]={"entries":entries,"paths":paths}
        summaries[m]={"test_rows":2500,"native_gate_summary":gate_summary,"scoreable":len(scored),
            "eligible":sum(x["eligible"] for x in rows),"ineligible":[{"sample_id":x["sample_id"],"reasons":x["ineligible_reasons"]} for x in rows if not x["eligible"]],
            "scoreable_median_cd":statistics.median(x["cd"] for x in scored),"scoreable_median_f1":statistics.median(x["f1"] for x in scored),
            "tier_counts":dict(Counter(x["complexity_tier"] for x in rows)),"reference_operation_object_counts":dict(Counter(op for x in rows for op in x["operation_set"])),
            "first_failure_counts":dict(Counter(x["gate_status"] for x in rows))}
        print(f"Source PASS {m}:2500 IDs, published Table7 rates, used plans and executed-code geometry inputs match; scoreable{len(scored)}, eligible{summaries[m]['eligible']}",flush=True)
    return cohorts,raw,files,summaries,checkpoint_sources


def materialize_case(cohort_row,selection,source_data,files,checkpoints,policy_record,cohort_path,checkout):
    sid,m=cohort_row["sample_id"],cohort_row["modality"]
    case_id=f"q-flone-{m}-b2legacy-{sid}"
    root=PACKAGE/"cases"/case_id
    require(not root.exists(),f"Refusing to reuse case directory: {root}")
    entries,paths=source_data["entries"],source_data["paths"]
    t=entries["test"][sid]["row"]
    p=entries["prediction"][sid]["row"]
    root.mkdir(parents=True)
    extracted={}
    def extract(role,relative,text):
        extracted[role]=write_text(root/relative,text)
        return str((root/relative).relative_to(PACKAGE))
    query_path=extract("exact_text","input/exact_text.txt",t["text"])
    raw_plan_path=extract("raw_plan","plans/raw.txt",entries["raw_plan"][sid]["row"]["predicted_ir"])
    used_plan_path=extract("used_plan","plans/canonicalized.txt",p["predicted_ir"])
    raw_code_path=extract("raw_code","code/raw_prediction.py",entries["raw_code"][sid]["row"]["prediction"])
    intermediate_path=extract("intermediate_code","code/extrude_repaired.py",entries["intermediate_code"][sid]["row"]["prediction"])
    code_path=extract("executed_code","code/prediction.py",p["prediction"])
    excerpt=extract("code_excerpt","code/excerpt.txt","# Literal first40 lines of executed prediction; full program is prediction.py\n"+"\n".join(p["prediction"].splitlines()[:40])+"\n")
    extract("reference_ir","reference/training_ir.txt",p["reference_ir"])
    extract("reference_code","reference/program.py",p["reference"])
    write_json(root/"logs/gate_row.json",entries["gate"][sid]["row"])
    write_json(root/"logs/geometry_row.json",entries["geometry"][sid]["row"])
    fail=cohort_row["gate_status"]!="pass" or not cohort_row["scoreable"]
    failure_path=None
    if fail:
        write_json(root/"logs/native_failure_messages.json",{"sample_id":sid,"modality":m,"gate_error":cohort_row["gate_error"],
            "geometry_error":cohort_row["geometry_error"],"note":"Original native error summaries, not an invented full traceback or visual feature diagnosis"})
        failure_path=str((root/"logs/native_failure_messages.json").relative_to(PACKAGE))
    locators={role:{"file":files[str(path)],"line_1based":entries[role][sid]["line_1based"],
        "line_bytes_sha256":entries[role][sid]["line_bytes_sha256"],"stable_key":{"sample_id":sid,"modality":m} if role!="test" and role!="gate" else {"sample_id":sid}}
        for role,path in paths.items()}
    locator_path=str((root/"prediction_locator.json").relative_to(PACKAGE))
    write_json(root/"prediction_locator.json",{"sample_id":sid,"modality":m,"locators":locators})
    assets=[]
    verified={}
    for role,value in {"reference_step":t["step_path"],"reference_point":t["point_path"],"input_image":t["iso_image_path"],
        "step_descriptor":t["step_feature_path"],"reference_ir_source":t["ir_path"],"reference_code_source":t["program_path"],
        "reference_feature_tree":t["feature_tree_path"],"reference_metadata":t["metadata_path"]}.items():
        path=Path(value)
        if not path.is_absolute(): path=SOURCE/path
        if path.is_file() and path.stat().st_size:
            item=file_record(path)
            verified[role]=item
            assets.append({"asset_role":role,"status":"existing","source_path":str(path),"package_path":None,
                "planned_path":None,"sha256":item["sha256"],"bytes":item["bytes"],"verified_utc":now(),"path_style":"WSL absolute"})
        else:
            assets.append({"asset_role":role,"status":"missing","source_path":None,"requested_source_path":str(path),
                "package_path":None,"planned_path":None,"sha256":None,"missing_reason":"Referenced original source absent/empty at collection; no substitute used"})
    if "reference_ir_source" in verified:
        require(Path(verified["reference_ir_source"]["path"]).read_text(encoding="utf-8").strip()==p["reference_ir"].strip(),"Reference IR changed since prediction record")
    if "reference_code_source" in verified:
        require(Path(verified["reference_code_source"]["path"]).read_text(encoding="utf-8").strip()==p["reference"].strip(),"Reference code changed since prediction record")
    for role,item in extracted.items():
        assets.append({"asset_role":role,"status":"existing","source_path":None,"package_path":str(Path(item["path"]).relative_to(PACKAGE)),
            "planned_path":None,"sha256":item["sha256"],"bytes":item["bytes"],"verified_utc":now(),"path_style":"package relative"})
    for view in ("view01","view02"):
        for who in ("reference","prediction"):
            status="planned" if who=="reference" or cohort_row["gate_flags"]["step_export_ok"] else "not_applicable"
            assets.append({"asset_role":who+"_gallery_render","status":status,"source_path":None,"package_path":None,
                "planned_path":f"cases/{case_id}/renders/{who}/{view}.png" if status=="planned" else None,
                "sha256":None,"view_id":view,"camera":None,"missing_reason":"Matched-camera gallery rendering not run" if status=="planned" else "No successful native STEP export; no substitute prediction solid"})
    exported=cohort_row["gate_flags"]["step_export_ok"]
    assets.append({"asset_role":"predicted_step","status":"planned" if exported else "not_applicable","source_path":None,
        "package_path":None,"planned_path":f"cases/{case_id}/prediction/model.step" if exported else None,"sha256":None,
        "missing_reason":"Native scorer used a deleted temporary STEP; persistent export requires a later authorized rendering workflow" if exported else "Native program did not pass STEP export"})
    write_json(root/"assets.json",{"case_id":case_id,"gallery_rendering":"NOT_RUN","assets":assets,
        "camera_policy":"At least two shared target/prediction cameras and common target scale; no independent prediction resizing",
        "original_input_image_note":"Existing dataset iso image is an original reference image/input, not proof of completed matched-camera gallery views"})
    write_json(root/"provenance.json",{"case_id":case_id,"created_utc":now(),"source_split":"test","experiment":"legacy_deployed_B2_Table7_repaired",
        "selection_policy":policy_record,"cohort":file_record(cohort_path),"selection":selection,"cohort_row":cohort_row,
        "checkout":checkout,"source_locators":locators,"extracted_fields":extracted,"original_assets":verified,
        "current_checkpoint_observations":checkpoints,"historical_checkpoint_binding":"UNATTESTED_IN_LEGACY_RUN_METADATA",
        "training_seed":None,"training_seed_note":"Default inference seed42 is not proof of historical training seed; do not invent a run attestation",
        "program_repair":True,"repair_sequence":["repair_extrude_on_face","repair_profile_cut_offset_P0"],
        "plan_canonicalization":"P1a face/extrude alias", "model_or_CAD_execution_during_packaging":False,
        "point_input_note":"Original NPZ source; normalized1024-FPS tensor not re-created or claimed identical here",
        "standalone_and_geometry_gates_agree":True})
    failure_category=None
    if cohort_row["gate_status"]!="pass":
        failure_category={"syntax_failure":"syntax","execution_failure":"execution","build_failure":"execution",
            "solid_invalid":"invalid_solid","step_export_failure":"step_export"}[cohort_row["gate_status"]]
    elif not cohort_row["scoreable"]: failure_category="geometry_unscoreable"
    input_role={"text":"exact_text","image":"input_image","point":"reference_point","step":"step_descriptor"}[m]
    input_path=query_path if m=="text" else verified.get(input_role,{}).get("path")
    representation={"text":"Exact dataset text field; deterministic and LLM text concatenation retained verbatim",
        "image":"Original iso_image_path PNG used by legacy image encoder",
        "point":"Original point NPZ source for normalized1024-FPS inference; processed tensor not retained/created here",
        "step":"Kernel-derived50-global-statistic descriptor JSON; not a face/edge B-Rep graph"}[m]
    schema=read_json(PACKAGE/"qualitative_case_registry.schema.json")
    row={key:None for key in schema["properties"]}
    row.update(case_id=case_id,registry_status="candidate",corpus="FllumaOne",source_split="test",modality=m,sample_id=sid,
        experiment_id="legacy_deployed_B2_Table7_repaired",arm="B2_legacy_deployed",seed=None,
        checkpoint_path=str(SOURCE/"outputs/qwen25_coder_1_5b_program_25k_stage4b"),checkpoint_sha256=None,
        protocol_path=str(POLICY),protocol_sha256=policy_record["sha256"],checkout_path=str(SOURCE),checkout_commit=checkout["commit"],
        program_repair=True,plan_canonicalization="P1a face/extrude alias",comparison_group_id=f"flone-iid-{m}-{sid}",
        case_type=selection["case_type"],tags=[selection["placement"],"candidate_not_visually_selected","legacy_repaired",
            "executable_scoreable_not_semantic_success" if cohort_row["scoreable"] else "native_failure", "tier_"+cohort_row["complexity_tier"]],
        selection_reason=selection["reason"],selection_cohort_path=str(cohort_path),
        selection_metric="F@1 percentile among complete modality scoreable cohort" if selection["case_type"] in ("representative_success","low_tail") else "CD percentile among complete modality scoreable cohort" if selection["case_type"]=="near_median" and selection["placement"]!="appendix_tier_coverage" else "See selection detail in provenance.json",
        selection_quantile_fraction=cohort_row.get("f1_percentile") if selection["case_type"] in ("representative_success","low_tail") else cohort_row.get("cd_percentile") if selection["case_type"]=="near_median" and selection["placement"]!="appendix_tier_coverage" else None,
        input_representation=representation,input_path=input_path,exact_text_input_path=query_path,
        reference_step_path=verified.get("reference_step",{}).get("path"),reference_render_path=verified.get("input_image",{}).get("path"),
        predicted_plan_path=used_plan_path,raw_plan_path=raw_plan_path,predicted_code_path=code_path,
        prediction_jsonl_path=str(paths["prediction"]),prediction_jsonl_line_1based=entries["prediction"][sid]["line_1based"],
        prediction_record_locator_path=locator_path,code_excerpt_path=excerpt,
        gate_summary_path=str(WINDOWS/f"scratch/exec_eval_25k_stage3b_{m}/execution_summary.json"),
        gate_row_path=str((root/"logs/gate_row.json").relative_to(PACKAGE)),geometry_row_path=str((root/"logs/geometry_row.json").relative_to(PACKAGE)),
        failure_log_path=failure_path,gate_status=cohort_row["gate_status"],syntax_ok=cohort_row["gate_flags"]["syntax_ok"],
        build_ok=cohort_row["gate_flags"]["build_ok"],step_export_ok=exported,scoreable=cohort_row["scoreable"],
        metric_status="measured" if cohort_row["scoreable"] else "not_scoreable",
        metric_missing_reason=None if cohort_row["scoreable"] else cohort_row["gate_error"] or cohort_row["geometry_error"] or "Native geometry not scoreable",
        cd=cohort_row["cd"],cd_units_and_scaling="Symmetric mean squared nearest-neighbour CD in native model coordinate units; no posthoc scaling; squared mm for this mm corpus",
        f1_at_1_fraction=cohort_row["f1"],iou_fraction=None,metric_protocol_path=str(SOURCE/"evaluate_geometry_nbest.py"),
        complexity_tier=cohort_row["complexity_tier"],operation_count=cohort_row["operation_count"],operation_set=cohort_row["operation_set"],
        failure_category=failure_category,failure_evidence_path=failure_path,provenance_manifest_path=str((root/"provenance.json").relative_to(PACKAGE)),
        asset_manifest_path=str((root/"assets.json").relative_to(PACKAGE)),
        notes="CANDIDATE only; no visual semantic-quality assessment or CAD execution. Historical training seed/runtime checkpoint-byte binding unresolved; seed/checkpoint SHA intentionally null. Raw, P1a plan, raw code and two code-repair stages are separately preserved. Predicted STEP/matched-camera renders are not retained and are not fabricated. Low-tail is metric-guided, not proof of a missing feature. IoU not measured by this evaluator.")
    write_json(root/"case.json",row)
    return row


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("audit","select"))
    args=parser.parse_args()
    cohorts,raw,files,summaries,checkpoints=scan()
    policy=file_record(POLICY)
    checkout={**observe_checkout(SOURCE),"canonical_windows_repository":observe_checkout(WINDOWS),
        "note":"Source/data root may be an unversioned copied tree. Never substitute the canonical Windows repository commit as a commit of that root. Current observations do not attest historical executed tree bytes; exact inspected source hashes retained"}
    source_audit={"created_utc":now(),"status":"PASS_LEGACY_TABLE7_SOURCE_ASSOCIATIONS","policy":policy,"collector":file_record(__file__),
        "source_files":files,"summaries":summaries,"checkout":checkout,"current_checkpoint_observations":checkpoints,
        "legacy_runtime_checkpoint_binding":"UNATTESTED","training_model_or_CAD_execution":False}
    if args.mode=="audit":
        write_json(PACKAGE/"selection/source_audit_v1.json",source_audit)
        print(json.dumps({"status":source_audit["status"],"summaries":summaries},indent=2),flush=True)
        return
    audit_path=PACKAGE/"selection/source_audit_v1.json"
    previous=read_json(audit_path)
    require(previous["policy"]==policy and previous["source_files"]==files,"Source/policy changed since source audit")
    require(not (PACKAGE/"selection/candidate_rows_v1.json").exists(),"Candidate snapshot already exists")
    before=file_record(PACKAGE/"qualitative_case_registry.csv")
    require(len((PACKAGE/"qualitative_case_registry.csv").read_text(encoding="utf-8").splitlines())==1,"Registry is populated; do not overwrite manual work")
    cohort_path=PACKAGE/"selection/cohort_v1.jsonl"
    write_text(cohort_path,"".join(json.dumps(row,ensure_ascii=True,allow_nan=False)+"\n" for m in MODALITIES for row in cohorts[m]))
    rows,choices,shortages=[],{},{}
    for m in MODALITIES:
        choices[m],shortages[m]=select_cases(cohorts[m])
        index={x["sample_id"]:x for x in cohorts[m]}
        for choice in choices[m]:
            rows.append(materialize_case(index[choice["sample_id"]],choice,raw[m],files,checkpoints,policy,cohort_path,checkout))
    for item in files.values(): require(file_record(item["path"])==item,"Original source changed during packaging")
    payload={"created_utc":now(),"status":"CANDIDATES_EXTRACTED_CSV_PENDING","registry_before":before,"schema":file_record(PACKAGE/"qualitative_case_registry.schema.json"),
        "selection_policy":policy,"collector":file_record(__file__),"source_audit":file_record(audit_path),"cohort":file_record(cohort_path),
        "choices":choices,"shortages":shortages,"rows":rows,"main_candidates":sum("main" in row["tags"] for row in rows),
        "appendix_candidates":sum("main" not in row["tags"] for row in rows),"all_registry_status":"candidate",
        "gallery_rendered":False,"training_model_or_CAD_execution":False}
    write_json(PACKAGE/"selection/candidate_rows_v1.json",payload)
    print(json.dumps({"status":payload["status"],"main":payload["main_candidates"],"appendix":payload["appendix_candidates"],"choices":choices,"shortages":shortages},indent=2),flush=True)


if __name__=="__main__": main()
