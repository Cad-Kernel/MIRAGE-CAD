"""Independent HTML/CSV/path checks and a separate new-asset SHA256 inventory."""
import csv
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
from render_common import *


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths=[]

    def handle_starttag(self, tag, attributes):
        for key,value in attributes:
            if key in ("href","src") and value:
                self.paths.append(value)


def main():
    original_count=verify_original_lock()
    summary=read(OUT/"cpu_render_actuals.json")
    require(summary["render_pngs"]==100 and summary["blank_renders"]==0,"Unexpected render counts")
    records=read(OUT/"render_assets.json")["records"]
    with (OUT/"render_asset_registry.csv").open(encoding="utf-8",newline="") as f:
        csvrows=list(csv.DictReader(f))
    require(len(csvrows)==len(records)==24,"CSV count mismatch")
    for expected,actual in zip(records,csvrows):
        for key,value in expected.items():
            normalized="" if value is None else str(value).lower() if isinstance(value,bool) else str(value)
            if isinstance(value,float):
                require(float(actual[key])==value,f"CSV metric drift: {key}")
            else:
                require(actual[key]==normalized,f"CSV path/flag drift: {key}")
    checked={}
    htmlcount=0
    for p in OUT.rglob("*.html"):
        parser=Links()
        parser.feed(p.read_text(encoding="utf-8"))
        htmlcount+=1
        for value in parser.paths:
            parts=urlsplit(value)
            require(parts.scheme in ("","file"),"Unexpected external gallery resource")
            if parts.scheme=="file":
                target=Path("//"+parts.netloc+unquote(parts.path)) if parts.netloc else Path(unquote(parts.path).lstrip("/"))
            else:
                target=(p.parent/unquote(parts.path)).resolve()
            if str(target) not in checked:
                require(target.is_file(),f"Broken final gallery target: {target}")
                checked[str(target)]=True
    require(htmlcount==25,"Expected 24 case pages and one index")
    old=read(ROOT.parent/"04/execution/final_evidence_inventory_20261022.json")
    for entry in old["files"].values():
        require(sha(local_path(entry["path"]))==entry["sha256"],"Review/04 final evidence changed")
    validation={"status":"PASS_FINAL_PATHS_CSV_AND_PRESERVATION","created_utc":utc(),
        "html_pages":htmlcount,"unique_existing_gallery_link_targets":len(checked),"broken_links":0,
        "csv_rows":24,"csv_fields_each":23,"csv_json_values_exactly_matched":True,
        "original_05_files_unchanged":original_count,"review_04_final_files_unchanged":len(old["files"]),
        "visual_review":"main eight, all four six-case contact sheets, CSV preview, and three supplemental prediction views reviewed; not semantic final selection",
        "no_new_training_or_model_prediction":True}
    write_new(OUT/"final_validation.json",validation)
    include=[p for p in OUT.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    include.extend(p for p in (ROOT/"render_support").glob("*") if p.is_file())
    include.append(ROOT/"05_cpu_rendering_results.md")
    files={str(p.relative_to(ROOT)).replace("\\","/"):artifact(p) for p in sorted(set(include))}
    inventory={"status":"CPU_RENDER_ASSETS_SEALED_V1","created_utc":utc(),"files":files,
        "file_count":len(files),"bytes":sum(i["bytes"] for i in files.values()),
        "original_candidate_lock_sha256":sha(ROOT/"selection/path_lock_manifest_v1.json"),
        "original_candidate_csv_sha256":sha(ROOT/"qualitative_case_registry.csv"),
        "registry_status":"candidate","scope":"new CPU exports/renders only, no training/evaluation changes"}
    write_new(OUT/"render_inventory_v1.json",inventory)
    for item in files.values():
        require(sha(ROOT/item["path"])==item["sha256"],"Final inventory recheck failed")
    print(json.dumps(dict(validation,sealed_files=len(files),sealed_bytes=inventory["bytes"]),indent=2))


if __name__=="__main__":
    main()
