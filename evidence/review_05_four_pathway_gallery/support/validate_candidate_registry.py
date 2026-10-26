#!/usr/bin/env python3
"""Validate CSV/schema contract, literal extractions, paths and all original sources; no CAD."""
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import sys

PACKAGE=Path(__file__).resolve().parents[1]


def require(ok,message):
    if not ok: raise ValueError(message)


def local(value):
    text=str(value)
    if os.name=="nt":
        if text.startswith("/mnt/") and len(text)>7:
            return Path(text[5].upper()+":/"+text[7:])
        if text.startswith("/"):
            return Path("\\\\wsl.localhost\\Ubuntu"+text.replace("/","\\"))
    else:
        if re.match(r"^[A-Za-z]:[\\/]",text):
            return Path("/mnt/"+text[0].lower()+"/"+text[3:].replace("\\","/"))
    path=Path(text)
    if path.is_absolute(): return path
    require(".." not in path.parts,"Package path escapes evidence root")
    return PACKAGE/path


def load(path):
    return json.loads(local(path).read_text(encoding="utf-8-sig"))


def record(path):
    path=local(path)
    return {"path":str(path),"bytes":path.stat().st_size,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}


class FixedSchemaContract:
    """All validation keywords used by the supplied fixed schema, not a general Draft2020 engine."""
    keywords={"$schema","$id","title","description","$defs","$ref","type","required","properties","additionalProperties",
        "enum","const","minimum","maximum","pattern","minLength","items","uniqueItems","allOf","if","then"}

    def __init__(self,schema):
        self.root=schema
        self.audit_keywords(schema)

    def audit_keywords(self,node):
        require(not(set(node)-self.keywords),f"Unsupported schema keyword(s): {set(node)-self.keywords}")
        for group in ("$defs","properties"):
            for child in node.get(group,{}).values(): self.audit_keywords(child)
        for child in node.get("allOf",[]): self.audit_keywords(child)
        for field in ("if","then","items"):
            if field in node: self.audit_keywords(node[field])

    def check(self,value,node=None,where="case"):
        node=self.root if node is None else node
        if "$ref" in node:
            prefix="#/$defs/"
            require(node["$ref"].startswith(prefix),"Only local definition refs are supported")
            self.check(value,self.root["$defs"][node["$ref"][len(prefix):]],where)
        types=node.get("type")
        if isinstance(types,str): types=[types]
        if types is not None:
            matches={"null":value is None,"string":isinstance(value,str),"object":isinstance(value,dict),
                "array":isinstance(value,list),"boolean":type(value) is bool,
                "integer":type(value) is int,"number":type(value) in (int,float) and math.isfinite(value)}
            require(any(matches[t] for t in types),f"{where}: wrong type")
        if "enum" in node:
            require(any(type(value) is type(v) and value==v for v in node["enum"]),f"{where}: enum")
        if "const" in node:
            require(type(value) is type(node["const"]) and value==node["const"],f"{where}: const")
        if isinstance(value,dict):
            require(set(node.get("required",[]))<=value.keys(),f"{where}: required key missing")
            props=node.get("properties",{})
            if node.get("additionalProperties") is False:
                require(not(set(value)-set(props)),f"{where}: additional property")
            for key,child in props.items():
                if key in value: self.check(value[key],child,where+"."+key)
        if isinstance(value,list):
            if node.get("uniqueItems"):
                require(len({json.dumps(x,sort_keys=True) for x in value})==len(value),f"{where}: duplicate array item")
            if "items" in node:
                for i,child in enumerate(value): self.check(child,node["items"],f"{where}[{i}]")
        if isinstance(value,str):
            if "minLength" in node: require(len(value)>=node["minLength"],f"{where}: minLength")
            if "pattern" in node: require(re.search(node["pattern"],value) is not None,f"{where}: pattern")
        if type(value) in (int,float):
            if "minimum" in node: require(value>=node["minimum"],f"{where}: minimum")
            if "maximum" in node: require(value<=node["maximum"],f"{where}: maximum")
        for child in node.get("allOf",[]): self.check(value,child,where)
        if "if" in node:
            try: self.check(value,node["if"],where)
            except ValueError: return
            if "then" in node: self.check(value,node["then"],where)


def decode_cell(text,spec,schema,key):
    if text=="": return "" if key=="notes" else None
    if "$ref" in spec: spec=schema["$defs"][spec["$ref"].split("/")[-1]]
    types=spec.get("type",[])
    if isinstance(types,str): types=[types]
    if "array" in types: return json.loads(text)
    if "boolean" in types:
        require(text in ("true","false"),"Noncanonical CSV boolean")
        return text=="true"
    if "integer" in types: return int(text)
    if "number" in types:
        value=float(text)
        require(math.isfinite(value),"Nonfinite CSV metric")
        return value
    return text


