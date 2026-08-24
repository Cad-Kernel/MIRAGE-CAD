"""Freeze the STEP -> mesh protocol, and prove the mesh is deterministic. No model, no checkpoint.

RUNS IN cadrecode_env. This is the last step before anything is downloaded, because both the IoU
metric and CAD-Recode's own input pipeline are built on the mesh this produces: its recipe
mesh -> 8192 surface samples -> farthest-point downsample to 256 starts from a mesh, and a mesh
that varies between calls would put noise into the model's input as well as into the metric.

WHY THE TOLERANCES ARE NOT A NEW CHOICE. linear 0.05 mm and angular 0.3 rad are the values
occt_file_to_pointcloud used for all 400 external Fusion360 clouds, left at library defaults by
external_prep.py. CadQuery's Shape.tessellate takes exactly those two quantities, so reusing the
numbers keeps the mesh tessellation numerically aligned with the sampling tessellation already in
the manuscript. The paper can say the external experiment reused the configuration that produced
its existing external data rather than picking a tolerance after seeing results.

WHAT IS FROZEN HERE, and every field is recorded whether or not the API exposes a knob for it,
because this stack is now a protocol component rather than a dependency: linear deflection, angular
deflection, whether the tolerance is absolute or relative, mesh cleaning, how multi-solid documents
are handled, and whether sewing or healing runs. A library default left unrecorded is not
acceptable when the same number feeds both the model input and the metric.

THE SELF-TESTS ARE THE POINT, not the report. Determinism, the normalisation contract the evaluator
assumes, and IoU(self) = 1 with CD(self) = the sampling floor. Discipline copied from pinning the
Chamfer formula at a hand-computed 1520: a known answer beats a plausible one.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

# FROZEN BY CONVERGENCE CALIBRATION, not by provenance. See the results log: an absolute
# tolerance was retired because it imports one method's scale convention into a comparison between
# methods, and across parts spanning 1.6 mm to 5 m the same millimetre figure is a completely
# different fidelity. The resolution is dimensionless:
#
#     linear_deflection = ALPHA * L,   L = the shape's largest bbox extent
#
# ALPHA = 1e-6 is the cost/accuracy knee over 20 held-out Fusion360 parts. Strict convergence was
# NOT attained at practical levels and is not claimed: against the ten-times-finer alpha = 1e-7
# reference the residual is a median absolute IoU deviation of 2.5e-5 and a 95th percentile of
# 3.73e-4, with CD within the independently measured sampling floor for 18 of 19 valid parts.
ALPHA = 1e-6
ANGULAR_DEFLECTION = 0.3
# Retained only so older reports remain readable; the operator no longer uses it.
LINEAR_DEFLECTION_LEGACY_ABSOLUTE = 0.05
N_SURFACE_POINTS = 8192
CD_SPACING_CONST = 2543.0   # floor ~ k * spacing^2, k measured in 10.12 across two samplers


def tessellate_step(path: str, alpha: float = ALPHA,
                    angular: float = ANGULAR_DEFLECTION, linear: float | None = None):
    """STEP -> (vertices, triangles). The canonical operator for the external comparison.

    The linear tolerance is RELATIVE: alpha * L, where L is the largest bbox extent over all
    solids in the document. Pass `linear` only to reproduce a pre-calibration artefact.
    """
    import cadquery as cq
    shape = cq.importers.importStep(str(path))
    solids = shape.vals()
    if not solids:
        raise ValueError("no solids in the STEP")
    if linear is None:
        L = 0.0
        for sd in solids:
            b = sd.BoundingBox()
            L = max(L, float(max(b.xlen, b.ylen, b.zlen)))
        linear = alpha * L
    # Multi-solid documents: tessellate every solid and concatenate, rather than silently keeping
    # the first. Fusion360 reconstruction models are usually single-solid, but "usually" is not a
    # protocol.
    verts, tris = [], []
    for s in solids:
        v, f = s.tessellate(linear, angular)
        off = len(verts)
        verts.extend([(p.x, p.y, p.z) for p in v])
        tris.extend([(a + off, b + off, c + off) for a, b, c in f])
    return np.asarray(verts, dtype=np.float64), np.asarray(tris, dtype=np.int64)


def to_trimesh(verts, tris, merge: bool = True):
    """OCP triangles -> trimesh, merging coincident vertices but changing no geometry.

    OCP emits vertices per face, so a box arrives with 24 of them for its 8 corners and adjacent
    triangles share none. Left unmerged the mesh is not manifold, no boolean engine will run on it,
    and IoU is unavailable. Merging identifies vertices that already occupy identical coordinates:
    connectivity changes, geometry does not. Everything that WOULD move geometry -- degenerate-face
    removal, normal repair, hole filling, smoothing -- stays off, which is what process=False buys.
    """
    import trimesh
    m = trimesh.Trimesh(vertices=verts, faces=tris, process=False)
    if merge:
        m.merge_vertices()
    return m


def report_protocol() -> dict:
    """Everything a later reader needs to reproduce this mesh, including what is not exposed."""
    import cadquery as cq
    fields = {
        "tessellator": "cadquery.Shape.tessellate (OCP / OpenCASCADE)",
        "cadquery_version": getattr(cq, "__version__", "unknown"),
        "alpha_relative_linear": ALPHA,
        "angular_deflection_rad": ANGULAR_DEFLECTION,
        "deflection_mode": "RELATIVE: linear_deflection = alpha * largest bbox extent. "
                           "cadquery.Shape.tessellate takes an absolute tolerance, so the "
                           "relative figure is converted per shape rather than being a library "
                           "option",
        "convergence_status": "residual tessellation sensitivity QUANTIFIED, not eliminated. "
                              "Strict convergence was not attained at practical levels: against "
                              "the ten-times-finer alpha=1e-7 reference the median absolute IoU "
                              "deviation is 2.5e-5 and the 95th percentile 3.73e-4, over 20 "
                              "held-out Fusion360 parts, with CD within the independently "
                              "measured sampling floor for 18 of 19 valid parts",
        "iou_reporting_contract": "IoU and CD may have different denominators. Every table states "
                                  "its metric-specific n, and evaluator failures are reported "
                                  "separately rather than silently discarded: on the calibration "
                                  "set 2 of 20 parts could not produce a usable IoU -- one "
                                  "boolean failed outright, one self-IoU was off by 3.7e-2",
        "mesh_topology_repair": "coincident vertices are merged (trimesh merge_vertices). OCP "
                                "emits vertices per face, so a box arrives with 24 for its 8 "
                                "corners; unmerged the mesh is non-manifold and no boolean engine "
                                "runs, so IoU is unavailable. Merging changes connectivity only "
                                "-- the vertices already share coordinates -- and the probe checks "
                                "that area, volume and the CD floor are unchanged by it",
        "mesh_geometric_cleaning": "none. process=False, so no degenerate-face removal, no normal "
                                   "repair, no hole filling, no smoothing. Anything that could "
                                   "MOVE geometry stays off; the surface scored is the surface "
                                   "OCCT produced",
        "multi_solid_handling": "every solid tessellated and concatenated, offsets applied; the "
                                "first solid is not silently taken",
        "sewing_or_healing": "none requested",
        "tolerance_provenance": "chosen by a convergence calibration over 20 held-out Fusion360 "
                                "parts, frozen before the model comparison. The earlier "
                                "justification -- reusing the absolute 0.05 mm that "
                                "occt_file_to_pointcloud used for all 400 clouds -- was retired: "
                                "CAD-Recode's demo tessellates predictions at 0.001 on a ~200-unit "
                                "shape, about 5e-6 relative against our 5.2e-4, so the numbers "
                                "were never the same fidelity",
    }
    try:
        import OCP
        fields["ocp_version"] = getattr(OCP, "__version__", "present, no __version__")
    except Exception as e:
        fields["ocp_version"] = f"unavailable: {type(e).__name__}"
    return fields


# ---------------------------------------------------------------------------
# self-tests
# ---------------------------------------------------------------------------
def make_reference_step(td: str) -> str:
    """A STEP of known geometry, so the checks have arithmetic answers and need no dataset."""
    import cadquery as cq
    p = os.path.join(td, "ref.step")
    cq.exporters.export(cq.Workplane("XY").box(2.0, 1.0, 0.5), p)
    return p


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--step", default=None,
                    help="a real STEP to check as well; a synthetic box is always checked")
    ap.add_argument("--steps-from", default=None,
                    help="queries.jsonl; runs a self-IoU distribution over --n-steps of its parts, "
                         "which is what would turn 'error on one part' into 'numerical floor'")
    ap.add_argument("--n-steps", type=int, default=20)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    results: list[tuple[str, bool, str]] = []
    protocol = report_protocol()

    print("=" * 78)
    print("STEP -> mesh protocol, frozen and checked")
    print("=" * 78)
    for k, v in protocol.items():
        print(f"  {k:24s} {v}")
    print()

    from external_geometry_eval import (chamfer_x1000, iou_meshes,  # noqa: E402
                                        normalise_per_shape, sample_surface)

    with tempfile.TemporaryDirectory() as td:
        cases = [("synthetic box 2x1x0.5", make_reference_step(td))]
        if args.step and os.path.exists(args.step):
            cases.append(("supplied STEP", args.step))

        for label, path in cases:
            print(f"--- {label} ---")
            try:
                v1, f1 = tessellate_step(path)
                v2, f2 = tessellate_step(path)
            except Exception as e:
                results.append((f"{label}: tessellate", False, f"{type(e).__name__}: {e}"))
                print(f"  [FAIL] tessellate: {type(e).__name__}: {e}\n")
                continue

            same = (v1.shape == v2.shape and f1.shape == f2.shape
                    and np.array_equal(v1, v2) and np.array_equal(f1, f2))
            results.append((f"{label}: tessellation is deterministic", same,
                            f"{len(v1)} vertices, {len(f1)} triangles; "
                            f"second call {'identical' if same else 'DIFFERS'}"))

            raw = to_trimesh(v1, f1, merge=False)
            m = to_trimesh(v1, f1, merge=True)
            results.append((f"{label}: merging makes the mesh watertight", bool(m.is_watertight),
                            f"unmerged watertight={raw.is_watertight} ({len(raw.vertices)} "
                            f"vertices), merged watertight={m.is_watertight} "
                            f"({len(m.vertices)} vertices)"))
            # The claim that merging is purely topological, checked rather than asserted.
            area_ok = math.isclose(float(raw.area), float(m.area), rel_tol=1e-12)
            vol_ok = math.isclose(abs(float(raw.volume)), abs(float(m.volume)), rel_tol=1e-9)
            results.append((f"{label}: merging changes no geometry", area_ok and vol_ok,
                            f"area {float(raw.area):.12f} -> {float(m.area):.12f}, "
                            f"volume {float(raw.volume):.12f} -> {float(m.volume):.12f}"))

            mn = normalise_per_shape(m)
            ext = float(max(mn.extents))
            results.append((f"{label}: normalisation puts max extent at 1.0",
                            math.isclose(ext, 1.0, abs_tol=1e-9),
                            f"max extent {ext:.12f}, bounds "
                            f"{np.round(mn.bounds, 6).tolist()}"))

            iou, st = iou_meshes(mn, normalise_per_shape(to_trimesh(v2, f2, merge=True)))
            results.append((f"{label}: IoU against itself is 1",
                            iou is not None and math.isclose(iou, 1.0, abs_tol=1e-6),
                            f"IoU={iou!r}, status={st}"))

            pa = sample_surface(mn, N_SURFACE_POINTS, 0)
            pb = sample_surface(mn, N_SURFACE_POINTS, 1)
            floor = chamfer_x1000(pa, pb)
            from scipy.spatial import cKDTree
            d, _ = cKDTree(pa).query(pa, k=2)
            spacing = float(np.mean(d[:, 1]))
            pred = CD_SPACING_CONST * spacing * spacing
            ratio = floor / pred if pred > 0 else float("nan")
            results.append((f"{label}: CD against itself matches the predicted floor",
                            0.8 < ratio < 1.25,
                            f"CD {floor:.4f}, predicted {pred:.4f} from spacing "
                            f"{spacing:.6f}, ratio {ratio:.3f}"))

            floor_raw = chamfer_x1000(
                sample_surface(normalise_per_shape(raw), N_SURFACE_POINTS, 0),
                sample_surface(normalise_per_shape(raw), N_SURFACE_POINTS, 1))
            results.append((f"{label}: merging leaves the CD floor unchanged",
                            math.isclose(floor, floor_raw, rel_tol=1e-9),
                            f"merged {floor:.6f}, unmerged {floor_raw:.6f} -- surface sampling "
                            f"runs over triangle positions, which merging does not move"))

            moved = to_trimesh(v1, f1)
            moved.apply_translation((41.0, -7.0, 3.0))
            moved.apply_scale(6.5)
            f_ts = chamfer_x1000(sample_surface(normalise_per_shape(moved), N_SURFACE_POINTS, 0),
                                 sample_surface(mn, N_SURFACE_POINTS, 1))
            results.append((f"{label}: translation+scale reproduces the floor",
                            math.isclose(f_ts, floor, rel_tol=0.02),
                            f"CD {f_ts:.4f} against floor {floor:.4f}"))
            print()

    # ---- optional: the self-IoU distribution that would license the word "floor" ----------
    dist = []
    if args.steps_from and os.path.exists(args.steps_from):
        print(f"--- self-IoU over up to {args.n_steps} parts, for a distribution rather than a "
              f"single point ---")
        rows = []
        with open(args.steps_from, encoding="utf-8-sig") as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line))
        # Spread across the size range on a log axis, as the floor work did: taking the first N
        # would sample one corner of a distribution that spans a factor of thousands.
        cand = [(float(r.get("bbox_diag", 0)), r.get("step_path") or r.get("step_path_wsl"))
                for r in rows]
        cand = [(d, p_) for d, p_ in cand if p_ and os.path.exists(p_) and d > 0]
        cand.sort()
        if cand:
            take = min(args.n_steps, len(cand))
            picked = [cand[int(i * (len(cand) - 1) / max(take - 1, 1))] for i in range(take)]
            for diag, sp in picked:
                try:
                    va, fa = tessellate_step(sp)
                    vb, fb = tessellate_step(sp)
                    i_, st_ = iou_meshes(normalise_per_shape(to_trimesh(va, fa, merge=True)),
                                        normalise_per_shape(to_trimesh(vb, fb, merge=True)))
                    if i_ is not None:
                        dist.append({"diag": diag, "dev": abs(i_ - 1.0), "status": st_})
                except Exception as e:
                    dist.append({"diag": diag, "dev": None,
                                 "status": f"{type(e).__name__}: {e}"})
            devs = [d["dev"] for d in dist if d["dev"] is not None]
            if devs:
                devs.sort()
                results.append(("self-IoU deviation across parts stays below 1e-6",
                                devs[-1] < 1e-6,
                                f"n={len(devs)} parts, min {devs[0]:.3e}, "
                                f"median {devs[len(devs)//2]:.3e}, max {devs[-1]:.3e}. "
                                f"A max at this level is what licenses calling it a numerical "
                                f"floor rather than one measurement."))
        print()

    print("=" * 78)
    failed = 0
    for name, ok, detail in results:
        failed += not ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        print(f"         {detail}")
    print()
    if failed:
        print(f"{failed} check(s) failed. Do not download the checkpoint: this mesh feeds BOTH")
        print("CAD-Recode's input pipeline and the IoU metric, so a non-deterministic or")
        print("non-watertight mesh would put noise into the model's input and the measurement")
        print("at once, and the two would be impossible to separate afterwards.")
    else:
        print("Mesh protocol frozen and verified. The tessellation is deterministic, the")
        print("normalisation contract the evaluator assumes holds, IoU against self is 1, and the")
        print("CD floor matches the constant measured independently in the OCCT calibration.")
        print("Next: download filapro/cad-recode-v1.5 and build its 8192-to-256 FPS input.")

    if args.out:
        Path(args.out).write_text(json.dumps(
            {"protocol": protocol,
             "checks": [{"name": n, "passed": p_, "detail": d} for n, p_, d in results],
             "self_iou_distribution": dist},
            indent=2), encoding="utf-8", newline="\n")
        print(f"\nwrote {args.out}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
