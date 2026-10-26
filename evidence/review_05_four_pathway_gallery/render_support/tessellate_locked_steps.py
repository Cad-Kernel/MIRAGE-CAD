"""Existing WSL CadQuery STEP tessellator, render-only tolerance, no model imports."""
import argparse
import importlib.util
import sys
import traceback
import numpy as np
from render_common import *


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-id")
    args = parser.parse_args()
    verify_original_lock()
    protocol = read(OUT / "render_protocol.json")
    config = protocol["tessellation"]
    helper = local_path(config["helper_path"])
    require(sha(helper) == config["helper_sha256"], "Tessellation helper drift")
    spec = importlib.util.spec_from_file_location("locked_cadquery_tessellation", helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    import cadquery
    for job in protocol["jobs"]:
        if args.case_id and args.case_id != job["case_id"]:
            continue
        base = local_path(job["output_dir"])
        base.mkdir(parents=True, exist_ok=True)
        items = [("reference", local_path(job["reference_step_path"]), job["reference_step_sha256"])]
        if job["historical_scoreable"]:
            export = read(base / "native_export.json")
            require(export["status"] == "EXPORTED_LOCKED_PREDICTION", "Prediction not exported")
            items.append(("prediction", ROOT / export["step"]["path"], export["step"]["sha256"]))
        for kind, source, expected_sha in items:
            require(sha(source) == expected_sha, f"STEP drift: {source}")
            report = base / f"{kind}_mesh.json"
            if report.exists():
                prior = read(report)
                require(prior["status"] == "TESSELLATED" and sha(ROOT / prior["mesh"]["path"]) == prior["mesh"]["sha256"], "Prior mesh drift")
                print("verified prior mesh:", job["case_id"], kind, flush=True)
                continue
            meshpath = base / f"{kind}_mesh.npz"
            require(not meshpath.exists(), "Unreported partial mesh")
            result = {"case_id": job["case_id"], "kind": kind, "source_sha256": expected_sha,
                "created_utc": utc(), "python": sys.version, "cadquery_version": cadquery.__version__,
                "tessellation": config, "coordinates_changed": False}
            vertices, faces = module.tessellate_step(source, linear=config["linear_deflection_mm"], angular=config["angular_deflection_radians"])
            require(len(vertices) > 3 and len(faces) > 0 and np.isfinite(vertices).all(), "Invalid mesh")
            require(faces.min() >= 0 and faces.max() < len(vertices), "Invalid mesh indices")
            original_vertices = len(vertices)
            # Exact welding changes connectivity only, never coordinates or triangle geometry.
            vertices, inverse = np.unique(vertices, axis=0, return_inverse=True)
            faces = inverse[faces]
            with meshpath.open("xb") as f:
                np.savez_compressed(f, vertices=vertices, faces=faces)
            result.update(status="TESSELLATED", mesh=artifact(meshpath), vertices=len(vertices),
                vertices_before_exact_weld=original_vertices, triangles=len(faces),
                bbox_min=vertices.min(axis=0).tolist(), bbox_max=vertices.max(axis=0).tolist())
            write_new(report, result)
            print("tessellated:", job["case_id"], kind, len(faces), "triangles", flush=True)
    print("Requested render meshes complete; original metrics untouched", flush=True)


if __name__ == "__main__":
    main()
