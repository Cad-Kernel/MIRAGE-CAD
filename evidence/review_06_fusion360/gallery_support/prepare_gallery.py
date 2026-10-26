"""Lock archive-backed render jobs and literal per-case records before conversion."""
from common import *

RASTER = Path(r"__FLLUMA_ROOT__\build\Desktop_Qt_6_8_3_MSVC2022_64bit-Release\bin\python\flluma\api\image_export.py")


def main():
    prior = verify_prior()
    selection = read(GALLERY/"selection_v1.json")
    require(selection["protocol_sha256"] == sha(POLICY), "Selection protocol changed")
    archive = read(ARCHIVE/"archive_manifest_v1.json")
    mapping = {x["path"]:x for x in archive["sources"]}
    jobs = []
    for case in selection["cases"]:
        base = GALLERY/"cases"/case["case_id"]
        assets = {}
        for role, source in case["master"]["assets"].items():
            require(source in mapping, "Asset omitted from archive: "+source)
            item=mapping[source]
            assets[role]={"original_path":source,"exists":item["exists"],"sha256":item["sha256"],
                          "archived_path":str(ARCHIVE/item["archive_path"]) if item["exists"] else None}
        write_new(base/"case_record.json",case)
        write_new(base/"archived_asset_paths.json",assets)
        for kind in ("mirage_raw","mirage_used","nn_raw","nn_used"):
            row=case["master"]["source_records"][kind]
            text_new(base/"code"/(kind+".py"),row["prediction"])
            text_new(base/"plans"/(kind+".txt"),row.get("predicted_ir") or "")
        text_new(base/"plans"/"mirage_raw_plan.txt",case["master"]["source_records"]["plan"]["predicted_ir"])
        for method in METHODS:
            source_key="reference" if method=="reference" else method+"_step"
            item=assets[source_key]
            eligible=method=="reference" or case["taxonomy"][method]["cd_scoreable"]
            require(not eligible or item["exists"],"Historically scoreable shape has no existing STEP")
            jobs.append({"case_id":case["case_id"],"sample_id":case["sample_id"],"method":method,
                "render_eligible":eligible,"historical_outcome":"REFERENCE" if method=="reference" else case["taxonomy"][method]["primary_outcome"],
                "archive_step_path":item["archived_path"],"step_sha256":item["sha256"],
                "mesh_path":str(base/(method+"_mesh.npz")),"mesh_record_path":str(base/(method+"_mesh.json"))})
    config={"status":"RENDER_JOBS_LOCKED_BEFORE_MESHING", "created_utc":utc(),
        "protocol_sha256":sha(POLICY),"selection_sha256":sha(GALLERY/"selection_v1.json"),
        "archive_manifest_sha256":sha(ARCHIVE/"archive_manifest_v1.json"),"prior_seals":prior,
        "methods":list(METHODS),"coordinate_series":["metric_space","reference_world"],
        "views":[{"name":"isometric","azimuth":45,"elevation":35.264389682754654},
                 {"name":"front","azimuth":270,"elevation":0}],
        "projection":"orthographic","field_of_view":None,"frame_occupancy":.82,
        "size":640,"background":[248,249,251],"body_color":[176,190,205],"edge_color":[72,79,89],
        "edge_angle_degrees":24,"light_world":[1,-1,2],
        "alpha":1e-4,"angular_tolerance":.3,"normalization":"mesh bbox midpoint, largest extent, then +0.5",
        "rasterizer_path":str(RASTER),"rasterizer_sha256":sha(RASTER),
        "prepare_script_sha256":sha(__file__),"mesh_script_sha256":sha(Path(__file__).parent/"tessellate_existing.py"),
        "renderer_script_sha256":sha(Path(__file__).parent/"render_gallery.py"),"jobs":jobs}
    write_new(GALLERY/"render_protocol_v1.json",config)
    print(f"Locked {len(jobs)} method slots; {sum(j['render_eligible'] for j in jobs)} existing STEP meshes eligible; no geometry executed.")


if __name__=="__main__":
    main()
