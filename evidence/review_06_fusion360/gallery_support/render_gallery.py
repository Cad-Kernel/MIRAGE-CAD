"""Shared-camera, dual-coordinate CPU rasterization of locked existing STEP meshes."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import html
import importlib.util
import itertools
import math
import os
import textwrap
from urllib.parse import quote
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from common import *

RASTER_PATH=Path(r"__FLLUMA_ROOT__\build\Desktop_Qt_6_8_3_MSVC2022_64bit-Release\bin\python\flluma\api\image_export.py")
spec=importlib.util.spec_from_file_location("flluma_cpu_rasterizer",RASTER_PATH)
RASTER=importlib.util.module_from_spec(spec)
spec.loader.exec_module(RASTER)
NAMES={"reference":"Reference","cadr":"CAD-Recode","mirage":"MIRAGE generated-plan","nn":"NN retrieval"}


def font(size,mono=False):
    return ImageFont.truetype(str(Path("C:/Windows/Fonts")/("consola.ttf" if mono else "arial.ttf")),size)


def corners(lo,hi):
    return np.array(list(itertools.product(*zip(lo,hi))),dtype=float)


def camera_for(points,view,config,series):
    direction=np.asarray(RASTER._spherical_direction(view["azimuth"],view["elevation"]))
    right=np.asarray(RASTER._normalize(RASTER._cross((0,0,1),direction)))
    up=np.cross(direction,right)
    basis=np.stack([right,up,direction],axis=1)
    center=(points.min(axis=0)+points.max(axis=0))/2
    projected=(points-center)@basis
    lo,hi=projected[:,:2].min(axis=0),projected[:,:2].max(axis=0)
    span=max(float(np.max(hi-lo)),1e-12)
    return {"series":series,"view":view,"projection":"orthographic","field_of_view":None,
        "center":center.tolist(),"basis":basis.tolist(),"projected_midpoint":((lo+hi)/2).tolist(),
        "span_world_units":span,"pixels_per_world_unit":config["size"]*config["frame_occupancy"]/span,
        "size":config["size"],"frame_occupancy":config["frame_occupancy"],
        "frame_source":"fixed_unit_cube" if series=="metric_space" else "shared_all_renderable_methods_union_bbox"}


def transform(vertices,scale,offset):
    forward=np.eye(4)
    forward[:3,:3]*=scale
    forward[:3,3]=offset
    return vertices*scale+offset,{"native_to_display":forward.tolist(),"display_to_native":np.linalg.inv(forward).tolist()}


def project(vertices,camera):
    p=(vertices-np.asarray(camera["center"]))@np.asarray(camera["basis"])
    mid=camera["projected_midpoint"]
    s=camera["pixels_per_world_unit"]
    return np.column_stack(((p[:,0]-mid[0])*s+camera["size"]/2,
                           camera["size"]/2-(p[:,1]-mid[1])*s,p[:,2]))


def render_mesh(vertices,faces,camera,path,config):
    size=config["size"]
    projected=project(vertices,camera)
    screen=[tuple(p) for p in projected]
    tris=[tuple(int(i) for i in t) for t in faces]
    normals=np.cross(vertices[faces[:,1]]-vertices[faces[:,0]],vertices[faces[:,2]]-vertices[faces[:,0]])
    normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-30)
    direction=np.asarray(camera["basis"])[:,2]
    lighting=normals.copy()
    lighting[(lighting@direction)<0]*=-1
    light=np.asarray(config["light_world"],dtype=float)
    light/=np.linalg.norm(light)
    shades=.30+.68*np.maximum(0,lighting@light)
    colors=np.clip(shades[:,None]*config["body_color"],0,255).astype(int)
    background=tuple(config["background"])
    pixels=[list(background) for _ in range(size*size)]
    depth=[-1e300]*(size*size)
    for i in np.argsort(projected[faces,2].mean(axis=1),kind="stable"):
        a,b,c=tris[i]
        RASTER._raster_triangle(screen[a],screen[b],screen[c],tuple(colors[i]),pixels,depth,size,size)
    edges=RASTER._visible_feature_edges(tris,[tuple(n) for n in normals],view_dir=tuple(direction),edge_angle_degrees=config["edge_angle_degrees"])
    epsilon=max(float(np.ptp(projected[:,2])),camera["span_world_units"])*.004
    for a,b in edges:
        RASTER._draw_line_depth(screen[a],screen[b],tuple(config["edge_color"]),pixels,depth,size,size,depth_epsilon=epsilon)
    array=np.asarray(pixels,dtype=np.uint8).reshape(size,size,3)
    mask=np.any(array!=background,axis=2)
    yy,xx=np.where(mask)
    extent=np.ptp(projected[:,:2],axis=0)
    outside=((projected[:,:2]<0)|(projected[:,:2]>=size)).any(axis=1)
    require(not path.exists(),"No render overwrite")
    Image.fromarray(array).save(path)
    return {"path":str(path),"sha256":sha(path),"camera":camera,
        "foreground_pixels":int(mask.sum()),"blank":not bool(mask.any()),
        "foreground_bbox_px":[int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())] if len(xx) else None,
        "projected_extent_px":extent.tolist(),"subpixel_warning":bool(np.max(extent)<1),
        "out_of_frame_vertices":int(outside.sum()),
        "border_foreground_pixels":int(mask[0].sum()+mask[-1].sum()+mask[:,0].sum()+mask[:,-1].sum())}


def placeholder(path,method,status,case,config):
    image=Image.new("RGB",(config["size"],config["size"]),tuple(config["background"]))
    draw=ImageDraw.Draw(image)
    lines=["NO RENDERED GEOMETRY",NAMES[method],status,"", "Historical result preserved.","No replacement or repair."]
    native=case["taxonomy"].get(method,{})
    lines+=textwrap.wrap(native.get("reported_error") or native.get("reason_subtype") or "",width=61)[:9]
    y=80
    for line in lines:
        for text in textwrap.wrap(line,width=52) or [""]:
            draw.text((25,y),text,font=font(18),fill=(105,55,55))
            y+=26
    require(not path.exists(),"No placeholder overwrite")
    image.save(path)
    return {"path":str(path),"sha256":sha(path),"placeholder":True,"status":status}


def make_panel(case,report,series,base):
    panel=Image.new("RGB",(1340,930),"white")
    draw=ImageDraw.Draw(panel)
    draw.text((18,12),case["slot"]+"  "+case["sample_id"],font=font(22),fill=(25,35,42))
    draw.text((18,43),case["selection_bucket"].replace("_"," "),font=font(18),fill=(55,65,70))
    title="Shape-normalized metric space: scale/translation removed" if series=="metric_space" else "Reference-world diagnostic: shared union frame, no independent zoom"
    draw.text((18,70),title,font=font(18),fill=(55,65,70))
    for i,method in enumerate(METHODS):
        x=18+i*330
        draw.text((x,108),NAMES[method],font=font(18),fill=(25,35,42))
        native=case["taxonomy"].get(method,{})
        if method=="reference":
            label="Original reference STEP"
        else:
            cd=native["CD"]
            iou=native["IoU"]
            label=(f"CD {cd:.3g}" if cd is not None else "CD unavailable")+"; "+(f"IoU {100*iou:.2f}%" if iou is not None else "IoU unavailable")
        draw.text((x,135),label,font=font(15),fill=(55,65,70))
        for j,view in enumerate(("isometric","front")):
            record=next(r for r in report["renders"] if r["series"]==series and r["method"]==method and r["view"]==view)
            y=176+j*354
            draw.text((x,y-21),view.capitalize(),font=font(15),fill=(60,70,75))
            with Image.open(record["path"]) as image:
                panel.paste(image.resize((320,320),Image.Resampling.LANCZOS),(x,y))
            if record.get("subpixel_warning"):
                draw.text((x,y+321),"Subpixel size in shared frame",font=font(14),fill=(130,65,25))
    draw.text((18,891),"Historical CD x1000 / IoU unchanged. Display meshes are not rescored. Semantic labels require visual review.",font=font(16),fill=(60,70,75))
    path=base/(series+"_panel.png")
    require(not path.exists(),"No panel overwrite")
    panel.save(path)
    return {"path":str(path),"sha256":sha(path)}


def render_case(case):
    config=read(GALLERY/"render_protocol_v1.json")
    require(config["renderer_script_sha256"]==sha(__file__),"Renderer drift")
    require(config["rasterizer_sha256"]==sha(RASTER_PATH),"Rasterizer drift")
    base=GALLERY/"cases"/case["case_id"]
    record_path=base/"render_manifest.json"
    require(not record_path.exists(),"Case already rendered; verification is separate")
    meshes={}
    records={m:read(base/(m+"_mesh.json")) for m in METHODS}
    for method,record in records.items():
        if record["counter_key"]=="meshed":
            mesh=base/(method+"_mesh.npz")
            require(sha(mesh)==record["mesh_sha256"],"Mesh changed")
            with np.load(mesh,allow_pickle=False) as data:
                meshes[method]=(data["vertices"],data["faces"])
    require("reference" in meshes,"Reference conversion failed; investigate without changing case")
    reference=meshes["reference"][0]
    ref_center=(reference.min(axis=0)+reference.max(axis=0))/2
    ref_extent=float(np.max(np.ptp(reference,axis=0)))
    report={"case_id":case["case_id"],"sample_id":case["sample_id"],"created_utc":utc(),
        "protocol_sha256":sha(GALLERY/"render_protocol_v1.json"),"renderer_sha256":sha(__file__),
        "rasterizer_sha256":sha(RASTER_PATH),"renders":[],"transforms":{},"panels":{},
        "semantic_review":"PENDING_VISUAL_INSPECTION","metrics_recomputed":False}
    for series in config["coordinate_series"]:
        changed={}
        report["transforms"][series]={}
        for method,(vertices,faces) in meshes.items():
            center=(vertices.min(axis=0)+vertices.max(axis=0))/2
            extent=float(np.max(np.ptp(vertices,axis=0)))
            require(extent>0,"Invalid mesh extent")
            if series=="metric_space":
                scale,offset=1/extent,.5-center/extent
            elif method=="cadr":
                scale,offset=ref_extent/200,ref_center
            else:
                scale,offset=1,np.zeros(3)
            display,matrix=transform(vertices,scale,offset)
            matrix.update(original_mesh_bbox=[vertices.min(axis=0).tolist(),vertices.max(axis=0).tolist()],
                display_bbox=[display.min(axis=0).tolist(),display.max(axis=0).tolist()],
                reference_extent_used=ref_extent if series=="reference_world" and method=="cadr" else None)
            report["transforms"][series][method]=matrix
            changed[method]=(display,faces)
        if series=="metric_space":
            frame=corners([0,0,0],[1,1,1])
        else:
            all_points=np.concatenate([v for v,f in changed.values()])
            frame=corners(all_points.min(axis=0),all_points.max(axis=0))
        for view in config["views"]:
            camera=camera_for(frame,view,config,series)
            for method in METHODS:
                path=base/f"{series}_{method}_{view['name']}.png"
                if method in changed:
                    v,f=changed[method]
                    record=render_mesh(v,f,camera,path,config)
                    require(record["out_of_frame_vertices"]==0,"Shared frame clipped geometry")
                    require(not record["blank"] or record["subpixel_warning"],"Unexpected blank mesh image")
                    record["placeholder"]=False
                else:
                    record=placeholder(path,method,records[method]["historical_outcome"] if records[method]["counter_key"]=="historical_placeholders" else "RENDER_CONVERSION_FAILURE",case,config)
                    record["camera"]=camera
                record.update(series=series,method=method,view=view["name"])
                report["renders"].append(record)
        report["panels"][series]=make_panel(case,report,series,base)
    write_new(record_path,report)
    print(case["case_id"]+" dual-series rendered",flush=True)
    return report


def rel(path,base=GALLERY):
    return quote(os.path.relpath(path,base).replace("\\","/"),safe="/.")


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--workers",type=int,default=4)
    args=parser.parse_args()
    require(read(GALLERY/"selection_v1.json")["protocol_sha256"]==sha(POLICY),"Protocol changed")
    cases=read(GALLERY/"selection_v1.json")["cases"]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        reports=list(pool.map(render_case,cases))
    body='<h1>Fusion 360 locked qualitative candidates</h1><p>18 cases; original metrics and failures retained. Shape-normalized images remove scale/translation. Reference-world images use a shared frame and explicit CAD-Recode DSL conversion. No new score.</p>'
    for case,report in zip(cases,reports):
        base=GALLERY/"cases"/case["case_id"]
        body+=f'<section><h2>{html.escape(case["slot"]+" "+case["sample_id"])}</h2><p>{html.escape(case["selection_bucket"])}</p>'
        for name in ("case_record.json","archived_asset_paths.json","render_manifest.json"):
            body+=f'<a href="{rel(base/name)}">{name}</a> '
        for series,panel in report["panels"].items():
            body+=f'<h3>{series}</h3><a href="{rel(panel["path"])}"><img loading="lazy" src="{rel(panel["path"])}" alt="Four-method two-view comparison"></a>'
        body+='</section>'
    text_new(GALLERY/"index.html",'<!doctype html><html lang="en"><meta charset="utf-8"><title>Fusion 360 gallery v1</title><style>body{font:16px Arial;max-width:1380px;margin:24px auto;padding:12px;color:#20303a;line-height:1.5}img{max-width:100%;height:auto}section{border-top:1px solid #ddd;margin-top:28px}a{color:#086b6a;margin-right:16px}</style><body>'+body+'</body></html>\n')
    for placement in ("main","appendix"):
        subset=[(c,r) for c,r in zip(cases,reports) if c["placement"]==placement]
        for series in ("metric_space","reference_world"):
            # Contact sheets are review conveniences; full-resolution individual views stay separate.
            thumb_w,thumb_h=670,465
            sheet=Image.new("RGB",(thumb_w*2,thumb_h*math.ceil(len(subset)/2)),"white")
            for i,(case,report) in enumerate(subset):
                with Image.open(report["panels"][series]["path"]) as image:
                    sheet.paste(image.resize((thumb_w,thumb_h),Image.Resampling.LANCZOS),((i%2)*thumb_w,(i//2)*thumb_h))
            sheet.save(GALLERY/f"{placement}_{series}_contact.png")
    write_new(GALLERY/"render_actuals_v1.json",{"status":"DUAL_SERIES_RENDERING_COMPLETE_SEMANTIC_REVIEW_PENDING", "cases":len(cases),
        "method_slots":len(cases)*4,"views_including_explicit_placeholders":len(cases)*16,
        "geometry_views":sum(not r["placeholder"] for report in reports for r in report["renders"]),
        "placeholder_views":sum(r["placeholder"] for report in reports for r in report["renders"]),
        "subpixel_warnings":sum(r.get("subpixel_warning",False) for report in reports for r in report["renders"]),
        "panels":len(cases)*2,"all_raw_meshes_and_transforms_retained":True,
        "new_training_prediction_execution_scoring":False})


if __name__=="__main__":
    main()
