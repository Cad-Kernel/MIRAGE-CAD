"""Choose the tessellation resolution by convergence, not by inheriting either method's setting.

RUNS IN cadrecode_env. No model, no checkpoint. Must finish before Stage 2, because Stage 2 writes
the tolerance into artefact hashes and changing it afterwards invalidates every product downstream.

WHY THE EARLIER JUSTIFICATION WAS RETIRED. The frozen protocol used linear 0.05 mm and angular
0.3 rad on the grounds that occt_file_to_pointcloud used them for all 400 external clouds. Reading
CAD-Recode's demo cell 6 shows it tessellates its PREDICTIONS at (0.001, 0.1) on a shape spanning
roughly 200 DSL units. Those are not the same fidelity:

    ours   0.05 mm / 95.93 mm  ~ 5.2e-4      theirs  0.001 / 200  ~ 5.0e-6

about two orders of magnitude apart. So "we reused the manuscript's existing numbers" establishes
that the choice was not arbitrary, and nothing about whether it is adequate. Worse, inheriting
either side's absolute value would import that side's scale convention into a comparison between
them.

WHAT REPLACES IT. A single DIMENSIONLESS resolution, frozen for all three arms:

    linear_deflection = alpha * L,   L = the shape's largest bbox extent

so every shape is tessellated to the same relative fidelity regardless of whether it is 1.6 mm or
5 metres across -- which is what "the same meshing operator" has to mean when the evaluator
normalises geometry anyway. alpha is chosen by convergence: the coarsest value whose refinement no
longer changes the evaluated geometry by more than the evaluator can resolve.

THE PLATEAU CRITERION IS FROZEN HERE, BEFORE ANY MEASUREMENT, so it cannot be fitted to whatever
the curve turns out to look like. alpha is acceptable when, against the next-finer level across all
calibration shapes:

    median IoU              >= 0.9999
    95th-percentile IoU loss <= 1e-3
    CD change               within (floor mean + 3 sd) for that shape

The last is the important one -- refinement stops mattering once its effect is smaller than the
metric's own resolution on that shape -- and its FIRST form was wrong. It read `CD change <= the
floor`, which compares two noisy estimates of the same quantity with a strict inequality: many of
these shapes are tessellation-insensitive (12 to 48 triangles at every alpha, being planar), so
their `cd_vs_finest` is simply another draw of the floor and the test passed about half the time by
chance. The floor's variability is now measured over several seed pairs, so the criterion says the
tessellation change is indistinguishable from sampling noise rather than comparing one sample to
another.

IOU IS NOT UNIFORMLY TRUSTWORTHY, WHICH THIS STUDY FOUND RATHER THAN ASSUMED. Across 19 calibration
shapes the self-IoU deviation runs 4.06e-09 to 3.71e-02: eighteen near 1e-7, one off by 3.7 % at
every level, and one where the boolean fails outright at every level. So IoU carries a PER-PART
validity requirement, and a part that cannot reproduce IoU(M, M) = 1 is IoU-invalid rather than
scored -- otherwise a 3.7 % boolean error is indistinguishable from a real difference of that size.

TWO STAGES, SEPARATELY, because sweeping both together would leave it unknown which parameter was
in control. Linear first at a fixed fine angular value, then angular at the chosen alpha.

ONE SUBTLETY IN THE COMPARISON. Normalising M_alpha and M_fine independently would HIDE a real
difference: a coarse mesh with a slightly smaller bounding box gets rescaled to match. So both are
placed in the unit cube by the FINEST mesh's transform, which preserves any genuine discrepancy
while putting the numbers on the scale where the floor constant applies.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics as st
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Extended past 1e-6 after the pilot showed 5e-6 -> 1e-6 still losing 6.08e-4 of IoU, well
# above the 2.5e-7 numerical noise, so the plateau lies finer than the original range.
ALPHAS = [5e-4, 1e-4, 5e-5, 1e-5, 5e-6, 1e-6, 5e-7, 1e-7]
ANGULARS = [0.3, 0.2, 0.1, 0.05]
ANGULAR_FOR_LINEAR_SWEEP = 0.1     # fine, and the value CAD-Recode's demo uses
N_SURFACE_POINTS = 8192
CD_SPACING_CONST = 2543.0

# Frozen before measurement.
PLATEAU_MEDIAN_IOU = 0.9999
PLATEAU_P95_IOU_LOSS = 1e-3


def shape_extent(step_path: str) -> float:
    """Largest bbox extent of the raw shape, which sets the absolute tolerance for a given alpha."""
    import cadquery as cq
    bb = cq.importers.importStep(str(step_path)).val().BoundingBox()
    return float(max(bb.xlen, bb.ylen, bb.zlen))


def tessellate_relative(step_path: str, alpha: float, angular: float):
    import cadquery as cq
    from probe_cadrecode_mesh import to_trimesh
    shape = cq.importers.importStep(str(step_path))
    solids = shape.vals()
    if not solids:
        raise ValueError("no solids")
    bb = solids[0].BoundingBox()
    L = float(max(bb.xlen, bb.ylen, bb.zlen))
    for s in solids[1:]:
        b = s.BoundingBox()
        L = max(L, float(max(b.xlen, b.ylen, b.zlen)))
    linear = alpha * L
    verts, tris = [], []
    for s in solids:
        v, f = s.tessellate(linear, angular)
        off = len(verts)
        verts.extend([(p.x, p.y, p.z) for p in v])
        tris.extend([(a + off, b + off, c + off) for a, b, c in f])
    return to_trimesh(np.asarray(verts, dtype=np.float64),
                      np.asarray(tris, dtype=np.int64), merge=True), linear, L


def unit_cube_transform(mesh):
    """The transform that puts THIS mesh in the unit cube, to be applied to both meshes.

    Applied to a second mesh it is no longer a normalisation but a shared frame, which is the
    point: normalising each independently would rescale away a genuine bbox difference.
    """
    lo, hi = mesh.bounds
    centre = (lo + hi) / 2.0
    ext = float(max(mesh.extents))
    scale = 1.0 / ext if ext > 0 else 1.0
    return centre, scale


def apply_transform(mesh, centre, scale):
    m = mesh.copy()
    m.apply_translation(-centre)
    m.apply_scale(scale)
    m.apply_translation([0.5, 0.5, 0.5])
    return m


def measure(step_path: str, sample_id: str, alpha: float, angular: float,
            max_triangles: int) -> dict:
    from external_geometry_eval import chamfer_x1000, sample_surface
    t0 = time.time()
    rec = {"sample_id": sample_id, "step_path": step_path, "alpha": alpha, "angular": angular}
    try:
        m, linear, L = tessellate_relative(step_path, alpha, angular)
    except Exception as e:
        rec.update(status=f"tessellate_failed: {type(e).__name__}: {e}")
        return rec
    rec.update(linear_deflection=linear, bbox_extent=L,
               vertices=int(len(m.vertices)), triangles=int(len(m.faces)),
               area=float(m.area), volume=float(m.volume),
               watertight=bool(m.is_watertight))
    if len(m.faces) > max_triangles:
        rec.update(status=f"too_fine: {len(m.faces)} triangles exceeds the {max_triangles} cap")
        return rec

    # Self-comparison at this level: the CD floor, and the IoU numerical deviation the earlier
    # single-part observation needs turned into a distribution.
    from external_geometry_eval import iou_meshes
    c, sc = unit_cube_transform(m)
    mn = apply_transform(m, c, sc)
    pa = sample_surface(mn, N_SURFACE_POINTS, 0)
    pb = sample_surface(mn, N_SURFACE_POINTS, 1)
    rec["self_cd_floor"] = chamfer_x1000(pa, pb)
    # The floor is an estimate, so its spread is what a change has to be measured against. Five
    # independent seed pairs; without this, "CD change <= the floor" is one draw against another.
    floor_reps = [chamfer_x1000(sample_surface(mn, N_SURFACE_POINTS, 10 + 2 * i),
                                sample_surface(mn, N_SURFACE_POINTS, 11 + 2 * i))
                  for i in range(5)]
    rec["floor_mean"] = float(np.mean(floor_reps))
    rec["floor_sd"] = float(np.std(floor_reps, ddof=1))
    rec["floor_reps"] = [round(x, 6) for x in floor_reps]
    from scipy.spatial import cKDTree
    d, _ = cKDTree(pa).query(pa, k=2)
    rec["spacing"] = float(np.mean(d[:, 1]))
    rec["floor_predicted"] = CD_SPACING_CONST * rec["spacing"] ** 2
    try:
        m2, _, _ = tessellate_relative(step_path, alpha, angular)
        i_, s_ = iou_meshes(mn, apply_transform(m2, c, sc))
        rec["self_iou"] = i_
        rec["self_iou_dev"] = None if i_ is None else abs(i_ - 1.0)
        rec["self_iou_status"] = s_
    except Exception as e:
        rec["self_iou_status"] = f"{type(e).__name__}: {e}"
    rec["status"] = "ok"
    rec["seconds"] = round(time.time() - t0, 2)
    rec["_mesh"] = m
    return rec


def compare_to_reference(rec: dict, ref: dict) -> dict:
    """CD and IoU of this level against the finest level, in the finest level's frame."""
    from external_geometry_eval import chamfer_x1000, iou_meshes, sample_surface
    out = {}
    if rec.get("_mesh") is None or ref.get("_mesh") is None:
        return out
    c, sc = unit_cube_transform(ref["_mesh"])
    a = apply_transform(rec["_mesh"], c, sc)
    b = apply_transform(ref["_mesh"], c, sc)
    out["cd_vs_finest"] = chamfer_x1000(sample_surface(b, N_SURFACE_POINTS, 0),
                                       sample_surface(a, N_SURFACE_POINTS, 1))
    i_, s_ = iou_meshes(b, a)
    out["iou_vs_finest"] = i_
    out["iou_vs_finest_status"] = s_
    return out


