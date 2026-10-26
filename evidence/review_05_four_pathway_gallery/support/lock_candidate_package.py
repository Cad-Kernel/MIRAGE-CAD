"""Snapshot the completed candidate-only package; never generate or execute a model."""
from datetime import datetime,timezone
from pathlib import Path
import json

from validate_candidate_registry import PACKAGE,load,record,require,local


def main():
    output=PACKAGE/"selection/path_lock_manifest_v1.json"
    require(not output.exists(),"Path-lock snapshot exists; do not overwrite")
    validation=load(PACKAGE/"selection/registry_validation_v1.json")
    payload=load(PACKAGE/"selection/candidate_rows_v1.json")
    population=load(PACKAGE/"support/registry_population_v1.json")
    require(validation["status"]=="PASS_CANDIDATES_SCHEMA_PATHS_LOCATORS_AND_HASHES","Final validation missing")
    require(record(PACKAGE/"qualitative_case_registry.csv")==validation["registry"],"CSV changed after final validation")
    require(record(validation["validator_source"]["path"])==validation["validator_source"],"Validator changed since PASS")
    require(record(PACKAGE/"support/build_registry.mjs")["sha256"]==population["builder_sha256"],"Builder changed since CSV export")
    for name,item in validation["case_inventory"].items(): require(record(item["path"])==item,f"Case changed after validation: {name}")
    closed=load(PACKAGE.parent/"04/execution/final_evidence_inventory_20261022.json")
    for item in closed["files"].values():
        current=record(local(item["path"]))
        require(current["bytes"]==item["bytes"] and current["sha256"]==item["sha256"],"Review04 closure evidence changed")
    names=["README.md","01_reviewer_requirements.md","02_folder_and_path_convention.md","03_candidate_selection_policy.md",
        "04_candidate_selection_and_path_locking_results.md","qualitative_case_registry.csv","qualitative_case_registry.schema.json",
        "selection/cohort_v1.jsonl","selection/source_audit_v1.json","selection/candidate_rows_v1.json",
        "selection/candidate_contract_tests_v2.json","selection/registry_validation_v1.json","selection/registry_header_before_v1.csv",
        "support/build_registry.mjs","support/registry_population_v1.json","support/registry_candidates_preview.png",
        "support/select_gallery_candidates.py","support/test_candidate_selection.py","support/validate_candidate_registry.py",
        "support/write_candidate_report.py","support/lock_candidate_package.py",*validation["case_inventory"]]
    require(len(names)==len(set(names)),"Duplicate inventory key")
    evidence={name:record(PACKAGE/name) for name in names}
    ids=[r["case_id"] for r in payload["rows"]]
    require(len(ids)==len(set(ids))==24,"Bad case identity count")
    report={"created_utc":datetime.now(timezone.utc).isoformat(),"status":"CANDIDATES_AND_EXISTING_PATHS_LOCKED_V1",
        "records":24,"main_candidates":8,"appendix_candidates":16,"unique_targets":22,"case_ids":ids,
        "files":evidence,"future_changes":"Create versioned visual-selection/render records; do not rewrite this candidate snapshot",
        "actual_generated_STEP_or_gallery_renders":0,"gallery_status":"NOT_RENDERED_VISUAL_REVIEW_PENDING",
        "legacy_training_seed_checkpoint_binding":"UNRESOLVED_NOT_FABRICATED","review04_closure_artifacts_unchanged":17,
        "training_model_or_CAD_execution":False}
    with output.open("x",encoding="utf-8") as stream: json.dump(report,stream,indent=2,ensure_ascii=True); stream.write("\n")
    print(f"Candidate package lock PASS:24 records,8 main+16 appendix,{len(evidence)} file hashes; no model/CAD execution")
    print(output)


if __name__=="__main__": main()
