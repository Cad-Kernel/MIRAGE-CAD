"""Seal new gallery/raw archive without changing any earlier phase snapshot."""
import sys
from common import *


def main():
    prior=verify_prior()
    sys.path.insert(0,str(ROOT/"support"))
    from audit_fusion360 import prior_seals
    upstream=prior_seals()
    require(read(GALLERY/"independent_validation_v1.json")["status"].startswith("PASS"),"Gallery validation incomplete")
    included=[]
    for folder in (GALLERY,ARCHIVE,ROOT/"gallery_support"):
        included.extend(p for p in folder.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    for name in ("04_case_selection_and_render_protocol.md","05_gallery_results_and_interpretation.md",
                 "06_raw_data_preservation_record.md","START_HERE.md", "fusion360_gallery_cases_v1.csv","fusion360_gallery_assets_v1.csv"):
        included.append(ROOT/name)
    seal={"status":"GALLERY_AND_REGISTERED_RAW_ARCHIVE_SEALED_V1", "created_utc":utc(),
        "scope":"18 locked cases, dual-coordinate display, all registered existing sources; author semantic confirmation pending",
        "prior_06_seals_unchanged":prior,"prior_04_05_seals_unchanged":upstream,
        "files":{str(p.relative_to(ROOT)).replace("\\","/"):{"bytes":p.stat().st_size,"sha256":sha(p)} for p in sorted(set(included))},
        "source_originals_overwritten":False,"later_layout_changes":"Separate version only; keep raw data",
        "author_semantic_confirmation":"PENDING"}
    seal["file_count"]=len(seal["files"])
    target=GALLERY/"gallery_archive_seal_v1.json"
    write_new(target,seal)
    for rel,item in read(target)["files"].items():
        require(sha(ROOT/rel)==item["sha256"],"New seal mismatch")
    print({"status":seal["status"],"file_count":seal["file_count"],"prior_06":prior,"prior_04_05":upstream,
           "author_semantic_confirmation":"PENDING"})


if __name__=="__main__":
    main()
