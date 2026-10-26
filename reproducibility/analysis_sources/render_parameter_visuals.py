"""Two-view current CPU illustrations, common union frame, unedited evidence."""
import hashlib
import html
import importlib.util
import json
import math
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE / "parameter_visuals_v1"
REVIEW = BASE.parent


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(path, value):
    with path.open("x",encoding="utf-8") as stream:
        json.dump(value,stream,indent=2,ensure_ascii=False)
        stream.write("\n")


def main():
    renderer_path = REVIEW / "05_qualitative/render_support/render_cpu.py"
    sys.path.insert(0,str(renderer_path.parent))
    spec = importlib.util.spec_from_file_location("existing_cpu_parameter_display",renderer_path)
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    renderer.artifact = lambda p:{"path":str(Path(p).relative_to(ROOT)).replace("\\","/"),"bytes":Path(p).stat().st_size,"sha256":sha(Path(p))}
    old_config = json.loads((REVIEW/"05_qualitative/rendering/cpu_v1/render_protocol.json").read_text())
    image_config = old_config["image"]
    prepared = json.loads((ROOT/"prepared_cases.json").read_text())
    records = []
    for case in prepared["cases"]:
        folder = ROOT/"cases"/case["case_id"]
        meshes,reports = {},{}
        for side in ("before","after"):
            reports[side] = json.loads((folder/side/"native_export.json").read_text())
            if reports[side]["gates"]["step_export_ok"]:
                with np.load(folder/side/"display_mesh.npz") as m:
                    meshes[side] = (m["vertices"],m["faces"])
        assert "before" in meshes, "Do not substitute for failed baseline"
        union = np.concatenate([m[0] for m in meshes.values()])
        camera_records = []
        for view_id,azimuth in enumerate((45,225),1):
            view={"azimuth":azimuth,"elevation":35.264389682754654}
            camera=renderer.camera_for(union,view,image_config["size"],kind="common_before_after_union_frame")
            for side in ("before","after"):
                destination=folder/side/f"view_{view_id}.png"
                if side in meshes:
                    v,f=meshes[side]
                    result=renderer.render_mesh(v,f,camera,destination,image_config)
                    assert not result["blank"] and result["out_of_frame_vertices"]==0
                    result["kind"]="current_geometry_render"
                else:
                    im=Image.new("RGB",(640,640),"#f8f1f0")
                    d=ImageDraw.Draw(im)
                    d.text((40,180),"EXECUTION / EXPORT FAILURE",fill="#8b2f2b",font=renderer.font(26))
                    d.text((40,230),"No replacement geometry",fill="#343434",font=renderer.font(23))
                    error=reports[side].get("error","")
                    import textwrap
                    for i,line in enumerate(textwrap.wrap(error,width=48)):
                        d.text((40,285+i*25),line,fill="#343434",font=renderer.font(18))
                    assert not destination.exists()
                    im.save(destination)
                    result={"image":renderer.artifact(destination),"kind":"failure_placeholder","camera":camera}
                result.update(side=side,view_id=view_id)
                camera_records.append(result)
        edit=case["historical_result"]
        panel=Image.new("RGB",(1340,1500),"white")
        draw=ImageDraw.Draw(panel)
        draw.text((20,14),f"{case['case_id']} | {case['sample_id']} | {case['bucket']}",fill="#172536",font=renderer.font(25))
        draw.text((20,53),f"{edit['param']}: {edit['from']:g} -> {edit['to']:g} | relative delta {edit['delta']:+.0%}",fill="#172536",font=renderer.font(23))
        draw.text((20,91),"Historical: "+edit["outcome"],fill="#343434",font=renderer.font(20))
        for col,side in enumerate(("before","after")):
            draw.text((20+col*660,125),side.upper(),fill="#172536",font=renderer.font(23))
            for v in (1,2):
                with Image.open(folder/side/f"view_{v}.png") as im:
                    panel.paste(im,(20+col*660,160+(v-1)*650))
        draw.text((20,1471),"Current CPU illustration; common scale/camera; not a semantic-edit accuracy test.",fill="#343434",font=renderer.font(17))
        assert not (folder/"panel.png").exists()
        panel.save(folder/"panel.png")
        metrics={}
        for side in meshes:
            metrics[side]=json.loads((folder/side/"mesh_record.json").read_text())
        comparison={"case_id":case["case_id"],"historical_outcome":edit["outcome"],"current_before_export_ok":reports["before"]["gates"]["step_export_ok"],
                    "current_after_export_ok":reports["after"]["gates"]["step_export_ok"],"current_after_failure_stage":reports["after"].get("failure_stage"),
                    "current_geometry_info":{s:{k:metrics[s][k] for k in ("brep_volume_current","brep_area_current","bbox_min","bbox_max")} for s in metrics},
                    "author_semantic_review":"PENDING","camera_contract":"Both sides share exact camera in each of 2 views", "images":camera_records}
        if "after" in meshes:
            a,b=meshes["before"][0],meshes["after"][0]
            comparison["display_vertex_sets_exactly_equal"]=bool(np.array_equal(a,b))
            comparison["brep_volume_delta_current"]=metrics["after"]["brep_volume_current"]-metrics["before"]["brep_volume_current"]
        write(folder/"render_record.json",comparison)
        before=(folder/"before.py").read_text(encoding="utf-8")
        after=(folder/"after.py").read_text(encoding="utf-8")
        content=f'''<!doctype html><meta charset="utf-8"><title>{case['case_id']} parameter evidence</title>
<style>body{{font:16px system-ui;max-width:1400px;margin:24px auto;color:#172536}}img{{max-width:100%}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f7f9;padding:16px}}.cols{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}</style>
<a href="../../index.html">All cases</a><h1>{case['case_id']} — {html.escape(case['sample_id'])}</h1>
<p>{html.escape(case['bucket'])}; {html.escape(edit['param'])}: {edit['from']} → {edit['to']}. Author semantic confirmation PENDING.</p>
<img src="panel.png"><p>Historical record: {html.escape(edit['outcome'])}. These are current CPU re-exports, not recovered historical STEP bytes.</p>
<p><a href="case.json">Original case metadata and literal examples</a> · <a href="change.diff">Exact code difference</a> · <a href="render_record.json">Camera and geometry diagnostics</a></p>
<div class="cols"><section><h2>Before</h2><a href="before/native_export.json">Native record</a><pre>{html.escape(before)}</pre></section><section><h2>After</h2><a href="after/native_export.json">Native record</a><pre>{html.escape(after)}</pre></section></div>'''
        (folder/"index.html").write_text(content,encoding="utf-8")
        records.append({"case_id":case["case_id"],"sample_id":case["sample_id"],"bucket":case["bucket"],"parameter":edit["param"],"historical_record":edit,
                        "page":f"cases/{case['case_id']}/index.html","panel":f"cases/{case['case_id']}/panel.png","comparison":comparison})
        print(case["case_id"],"two views / side rendered",flush=True)
    sheet=Image.new("RGB",(1340,2250),"white")
    for i,record in enumerate(records):
        with Image.open(ROOT/record["panel"]) as im:
            thumb=im.resize((670,750),Image.Resampling.LANCZOS)
            sheet.paste(thumb,((i%2)*670,(i//2)*750))
    sheet.save(ROOT/"contact_sheet.png")
    links="".join(f'<li><a href="{r["page"]}">{r["case_id"]} — {html.escape(r["bucket"])} — {r["sample_id"]}</a></li>' for r in records)
    (ROOT/"index.html").write_text(f'<!doctype html><meta charset="utf-8"><title>Parameter CPU evidence</title><style>body{{font:17px system-ui;max-width:1400px;margin:24px auto}}img{{max-width:100%}}</style><h1>Parameter before/after — six fixed candidates</h1><p>Current CPU illustrations from recorded perturbations. No semantic-edit correctness claim. Author signoff pending.</p><ul>{links}</ul><img src="contact_sheet.png">',encoding="utf-8")
    write(ROOT/"case_registry.json",records)
    write(ROOT/"render_summary.json",{"status":"CPU_PARAMETER_VISUAL_ASSETS_COMPLETE_PENDING_AUTHOR_SEMANTICS","cases":6,"actual_geometry_views":20,"failure_placeholder_views":4,
          "native_steps":10,"panels":6,"old_statistics_changed":False,"renderer_source_sha256":sha(renderer_path),"new_script_sha256":sha(Path(__file__)),"author_signoff":"PENDING"})


if __name__ == "__main__":
    main()
