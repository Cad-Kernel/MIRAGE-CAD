"""Inspect existing log vocabulary only; no classification or case selection."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    seal=json.loads((ROOT/"audit/step1_package_seal_v1.json").read_text())
    for rel,item in seal["files"].items():
        if digest(ROOT/rel)!=item["sha256"]:
            raise ValueError("Step-1 bytes changed: "+rel)
    master=json.loads((ROOT/"audit/master_records_v1.json").read_text())
    fields={m:Counter() for m in ("mirage","nn","cadr")}
    examples={m:{} for m in fields}
    for row in master["rows"]:
        for method in fields:
            native=row["native_records"][method]
            if method=="cadr":
                execution=native.get("execution") or {}
                result=execution.get("runner_result") or {}
                messages=[str(result.get("error") or native.get("reason") or "")]
                if native.get("pipeline_status")!="SUCCESS":
                    examples[method].setdefault(native["pipeline_status"],[]).append({"sample_id":row["sample_id"],"native":native})
            else:
                messages=[row["source_records"][method+"_gate"].get("error") or ""]
                if native.get("pipeline_status") not in ("SUCCESS","NO_GEOMETRY"):
                    examples[method].setdefault(native["pipeline_status"],{"sample_id":row["sample_id"],"native":native})
            for message in messages:
                if message:
                    fields[method][message]+=1
    result={"scope":"read-only log vocabulary; no taxonomy applied","messages":{m:dict(v) for m,v in fields.items()},"native_status_examples":examples}
    out=ROOT/"taxonomy/log_vocabulary_v1.json"
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("x",encoding="utf-8") as f:
        json.dump(result,f,indent=2)
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
