"""Native Flluma mesh-interface smoke on an existing reference STEP; no model inference."""
import hashlib
import json
from pathlib import Path
import sys
import traceback

ROOT=Path(r"__EVIDENCE_SOURCE_ROOT__\05_qualitative")
OUTPUT=ROOT/"rendering/cpu_v1/probes/native_mesh_probe.json"
require=lambda ok,message: None if ok else (_ for _ in ()).throw(ValueError(message))


def main():
    require(not OUTPUT.exists(),"Native mesh probe exists")
    provenance=json.loads((ROOT/"cases/q-flone-image-b2legacy-flluma_0093014/provenance.json").read_text())
    item=provenance["original_assets"]["reference_step"]
    path=Path(item["path"].replace("/mnt/c/","C:/"))
    require(hashlib.sha256(path.read_bytes()).hexdigest()==item["sha256"],"Reference STEP hash drift")
    result={"python_version":sys.version,"reference_step":str(path),"source_sha256":item["sha256"],
        "model_inference_or_training":False,"predicted_code_execution":False}
    import flluma
    import flluma.api as api
    from flluma.api import evaluation
    result["flluma_module_path"]=getattr(flluma,"__file__",None)
    result["api_module_path"]=getattr(api,"__file__",None)
    result["evaluation_module_path"]=getattr(evaluation,"__file__",None)
    try:
        node=api.import_model(str(path))
        mesh=evaluation.evaluate(node)
        pts=[mesh.get_position(i) for i in range(mesh.vertex_count)]
        indices=mesh.get_indices()
        result.update(status="PASS_REFERENCE_STEP_NATIVE_MESH",vertex_count=len(pts),index_count=len(indices),
            bbox_min=[min(getattr(p,k) for p in pts) for k in ("x","y","z")],
            bbox_max=[max(getattr(p,k) for p in pts) for k in ("x","y","z")])
    except Exception as exc:
        result.update(status="REFERENCE_STEP_NATIVE_MESH_UNAVAILABLE",error=f"{type(exc).__name__}: {exc}",traceback=traceback.format_exc())
    for name in ("occt_file_shape_info","occt_file_brep_features"):
        try: result[name]=getattr(evaluation,name)(str(path))
        except Exception as exc: result[name]={"error":str(exc)}
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    with OUTPUT.open("x",encoding="utf-8") as stream: json.dump(result,stream,indent=2,default=str)
    print(json.dumps(result,indent=2,default=str),flush=True)


if __name__=="__main__": main()
