"""Score ONE (sample, arm) through the common evaluator, in its own process. Runs in cadrecode_env.

WHY A SUBPROCESS. The in-process batch was killed by the OOM killer after 15 samples. The cause is
not a leak: MIRAGE's exported STEP tessellates to a median of ~203,000 triangles against ~888 for
CAD-Recode and ~1,994 for the ground truth of the same part, at the identical frozen alpha. A
manifold boolean over a 640,000-triangle non-watertight mesh is what exhausted memory, and in one
process that takes the whole batch down along with every part that had nothing wrong with it.

WHAT THIS DOES NOT DO IS RETUNE ANYTHING. alpha = 1e-6 was frozen before any output was seen and
the CAD-Recode arm is already measured against it; lowering it here to make MIRAGE's meshes fit in
memory would silently change what the protocol means and would invalidate the frozen arm. A part
whose IoU cannot be computed within the memory budget is an evaluator failure -- named, reported,
excluded from IoU's denominator, never recorded as IoU 0. That is the same contract that already
covers the 13 boolean failures on the CAD-Recode side.

CD SURVIVES WHAT IoU DOES NOT. Chamfer needs surface sampling only, which is cheap even at 640,000
triangles; IoU needs a boolean, which is what blows up. In one process an OOM during IoU destroyed
the CD that had already been computed. Here the metrics are written before the process can die on
the next one, so a part can contribute CD and not IoU -- which is exactly why the two metrics have
separate denominators.

IT ALSO RECORDS WHY THE MESH IS LARGE, since that is now a finding rather than an annoyance: the
solid count, face count and per-solid triangle counts of the prediction. The frozen operator
concatenates every solid in the document, so a multi-solid export would explain both the triangle
count and the non-watertightness at once. This is a new diagnostic beside the operator, not a
change to it.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def cap_memory(mb: int) -> str:
    """Fail as a MemoryError we can record, rather than as a kill we can only infer."""
    if mb <= 0:
        return "uncapped"
    try:
        import resource
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        want = mb * 1024 * 1024
        if hard != resource.RLIM_INFINITY:
            want = min(want, hard)
        resource.setrlimit(resource.RLIMIT_AS, (want, hard))
        return f"RLIMIT_AS={mb}MB"
    except Exception as e:                       # noqa: BLE001
        return f"uncapped ({type(e).__name__})"


def step_diagnostics(path: str) -> dict:
    """Solid and face counts for a STEP, to explain mesh size rather than just suffer it."""
    out: dict = {}
    try:
        import cadquery as cq
        from OCP.TopAbs import TopAbs_FACE
        from OCP.TopExp import TopExp_Explorer
        shape = cq.importers.importStep(str(path))
        solids = shape.vals()
        out["n_solids"] = len(solids)
        faces, per_solid = 0, []
        for s in solids:
            n = 0
            exp = TopExp_Explorer(s.wrapped, TopAbs_FACE)
            while exp.More():
                n += 1
                exp.Next()
            per_solid.append(n)
            faces += n
        out["n_faces"] = faces
        out["faces_per_solid"] = per_solid[:20]
        b = solids[0].BoundingBox()
        out["first_solid_bbox"] = [b.xlen, b.ylen, b.zlen]
    except Exception as e:                       # noqa: BLE001
        out["diagnostics_error"] = f"{type(e).__name__}: {e}"
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gt-step", required=True)
    ap.add_argument("--expect-source-sha", required=True)
    ap.add_argument("--expect-mesh-sha", required=True)
    ap.add_argument("--pred-step", required=True)
    ap.add_argument("--sample-id", required=True)
    ap.add_argument("--arm", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mem-mb", type=int, default=8192)
    args = ap.parse_args()

    cap = cap_memory(args.mem_mb)
    man: dict = {"sample_id": args.sample_id, "arm": args.arm, "terminal": False,
                 "memory_cap": cap, "gt_verified": False,
                 "cd_status": None, "iou_status": None,
                 "evaluator": "cadrecode_stage2.evaluate, the identical function and frozen "
                              "alpha = 1e-6 operator used for CAD-Recode",
                 "prediction_step": args.pred_step}

    def save(status: str) -> int:
        man["pipeline_status"] = status
        man["terminal"] = True
        Path(args.out).write_text(json.dumps(man, indent=2, default=str),
                                  encoding="utf-8", newline="\n")
        return 0 if status == "SUCCESS" else 1

    try:
        from cadrecode_stage2 import build_input, evaluate
    except Exception as e:                       # noqa: BLE001
        man["reason"] = f"import failed: {type(e).__name__}: {e}"
        return save("IMPORT_FAILED")

    # ---- ground truth, identity proven against what CAD-Recode was scored on ----
    try:
        inp = build_input(args.gt_step)
        if inp["source_step_sha256"] != args.expect_source_sha:
            raise ValueError("GT STEP file changed since the CAD-Recode run")
        if inp["canonical_mesh_sha256"] != args.expect_mesh_sha:
            raise ValueError("GT mesh is not bit-identical to the one CAD-Recode was scored "
                             "against; the arms would not be paired")
        gt_mesh = inp["_mesh"]
        man["gt_verified"] = True
        man["gt_mesh_triangles"] = inp["mesh_triangle_count"]
    except MemoryError:
        man["reason"] = f"MemoryError building the GT mesh under {cap}"
        return save("GT_OOM")
    except Exception as e:                       # noqa: BLE001
        man["reason"] = f"{type(e).__name__}: {e}"
        return save("GT_UNVERIFIED")

    # ---- why the prediction mesh is the size it is -------------------------
    man["prediction_step_diagnostics"] = step_diagnostics(args.pred_step)

    # ---- the metrics ------------------------------------------------------
    try:
        ev = evaluate(gt_mesh, args.pred_step)
    except MemoryError:
        man["reason"] = (f"MemoryError inside evaluate under {cap}. CD and IoU are both lost for "
                         f"this part; it is an evaluator failure, not a geometry of zero.")
        return save("EVAL_OOM")
    except Exception as e:                       # noqa: BLE001
        man["reason"] = f"{type(e).__name__}: {e}"
        # Classify rather than leave a raw TypeError in the record. `evaluate` normalises the
        # prediction outside a try block, and normalise_per_shape unpacks `mesh.bounds`, which
        # trimesh returns as None for an EMPTY mesh -- so a solid that tessellates to zero
        # triangles crashes there with an unpack error that names nothing. Re-tessellating costs a
        # few seconds and only ever runs on a failure, and it distinguishes "the prediction has no
        # surface" from an unknown fault. `evaluate` itself is left alone: it is the function that
        # produced the frozen CAD-Recode arm, and this path never fired for any of those 392.
        try:
            from probe_cadrecode_mesh import tessellate_step, to_trimesh
            v, f = tessellate_step(args.pred_step)
            mesh = to_trimesh(v, f, merge=True)
            man["pred_mesh_triangles_on_failure"] = int(len(mesh.faces))
            man["pred_mesh_vertices_on_failure"] = int(len(mesh.vertices))
            if len(mesh.faces) == 0 or mesh.bounds is None:
                man["reason"] = ("the prediction STEP tessellates to an EMPTY mesh (0 triangles), "
                                 "so it has no surface to sample or intersect. Flluma reported "
                                 "build_ok, solid_valid and step_export_ok for it.")
                return save("EMPTY_PREDICTION_MESH")
        except Exception as e2:                  # noqa: BLE001
            man["classification_error"] = f"{type(e2).__name__}: {e2}"
        return save("EVAL_FAILED")

    man["evaluation"] = ev
    man["cd_status"] = ev.get("cd_status")
    man["iou_status"] = "ok" if ev.get("iou_eligible") else (ev.get("iou_status") or "ineligible")
    if ev.get("cd_x1000") is not None and ev.get("cd_floor_gt"):
        man["cd_floor_ratio"] = ev["cd_x1000"] / ev["cd_floor_gt"]
    return save("SUCCESS" if ev.get("remesh_status") == "ok" else "REMESH_FAILED")


if __name__ == "__main__":
    raise SystemExit(main())
