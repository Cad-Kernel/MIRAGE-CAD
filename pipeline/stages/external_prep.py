"""Turn Fusion 360 Gallery into queries the MIRAGE-CAD pipeline can consume.

Two modes, because the archive's layout and units have to be checked before anything is
written:

    inventory   scan and report -- file pairing, naming convention, unit scale against
                the corpus, complexity -- and write nothing
    build       sample reference clouds, emit the query manifest, calibrate the metrics

REFERENCE CLOUDS COME FROM .obj, SAMPLED HERE. Not because Flluma cannot do it -- its C++ can,
via Core::CADAsset::ImportFromSTEP into PointCloudExporter, which samples
TopoDS_Face -> UV -> BRepAdaptor_Surface::D1 and handles cylinders and fillets better than
the estimator below. The gap is a missing PYTHON BINDING: occt_file_brep_features imports a
STEP but returns a dict, export_asset_to_pointcloud wants an Asset, and no py::class_ ever
exposes one, so the two halves cannot be joined from Python.
(scratch/occt_file_to_pointcloud.patch.cpp closes it in ~40 lines and a rebuild.) Fusion 360 ships .obj beside every
.step, so the reference geometry is the dataset's own triangulation of its own B-Rep --
which does not pass through our kernel at all, and is the more faithful ground truth for
that reason. The cost is that reference clouds are sampled here and generated clouds by
Flluma; that difference is systematic across every arm and so cannot move the A-vs-B
contrast, but it is stated in the paper rather than assumed away.

THE UNIT TRAP. Fusion 360's API works in centimetres, FllumaOne in millimetres. The STEP
descriptor the encoder reads carries bbox extents, area and volume under log1p, so a
ten-fold scale error does not rescale the input -- it moves it somewhere the encoder was
never trained, and the STEP arm would fail for a reason unrelated to cross-source
generalisation. Inventory prints both distributions side by side; --scale applies a
correction, and the manifest records it.

    python training_25k/scripts/external_prep.py --root <dir> --output-dir <dir> \\
        --mode inventory|build [--limit 500] [--point-count 8192] [--scale 10.0]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import statistics
import sys
from collections import Counter
from pathlib import Path

import numpy as np

SEED = 20260810


# --------------------------------------------------------------------- obj I/O
def read_obj(path: Path) -> tuple[np.ndarray, np.ndarray] | None:
    """Return (vertices, triangles). Polygons are fanned; only v/f lines are read."""
    verts: list[tuple[float, float, float]] = []
    tris: list[tuple[int, int, int]] = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if line.startswith("v "):
                    p = line.split()
                    verts.append((float(p[1]), float(p[2]), float(p[3])))
                elif line.startswith("f "):
                    # "f v", "f v/vt", "f v//vn", "f v/vt/vn"; OBJ indices are 1-based
                    idx = [int(tok.split("/")[0]) for tok in line.split()[1:]]
                    idx = [i - 1 if i > 0 else len(verts) + i for i in idx]
                    for k in range(1, len(idx) - 1):
                        tris.append((idx[0], idx[k], idx[k + 1]))
    except (OSError, ValueError, IndexError):
        return None
    if len(verts) < 3 or not tris:
        return None
    return np.asarray(verts, dtype=np.float64), np.asarray(tris, dtype=np.int64)


def sample_surface(v: np.ndarray, f: np.ndarray, n: int, seed: int) -> np.ndarray:
    """Area-weighted uniform surface sampling -- the standard estimator, no dependency.

    Triangles are chosen with probability proportional to area, then a point is drawn
    uniformly inside each via the square-root barycentric transform. Sampling uniformly
    over TRIANGLES instead would over-represent dense regions of the tessellation, which
    on a CAD mesh means small fillet faces dominate the cloud.
    """
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    areas = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    total = areas.sum()
    if not np.isfinite(total) or total <= 0:
        return np.empty((0, 3))
    rng = np.random.RandomState(seed)
    pick = rng.choice(len(f), size=n, p=areas / total)
    u = rng.random_sample((n, 1))
    w = rng.random_sample((n, 1))
    su = np.sqrt(u)
    return ((1 - su) * a[pick] + su * (1 - w) * b[pick] + su * w * c[pick])


def bbox_diag(p: np.ndarray) -> float:
    return float(np.linalg.norm(p.max(0) - p.min(0)))


# ----------------------------------------------------------------- inventory
def find_pairs(root: Path) -> list[tuple[str, Path, Path]]:
    """Every .obj with a same-stem .step beside it, keyed by stem."""
    pairs = []
    for obj in root.rglob("*.obj"):
        step = obj.with_suffix(".step")
        if step.is_file():
            pairs.append((obj.stem, step, obj))
    return sorted(pairs)


def final_only(pairs: list[tuple[str, Path, Path]]) -> list[tuple[str, Path, Path]]:
    """Keep one model per design.

    Fusion 360's reconstruction sequences emit a file per extrude, named
    <design>_<index>. Scoring intermediates would count partial solids as targets, so the
    highest index per design wins. Stems without that shape are passed through unchanged.
    """
    groups: dict[str, list[tuple[str, Path, Path]]] = {}
    for stem, step, obj in pairs:
        base, _, tail = stem.rpartition("_")
        key = base if (base and tail.isdigit()) else stem
        groups.setdefault(key, []).append((stem, step, obj))

    out = []
    for key, items in groups.items():
        if len(items) == 1:
            out.append(items[0])
            continue
        def order(it):
            _, _, tail = it[0].rpartition("_")
            return int(tail) if tail.isdigit() else -1
        out.append(max(items, key=order))
    return sorted(out)


def corpus_bbox_sample(n: int = 200) -> list[float]:
    """Bbox diagonals from the corpus, for the units comparison."""
    test = Path.home() / "workspace/MIRAGE/src/data/25k/test.jsonl"
    if not test.is_file():
        test = Path("data/25k/test.jsonl")
    if not test.is_file():
        return []
    out = []
    for i, line in enumerate(test.read_text(encoding="utf-8").splitlines()):
        if i >= n or not line.strip():
            break
        f = Path(json.loads(line).get("point_path", ""))
        if not f.is_file():
            continue
        try:
            d = np.load(f)
            k = "points" if "points" in d else list(d.keys())[0]
            out.append(bbox_diag(np.asarray(d[k], dtype=np.float64)))
        except Exception:
            continue
    return out


def inventory(root: Path, limit: int) -> int:
    pairs = find_pairs(root)
    print(f"=== {root} ===")
    print(f"  .obj with a matching .step: {len(pairs)}")
    if not pairs:
        print("  ** none found. Is the archive extracted, and does it contain the")
        print("     reconstruction subset rather than only its documentation? **")
        return 1

    finals = final_only(pairs)
    print(f"  after keeping one per design:  {len(finals)}"
          f"   ({len(pairs) - len(finals)} intermediates dropped)")

    ext = Path(pairs[0][2]).parent
    print(f"  example directory: {ext}")
    print(f"  example stems: {', '.join(s for s, _, _ in pairs[:4])}")

    print("\n=== geometry, first 60 finals ===")
    diags, tri_counts, bad = [], [], 0
    for stem, _, obj in finals[:60]:
        m = read_obj(obj)
        if m is None:
            bad += 1
            continue
        v, f = m
        diags.append(bbox_diag(v))
        tri_counts.append(len(f))
    if not diags:
        print("  ** no readable .obj **")
        return 1
    print(f"  unreadable: {bad}")
    print(f"  triangles   median {statistics.median(tri_counts):.0f}   "
          f"min {min(tri_counts)}   max {max(tri_counts)}")
    print(f"  bbox diag   median {statistics.median(diags):.4g}   "
          f"p10 {sorted(diags)[len(diags)//10]:.4g}   p90 {sorted(diags)[9*len(diags)//10]:.4g}")

    print("\n=== THE UNIT CHECK ===")
    corpus = corpus_bbox_sample()
    if not corpus:
        print("  could not read corpus point clouds; compare manually before building")
    else:
        cm, em = statistics.median(corpus), statistics.median(diags)
        print(f"  corpus   bbox diag median {cm:.4g}   (FllumaOne, millimetres)")
        print(f"  external bbox diag median {em:.4g}")
        ratio = cm / em if em else float("nan")
        print(f"  ratio corpus/external = {ratio:.3g}")
        if 0.5 < ratio < 2:
            print("  -> comparable; no --scale needed")
        elif 5 < ratio < 20:
            print(f"  -> external looks ~{ratio:.0f}x smaller. Fusion 360 works in")
            print(f"     CENTIMETRES; pass --scale {round(ratio)} so the STEP descriptors")
            print("     land where the encoder was trained.")
        else:
            print("  -> scales differ by an unexpected factor. Do not guess a correction;")
            print("     find out why before building.")

    print(f"\n=== would build {min(limit, len(finals))} of {len(finals)} ===")
    print("  nothing written. Re-run with --mode build when the above looks right.")
    print("\n  One thing this cannot check from WSL: whether Flluma can import a .obj")
    print("  (OBJImporter exists in its source, unlike the STEP path which failed). If it")
    print("  can, reference and generated clouds could share a sampler. Worth one probe")
    print("  against a file listed above, but the numpy sampler below does not need it.")
    return 0


# --------------------------------------------------------------------- build
def build(root: Path, out_dir: Path, limit: int, point_count: int, scale: float) -> int:
    finals = final_only(find_pairs(root))
    if not finals:
        print("no .step/.obj pairs found", file=sys.stderr)
        return 1
    rng = random.Random(SEED)
    rng.shuffle(finals)

    cloud_dir = out_dir / "clouds"
    cloud_dir.mkdir(parents=True, exist_ok=True)
    rows, skipped = [], Counter()

    for stem, step, obj in finals:
        if len(rows) >= limit:
            break
        m = read_obj(obj)
        if m is None:
            skipped["unreadable obj"] += 1
            continue
        v, f = m
        if len(f) < 4:
            skipped["degenerate mesh"] += 1
            continue
        pts = sample_surface(v, f, point_count, SEED)
        if len(pts) < point_count:
            skipped["sampling failed"] += 1
            continue
        if scale != 1.0:
            pts = pts * scale
        d = bbox_diag(pts)
        if not (math.isfinite(d) and d > 1e-6):
            skipped["degenerate bbox"] += 1
            continue

        npz = cloud_dir / f"{stem}.npz"
        np.savez_compressed(npz, points=pts.astype(np.float32))
        rows.append({
            "sample_id": f"f360_{stem}",
            "source_dataset": "fusion360_gallery_r1.0.1",
            "external_id": stem,
            "step_path": str(step),
            "point_path": str(npz),
            "bbox_diag": d,
            "n_triangles": int(len(f)),
            "scale_applied": scale,
        })

    manifest = out_dir / "queries.jsonl"
    manifest.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                        encoding="utf-8")
    print(f"wrote {len(rows)} queries -> {manifest}")
    for k, n in skipped.most_common():
        print(f"  skipped {n}: {k}")

    (out_dir / "run_metadata.json").write_text(json.dumps({
        "source": str(root),
        "dataset": "Fusion 360 Gallery reconstruction r1.0.1",
        "n": len(rows),
        "point_count": point_count,
        "scale_applied": scale,
        "seed": SEED,
        "reference_clouds": "area-weighted surface sampling of the dataset's own .obj, "
                            "in numpy -- Flluma cannot import a STEP into anything it will "
                            "sample (see scratch/probe_step_import.txt)",
        "caveat": "reference clouds and generated clouds come from different samplers; "
                  "systematic across all arms, so it cannot move the A-vs-B contrast, "
                  "but it must be stated",
    }, indent=2), encoding="utf-8")

    calibrate(rows, point_count)
    return 0


# ---------------------------------------------------------------- calibration
def calibrate(rows: list[dict], point_count: int) -> None:
    """What can the geometry metrics express on THIS set?

    Same method as docs SS9.15: two disjoint halves of one reference cloud differ only by
    sampling, so whatever they score bounds a perfect reconstruction. The internal ceiling
    of 0.244 was measured at 1,024 points on FllumaOne parts and does not transfer -- both
    the density and the part sizes differ.
    """
    if not rows:
        return
    half = point_count // 2
    rng = np.random.RandomState(SEED)
    f_at, cds, spacings = {0.01: [], 0.02: [], 0.05: []}, [], []

    for r in rows[:200]:
        try:
            d = np.load(r["point_path"])
            pts = np.asarray(d["points"], dtype=np.float64)
        except Exception:
            continue
        if len(pts) < 2 * half:
            continue
        idx = rng.permutation(len(pts))
        A, B = pts[idx[:half]], pts[idx[half:2 * half]]
        dAB = np.sqrt(((A[:, None, :] - B[None, :, :]) ** 2).sum(-1).min(1))
        dBA = np.sqrt(((B[:, None, :] - A[None, :, :]) ** 2).sum(-1).min(1))
        diag = r["bbox_diag"]
        cds.append(0.5 * (dAB ** 2).mean() + 0.5 * (dBA ** 2).mean())
        spacings.append(float(np.median(dAB)))
        for t in f_at:
            thr = t * diag
            p, rc = float((dAB < thr).mean()), float((dBA < thr).mean())
            f_at[t].append(0.0 if p + rc == 0 else 2 * p * rc / (p + rc))

    if not cds:
        print("\ncalibration: no usable clouds")
        return
    print(f"\n=== metric calibration on this external set ({len(cds)} parts, "
          f"{half} points per side) ===")
    print(f"  median nearest-neighbour spacing  {statistics.median(spacings):.4g}")
    print(f"  median bbox diagonal              {statistics.median(r['bbox_diag'] for r in rows[:200]):.4g}")
    for t in sorted(f_at):
        v = f_at[t]
        print(f"  F@{100*t:.0f}% ceiling   median {statistics.median(v):.3f}   "
              f"mean {statistics.fmean(v):.3f}")
    print(f"  Chamfer noise floor  median {statistics.median(cds):.4g}")
    print("\n  Quote these beside any external geometry figure. The internal ceiling of")
    print("  0.244 and floor of 1.963 mm^2 were measured at 1,024 points on FllumaOne")
    print("  parts and do not transfer to this set.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--mode", choices=["inventory", "build"], default="inventory")
    ap.add_argument("--limit", type=int, default=500)
    ap.add_argument("--point-count", type=int, default=8192)
    ap.add_argument("--scale", type=float, default=float(os.environ.get("EXT_SCALE", 1.0)),
                    help="multiply sampled coordinates; see the unit check in inventory")
    args = ap.parse_args()

    if args.mode == "inventory":
        return inventory(args.root, args.limit)
    return build(args.root, args.output_dir, args.limit, args.point_count, args.scale)


if __name__ == "__main__":
    raise SystemExit(main())
