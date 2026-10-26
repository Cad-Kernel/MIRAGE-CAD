"""Validate all actual render assets and create a local, source-linked gallery."""
import html
import os
from pathlib import Path
from urllib.parse import quote
import numpy as np
from PIL import Image, ImageDraw
from render_common import *
from render_cpu import font


def url(path, start):
    path = local_path(path).resolve()
    require(path.exists(), f"Broken gallery link: {path}")
    if path.drive.lower() != Path(start).drive.lower():
        return path.as_uri()
    return quote(os.path.relpath(path, start).replace("\\", "/"), safe="/:.")


def link(path, title, start):
    return f'<a href="{html.escape(url(path,start),quote=True)}">{html.escape(title)}</a>'


STYLE = """body{font:16px Arial,sans-serif;color:#202a32;margin:0 auto;padding:28px;max-width:1400px;background:#fff}h1{font-size:26px}h2{font-size:21px}h3{font-size:17px}a{color:#086b6a}nav{display:flex;gap:16px;flex-wrap:wrap;padding:12px 0;border-bottom:1px solid #ccc}p{line-height:1.5}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:10px;text-align:left;border-bottom:1px solid #ddd;overflow-wrap:anywhere}th{background:#eef1f3}pre{white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.5;background:#f7f8fa;padding:16px;border:1px solid #d9dfe2;font-size:13px}img.panel{width:100%;height:auto}img.input{max-width:640px;width:100%;height:auto}.warn{border-left:4px solid #a66b00;padding:8px 16px;background:#fff7e7}.views{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.views img{width:100%}details{margin:20px 0}summary{cursor:pointer;font-weight:bold}code{overflow-wrap:anywhere}@media(max-width:700px){body{padding:12px}.views{grid-template-columns:1fr}table{font-size:12px}td,th{padding:6px}}"""


def page(title, body):
    return f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(title)}</title><style>{STYLE}</style><body>{body}</body></html>\n'


def write_text_new(path, text):
    with Path(path).open("x",encoding="utf-8") as f:
        f.write(text)


def create_case_page(row, report, base):
    start = base
    snapshot = ROOT / "cases" / row["case_id"]
    provenance = read(snapshot / "provenance.json")
    body = '<nav>' + link(OUT / "index.html", "All cases", start) + '</nav>' if (OUT / "index.html").exists() else '<nav><a href="../../index.html">All cases</a></nav>'
    body += f'<h1>{html.escape(row["modality"].upper())} {row["sample_id"]}</h1>'
    body += f'<p>{html.escape(row["case_type"])}; {row["complexity_tier"]}; historical deployed repaired B2. Candidate status is unchanged.</p>'
    body += '<p>' + html.escape(row["selection_reason"]) + '</p>'
    body += '<p class="warn">These are new CPU exports of locked historical code, not newly generated model predictions or recovered original temporary STEP files. Executable does not mean semantically accurate. Historical seed/checkpoint-byte binding remains unresolved.</p>'
    body += f'<img class="panel" src="{url(base / "panel.png",start)}" alt="Matched-camera two-view reference and prediction comparison">'
    if report["supplemental_union_frame"]:
        body += '<h2>Additional Shared Union Frame</h2><p>Both meshes use the same enlarged frame. These views supplement, not replace, the target-framed images above.</p><div class="views">'
        for r in report["renders"]:
            if r["camera"]["frame"] == "supplemental_shared_union_frame":
                label = r["kind"] + " " + r["camera"]["view"]["name"]
                body += f'<div><h3>{label}</h3><img src="{url(ROOT / r["image"]["path"],start)}" alt="{label}"></div>'
        body += '</div>'
    body += '<h2>Inputs and Original Evidence</h2><nav>'
    for key,label in [("reference_step","Reference STEP"),("reference_point","Reference point NPZ"),
                      ("reference_feature_tree","Reference feature tree"),("step_descriptor","STEP descriptor")]:
        item = provenance["original_assets"].get(key)
        if item and item.get("path"):
            body += link(item["path"],label,start)
    if row["scoreable"]:
        body += link(base / "prediction.step","New prediction STEP",start)
    for rel,label in [("plans/raw.txt","Raw plan"),("plans/canonicalized.txt","P1a plan"),
                      ("code/raw_prediction.py","Raw code"),("code/prediction.py","Executed repaired code"),
                      ("logs/gate_row.json","Historical gate row"),("logs/geometry_row.json","Historical geometry row")]:
        body += link(snapshot / rel,label,start)
    body += '</nav>'
    if row["modality"] == "image":
        body += f'<h3>Exact Image Input</h3><img class="input" src="{url(row["input_path"],start)}" alt="Original encoder image input">'
    elif row["modality"] in ("point","step"):
        body += '<p>Input asset: ' + link(row["input_path"],row["input_representation"],start) + '. CAD renders above show geometry, not a fabricated point-cloud or descriptor input.</p>'
    text = (snapshot / "input/exact_text.txt").read_text(encoding="utf-8")
    body += f'<details{" open" if row["modality"] == "text" else ""}><summary>{"Exact Text Input" if row["modality"] == "text" else "Dataset Text (not this modality input)"}</summary><pre>{html.escape(text)}</pre></details>'
    for rel,title in [("plans/canonicalized.txt","Generated Plan (P1a canonicalized)"),
                      ("code/excerpt.txt","Code Excerpt (literal first 40 lines, not a semantic summary)")]:
        body += f'<details open><summary>{title}</summary><pre>{html.escape((snapshot/rel).read_text(encoding="utf-8"))}</pre></details>'
    if not row["scoreable"]:
        body += '<h2>Original Failure Evidence</h2><pre>' + html.escape((snapshot / "logs/native_failure_messages.json").read_text(encoding="utf-8")) + '</pre>'
    body += '<h2>Provenance</h2><nav>' + link(snapshot / "case.json","Locked case record",start) + link(snapshot / "provenance.json","Original source hashes",start) + link(base / "render_manifest.json","New camera/pixel/hash manifest",start) + '</nav>'
    write_text_new(base / "index.html",page(row["case_id"],body))


