"""Copy every existing registered source; keep original bytes and missing entries."""
import argparse
from pathlib import Path
import shutil
from common import ROOT, ARCHIVE, read, require, sha, utc, verify_prior, write_new, text_new


def run():
    require(not (ARCHIVE/"archive_manifest_v1.json").exists(), "Archive complete; use verify")
    prior = verify_prior()
    source = read(ROOT/"audit/source_files_v1.json")
    mapping = []
    objects = {}
    for key, entry in source["files"].items():
        require(entry["path"] == key, "Source path key mismatch")
        item = dict(entry)
        if entry["exists"]:
            suffix = Path(key).suffix.lower()
            require(not suffix or suffix[1:].isalnum(), "Unsafe suffix")
            item["archive_path"] = "objects/" + entry["sha256"] + suffix
            objects.setdefault(item["archive_path"], item)
        else:
            item["archive_path"] = None
        mapping.append(item)
    needed = sum(x["bytes"] for x in objects.values())
    require(shutil.disk_usage(ROOT).free > needed + 100*1024*1024, "Not enough archive space")
    for i, item in enumerate(objects.values(), 1):
        original = Path(item["path"])
        target = ARCHIVE/item["archive_path"]
        require(original.is_file() and original.stat().st_size == item["bytes"], "Source absent or size changed: "+str(original))
        require(sha(original) == item["sha256"], "Source hash changed: "+str(original))
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            with original.open("rb") as src, target.open("xb") as dst:
                shutil.copyfileobj(src, dst, 1024*1024)
        require(target.stat().st_size == item["bytes"] and sha(target) == item["sha256"], "Archive bytes differ")
        if i%300 == 0 or i==len(objects):
            print(f"exact source archive {i}/{len(objects)}",flush=True)
    text_new(ARCHIVE/"README.md", "# Fusion 360 Raw Evidence Archive v1\n\n"
        "All existing files registered by the 400-case Step 1 audit are retained as byte-exact copies. "
        "archive_manifest_v1.json maps every original path and role to its content-addressed object, "
        "including entries for historically missing files. Empty original logs are preserved.\n\n"
        "This includes full registered predictions, plans, source JSONLs, reference STEP and point inputs, "
        "successful prediction STEP files, metric manifests and execution logs. "
        "This is not all training data, all model weights, or all official Fusion 360 cases.\n\n"
        "Page limits may reduce manuscript figures, not this research archive. Create separate "
        "layout/submission versions. Do not delete original evidence or replace failed outputs.\n")
    manifest = {"status":"COMPLETE_BYTE_EXACT_REGISTERED_SOURCE_ARCHIVE", "created_utc":utc(),
        "inventory_sha256":sha(ROOT/"audit/source_files_v1.json"),"archive_script_sha256":sha(__file__),
        "registered_paths":len(mapping),"existing_source_paths":sum(x["exists"] for x in mapping),
        "historically_missing_paths":sum(not x["exists"] for x in mapping),
        "unique_content_objects":len(objects),"archived_bytes":needed,"prior_seals":prior,"sources":mapping,
        "all_400_ids_preserved":read(ROOT/"audit/master_ids_v1.txt") if False else (ROOT/"audit/master_ids_v1.txt").read_text().splitlines(),
        "originals_modified":False,"new_predictions_or_scores":False}
    write_new(ARCHIVE/"archive_manifest_v1.json",manifest)
    verify()


def verify():
    manifest = read(ARCHIVE/"archive_manifest_v1.json")
    for item in manifest["sources"]:
        if item["exists"]:
            target=ARCHIVE/item["archive_path"]
            require(target.stat().st_size==item["bytes"] and sha(target)==item["sha256"], "Archive drift")
        else:
            require(item["archive_path"] is None,"Missing source received fabricated archive object")
    verify_prior()
    print({k:manifest[k] for k in ("status","registered_paths","existing_source_paths","historically_missing_paths","unique_content_objects","archived_bytes")},flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("mode",choices=("run","verify"))
    args=parser.parse_args()
    run() if args.mode=="run" else verify()
