"""Byte-exact, additive archive of registered qualitative sources; no inference."""
import argparse
from datetime import datetime, timezone
import hashlib
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import shutil
from urllib.parse import quote, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "raw_archive_v1"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as f:
        json.dump(value, f, indent=2, ensure_ascii=True, allow_nan=False)
        f.write("\n")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()


def local(path):
    value = str(path)
    if value.startswith("/mnt/c/"):
        return Path("C:/" + value[7:])
    if value.startswith("/home/"):
        return Path("//wsl.localhost/Ubuntu" + value)
    return Path(path)


def utc():
    return datetime.now(timezone.utc).isoformat()


def verify_prior_seals():
    counts = {}
    for label, path in [
        ("candidate", ROOT / "selection/path_lock_manifest_v1.json"),
        ("render", ROOT / "rendering/cpu_v1/render_inventory_v1.json"),
        ("review04", ROOT.parent / "04/execution/final_evidence_inventory_20261022.json")]:
        source = read(path)
        for item in source["files"].values():
            target = local(item["path"])
            if not target.is_absolute():
                target = ROOT / target
            require(target.is_file() and sha(target) == item["sha256"], f"Previously sealed file changed: {target}")
        counts[label] = len(source["files"])
    return counts


def add_source(mapping, item, role):
    key = item["path"]
    if key in mapping:
        require(mapping[key]["sha256"] == item["sha256"] and mapping[key]["bytes"] == item["bytes"], "Conflicting expected source bytes")
        if role not in mapping[key]["roles"]:
            mapping[key]["roles"].append(role)
        return
    suffix = Path(key).suffix.lower()
    require(not suffix or suffix[1:].isalnum(), "Unsafe archive extension")
    digest = item["sha256"]
    require(len(digest) == 64 and all(c in "0123456789abcdef" for c in digest), "Invalid SHA256")
    mapping[key] = {"source_path": key, "sha256": digest, "bytes": item["bytes"],
        "archive_path": f"objects/{digest}{suffix}", "roles": [role]}


def plan():
    require(not (ARCHIVE/"archive_plan.json").exists(), "Archive plan already exists")
    prior = verify_prior_seals()
    audit = read(ROOT/"selection/source_audit_v1.json")
    mapping = {}
    for item in audit["source_files"].values():
        role = "full_registered_source_file"
        if "/adapter_model.safetensors" in item["path"] or item["path"].endswith("/soft_prefix.pt"):
            role = "current_checkpoint_observation_NOT_historical_runtime_attestation"
        add_source(mapping, item, role)
    lock = read(ROOT/"selection/path_lock_manifest_v1.json")
    case_records = []
    for key in lock["case_ids"]:
        provenance = read(ROOT/"cases"/key/"provenance.json")
        assets = {}
        for role, item in provenance["original_assets"].items():
            add_source(mapping, item, f"{key}:{role}")
            assets[role] = {"source_path": item["path"], "archive_path": mapping[item["path"]]["archive_path"], "sha256": item["sha256"]}
        case_records.append({"case_id": key, "assets": assets})
    unique = {r["archive_path"]: r for r in mapping.values()}
    needed = sum(r["bytes"] for r in unique.values())
    require(shutil.disk_usage(ROOT).free > needed + 100*1024*1024, "Insufficient free disk space for exact archive")
    for i, item in enumerate(mapping.values(), 1):
        path = local(item["source_path"])
        require(path.is_file() and path.stat().st_size == item["bytes"], f"Original source unavailable/size drift: {path}")
        require(sha(path) == item["sha256"], f"Original source hash drift: {path}")
        if i % 25 == 0:
            print(f"source preflight verified {i}/{len(mapping)}", flush=True)
    result = {"schema": "qualitative_raw_archive_plan_v1", "created_utc": utc(),
        "scope": "All 24 selected cases' 8 original asset roles, plus all 55 full source files already inventoried in the source audit; not the entire 100K corpus or full training environment",
        "preservation_policy": "Keep complete research archive. Trim only manuscript figures or a separately versioned submission subset. Never overwrite/delete original observations to satisfy page limits.",
        "source_audit_sha256": sha(ROOT/"selection/source_audit_v1.json"),
        "prior_seals_verified": prior, "registered_source_file_count":len(audit["source_files"]),
        "source_paths": len(mapping), "unique_archive_objects": len(unique), "planned_bytes": needed,
        "case_count": len(case_records), "unique_targets": len({read(ROOT/"cases"/c/"case.json")["sample_id"] for c in lock["case_ids"]}),
        "sources": list(mapping.values()), "cases": case_records,
        "no_training_model_or_CAD_execution": True, "originals_modified": False}
    write_new(ARCHIVE/"archive_plan.json", result)
    print(json.dumps({k:result[k] for k in ("case_count","unique_targets","source_paths","unique_archive_objects","planned_bytes","prior_seals_verified")},indent=2), flush=True)


