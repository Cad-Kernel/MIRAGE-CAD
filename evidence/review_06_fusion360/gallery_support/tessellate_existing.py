"""CPU conversion of archived existing STEP, in existing WSL cadrecode_env only."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import traceback
import cadquery as cq
import numpy as np
import OCP


def local(value):
    return Path("/mnt/"+value[0].lower()+value[2:].replace("\\","/")) if len(value)>2 and value[1]==":" else Path(value)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_new(path,value):
    with path.open("x",encoding="utf-8") as stream:
        json.dump(value,stream,indent=2,allow_nan=False)
        stream.write("\n")


def main():
    root=Path(__file__).resolve().parents[1]
    config_path=root/"gallery_v1/render_protocol_v1.json"
    config=json.loads(config_path.read_text())
    if sha(__file__)!=config["mesh_script_sha256"]:
        raise ValueError("Mesh implementation drift")
    counts={"meshed":0,"historical_placeholders":0,"conversion_failures":0}
    for job in config["jobs"]:
        record_path=local(job["mesh_record_path"])
        if record_path.exists():
            old=json.loads(record_path.read_text())
            if old.get("mesh_sha256") and sha(local(job["mesh_path"]))!=old["mesh_sha256"]:
                raise ValueError("Existing mesh changed")
            counts[old["counter_key"]]+=1
            continue
        report={"case_id":job["case_id"],"sample_id":job["sample_id"],"method":job["method"],
            "step_sha256":job["step_sha256"],"historical_outcome":job["historical_outcome"],
            "created_utc":datetime.now(timezone.utc).isoformat(),"mesh_script_sha256":sha(__file__),
            "render_protocol_sha256":sha(config_path),"cadquery":cq.__version__,"OCP":getattr(OCP,"__version__","unavailable"),
            "alpha":config["alpha"],"angular_tolerance":config["angular_tolerance"],
            "new_program_execution_or_score":False}
        if not job["render_eligible"]:
            report.update(status="HISTORICAL_FAILURE_PLACEHOLDER",counter_key="historical_placeholders")
        else:
            try:
                source=local(job["archive_step_path"])
                if sha(source)!=job["step_sha256"]:
                    raise ValueError("Archived STEP changed")
                shapes=cq.importers.importStep(str(source)).vals()
                if not shapes:
                    raise ValueError("No imported shapes")
                boxes=[s.BoundingBox() for s in shapes]
                lo=np.min([[b.xmin,b.ymin,b.zmin] for b in boxes],axis=0)
                hi=np.max([[b.xmax,b.ymax,b.zmax] for b in boxes],axis=0)
                extent=float(np.max(hi-lo))
                if not np.isfinite(extent) or extent<=0:
                    raise ValueError("Invalid BRep bbox")
                tolerance=config["alpha"]*extent
                vertices,faces=[],[]
                for shape in shapes:
                    v,f=shape.tessellate(tolerance,config["angular_tolerance"])
                    off=len(vertices)
                    vertices.extend([(p.x,p.y,p.z) for p in v])
                    faces.extend([(a+off,b+off,c+off) for a,b,c in f])
                raw_v=np.asarray(vertices,dtype=np.float64)
                raw_f=np.asarray(faces,dtype=np.int64)
                if raw_v.ndim!=2 or raw_v.shape[1]!=3 or raw_f.ndim!=2 or raw_f.shape[1]!=3 or not len(raw_f) or not np.isfinite(raw_v).all():
                    raise ValueError("Empty/invalid render mesh")
                unique,inverse=np.unique(raw_v,axis=0,return_inverse=True)
                welded_faces=inverse[raw_f]
                target=local(job["mesh_path"])
                with target.open("xb") as stream:
                    np.savez_compressed(stream,vertices=unique,faces=welded_faces,raw_vertices=raw_v,raw_faces=raw_f)
                report.update(status="EXISTING_STEP_MESHED_FOR_DISPLAY_ONLY",counter_key="meshed",
                    mesh_sha256=sha(target),mesh_path=job["mesh_path"],brep_bbox=[lo.tolist(),hi.tolist()],
                    mesh_bbox=[unique.min(axis=0).tolist(),unique.max(axis=0).tolist()],
                    linear_deflection_native_units=tolerance,vertices=len(unique),raw_vertices=len(raw_v),triangles=len(raw_f),
                    geometry_modification="Exact-coordinate vertex welding for shared feature edges only; raw arrays also retained")
            except Exception as exc:
                report.update(status="RENDER_CONVERSION_FAILURE_NO_CASE_REPLACEMENT",counter_key="conversion_failures",
                    error=f"{type(exc).__name__}: {exc}",traceback=traceback.format_exc())
        write_new(record_path,report)
        counts[report["counter_key"]]+=1
        print(job["case_id"],job["method"],report["status"],flush=True)
    write_new(root/"gallery_v1/mesh_actuals_v1.json",{"counts":counts,"CPU_only":True,
        "new_predictions_or_scores":False,"render_protocol_sha256":sha(config_path)})
    print(counts,flush=True)


if __name__=="__main__":
    main()
