"""Freeze render-only settings before native export; never alters candidate selection."""
from render_common import *


def main():
    count = verify_original_lock()
    require(not (OUT / "render_protocol.json").exists(), "Render protocol already exists")
    rows = cases()
    require(len(rows) == 24 and sum(x["scoreable"] for x in rows) == 20, "Candidate contract drift")
    jobs = []
    for row in rows:
        key = row["case_id"]
        base = ROOT / "cases" / key
        provenance = read(base / "provenance.json")
        ref = provenance["original_assets"]["reference_step"]
        ref_path = local_path(ref["path"])
        require(sha(ref_path) == ref["sha256"], f"Reference hash drift: {key}")
        code = base / "code/prediction.py"
        job = {"case_id": key, "sample_id": row["sample_id"], "modality": row["modality"],
               "historical_scoreable": row["scoreable"], "case_snapshot_sha256": sha(base / "case.json"),
               "code_path": str(code), "code_sha256": sha(code),
               "reference_step_path": str(ref_path), "reference_step_sha256": sha(ref_path),
               "output_dir": str(OUT / "cases" / key),
               "failure_evidence": str(base / "logs/native_failure_messages.json") if not row["scoreable"] else None}
        write_new(OUT / "jobs" / (key + ".json"), job)
        jobs.append(job)
    helper = Path(r"__DEV_ROOT__\src\scratch\probe_cadrecode_mesh.py")
    protocol = {"schema": "qualitative_cpu_render_v1", "created_utc": utc(),
        "scope": "24 locked historical deployed repaired B2 candidates; render-only, no new model prediction or metrics",
        "original_locked_files_verified": count,
        "candidate_csv_sha256": sha(ROOT / "qualitative_case_registry.csv"),
        "candidate_lock_sha256": sha(ROOT / "selection/path_lock_manifest_v1.json"),
        "native_cli": str(NATIVE / "FllumaCLI.exe"), "native_cli_sha256": sha(NATIVE / "FllumaCLI.exe"),
        "native_export": "execute exact locked prediction.py for 20 historically scoreable cases; no further repair",
        "historical_hard_failures": "4; not re-executed; preserve reference views and original native error evidence",
        "tessellation": {"helper_path": str(helper), "helper_sha256": sha(helper),
            "function": "tessellate_step", "linear_deflection_mm": 0.03, "angular_deflection_radians": 0.3,
            "render_only": True, "metric_recomputation": False, "mesh_postprocessing": "exact coincident-vertex weld only; no smoothing, repairs or coordinate transforms"},
        "camera": {"projection": "orthographic", "views": [
            {"name": "iso_pos", "azimuth": 45.0, "elevation": 35.264389682754654},
            {"name": "iso_neg", "azimuth": 225.0, "elevation": 35.264389682754654}],
            "primary": "reference-bbox center, reference-projected frame and 82 percent fit; identical for both meshes",
            "clipping": "record out-of-frame vertices; supplement with joint-union frame for BOTH meshes, never independently fit prediction"},
        "image": {"size": 640, "background": [248,249,251], "body_color": [176,190,205],
            "edge_color": [72,79,89], "edge_angle_degrees": 28.0},
        "runtime": "Flluma native CPU export; existing WSL cadrecode_env STEP tessellation; Windows numpy/Pillow software rendering",
        "training": False, "model_forward": False, "new_program_code_repair": False,
        "source_scripts_at_start": {p.name: sha(p) for p in Path(__file__).parent.glob("*.py")},
        "jobs": jobs}
    write_new(OUT / "render_protocol.json", protocol)
    print(f"Render-only protocol saved; {count} original files verified; 20 export jobs, 4 preserved failures", flush=True)


if __name__ == "__main__":
    main()