def contract_mutation_tests(validator,row):
    import copy
    mutations=[]
    for field,value in (("case_id","INVALID ID"),("registry_status","finished"),("f1_at_1_fraction",1.01),
        ("cd",-1.),("build_ok",1),("seed",-1),("operation_set",["OP_A","OP_A"]),("checkpoint_sha256","bad"),
        ("sample_id",""),("prediction_jsonl_line_1based",0)):
        item=copy.deepcopy(row); item[field]=value; mutations.append(item)
    item=copy.deepcopy(row); del item["selection_reason"]; mutations.append(item)
    item=copy.deepcopy(row); item["unregistered_field"]=True; mutations.append(item)
    item=copy.deepcopy(row); item.update(registry_status="selected",input_path=None); mutations.append(item)
    item=copy.deepcopy(row); item.update(metric_status="measured",geometry_row_path=None); mutations.append(item)
    for item in mutations:
        try: validator.check(item)
        except ValueError: continue
        raise ValueError("Schema contract failed to reject a deliberate malformed case")
    return len(mutations)


def main():
    destination=PACKAGE/"selection/registry_validation_v1.json"
    require(not destination.exists(),"Validation report already exists")
    schema=load(PACKAGE/"qualitative_case_registry.schema.json")
    validator=FixedSchemaContract(schema)
    payload=load(PACKAGE/"selection/candidate_rows_v1.json")
    population=load(PACKAGE/"support/registry_population_v1.json")
    with (PACKAGE/"qualitative_case_registry.csv").open(encoding="utf-8",newline="") as stream:
        reader=csv.DictReader(stream)
        require(reader.fieldnames==list(schema["properties"]),"CSV column order changed")
        rows=[{key:decode_cell(value,schema["properties"][key],schema,key) for key,value in row.items()} for row in reader]
    require(len(rows)==24 and len({r["case_id"] for r in rows})==24,"Wrong registry row identity/count")
    require(rows==payload["rows"],"CSV typed values differ from frozen candidate snapshots")
    require(record(PACKAGE/"qualitative_case_registry.csv")["sha256"]==population["csv"]["sha256"],"CSV export hash drift")
    for row in rows: validator.check(row)
    mutation_checks=contract_mutation_tests(validator,rows[0])
    for types,field,expected in (("boolean","build_ok",False),("number","cd",0.),("integer","seed",0)):
        require(decode_cell("false" if types=="boolean" else "0",schema["properties"][field],schema,field)==expected,"Zero/false converted to missing")
        require(decode_cell("",schema["properties"][field],schema,field) is None,"Missing converted to false/zero")
    source_audit=load(payload["source_audit"]["path"])
    verified={}
    byte_cache={}
    line_cache={}
    def verify(item):
        path=local(item["path"])
        key=str(path)
        if key not in verified:
            raw=path.read_bytes()
            require(len(raw)==item["bytes"] and hashlib.sha256(raw).hexdigest()==item["sha256"],f"Source/extraction hash drift: {path}")
            verified[key]={"path":key,"bytes":len(raw),"sha256":item["sha256"],"mtime_ns":path.stat().st_mtime_ns}
            if path.suffix==".jsonl": byte_cache[key]=raw
        else:
            require(verified[key]["sha256"]==item["sha256"],"Conflicting source hash authorities")
    for item in source_audit["source_files"].values(): verify(item)
    for item in (payload["collector"],payload["selection_policy"],payload["schema"],payload["source_audit"],payload["cohort"]): verify(item)
    tests=load(PACKAGE/"selection/candidate_contract_tests_v2.json")
    require(tests["status"]=="PASS" and tests["tests_run"]==13,"Current rule tests missing")
    verify(tests["source"]); verify(tests["test_source"])
    spec=importlib.util.spec_from_file_location("gallery_rules",PACKAGE/"support/select_gallery_candidates.py")
    rules=importlib.util.module_from_spec(spec); spec.loader.exec_module(rules)
    cohort=[json.loads(line) for line in local(payload["cohort"]["path"]).read_text().splitlines() if line.strip()]
    require(len(cohort)==10000,"Incomplete selection cohort")
    for m in rules.MODALITIES:
        data=[x for x in cohort if x["modality"]==m]
        choices,shortages=rules.select_cases(data)
        require(choices==payload["choices"][m] and shortages==payload["shortages"][m],"Selection IDs/reasons no longer reproduce")
    case_inventory={}
    main_rows=[]
    missing_assets=[]
    for row in rows:
        root=PACKAGE/"cases"/row["case_id"]
        require(load(root/"case.json")==row,"Per-case snapshot/CSV mismatch")
        prov=load(root/"provenance.json")
        require(prov["case_id"]==row["case_id"] and prov["standalone_and_geometry_gates_agree"] is True,"Wrong case provenance")
        extracted=prov["extracted_fields"]
        for item in extracted.values(): verify(item)
        for item in prov["original_assets"].values(): verify(item)
        source_rows={}
        for role,locator in prov["source_locators"].items():
            verify(locator["file"])
            path=str(local(locator["file"]["path"]))
            if path not in line_cache: line_cache[path]=byte_cache[path].splitlines()
            line=line_cache[path][locator["line_1based"]-1]
            require(hashlib.sha256(line).hexdigest()==locator["line_bytes_sha256"],"Physical JSONL line hash drift")
            original=json.loads(line.decode("utf-8-sig"))
            for key,value in locator["stable_key"].items(): require(original[key]==value,"Locator stable-key mismatch")
            source_rows[role]=original
        for role,source_role,field in (("raw_plan","raw_plan","predicted_ir"),("used_plan","used_plan","predicted_ir"),
            ("raw_code","raw_code","prediction"),("intermediate_code","intermediate_code","prediction"),
            ("executed_code","prediction","prediction"),("reference_ir","prediction","reference_ir"),
            ("reference_code","prediction","reference"),("exact_text","test","text")):
            require(local(extracted[role]["path"]).read_bytes()==source_rows[source_role][field].encode("utf-8"),"Literal plan/code/text extraction changed")
        require(load(root/"logs/gate_row.json")==source_rows["gate"] and load(root/"logs/geometry_row.json")==source_rows["geometry"],"Native row extraction changed")
        g=source_rows["geometry"]["candidate_results"][0]
        if row["scoreable"]:
            require(row["cd"]==g["cd"] and row["f1_at_1_fraction"]==g["f_score_1pct"],"Case metric differs from native record")
        else:
            require(row["cd"] is None and row["f1_at_1_fraction"] is None,"Unscoreable case has fabricated zero metric")
        require(row["program_repair"] is True and row["seed"] is None and row["checkpoint_sha256"] is None,"Legacy condition/uncertainty was silently changed")
        require(row["predicted_step_path"] is None and row["predicted_render_path"] is None,"Unrendered predicted asset must stay null")
        for key,value in row.items():
            if key.endswith("_path") and value is not None:
                path=local(value)
                require(path.exists(),f"Registered actual path does not exist: {key}/{value}")
                if path.is_file(): require(path.stat().st_size>0,"Registered empty asset")
        assets=load(root/"assets.json")
        require(assets["gallery_rendering"]=="NOT_RUN","Candidate packaging cannot imply completed gallery rendering")
        for asset in assets["assets"]:
            if asset["status"]=="existing":
                path=local(asset["source_path"] or asset["package_path"])
                require(path.is_file() and path.stat().st_size>0,"Existing asset missing/empty")
                require(record(path)["sha256"]==asset["sha256"],"Asset hash mismatch")
            else:
                require(asset.get("package_path") is None and asset.get("sha256") is None,"Planned/missing asset masquerades as existing")
                if asset["status"]=="missing": missing_assets.append({"case_id":row["case_id"],"asset":asset})
        for path in root.rglob("*"):
            if path.is_file(): case_inventory[str(path.relative_to(PACKAGE))]=record(path)
        if "main" in row["tags"]: main_rows.append(row)
    for m in rules.MODALITIES:
        subset=[r for r in rows if r["modality"]==m]
        require(len(subset)==6 and {r["complexity_tier"] for r in subset}=={"L1","L2","L3","L4"},"Modality/category/tier coverage incomplete")
    require(len(main_rows)==8 and all(r["registry_status"]=="candidate" for r in rows),"Wrong main/status counts")
    # Quantitative closure records and live indexes must not be edited by this task.
    closed=load(PACKAGE.parent/"04/execution/final_evidence_inventory_20261022.json")
    for item in closed["files"].values(): verify(item)
    for item in verified.values():
        stat=Path(item["path"]).stat()
        require(stat.st_size==item["bytes"] and stat.st_mtime_ns==item["mtime_ns"],"Verified source changed during validation")
    report={"created_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS_CANDIDATES_SCHEMA_PATHS_LOCATORS_AND_HASHES",
        "registry":record(PACKAGE/"qualitative_case_registry.csv"),"rows":24,"columns":63,"unique_target_ids":len({r["sample_id"] for r in rows}),
        "main_candidates":8,"appendix_candidates":16,"per_modality":dict(Counter(r["modality"] for r in rows)),
        "case_types":dict(Counter(r["case_type"] for r in rows)),"scoreable_candidates":sum(r["scoreable"] for r in rows),
        "schema_validator":"Fixed contract validator covers every keyword in the supplied63-column schema; not a general Draft2020 implementation",
        "schema_negative_mutation_tests":mutation_checks,"selection_unit_tests":13,"source_files_verified":len(verified),
        "case_inventory":case_inventory,"validator_source":record(__file__),"selection_policy":payload["selection_policy"],
        "schema":payload["schema"],"cohort":payload["cohort"],"missing_original_assets":missing_assets,
        "gallery_rendering":"NOT_STARTED","visual_verification":"PENDING","all_status":"candidate",
        "original_quantitative_review04_inventory":"UNCHANGED_ALL17_ARTIFACTS",
        "historical_seed_checkpoint_binding":"UNRESOLVED_NOT_FABRICATED","training_model_or_CAD_execution":False}
    destination.write_text(json.dumps(report,indent=2,ensure_ascii=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k not in ("case_inventory",)},indent=2),flush=True)


if __name__=="__main__": main()
