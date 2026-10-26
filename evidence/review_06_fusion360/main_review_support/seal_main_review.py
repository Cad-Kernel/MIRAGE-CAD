"""Seal only the additive six-case recheck version and verify parent bytes."""
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"gallery_support"))
from common import ROOT, read, require, sha, utc, write_new
from build_main_review import OUT, PARENT_SEAL, verify_parent


def main():
    unchanged=verify_parent()
    result=read(OUT/"validation_v1.json")
    require(result["status"].startswith("PASS"),"Review validation not complete")
    require(result["author_confirmation"]=="PENDING","Do not invent author approval")
    records=read(OUT/"main_review_records_v1.json")
    require(len(records["rows"])==6 and all(not r["author_confirmed"] for r in records["rows"]),"Incorrect sign-off status")
    included=[p for p in OUT.rglob("*") if p.is_file()]
    included += [p for p in Path(__file__).parent.glob("*.py")]
    included.append(ROOT/"07_main_case_visual_review.md")
    seal={"status":"SIX_CASE_ASSISTANT_VISUAL_RECHECK_SEALED_AUTHOR_SIGNOFF_PENDING",
        "created_utc":utc(),"parent_seal_sha256":sha(PARENT_SEAL),"parent_files_unchanged":unchanged,
        "files":{str(p.relative_to(ROOT)).replace("\\","/"):{"sha256":sha(p),"bytes":p.stat().st_size} for p in sorted(included)},
        "author_confirmation":None,"no_training_prediction_execution_scoring_or_new_rendering":True,
        "Review07_started":False}
    write_new(OUT/"review_seal_v1.json",seal)
    for rel,item in read(OUT/"review_seal_v1.json")["files"].items():
        require(sha(ROOT/rel)==item["sha256"],"New review seal mismatch")
    print("Sealed",len(seal["files"]),"new files; parent",unchanged,"files unchanged; author confirmation pending.")


if __name__=="__main__":
    main()
