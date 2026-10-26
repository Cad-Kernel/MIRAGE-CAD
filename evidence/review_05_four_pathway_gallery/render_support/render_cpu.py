"""Reference-framed orthographic adapter around Flluma's proven CPU rasterizer."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import importlib.util
import math
import textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from render_common import *

RASTER_PATH = NATIVE / "python/flluma/api/image_export.py"
spec = importlib.util.spec_from_file_location("flluma_software_rasterizer", RASTER_PATH)
RASTER = importlib.util.module_from_spec(spec)
spec.loader.exec_module(RASTER)


def font(size, mono=False):
    p = Path("C:/Windows/Fonts") / ("consola.ttf" if mono else "arial.ttf")
    return ImageFont.truetype(str(p), size) if p.exists() else ImageFont.load_default(size=size)


def camera_for(points, view, size, kind="reference_frame"):
    direction = np.asarray(RASTER._spherical_direction(view["azimuth"], view["elevation"]))
    right = np.asarray(RASTER._normalize(RASTER._cross((0, 0, 1), direction)))
    up = np.cross(direction, right)
    center = (points.min(axis=0) + points.max(axis=0)) / 2
    basis = np.stack([right, up, direction], axis=1)
    projected = (points - center) @ basis
    lo, hi = projected[:, :2].min(axis=0), projected[:, :2].max(axis=0)
    span = max(float(np.max(hi - lo)), 1e-9)
    return {"frame": kind, "view": view, "center": center.tolist(), "basis": basis.tolist(),
        "projected_midpoint": ((lo + hi) / 2).tolist(), "span_mm": span,
        "pixels_per_mm": size * .82 / span, "size": size}


def project(points, camera):
    p = (points - np.asarray(camera["center"])) @ np.asarray(camera["basis"])
    s = camera["pixels_per_mm"]
    mid = camera["projected_midpoint"]
    return np.column_stack(((p[:, 0] - mid[0]) * s + camera["size"] / 2,
        camera["size"] / 2 - (p[:, 1] - mid[1]) * s, p[:, 2]))


def render_mesh(vertices, faces, camera, path, config):
    size = config["size"]
    screen_array = project(vertices, camera)
    screen = [tuple(v) for v in screen_array]
    triangles = [tuple(int(i) for i in tri) for tri in faces]
    n = np.cross(vertices[faces[:,1]] - vertices[faces[:,0]], vertices[faces[:,2]] - vertices[faces[:,0]])
    norms = np.linalg.norm(n, axis=1)
    n /= np.maximum(norms[:,None], 1e-30)
    direction = np.asarray(camera["basis"])[:,2]
    lighting_normals = n.copy()
    lighting_normals[(lighting_normals @ direction) < 0] *= -1
    light = np.asarray(RASTER._normalize(tuple(direction + [.25, -.35, .65])))
    shades = .30 + .68 * np.maximum(0, lighting_normals @ light)
    colors = np.clip(shades[:,None] * config["body_color"], 0, 255).astype(int)
    bg = tuple(config["background"])
    pixels = [list(bg) for _ in range(size * size)]
    depth = [-1e300] * (size * size)
    for i in np.argsort(screen_array[faces, 2].mean(axis=1), kind="stable"):
        a, b, c = triangles[i]
        RASTER._raster_triangle(screen[a], screen[b], screen[c], tuple(colors[i]), pixels, depth, size, size)
    edges = RASTER._visible_feature_edges(triangles, [tuple(v) for v in n],
        view_dir=tuple(direction), edge_angle_degrees=config["edge_angle_degrees"])
    epsilon = max(float(np.ptp(screen_array[:,2])), camera["span_mm"]) * .004
    for a, b in edges:
        RASTER._draw_line_depth(screen[a], screen[b], tuple(config["edge_color"]), pixels,
            depth, size, size, depth_epsilon=epsilon)
    arr = np.asarray(pixels, dtype=np.uint8).reshape(size, size, 3)
    mask = np.any(arr != bg, axis=2)
    yy, xx = np.where(mask)
    outside = ((screen_array[:,0] < 0) | (screen_array[:,0] >= size) |
        (screen_array[:,1] < 0) | (screen_array[:,1] >= size))
    require(not path.exists(), f"Image exists: {path}")
    Image.fromarray(arr).save(path)
    return {"image": artifact(path), "camera": camera, "width": size, "height": size,
        "foreground_pixels": int(mask.sum()), "out_of_frame_vertices": int(outside.sum()),
        "mesh_vertex_count": len(vertices), "border_foreground_pixels": int(mask[0].sum()+mask[-1].sum()+mask[:,0].sum()+mask[:,-1].sum()),
        "foreground_bbox_px": [int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())] if len(xx) else None,
        "blank": not bool(mask.any())}


def make_panel(row, report, base):
    width, margin, thumb = 1340, 20, 640
    panel = Image.new("RGB", (width, 1490), "white")
    draw = ImageDraw.Draw(panel)
    title = f"{row['modality'].upper()} | {row['sample_id']} | {row['case_type']} | {row['complexity_tier']}"
    draw.text((margin, 14), title, fill=(20,30,40), font=font(24))
    metric = f"Historical: Build={row['build_ok']} | Scoreable={row['scoreable']}"
    if row["scoreable"]:
        metric += f" | CD={row['cd']:.4g} | F@1={row['f1_at_1_fraction']*100:.3f}%"
    draw.text((margin, 50), metric, fill=(50,60,70), font=font(19))
    draw.text((margin, 79), "Locked legacy repaired B2; CPU re-export. Same reference-derived camera and scale in each column.", fill=(50,60,70), font=font(17))
    refs = [r for r in report["renders"] if r["kind"] == "reference" and r["camera"]["frame"] == "reference_frame"]
    preds = [r for r in report["renders"] if r["kind"] == "prediction" and r["camera"]["frame"] == "reference_frame"]
    for i in range(2):
        x = margin + i * (thumb + 20)
        draw.text((x, 109), f"Reference | {['+X+Y+Z', '-X-Y+Z'][i]}", fill=(25,40,50), font=font(19))
        with Image.open(ROOT / refs[i]["image"]["path"]) as im:
            panel.paste(im, (x, 138))
        draw.text((x, 788), "Prediction" if preds else "Prediction: historical execution failure", fill=(25,40,50), font=font(19))
        if preds:
            with Image.open(ROOT / preds[i]["image"]["path"]) as im:
                panel.paste(im, (x, 817))
        else:
            draw.rectangle((x,817,x+thumb-1,1456), fill=(249,246,246))
            error = (ROOT / row["failure_log_path"]).read_text(encoding="utf-8")
            lines = textwrap.wrap(error, width=65, break_long_words=True)
            y = 850
            for line in ["NO PREDICTED SOLID", "Original native error evidence:", ""] + lines[:14]:
                draw.text((x+22,y),line,fill=(120,40,40),font=font(16,True))
                y += 25
    if report["supplemental_union_frame"]:
        draw.rectangle((15,1459,width-15,1488),fill=(255,241,204))
        draw.text((24,1462),"Prediction exceeds target frame. Additional shared union-frame views are retained; geometry is not resized independently.",fill=(90,65,10),font=font(16))
    else:
        draw.text((margin,1463),"Candidate preview, not a semantic-success claim. Original plan, code, metrics and errors remain linked in index.html.",fill=(80,90,100),font=font(16))
    target = base / "panel.png"
    require(not target.exists(), "No panel overwrite")
    panel.save(target)
    return artifact(target)


def render_case(key):
    row = read(ROOT / "cases" / key / "case.json")
    protocol = read(OUT / "render_protocol.json")
    job = next(j for j in protocol["jobs"] if j["case_id"] == key)
    base = local_path(job["output_dir"])
    result_path = base / "render_manifest.json"
    if result_path.exists():
        previous = read(result_path)
        for r in previous["renders"]:
            require(sha(ROOT / r["image"]["path"]) == r["image"]["sha256"], "Existing render drift")
        require(sha(ROOT / previous["panel"]["path"]) == previous["panel"]["sha256"], "Existing panel drift")
        return key + " verified existing renders"
    meshes = {}
    for kind in ("reference", "prediction") if row["scoreable"] else ("reference",):
        m = read(base / (kind + "_mesh.json"))
        path = ROOT / m["mesh"]["path"]
        require(sha(path) == m["mesh"]["sha256"], "Mesh hash drift")
        with np.load(path, allow_pickle=False) as archive:
            meshes[kind] = (archive["vertices"], archive["faces"])
    report = {"case_id": key, "created_utc": utc(), "status": "RENDERED_CANDIDATE_NOT_FINAL_SELECTION",
        "renders": [], "historical_scoreable": row["scoreable"], "supplemental_union_frame": False,
        "protocol_sha256": sha(OUT / "render_protocol.json"), "adapter_sha256": sha(__file__),
        "rasterizer_path": str(RASTER_PATH), "rasterizer_sha256": sha(RASTER_PATH),
        "failure_evidence_path": row["failure_log_path"], "metrics": "unchanged historical values in locked case.json"}
    for view in protocol["camera"]["views"]:
        camera = camera_for(meshes["reference"][0], view, protocol["image"]["size"])
        clipped = False
        for kind, (vertices, faces) in meshes.items():
            path = base / f"{kind}_{view['name']}.png"
            r = render_mesh(vertices, faces, camera, path, protocol["image"])
            r["kind"] = kind
            report["renders"].append(r)
            require(kind != "reference" or (not r["blank"] and r["out_of_frame_vertices"] == 0), "Reference framing failed")
            clipped |= kind == "prediction" and (r["out_of_frame_vertices"] > 0 or r["blank"])
        if clipped:
            report["supplemental_union_frame"] = True
            union = np.concatenate([item[0] for item in meshes.values()])
            joint = camera_for(union, view, protocol["image"]["size"], "supplemental_shared_union_frame")
            for kind, (vertices, faces) in meshes.items():
                path = base / f"{kind}_{view['name']}_shared_union.png"
                r = render_mesh(vertices, faces, joint, path, protocol["image"])
                r["kind"] = kind
                require(not r["blank"] and r["out_of_frame_vertices"] == 0, "Joint-frame rendering failed")
                report["renders"].append(r)
    report["panel"] = make_panel(row, report, base)
    write_new(result_path, report)
    return key + f" rendered ({len(report['renders'])} views)"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-id")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    verify_original_lock()
    keys = [c["case_id"] for c in cases() if not args.case_id or c["case_id"] == args.case_id]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for result in pool.map(render_case, keys):
            print(result, flush=True)


if __name__ == "__main__":
    main()
