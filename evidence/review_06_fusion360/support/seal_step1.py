"""Seal Step-1 artifacts only; no source modification and no later-phase work."""
from audit_fusion360 import ROOT,read,write_new,sha,utc


def main():
    result=read(ROOT/"audit/independent_validation_v1.json")
    if result["status"]!="PASS_INDEPENDENT_STEP1_VALIDATION":
        raise ValueError("Independent audit has not passed")
    if sha(ROOT/"fusion360_case_registry.csv")!=result["registry_sha256"]:
        raise ValueError("CSV changed after independent audit")
    paths=[p for p in ROOT.iterdir() if p.is_file()]
    paths.extend(p for p in (ROOT/"audit").iterdir() if p.is_file())
    paths.extend(p for p in (ROOT/"support").iterdir() if p.is_file())
    output=ROOT/"audit/step1_package_seal_v1.json"
    if output.exists():
        raise ValueError("Step-1 seal exists; do not overwrite")
    files={str(p.relative_to(ROOT)).replace("\\","/"):{"sha256":sha(p),"bytes":p.stat().st_size} for p in sorted(paths)}
    record={"created_utc":utc(),"status":"STEP1_EXISTING_EVIDENCE_AUDIT_SEALED_V1","files":files,
        "master_rows":400,"CSV_columns":67,"Step2_taxonomy":"NOT_STARTED","Step3_selection_rendering":"NOT_STARTED",
        "Step4_raw_asset_archive":"NOT_STARTED","no_new_training_prediction_CAD_or_metric_evaluation":True,
        "later_changes":"Create a new version for later taxonomy/selection; preserve this Step-1 CSV/master/seal"}
    write_new(output,record)
    for rel,entry in files.items():
        if sha(ROOT/rel)!=entry["sha256"]:
            raise ValueError("Seal postcheck failed")
    print(f"Step 1 sealed: {len(files)} files, 400 master IDs, 67 CSV columns; later steps NOT STARTED")


if __name__=="__main__":
    main()
