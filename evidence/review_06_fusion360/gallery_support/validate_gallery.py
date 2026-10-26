"""Independent archive, selection, transform, pixel, CSV and local-link checks."""
from collections import Counter
import csv
from html.parser import HTMLParser
import subprocess
import sys
from urllib.parse import unquote, urlsplit
import numpy as np
from PIL import Image
from common import *
from select_cases import select


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets=[]
    def handle_starttag(self,tag,attrs):
        self.targets.extend(v for k,v in attrs if k in ("src","href"))


def csv_rows(path):
    with path.open(encoding="utf-8",newline="") as stream:
        return list(csv.DictReader(stream))


def main():
    prior=verify_prior()
    selection=read(GALLERY/"selection_v1.json")
    master=read(ROOT/"audit/master_records_v1.json")
    taxonomy=read(ROOT/"taxonomy/failure_taxonomy_v1.json")
    slots,order=select(master,taxonomy)
    require(slots==selection["slots"] and order==selection["allocation_order"],"Selection not reproduced")
    require(selection["protocol_sha256"]==sha(POLICY),"Protocol changed after selection")
    require(selection["selector_sha256"]==sha(Path(__file__).parent/"select_cases.py"),"Selector changed")
    require(selection["master_sha256"]==sha(ROOT/"audit/master_records_v1.json"),"Master changed")
    require(selection["taxonomy_sha256"]==sha(ROOT/"taxonomy/failure_taxonomy_v1.json"),"Taxonomy changed")
    require(len(selection["cases"])==len({c["sample_id"] for c in selection["cases"]})==18,"Duplicate/lost selected ID")
    require(Counter(c["placement"] for c in selection["cases"])=={"main":6,"appendix":12},"Placement count differs")
    originals=read(ROOT/"audit/source_files_v1.json")["files"]
    archive=read(ARCHIVE/"archive_manifest_v1.json")
    require(archive["inventory_sha256"]==sha(ROOT/"audit/source_files_v1.json"),"Archive source changed")
    require(len(archive["sources"])==len(originals),"Source omitted from archive")
    objects={}
    for item in archive["sources"]:
        original=originals[item["path"]]
        require(all(item[k]==v for k,v in original.items()),"Original archive metadata changed")
        if item["exists"]:
            objects[item["archive_path"]]=item
        else:
            require(item["archive_path"] is None,"Historically missing source fabricated")
    for rel,item in objects.items():
        path=ARCHIVE/rel
        require(path.stat().st_size==item["bytes"] and sha(path)==item["sha256"],"Archive object changed")
    require(len(archive["all_400_ids_preserved"])==400,"Master IDs omitted")
    config=read(GALLERY/"render_protocol_v1.json")
    require(config["protocol_sha256"]==sha(POLICY),"Render protocol differs")
    for key,name in (("mesh_script_sha256","tessellate_existing.py"),("renderer_script_sha256","render_gallery.py")):
        require(config[key]==sha(Path(__file__).parent/name),"Frozen implementation changed")
    require(config["rasterizer_sha256"]==sha(config["rasterizer_path"]),"Rasterizer changed")
    geometry=placeholders=subpixel=0
    mesh_count=0
    for case in selection["cases"]:
        base=GALLERY/"cases"/case["case_id"]
        require(read(base/"case_record.json")==case,"Literal case record changed")
        render=read(base/"render_manifest.json")
        require(render["protocol_sha256"]==sha(GALLERY/"render_protocol_v1.json"),"Wrong render provenance")
        require(len(render["renders"])==16,"Two-series/two-view/method grid incomplete")
        require(len({(r["series"],r["method"],r["view"]) for r in render["renders"]})==16,"Duplicate image slot")
        require(not render["metrics_recomputed"],"Unexpected new metric")
        ref_mesh=np.load(base/"reference_mesh.npz",allow_pickle=False)["vertices"]
        ref_center=(ref_mesh.min(axis=0)+ref_mesh.max(axis=0))/2
        ref_extent=np.max(np.ptp(ref_mesh,axis=0))
        for method in METHODS:
            record=read(base/(method+"_mesh.json"))
            if record["counter_key"]=="meshed":
                mesh_count+=1
                p=base/(method+"_mesh.npz")
                require(sha(p)==record["mesh_sha256"],"Mesh drift")
                with np.load(p,allow_pickle=False) as data:
                    unique,inverse=np.unique(data["raw_vertices"],axis=0,return_inverse=True)
                    require(np.array_equal(unique,data["vertices"]),"Vertex coordinates modified")
                    require(np.array_equal(inverse[data["raw_faces"]],data["faces"]),"Triangle geometry modified")
                    vertices=data["vertices"]
                for series in ("metric_space","reference_world"):
                    t=render["transforms"][series][method]
                    f=np.asarray(t["native_to_display"])
                    inv=np.asarray(t["display_to_native"])
                    np.testing.assert_allclose(f@inv,np.eye(4),rtol=1e-12,atol=1e-8)
                    transformed=np.column_stack((vertices,np.ones(len(vertices))))@f.T
                    lo,hi=transformed[:,:3].min(axis=0),transformed[:,:3].max(axis=0)
                    if series=="metric_space":
                        np.testing.assert_allclose((lo+hi)/2,[.5,.5,.5],atol=1e-8)
                        np.testing.assert_allclose(np.max(hi-lo),1,atol=1e-8)
                    else:
                        expected=np.eye(4)
                        if method=="cadr":
                            expected[:3,:3]*=ref_extent/200
                            expected[:3,3]=ref_center
                        np.testing.assert_allclose(f,expected,rtol=1e-12,atol=1e-8)
            else:
                require(not (base/(method+"_mesh.npz")).exists(),"Failed output received geometry")
                require(not case["taxonomy"][method]["cd_scoreable"],"Historically scoreable geometry unexpectedly omitted")
        for series in ("metric_space","reference_world"):
            for view in ("isometric","front"):
                group=[r for r in render["renders"] if r["series"]==series and r["view"]==view]
                require(len(group)==4 and all(r["camera"]==group[0]["camera"] for r in group),"Independent per-method camera/scale")
                require(group[0]["camera"]["projection"]=="orthographic","Projection changed")
        for image in render["renders"]:
            require(sha(image["path"])==image["sha256"],"Image hash changed")
            with Image.open(image["path"]) as im:
                require(im.size==(640,640),"Image dimensions changed")
                pixels=np.asarray(im.convert("RGB"))
            if image["placeholder"]:
                placeholders+=1
            else:
                geometry+=1
                foreground=np.any(pixels!=config["background"],axis=2)
                require(int(foreground.sum())==image["foreground_pixels"],"Pixel count differs")
                require(foreground.any() or image["subpixel_warning"],"Unexplained blank image")
                require(image["out_of_frame_vertices"]==0 and image["border_foreground_pixels"]==0,"Geometry clipped")
                subpixel+=image["subpixel_warning"]
        for panel in render["panels"].values():
            require(sha(panel["path"])==panel["sha256"],"Panel changed")
    selected_csv=csv_rows(ROOT/"fusion360_gallery_cases_v1.csv")
    assets_csv=csv_rows(ROOT/"fusion360_gallery_assets_v1.csv")
    require(len(selected_csv)==18 and len(assets_csv)==72,"CSV row count changed")
    for original,parsed in zip(selection["cases"],selected_csv):
        require(original["sample_id"]==parsed["sample_id"] and original["slot"]==parsed["slot"],"CSV ID/order mismatch")
        for m in ("mirage","nn","cadr"):
            for metric,col in (("CD","CD_x1000"),("IoU","IoU")):
                expected=original["master"]["view"][m+"_"+metric]
                literal=parsed[m+"_"+col]
                require((literal=="" if expected is None else float(literal)==expected),"CSV historical metric changed")
    for row in assets_csv:
        for key in ("archived_step_path","mesh_npz_path","native_mesh_record","normalized_isometric","normalized_front","world_isometric","world_front","camera_and_transform_record","archived_asset_paths","visual_review_record"):
            if row[key]:
                require(Path(row[key]).is_file(),"CSV local asset path broken: "+row[key])
    link_count=0
    for page in GALLERY.rglob("*.html"):
        parser=Links()
        parser.feed(page.read_text(encoding="utf-8"))
        for target in parser.targets:
            parsed=urlsplit(target)
            require(not parsed.scheme,"Unexpected remote gallery dependency")
            require((page.parent/unquote(parsed.path)).is_file(),"Broken local HTML link")
            link_count+=1
    visual=read(GALLERY/"visual_review_v1.json")
    require(len(visual["rows"])==18 and all(not r["author_confirmed"] and r["verified_semantic_failure"] is None for r in visual["rows"]),"Unperformed author review claimed")
    tests=0
    for name,n in (("test_selection.py",8),("test_render_contract.py",6)):
        p=subprocess.run([sys.executable,str(Path(__file__).parent/name)],capture_output=True,text=True,timeout=60)
        require(p.returncode==0,"Contract test failure: "+p.stderr)
        tests+=n
    result={"status":"PASS_ARCHIVE_SELECTION_SHARED_CAMERAS_TRANSFORMS_PIXELS_AND_CSV", "created_utc":utc(),
        "selected_unique_cases":18,"main":6,"appendix":12,"meshes":mesh_count,
        "geometry_views":geometry,"historical_placeholder_views":placeholders,"subpixel_views_explicit":subpixel,
        "all_shared_cameras_equal":True,"all_transforms_reversible":True,"raw_mesh_geometry_preserved":True,
        "source_paths_preserved":len(archive["sources"]),"archive_objects_rehashed":len(objects),
        "archive_bytes":archive["archived_bytes"],"prior_seals_unchanged":prior,
        "case_csv_rows":18,"asset_csv_rows":72,"local_html_links_verified":link_count,"contract_tests":tests,
        "historical_metrics_unchanged":True,"author_semantic_confirmation":"PENDING",
        "training_new_predictions_program_execution_or_metric_scoring":False}
    write_new(GALLERY/"independent_validation_v1.json",result)
    print(result)


if __name__=="__main__":
    main()