def copy_exact(source, destination, expected):
    require(not destination.exists(), f"No implicit archive overwrite: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as src, destination.open("xb") as dst:
        shutil.copyfileobj(src, dst, length=1024*1024)
    require(sha(destination) == expected, f"Byte-exact archive copy failed: {destination}")


def relative(path, start=ARCHIVE):
    return quote(os.path.relpath(path, start).replace("\\", "/"), safe="/.")


def link(path, label):
    require(Path(path).is_file(), f"Archive browse target missing: {path}")
    return f'<a href="{relative(path)}">{html.escape(label)}</a>'


def index(plan):
    body = '<h1>MIRAGE Qualitative Raw Archive</h1><p>Complete registered research evidence is preserved here. Manuscript length limits apply to figure selection, not deletion of observations.</p>'
    body += '<p>24 modality cases, 22 unique reference objects. Every archived file is a byte-exact copy with SHA256. This is not a backup of the entire 100K CAD corpus. Current checkpoint observations do not resolve historical checkpoint attribution.</p>'
    body += '<nav>'+link(ARCHIVE/"archive_plan.json","Original-to-archive mapping")+link(ARCHIVE/"README.md","Preservation policy")+link(ROOT/"qualitative_case_registry.csv","Original case registry")+'</nav>'
    for item in plan["cases"]:
        key = item["case_id"]
        row = read(ROOT/"cases"/key/"case.json")
        body += f'<section><h2>{html.escape(row["modality"].upper())} {row["sample_id"]}</h2><p>{html.escape(row["case_type"])}; {row["complexity_tier"]}; historical scoreable={row["scoreable"]}</p>'
        body += '<nav>'+link(ROOT/"cases"/key/"case.json","Locked case record")+link(ROOT/"cases"/key/"provenance.json","Original provenance")+'</nav><ul>'
        for role, asset in item["assets"].items():
            body += '<li>'+link(ARCHIVE/asset["archive_path"],role)+'</li>'
        body += '</ul><nav>'
        for rel,label in [("input/exact_text.txt","Exact dataset text"),("plans/raw.txt","Raw plan"),("plans/canonicalized.txt","P1a plan"),("code/raw_prediction.py","Raw generated code"),("code/prediction.py","Historical executed code"),("logs/gate_row.json","Original gate row"),("logs/geometry_row.json","Original geometry row")]:
            body += link(ROOT/"cases"/key/rel,label)
        if row["failure_log_path"]:
            body += link(ROOT/row["failure_log_path"],"Original failure evidence")
        body += '</nav>'
        panel=ROOT/"rendering/cpu_v1/cases"/key/"panel.png"
        body += f'<p>{link(panel,"Two-view comparison")}</p><img loading="lazy" src="{relative(panel)}" alt="Reference/prediction or original failure evidence">'
        if row["modality"] == "image":
            image=ARCHIVE/item["assets"]["input_image"]["archive_path"]
            body += f'<p>Exact archived image input</p><img class="input" loading="lazy" src="{relative(image)}" alt="Original model image input">'
        body += '</section>'
    body += '<h2>Full Registered Source Files</h2><p>Full JSONL files are retained, not only the selected lines. Dataset JSONL references for unselected samples may still refer to the original full corpus outside this archive.</p><table><tr><th>Original path</th><th>Archive copy</th><th>Bytes</th></tr>'
    for source in plan["sources"]:
        if any(r=="full_registered_source_file" or r.startswith("current_checkpoint_observation") for r in source["roles"]):
            body += '<tr><td>'+html.escape(source["source_path"])+'</td><td>'+link(ARCHIVE/source["archive_path"],Path(source["source_path"]).name)+'</td><td>'+str(source["bytes"])+'</td></tr>'
    body += '</table>'
    text='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MIRAGE Raw Archive</title><style>body{font:16px Arial,sans-serif;line-height:1.5;margin:24px auto;padding:16px;max-width:1200px;color:#20303a}h1{font-size:26px}h2{font-size:21px}section{border-top:1px solid #ccc;margin:28px 0;padding-top:12px}nav{display:flex;flex-wrap:wrap;gap:14px}img{max-width:100%;height:auto}img.input{max-width:512px}a{color:#086b6a}table{border-collapse:collapse;width:100%;font-size:13px;table-layout:fixed}td,th{padding:8px;text-align:left;border-bottom:1px solid #ddd;overflow-wrap:anywhere}td:first-child,th:first-child{width:60%}</style><body>'+body+'</body></html>\n'
    with (ARCHIVE/"index.html").open("x",encoding="utf-8") as f:
        f.write(text)


def run():
    require(not (ARCHIVE/"archive_manifest.json").exists(), "Archive complete; use verify, not run")
    plan=read(ARCHIVE/"archive_plan.json")
    unique={r["archive_path"]:r for r in plan["sources"]}
    for i,(name,item) in enumerate(unique.items(),1):
        target=ARCHIVE/name
        if target.exists():
            require(target.stat().st_size==item["bytes"] and sha(target)==item["sha256"], "Partial archive bytes do not match; do not overwrite")
        else:
            copy_exact(local(item["source_path"]),target,item["sha256"])
        if i%20==0 or i==len(unique):
            print(f"archived and hash-verified {i}/{len(unique)}",flush=True)
    prior=verify_prior_seals()
    index(plan)
    actuals={"status":"COMPLETE_BYTE_EXACT_RAW_ARCHIVE","created_utc":utc(),
        "case_count":plan["case_count"],"unique_targets":plan["unique_targets"],
        "registered_full_sources":plan["registered_source_file_count"],"original_asset_roles_per_case":8,
        "source_paths":plan["source_paths"],"unique_objects":len(unique),"archived_bytes":plan["planned_bytes"],
        "prior_seals_unchanged":prior,"model_training_or_CAD_execution":False,
        "scope_limit":"Registered qualitative source files and all selected target/input assets, not the entire raw training corpus or full model environment",
        "retention":"Full research archive retained regardless of manuscript/submission figure reduction"}
    write_new(ARCHIVE/"archive_actuals.json",actuals)
    included=[p for p in ARCHIVE.rglob("*") if p.is_file()]
    included.extend(p for p in Path(__file__).parent.glob("*") if p.is_file())
    included.append(ROOT/"06_raw_data_preservation_record.md")
    manifest={"status":"RAW_ARCHIVE_SEALED_V1","created_utc":utc(),"files":{
        str(p.relative_to(ROOT)).replace("\\","/"):{"sha256":sha(p),"bytes":p.stat().st_size}
        for p in sorted(included)},"archive_plan_sha256":sha(ARCHIVE/"archive_plan.json")}
    write_new(ARCHIVE/"archive_manifest.json",manifest)
    verify()
    print(json.dumps(actuals,indent=2),flush=True)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets=[]
    def handle_starttag(self,tag,attrs):
        self.targets.extend(value for key,value in attrs if key in ("src","href"))


def verify():
    manifest=read(ARCHIVE/"archive_manifest.json")
    for rel,item in manifest["files"].items():
        p=ROOT/rel
        require(p.is_file() and p.stat().st_size==item["bytes"] and sha(p)==item["sha256"],f"Archive integrity failure: {rel}")
    parser=Links()
    parser.feed((ARCHIVE/"index.html").read_text(encoding="utf-8"))
    for value in parser.targets:
        parts=urlsplit(value)
        require(not parts.scheme and not parts.netloc,"Archive index depends on an external resource")
        p=(ARCHIVE/unquote(parts.path)).resolve()
        require(p.is_relative_to(ROOT) and p.is_file(),f"Archive link outside package or missing: {p}")
    counts=verify_prior_seals()
    print(json.dumps({"status":"PASS_ARCHIVE_BYTES_LINKS_AND_PRIOR_SEALS","sealed_files":len(manifest["files"]),"local_index_links":len(parser.targets),"prior_seals_unchanged":counts}),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("action",choices=("plan","run","verify"))
    args=parser.parse_args()
    globals()[args.action]()
