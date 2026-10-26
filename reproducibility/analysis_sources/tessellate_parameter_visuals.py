"""CPU render meshes from the new native STEP illustrations, not metric scoring."""
import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np
import cadquery

ROOT = Path("__EVIDENCE_SOURCE_ROOT__/09_cpu_preparation/parameter_visuals_v1")


def local(value):
    s = str(value).replace("\\", "/")
    return Path("/mnt/" + s[0].lower() + s[2:]) if len(s) > 2 and s[1] == ":" else Path(s)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    config = json.loads((ROOT.parents[1] / "05_qualitative/rendering/cpu_v1/render_protocol.json").read_text())["tessellation"]
    helper = local(config["helper_path"])
    assert sha(helper) == config["helper_sha256"]
    spec = importlib.util.spec_from_file_location("existing_display_tessellator", helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    prepared = json.loads((ROOT / "prepared_cases.json").read_text())
    records = []
    for case in prepared["cases"]:
        for side in ("before", "after"):
            folder = ROOT / "cases" / case["case_id"] / side
            native = json.loads((folder / "native_export.json").read_text())
            if not native["gates"]["step_export_ok"]:
                records.append({"case_id":case["case_id"],"side":side,"status":"CURRENT_EXECUTION_FAILURE_PLACEHOLDER","failure_stage":native["failure_stage"]})
                continue
            step = folder / "model.step"
            assert sha(step) == native["step_sha256"]
            v,f = module.tessellate_step(step,linear=.03,angular=.3)
            assert len(v) > 3 and len(f) and np.isfinite(v).all()
            unique,inverse = np.unique(v,axis=0,return_inverse=True)
            faces = inverse[f]
            target = folder / "display_mesh.npz"
            with target.open("xb") as stream:
                np.savez_compressed(stream,vertices=unique,faces=faces)
            shapes = cadquery.importers.importStep(str(step)).vals()
            report = {"case_id":case["case_id"],"side":side,"status":"CPU_DISPLAY_MESH_CREATED","step_sha256":sha(step),"mesh_sha256":sha(target),
                      "vertices":len(unique),"triangles":len(faces),"bbox_min":unique.min(axis=0).tolist(),"bbox_max":unique.max(axis=0).tolist(),
                      "brep_volume_current":sum(s.Volume() for s in shapes),"brep_area_current":sum(s.Area() for s in shapes),
                      "display_tolerance_mm":.03,"angular_tolerance_rad":.3,"old_metrics_recomputed":False,"cadquery":cadquery.__version__}
            with (folder / "mesh_record.json").open("x") as stream:
                json.dump(report,stream,indent=2)
            records.append(report)
            print(case["case_id"],side,len(faces),"display triangles",flush=True)
    with (ROOT / "display_mesh_summary.json").open("x") as stream:
        json.dump({"records":records,"helper_sha256":sha(helper),"CPU_only":True,"historical_stats_unchanged":True},stream,indent=2)


if __name__ == "__main__":
    main()
