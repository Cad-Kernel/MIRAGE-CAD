"""Read existing external-evaluation JSON only; no imports of model/CAD modules."""
from collections import Counter
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPO=Path(r"__DEV_ROOT__")
WSL=Path(r"__RUN_SOURCE_ROOT__")


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main():
    output={"action":"read_only_schema_and_source_discovery","collections":{},"manifests":{}}
    for name,path in {
        "rows":WSL/"data/external/fusion360/rows.jsonl",
        "queries":WSL/"data/external/fusion360/queries.jsonl",
        "step_index":WSL/"data/external/fusion360/step_index.jsonl",
        "old_manifest":REPO/"scratch/external_manifest/manifest.jsonl",
        "genplan_raw":WSL/"outputs/external_fusion360/gen_point_genplan.jsonl",
        "genplan_used":WSL/"outputs/external_fusion360/gen_point_genplan_repaired_p0.jsonl",
        "nn_raw":WSL/"outputs/external_fusion360/gen_point_nnir.jsonl",
        "nn_used":WSL/"outputs/external_fusion360/gen_point_nnir_repaired_p0.jsonl",
        "genplan_ir":WSL/"outputs/external_fusion360/ir_point.jsonl",
        "gate_genplan":REPO/"scratch/exec_ext_point_genplan/execution_rows.jsonl",
        "gate_nn":REPO/"scratch/exec_ext_point_nnir/execution_rows.jsonl"}.items():
        if not path.exists():
            output["collections"][name]={"path":str(path),"exists":False}
            continue
        entries=[json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
        output["collections"][name]={"path":str(path),"exists":True,"rows":len(entries),
            "keys":list(entries[0]) if entries else [],"first":entries[0] if entries else None,
            "last_id":entries[-1].get("sample_id") if entries else None}
    for name,base,filename in [
        ("cadr",REPO/"scratch/cadrecode_runs","run_manifest.json"),
        ("mirage",REPO/"scratch/mirage_runs/point_genplan","score_manifest.json"),
        ("nn",REPO/"scratch/mirage_runs/point_nnir","score_manifest.json")]:
        paths=sorted(base.glob("*/"+filename))
        statuses=Counter()
        cd=Counter()
        iou=Counter()
        examples={}
        names=Counter()
        for p in paths:
            m=read(p)
            status=m.get("pipeline_status")
            statuses[str(status)]+=1
            cd[str(m.get("cd_status"))]+=1
            iou[str(m.get("iou_status"))]+=1
            examples.setdefault(str(status),{"path":str(p),"record":m})
            for item in p.parent.iterdir():
                if item.is_file():
                    names[item.name]+=1
        output["manifests"][name]={"count":len(paths),"pipeline_statuses":statuses,
            "cd_statuses":cd,"iou_statuses":iou,"file_names":names,"examples":examples}
    path=ROOT/"audit/discovery_v1.json"
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as f:
        json.dump(output,f,indent=2)
    print(json.dumps({"collections":{k:{x:v.get(x) for x in ("exists","rows","keys")} for k,v in output["collections"].items()},
        "manifests":{k:{x:v[x] for x in ("count","pipeline_statuses","cd_statuses","iou_statuses","file_names")} for k,v in output["manifests"].items()}},indent=2))


if __name__=="__main__":
    main()
