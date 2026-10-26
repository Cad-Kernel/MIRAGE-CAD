"""Additive Step-2 inventory; never rewrite the Step-1 seal or data."""
from pathlib import Path
from datetime import datetime, timezone
from classify_native_logs import ROOT,read,sha,write_new,verify_step1


def main():
    old=read(ROOT/"audit/step1_package_seal_v1.json")
    verify_step1()
    validation=read(ROOT/"taxonomy/independent_validation_v1.json")
    if validation["status"]!="PASS_INDEPENDENT_NATIVE_LOG_TAXONOMY_VALIDATION":
        raise ValueError("Independent validation missing")
    for item in read(ROOT/"taxonomy/csv_validation_v1.json")["files"]:
        if sha(ROOT/item["name"])!=item["sha256"]:
            raise ValueError("Step-2 CSV changed after validation")
    if not (ROOT/"03_failure_taxonomy_results.md").is_file():
        raise ValueError("Human-readable result record missing")
    paths=[p for p in ROOT.iterdir() if p.is_file() and p.name not in old["files"]]
    paths.extend(p for p in (ROOT/"taxonomy").rglob("*") if p.is_file())
    paths.extend(p for p in (ROOT/"taxonomy_support").iterdir() if p.is_file())
    output=ROOT/"taxonomy/step2_package_seal_v1.json"
    if output.exists():
        raise ValueError("Step-2 seal already exists")
    files={str(p.relative_to(ROOT)).replace("\\","/"):{"sha256":sha(p),"bytes":p.stat().st_size} for p in sorted(set(paths))}
    record={"status":"STEP2_NATIVE_LOG_TAXONOMY_SEALED_V1","created_utc":datetime.now(timezone.utc).isoformat(),
        "files":files,"file_count":len(files),"prior_step1_seal_sha256":sha(ROOT/"audit/step1_package_seal_v1.json"),
        "scope":"1200 native-log outcome records; no new model/CAD/geometry evaluation",
        "Step3_selection_rendering_semantic_review":"NOT_STARTED","Step4_raw_asset_archive":"NOT_STARTED"}
    write_new(output,record)
    for rel,item in files.items():
        if sha(ROOT/rel)!=item["sha256"]:
            raise ValueError("Step-2 inventory postcheck failed")
    verify_step1()
    print(f"Step 2 sealed: {len(files)} new files; Step 1 unchanged; Step 3/4 NOT STARTED")


if __name__=="__main__":
    main()