def contact_sheet(rows, name, columns):
    tw, th = 670, 745
    sheet = Image.new("RGB",(columns*tw+40,math_ceil(len(rows)/columns)*th+100),(238,241,243))
    draw=ImageDraw.Draw(sheet)
    draw.text((20,16),name.replace("_"," "),fill=(20,30,40),font=font(26))
    draw.text((20,51),"Locked candidate set. Reference and prediction retain shared camera/scale. Failures have no predicted solid.",fill=(50,60,70),font=font(18))
    for i,row in enumerate(rows):
        p=OUT/"cases"/row["case_id"]/"panel.png"
        with Image.open(p) as im:
            preview=im.resize((tw,th),Image.Resampling.LANCZOS)
            sheet.paste(preview,(20+(i%columns)*tw,90+(i//columns)*th))
    target=OUT/(name+".png")
    require(not target.exists(),"Contact sheet already exists")
    sheet.save(target)
    return artifact(target)


def math_ceil(value):
    return int(np.ceil(value))


def main():
    original_count=verify_original_lock()
    require(not (OUT/"render_assets.json").exists(),"Finalization already exists; do not overwrite")
    rows=cases()
    all_views=[]
    records=[]
    issues=[]
    for row in rows:
        key=row["case_id"]
        base=OUT/"cases"/key
        report=read(base/"render_manifest.json")
        require(report["historical_scoreable"] == row["scoreable"],"Historical outcome changed")
        for r in report["renders"]:
            p=ROOT/r["image"]["path"]
            require(sha(p)==r["image"]["sha256"],"Image hash mismatch")
            with Image.open(p) as im:
                require(im.size==(640,640) and im.mode=="RGB","Invalid render format")
                arr=np.asarray(im)
            fg=int(np.any(arr!=[248,249,251],axis=2).sum())
            require(fg==r["foreground_pixels"],"Pixel audit mismatch")
            require(fg>100,"Blank or degenerate rendering")
            all_views.append(r)
        for view_name in ("iso_pos","iso_neg"):
            group=[r for r in report["renders"] if r["camera"]["view"]["name"]==view_name]
            for frame in set(r["camera"]["frame"] for r in group):
                same=[r for r in group if r["camera"]["frame"]==frame]
                require(len(same)==(2 if row["scoreable"] else 1),"Missing paired view")
                require(all(x["camera"]==same[0]["camera"] for x in same),"Mismatched camera/scale")
        require(sha(ROOT/report["panel"]["path"])==report["panel"]["sha256"],"Panel hash drift")
        if report["supplemental_union_frame"]:
            issues.append({"case_id":key,"issue":"prediction extends beyond reference frame","action":"original primary views retained; additional shared union-frame pair retained"})
        if row["scoreable"]:
            export=read(base/"native_export.json")
            require(sha(ROOT/export["step"]["path"])==export["step"]["sha256"],"New STEP hash mismatch")
        else:
            require(not (base/"prediction.step").exists() and not (base/"native_export.json").exists(),"Historical failure unexpectedly retried")
        create_case_page(row,report,base)
        def image_path(kind,name):
            matches=[r for r in report["renders"] if r["kind"]==kind and r["camera"]["view"]["name"]==name and r["camera"]["frame"]=="reference_frame"]
            return str(ROOT/matches[0]["image"]["path"]) if matches else None
        records.append({"case_id":key,"modality":row["modality"],"sample_id":row["sample_id"],
            "placement":"main" if "main" in row["tags"] else "appendix", "case_type":row["case_type"],
            "scoreable_historical":row["scoreable"],"cd_historical":row["cd"],"f1_at_1_fraction_historical":row["f1_at_1_fraction"],
            "reference_step_path":str(local_path(row["reference_step_path"])),
            "new_predicted_step_path":str(base/"prediction.step") if row["scoreable"] else None,
            "reference_view_1_path":image_path("reference","iso_pos"), "reference_view_2_path":image_path("reference","iso_neg"),
            "prediction_view_1_path":image_path("prediction","iso_pos"), "prediction_view_2_path":image_path("prediction","iso_neg"),
            "additional_shared_union_frame":report["supplemental_union_frame"],
            "case_page_path":str(base/"index.html"),"case_panel_path":str(base/"panel.png"),
            "render_manifest_path":str(base/"render_manifest.json"),
            "locked_plan_path":str(ROOT/row["predicted_plan_path"]),"locked_code_path":str(ROOT/row["predicted_code_path"]),
            "original_failure_log_path":str(ROOT/row["failure_log_path"]) if row["failure_log_path"] else None,
            "registry_status":"candidate","historical_metrics_recomputed":False})
    contacts=[contact_sheet([r for r in rows if "main" in r["tags"]],"main_8_candidates",4)]
    for modality in ("text","image","point","step"):
        contacts.append(contact_sheet([r for r in rows if r["modality"]==modality],f"{modality}_6_candidates",2))
    intro='<h1>MIRAGE Qualitative Candidates</h1><p>24 locked historical deployed B2 cases: 8 main candidates and 16 appendix candidates. New CPU exports and two complementary isometric views are preserved separately from original measurements.</p>'
    intro+='<p class="warn">Representative success means executable/scoreable near the complete-cohort metric median, not high semantic accuracy. Four historical failures have no prediction mesh. Original training seed/checkpoint binding is unresolved. This package does not replace Review/01-04 results.</p>'
    intro+='<nav>'+link(ROOT/"qualitative_case_registry.csv","Original locked CSV",OUT)+'<a href="render_assets.json">Actual asset paths (JSON)</a>'
    intro+='<a href="render_asset_registry.csv">Actual asset paths (CSV)</a>'+link(OUT/"render_protocol.json","Render-only protocol",OUT)+'</nav>'
    for contact in contacts:
        intro+='<p>'+link(ROOT/contact["path"],Path(contact["path"]).stem.replace("_"," "),OUT)+'</p>'
    for modality in ("text","image","point","step"):
        intro+=f'<h2>{modality.upper()}</h2><table><thead><tr><th>Sample</th><th>Placement</th><th>Type</th><th>Historical scoreable</th><th>Historical CD</th><th>Historical F@1</th><th>Frame warning</th></tr></thead><tbody>'
        for record in [r for r in records if r["modality"]==modality]:
            cd=f'{record["cd_historical"]:.5g}' if record["cd_historical"] is not None else 'not scoreable'
            f1=f'{record["f1_at_1_fraction_historical"]*100:.3f}%' if record["f1_at_1_fraction_historical"] is not None else 'not scoreable'
            intro+=f'<tr><td>{link(record["case_page_path"],record["sample_id"],OUT)}</td><td>{record["placement"]}</td><td>{record["case_type"]}</td><td>{record["scoreable_historical"]}</td><td>{cd}</td><td>{f1}</td><td>{"Additional joint frame" if record["additional_shared_union_frame"] else ""}</td></tr>'
        intro+='</tbody></table>'
    write_text_new(OUT/"index.html",page("MIRAGE qualitative candidates",intro))
    write_new(OUT/"render_assets.json",{"schema":"qualitative_render_actual_assets_v1","created_utc":utc(),"records":records,"contact_sheets":contacts})
    summary={"status":"PASS_CPU_ASSETS_CAMERA_PIXEL_AND_ORIGINAL_LOCK_AUDIT","created_utc":utc(),
        "cases":len(rows),"main_candidates":8,"appendix_candidates":16,"new_prediction_steps":20,
        "historical_failures_preserved_not_retried":4,"meshes":44,
        "primary_view_pngs":sum(r["camera"]["frame"]=="reference_frame" for r in all_views),
        "supplemental_view_pngs":sum(r["camera"]["frame"]!="reference_frame" for r in all_views),
        "case_panels":24,"contact_sheets":len(contacts),"render_pngs":len(all_views),
        "blank_renders":sum(r["blank"] for r in all_views),
        "clipped_primary_views":sum(r["out_of_frame_vertices"]>0 and r["camera"]["frame"]=="reference_frame" for r in all_views),
        "shared_union_supplement_cases":issues,"original_locked_files_verified_unchanged":original_count,
        "tests":{"camera_and_raster_unit_tests":5,"paired_camera_checks":"PASS","pixel_recount":"PASS","image_hashes":"PASS","native_export_successes":20},
        "historical_metrics":"not recomputed or changed","model_forward_or_training":False,
        "registry_status":"candidate; final manuscript selection remains open",
        "execution_notes":["Native reference STEP import-to-CustomNode was unavailable; original failed probe retained. Existing CadQuery STEP tessellator used for both reference and prediction.",
            "Initial tessellation run stopped before a failure-reference mesh write because the case output directory did not yet exist; mkdir fix only, verified prior assets reused, no geometry or camera policy changes.",
            "20 current native re-exports succeeded. No claim of byte identity to deleted original temporary STEP files."]}
    write_new(OUT/"cpu_render_actuals.json",summary)
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