def pick_shapes(queries: str, n: int) -> list[tuple[str, str, float]]:
    """Deterministic, log-stratified by bbox diagonal, with the defect outlier excluded.

    Frozen before any comparison result is seen, and the chosen ids are written to the report so
    that can be audited rather than asserted.
    """
    rows = []
    with open(queries, encoding="utf-8-sig") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    cand = []
    for r in rows:
        p = r.get("step_path_wsl") or r.get("step_path")
        d = float(r.get("bbox_diag", 0))
        if p and d > 0 and Path(p).exists():
            cand.append((r["sample_id"], p, d))
    if not cand:
        return []
    diags = sorted(d for _, _, d in cand)
    p99 = diags[int(0.99 * (len(diags) - 1))]
    cand = [c for c in cand if c[2] <= 100.0 * p99]      # the 4 km defect, by the same gap rule
    cand.sort(key=lambda c: c[2])
    take = min(n, len(cand))
    lo, hi = math.log(cand[0][2]), math.log(cand[-1][2])
    picked, seen = [], set()
    for i in range(take):
        target = lo + (hi - lo) * i / max(take - 1, 1)
        best = min((c for c in cand if c[0] not in seen),
                   key=lambda c: abs(math.log(c[2]) - target), default=None)
        if best:
            picked.append(best)
            seen.add(best[0])
    return picked


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--step", default=None, help="pilot: one STEP")
    ap.add_argument("--steps-from", default=None, help="calibration: queries.jsonl")
    ap.add_argument("--n-steps", type=int, default=20)
    ap.add_argument("--max-triangles", type=int, default=2_000_000,
                    help="a level finer than this is recorded as too_fine rather than run; at "
                         "alpha=1e-6 on a 95 mm part the absolute tolerance is 1e-4 mm and the "
                         "triangle count can reach millions")
    ap.add_argument("--angular-sweep", action="store_true",
                    help="second stage: fix alpha and sweep angular deflection")
    ap.add_argument("--alpha", type=float, default=None, help="fixed alpha for the angular sweep")
    ap.add_argument("--log", default=None, help="jsonl, appended and resumable")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    if args.step:
        shapes = [("pilot", args.step, shape_extent(args.step))]
    elif args.steps_from:
        shapes = pick_shapes(args.steps_from, args.n_steps)
    else:
        print("give --step for a pilot or --steps-from for calibration", file=sys.stderr)
        return 2
    if not shapes:
        print("no usable shapes", file=sys.stderr)
        return 1

    levels = ([(args.alpha or 5e-5, a) for a in ANGULARS] if args.angular_sweep
              else [(al, ANGULAR_FOR_LINEAR_SWEEP) for al in ALPHAS])

    print("=" * 78)
    print("tessellation convergence: a dimensionless resolution, chosen by refinement")
    print("=" * 78)
    print(f"  shapes            {len(shapes)}")
    print(f"  sweep             {'angular at alpha=' + str(args.alpha or 5e-5) if args.angular_sweep else 'linear alpha, angular fixed at ' + str(ANGULAR_FOR_LINEAR_SWEEP)}")
    print(f"  levels            {levels}")
    print(f"  plateau criterion median IoU >= {PLATEAU_MEDIAN_IOU}, p95 IoU loss <= "
          f"{PLATEAU_P95_IOU_LOSS}, CD change <= that shape's sampling floor")
    print(f"  frozen before any measurement, so it cannot be fitted to the curve")
    print(f"  shape ids         {[s[0] for s in shapes]}")
    print()

    log_path = Path(args.log) if args.log else None
    done = {}
    if log_path and log_path.exists():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                done[(r["sample_id"], r["alpha"], r["angular"])] = r

    rows: list[dict] = []
    for sid, path, diag in shapes:
        per_shape = []
        for alpha, angular in levels:
            key = (sid, alpha, angular)
            rec = measure(path, sid, alpha, angular, args.max_triangles)
            per_shape.append(rec)
            if log_path:
                with log_path.open("a", encoding="utf-8", newline="\n") as f:
                    f.write(json.dumps({k: v for k, v in rec.items()
                                        if not k.startswith("_")}) + "\n")
            tri = rec.get("triangles")
            print(f"  {sid[:28]:28s} a={alpha:.0e} ang={angular:<5} "
                  f"tri={tri if tri is not None else '-':>9} "
                  f"floor={rec.get('self_cd_floor', float('nan')):.4f} "
                  f"selfIoUdev={rec.get('self_iou_dev')} {rec.get('status', '')[:36]}")
        # Compare every level to the finest that actually ran.
        usable = [r for r in per_shape if r.get("status") == "ok" and r.get("_mesh") is not None]
        if usable:
            ref = usable[-1]
            for r in usable:
                r.update(compare_to_reference(r, ref))
                r["reference_alpha"] = ref["alpha"]
                r["reference_angular"] = ref["angular"]
        rows.extend(per_shape)
        print()

    # ---- apply the frozen criterion ------------------------------------------------
    print("=" * 78)
    print("levels against the finest that ran, per shape")
    print("=" * 78)
    by_level: dict[tuple, list[dict]] = {}
    for r in rows:
        if r.get("status") == "ok" and r.get("iou_vs_finest") is not None:
            by_level.setdefault((r["alpha"], r["angular"]), []).append(r)
    # The reference level is compared to itself, so it passes by construction and must be
    # EXCLUDED from candidacy. A level cannot certify itself as converged.
    ref_levels = {(r.get("reference_alpha"), r.get("reference_angular")) for r in rows
                  if r.get("reference_alpha") is not None}
    verdict = None
    summary = {}
    for (alpha, angular), rs in sorted(by_level.items(), key=lambda kv: -kv[0][0]):
        # Parts whose own boolean cannot return IoU(M, M) = 1 to 1e-4 are IoU-invalid: on this
        # calibration set one part is off by 3.7 % at every level and another fails outright, and
        # a boolean error of that size is indistinguishable from a real geometric difference.
        iou_valid = [r for r in rs if r.get("self_iou_dev") is not None
                     and r["self_iou_dev"] <= 1e-4]
        n_gated = len(rs) - len(iou_valid)
        ious = [r["iou_vs_finest"] for r in iou_valid]
        if not ious:
            print(f"  a={alpha:.0e} ang={angular:<5} no IoU-valid shapes at this level")
            continue
        losses = sorted(1.0 - i for i in ious)
        # Against the floor's mean plus three standard deviations, not against a single draw of
        # it. Shapes whose mesh does not change with alpha have cd_vs_finest = another sample of
        # the floor, and a strict inequality between two samples of one distribution is a coin
        # flip -- which is what the first version of this measured.
        pairs = [(r.get("cd_vs_finest"), r.get("floor_mean"), r.get("floor_sd"))
                 for r in rs if r.get("cd_vs_finest") is not None
                 and r.get("floor_mean") is not None]
        cds = [p[0] for p in pairs]
        within = sum(1 for c, m, sd in pairs if c <= m + 3.0 * (sd or 0.0))
        med = st.median(ious)
        p95 = losses[int(0.95 * (len(losses) - 1))] if losses else float("nan")
        is_ref = (alpha, angular) in ref_levels
        meets = (med >= PLATEAU_MEDIAN_IOU and p95 <= PLATEAU_P95_IOU_LOSS
                 and within == len(cds))
        summary[(alpha, angular)] = {"median_iou": med, "p95_loss": p95,
                                     "cd_within_floor": f"{within}/{len(cds)}",
                                     "is_reference": is_ref, "meets": meets}
        tag = ("REFERENCE, cannot certify itself" if is_ref
               else ("MEETS criterion" if meets else "does not meet"))
        print(f"  a={alpha:.0e} ang={angular:<5} n={len(rs):3d}  "
              f"IoU-valid {len(iou_valid):3d} (gated {n_gated})  median IoU {med:.6f}  "
              f"p95 loss {p95:.2e}  CD within noise {within}/{len(cds)}  {tag}")
        if meets and not is_ref and verdict is None:
            verdict = (alpha, angular)

    # Something must certify the reference. If the second-finest does not already satisfy the
    # criterion against it, the sweep does not reach far enough to locate the plateau at all --
    # which is a result to report, not a threshold to relax.
    non_ref = sorted((k for k in summary if not summary[k]["is_reference"]),
                     key=lambda k: k[0])
    reference_converged = bool(non_ref) and summary[non_ref[0]]["meets"]
    if non_ref:
        f = non_ref[0]
        print()
        print(f"  reference self-certification: the finest non-reference level a={f[0]:.0e} "
              f"{'DOES' if reference_converged else 'does NOT'} meet the criterion against the "
              f"reference")
        if not reference_converged:
            print(f"    median IoU {summary[f]['median_iou']:.6f}, p95 loss "
                  f"{summary[f]['p95_loss']:.2e}, CD within floor "
                  f"{summary[f]['cd_within_floor']}")
            print("    So the sweep is too coarse to know where the plateau is. Extend it rather")
            print("    than accepting a verdict the data does not support.")

    bad_iou = {}
    for r in rows:
        if r.get("status") != "ok":
            continue
        d_ = r.get("self_iou_dev")
        if d_ is None:
            bad_iou.setdefault(r["sample_id"], "boolean returned nothing at every level")
        elif d_ > 1e-4:
            bad_iou[r["sample_id"]] = f"self-IoU off by {d_:.3e}"
    if bad_iou:
        print()
        print(f"  IOU-INVALID PARTS: {len(bad_iou)} of "
              f"{len({r['sample_id'] for r in rows})} shapes cannot reproduce IoU(M, M) = 1")
        for sid, why in bad_iou.items():
            print(f"    {sid}  {why}")
        print("  These must be gated out of IoU statistics rather than scored: an error of that")
        print("  size is indistinguishable from a real geometric difference of the same size.")

    devs = [r["self_iou_dev"] for r in rows if r.get("self_iou_dev") is not None]
    dev_shapes = {r["sample_id"] for r in rows if r.get("self_iou_dev") is not None}
    if devs:
        devs.sort()
        print()
        print(f"  self-IoU deviation across {len(devs)} (shape, level) pairs on "
              f"{len(dev_shapes)} distinct shape(s): min {devs[0]:.2e}  "
              f"median {devs[len(devs)//2]:.2e}  max {devs[-1]:.2e}")
        # Levels of ONE shape are not a distribution across topologies. Ten distinct shapes was
        # the requirement, and six levels of one part is not a substitute for it.
        if len(dev_shapes) < 10:
            print(f"  Not enough shapes to call this a floor: {len(dev_shapes)} distinct, and the")
            print(f"  requirement is ten or more. Levels of one part measure that part, not the")
            print(f"  boolean's behaviour across topologies. Report the number, not the word.")
        elif devs[-1] < 1e-6:
            print(f"  {len(dev_shapes)} distinct shapes with a maximum under 1e-6, so `observed")
            print(f"  numerical self-IoU floor` is earned.")
        else:
            print(f"  Maximum exceeds 1e-6 across {len(dev_shapes)} shapes, so it is not a floor.")
            print(f"  Report the distribution instead of the word.")

    print()
    if verdict and not reference_converged:
        print(f"A level meets the criterion (alpha={verdict[0]:.0e}) but THE REFERENCE IS NOT")
        print("SELF-CERTIFIED, so that verdict is not usable: it says this level matches a")
        print("reference that has not itself been shown to be converged. Extend the sweep.")
        verdict = None
    if verdict:
        print(f"COARSEST LEVEL MEETING THE FROZEN CRITERION: alpha={verdict[0]:.0e}, "
              f"angular={verdict[1]}")
        print("Refining further does not change the evaluated geometry by more than the evaluator")
        print("can resolve, which is a stronger basis than inheriting either method's absolute")
        print("setting.")
    else:
        print("No level met the criterion. Either the sweep does not reach fine enough, or the")
        print("criterion is stricter than this metric can satisfy -- report which, do not relax it")
        print("after the fact.")

    if args.out:
        Path(args.out).write_text(json.dumps({
            "frozen_criterion": {"median_iou": PLATEAU_MEDIAN_IOU,
                                 "p95_iou_loss": PLATEAU_P95_IOU_LOSS,
                                 "cd_change": "<= floor mean + 3 sd, over 5 seed pairs",
                                 "iou_validity_gate": "self-IoU deviation <= 1e-4"},
            "iou_invalid_parts": bad_iou,
            "shape_ids": [s[0] for s in shapes],
            "levels": levels,
            "verdict": {"alpha": verdict[0], "angular": verdict[1]} if verdict else None,
            "reference_self_certified": reference_converged,
            "per_level": {f"a{k[0]:.0e}_ang{k[1]}": v for k, v in summary.items()},
            "rows": [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows],
        }, indent=2, default=str), encoding="utf-8", newline="\n")
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
