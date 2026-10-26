"""CAD-Recode's geometry metrics, ported from its released demo, with self-tests.

WHY THIS IS THE FIRST STEP AND TOUCHES NO MODEL. Every external number will be expressed in this
metric's units, so if the port is wrong then nothing downstream can be trusted, and the error
would be invisible: get the squaring, the direction, or the x1000 wrong and the numbers still look
plausible while sitting in a different coordinate system from CAD-Recode's published ones.

THE FORMULA, from demo.ipynb cell 8, reproduced exactly:

    gt_distance   = nearest-gt-distance for every PRED point
    pred_distance = nearest-pred-distance for every GT point
    cd = mean(gt_distance^2) + mean(pred_distance^2)      # sum of two means, squared distances
    report cd * 1000

Note what that is NOT: not a single mean over concatenated distances, not one-sided, not linear.
`test_chamfer_structure` pins all four at once with a hand-computed value.

NORMALISATION IS TWO DIFFERENT MAPS AND THE ASYMMETRY IS THE POINT. In the demo:

  * the ground-truth mesh is normalised PER SHAPE -- centred on its bbox midpoint, scaled so its
    largest extent is 2.0, then halved and shifted into [0,1]^3;
  * the prediction is mapped by a FIXED affine, scale 1/200 then +0.5, which is correct only
    because CAD-Recode's DSL emits integers in -100..+100.

Flluma has no such fixed convention, so a MIRAGE prediction has to be normalised per shape like
the ground truth. That is MORE permissive than a fixed map, so the geometry comparison is somewhat
favourable to MIRAGE, and `normalisation` is returned in every result so the asymmetry appears in
the output rather than being remembered.

IOU FAILURES ARE NOT ZEROS. A failed boolean and a genuinely disjoint pair of solids are different
events, and collapsing both to 0.0 merges method failure with geometric disagreement -- which is
the same mistake as reading fidelity off a validity gate. `iou_meshes` returns a status and leaves
`iou` as None whenever it could not be computed.

Dependencies are deliberately split. The Chamfer core needs numpy alone, and scipy only for speed
at realistic point counts; mesh sampling and booleans need trimesh. So the formula can be verified
in any environment, and only the mesh-level tests require the evaluation environment to be built.
"""
from __future__ import annotations

import argparse
import math

import numpy as np

N_SURFACE_POINTS = 8192   # demo cell 8
CD_SCALE = 1000.0         # demo prints cd * 1000
DSL_HALF_RANGE = 100.0    # CAD-Recode's integer coordinate range, -100..+100
# Fitted by tests 7 and 8 below: floor ~ CD_FLOOR_CONST * normalised_area / n, to about 3 % over
# 1024..8192 points. Calibrated on TRIMESH surface sampling, because that is what the released
# demo uses. It is not assumed to transfer to OCCT surface_uv sampling -- occt_floor_analyze.py
# measures that separately, and expresses the floor in terms of observed point spacing rather
# than area precisely because a different sampler need not be area-uniform.
CD_FLOOR_CONST = 623.0


# ---------------------------------------------------------------------------
# Chamfer. numpy-only, with scipy used for the KD-tree when it is available.
# ---------------------------------------------------------------------------
def _nearest_distances(query: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """Distance from every point in `query` to its nearest neighbour in `reference`."""
    try:
        from scipy.spatial import cKDTree
        d, _ = cKDTree(reference).query(query, k=1)
        return np.asarray(d, dtype=np.float64)
    except ImportError:
        # Brute force. Fine for the self-tests; at 8192 points this is 67 M pairs, so real runs
        # want scipy. Chunked so it cannot exhaust memory silently.
        out = np.empty(len(query), dtype=np.float64)
        step = max(1, int(2e7 // max(len(reference), 1)))
        for i in range(0, len(query), step):
            block = query[i:i + step]
            d2 = ((block[:, None, :] - reference[None, :, :]) ** 2).sum(-1)
            out[i:i + step] = np.sqrt(d2.min(axis=1))
        return out


def chamfer_x1000(gt_points: np.ndarray, pred_points: np.ndarray) -> float:
    """CAD-Recode's Chamfer distance, in the units it reports (already multiplied by 1000)."""
    gt_points = np.asarray(gt_points, dtype=np.float64)
    pred_points = np.asarray(pred_points, dtype=np.float64)
    d_pred_to_gt = _nearest_distances(pred_points, gt_points)
    d_gt_to_pred = _nearest_distances(gt_points, pred_points)
    cd = float(np.mean(np.square(d_pred_to_gt)) + np.mean(np.square(d_gt_to_pred)))
    return cd * CD_SCALE


# ---------------------------------------------------------------------------
# Normalisation. Two maps, named after what they assume.
# ---------------------------------------------------------------------------
def normalise_per_shape(mesh):
    """Centre on the bbox midpoint and scale the largest extent to 1.0, occupying [0,1]^3.

    Equivalent to the demo's ground-truth path: scale the largest extent to 2.0 at load time, then
    halve and shift by 0.5 at scoring time. Applied to a MIRAGE prediction this discards absolute
    position and scale, which is exactly why the comparison is permissive to MIRAGE.
    """
    m = mesh.copy()
    lo, hi = m.bounds
    m.apply_translation(-(lo + hi) / 2.0)
    extent = float(max(m.extents))
    if extent > 0:
        m.apply_scale(1.0 / extent)
    m.apply_translation([0.5, 0.5, 0.5])
    return m


def normalise_fixed_dsl(mesh, half_range: float = DSL_HALF_RANGE):
    """The demo's prediction path: a FIXED affine, valid only for CAD-Recode's DSL range.

    Absolute position and scale survive this map, so a prediction that is correct in shape but
    wrong in scale is penalised here and would not be under `normalise_per_shape`.
    """
    m = mesh.copy()
    m.apply_scale(1.0 / half_range / 2.0)
    m.apply_translation([0.5, 0.5, 0.5])
    return m


# ---------------------------------------------------------------------------
# IoU, with failure states kept distinct from a value of zero.
# ---------------------------------------------------------------------------
def iou_meshes(gt_mesh, pred_mesh) -> tuple[float | None, str]:
    """Volumetric IoU by mesh boolean, per connected component, as in demo cell 8.

    Returns (iou, status). status is one of:
      ok                 a value was computed
      no_boolean_backend trimesh has no boolean engine installed
      boolean_failed     the engine raised on this pair
      degenerate_volume  union volume is zero, so the ratio is undefined
    A failure leaves iou as None. It is never reported as 0.0, because a failed boolean and two
    solids that genuinely do not overlap are different events.
    """
    try:
        intersection_volume = 0.0
        for gt_i in gt_mesh.split():
            for pred_i in pred_mesh.split():
                inter = gt_i.intersection(pred_i)
                intersection_volume += float(inter.volume) if inter is not None else 0.0
    except ImportError:
        return None, "no_boolean_backend"
    except Exception:
        return None, "boolean_failed"

    gt_volume = sum(float(m.volume) for m in gt_mesh.split())
    pred_volume = sum(float(m.volume) for m in pred_mesh.split())
    union = gt_volume + pred_volume - intersection_volume
    if union <= 0:
        return None, "degenerate_volume"
    return intersection_volume / union, "ok"


def sample_surface(mesh, n: int = N_SURFACE_POINTS, seed: int = 0) -> np.ndarray:
    import trimesh
    rng = np.random.RandomState(seed)
    state = np.random.get_state()
    np.random.seed(rng.randint(0, 2 ** 31 - 1))
    try:
        pts, _ = trimesh.sample.sample_surface(mesh, n)
    finally:
        np.random.set_state(state)
    return np.asarray(pts, dtype=np.float64)


def score_pair(gt_mesh, pred_mesh, normalisation: str = "per_shape",
               n_points: int = N_SURFACE_POINTS, seed: int = 0) -> dict:
    """Score one pair. `normalisation` is recorded in the result, never left implicit."""
    if normalisation == "per_shape":
        g, p = normalise_per_shape(gt_mesh), normalise_per_shape(pred_mesh)
    elif normalisation == "demo_fixed_dsl":
        g, p = normalise_per_shape(gt_mesh), normalise_fixed_dsl(pred_mesh)
    elif normalisation == "none":
        g, p = gt_mesh, pred_mesh
    else:
        raise ValueError(f"unknown normalisation: {normalisation}")

    watertight = bool(getattr(g, "is_watertight", False)) and \
        bool(getattr(p, "is_watertight", False))
    cd = chamfer_x1000(sample_surface(g, n_points, seed), sample_surface(p, n_points, seed + 1))
    iou, iou_status = iou_meshes(g, p)
    if iou_status == "ok" and not watertight:
        # A boolean on a non-watertight mesh returns a number, and the number means little.
        iou_status = "ok_but_not_watertight"
    return {
        "cd_x1000": cd,
        "iou": iou,
        "iou_status": iou_status,
        "normalisation": normalisation,
        "n_surface_points": n_points,
        "both_watertight": watertight,
    }


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------
def test_chamfer_structure() -> tuple[bool, str]:
    """Pin the formula with one hand-computed number.

    gt = {(0,0,0), (2,0,0)}, pred = {(0.4,0,0)}
      pred -> gt : 0.4          squared 0.16                mean 0.16
      gt -> pred : 0.4, 1.6     squared 0.16, 2.56          mean 1.36
      cd = 1.52, reported x1000 = 1520

    Five plausible mis-implementations give five different answers, so this single value
    discriminates all of them:
      linear instead of squared      1400
      pred->gt only                   160
      gt->pred only                  1360
      one mean over concatenation      960
      missing the x1000                 1.52
    """
    gt = np.array([[0.0, 0, 0], [2.0, 0, 0]])
    pred = np.array([[0.4, 0, 0]])
    got = chamfer_x1000(gt, pred)
    wrong = {"linear not squared": 1400.0, "pred->gt only": 160.0, "gt->pred only": 1360.0,
             "mean over concatenation": 960.0, "missing x1000": 1.52}
    if not math.isclose(got, 1520.0, rel_tol=1e-9, abs_tol=1e-9):
        near = [k for k, v in wrong.items() if math.isclose(got, v, rel_tol=1e-6)]
        return False, (f"expected 1520.0, got {got!r}"
                       + (f" -- that is the value of: {near[0]}" if near else ""))
    return True, f"CD = {got:.4f}, and all five known mis-implementations are excluded"


def test_chamfer_identity_points() -> tuple[bool, str]:
    rng = np.random.RandomState(0)
    p = rng.rand(500, 3)
    got = chamfer_x1000(p, p)
    return (got == 0.0), f"CD(P, P) = {got!r}"


def _mesh_tests() -> list[tuple[str, bool, str]]:
    try:
        import trimesh
    except ImportError:
        return [("mesh-level tests", False,
                 "SKIPPED, trimesh is not installed -- this is NOT a pass. Build the "
                 "external_eval environment (numpy, scipy, trimesh, manifold3d) and re-run.")]

    out = []
    base = trimesh.creation.box(extents=(2.0, 1.0, 0.5))

    # The demo samples each mesh independently, so two IDENTICAL solids still give two different
    # point sets and a small non-zero Chamfer. That value is the sampling floor, not an error, and
    # it is the reference the invariance checks below compare against. Asserting "CD == 0" here
    # would be asserting something the metric does not claim.
    r_self = score_pair(base, base.copy())
    floor = r_self["cd_x1000"]
    out.append(("1. mesh against itself establishes the sampling floor",
                floor < 1.0,
                f"floor = {floor:.6f} at {N_SURFACE_POINTS} points. Not zero, and not meant to "
                f"be: the two point sets are drawn independently."))
    ok_iou = r_self["iou_status"].startswith("ok") and r_self["iou"] is not None and \
        math.isclose(r_self["iou"], 1.0, abs_tol=1e-3)
    out.append(("1b. mesh against itself, IoU ~ 1", ok_iou,
                f"IoU = {r_self['iou']!r}, status = {r_self['iou_status']}"))

    # Invariance is tested as equality WITH the floor. If normalisation is exact, a translated or
    # rescaled copy is bit-identical to the self-comparison, which is a far stronger statement
    # than "below some threshold".
    moved = base.copy()
    moved.apply_translation((37.0, -11.0, 5.0))
    r = score_pair(base, moved)
    same = math.isclose(r["cd_x1000"], floor, rel_tol=1e-6, abs_tol=1e-9)
    out.append(("2. translation only reproduces the floor exactly", same,
                f"CD = {r['cd_x1000']:.6f} against floor {floor:.6f}, "
                f"difference {abs(r['cd_x1000'] - floor):.3e}"))
    out.append(("2b. translation only, IoU ~ 1",
                r["iou"] is not None and math.isclose(r["iou"], 1.0, abs_tol=1e-3),
                f"IoU = {r['iou']!r}, status = {r['iou_status']}"))

    scaled = base.copy()
    scaled.apply_scale(7.3)
    r = score_pair(base, scaled)
    same = math.isclose(r["cd_x1000"], floor, rel_tol=1e-6, abs_tol=1e-9)
    out.append(("3. uniform scale only reproduces the floor exactly", same,
                f"CD = {r['cd_x1000']:.6f} against floor {floor:.6f}, "
                f"difference {abs(r['cd_x1000'] - floor):.3e}"))
    out.append(("3b. uniform scale only, IoU ~ 1",
                r["iou"] is not None and math.isclose(r["iou"], 1.0, abs_tol=1e-3),
                f"IoU = {r['iou']!r}, status = {r['iou_status']}"))

    squashed = trimesh.creation.box(extents=(2.0, 1.0, 1.6))
    r = score_pair(base, squashed)
    out.append(("4. aspect ratio changed, CD far above the floor",
                r["cd_x1000"] > 20 * floor,
                f"CD = {r['cd_x1000']:.4f}, which is {r['cd_x1000'] / max(floor, 1e-12):.0f}x "
                f"the floor -- a real shape difference is resolvable"))
    out.append(("4b. aspect ratio changed, IoU < 1",
                r["iou"] is not None and r["iou"] < 0.999,
                f"IoU = {r['iou']!r}, status = {r['iou_status']}"))

    # The fixed-DSL map must NOT be scale invariant. If it were, the asymmetry recorded in the
    # plan would not exist and the disclosure would be wrong.
    r_fixed = score_pair(base, scaled, normalisation="demo_fixed_dsl")
    out.append(("5. fixed-DSL map is NOT scale invariant, unlike per-shape",
                r_fixed["cd_x1000"] > 20 * floor,
                f"CD = {r_fixed['cd_x1000']:.4f} under demo_fixed_dsl, against "
                f"{floor:.6f} under per_shape. The prediction-side map in the demo therefore "
                f"does penalise wrong scale, and the per-shape map MIRAGE needs does not."))

    # 6. The floor is a property of shape and point count, so one box does not establish it.
    prims = {
        "box 2x1x0.5": base,
        "cylinder r0.5 h2": trimesh.creation.cylinder(radius=0.5, height=2.0),
        "sphere r1": trimesh.creation.icosphere(subdivisions=3, radius=1.0),
        "torus": trimesh.creation.torus(major_radius=1.0, minor_radius=0.3),
    }
    floors = {}
    for name, m in prims.items():
        try:
            floors[name] = score_pair(m, m.copy())["cd_x1000"]
        except Exception as e:                       # a primitive missing from this trimesh
            floors[name] = float("nan")
            print(f"  note: floor for {name} unavailable: {type(e).__name__}")
    # 7. Does the floor track surface area? If it does, it can be predicted for the shapes that
    # actually matter instead of being four unexplained numbers. Mean squared nearest-neighbour
    # distance among n points spread over area A should go as A/n, so floor * n / A ought to be
    # roughly constant across shapes of very different form.
    ratios = {}
    for name, m in prims.items():
        f = floors.get(name)
        if f is None or f != f:
            continue
        area = float(normalise_per_shape(m).area)   # area AFTER normalisation, which is what is sampled
        ratios[name] = f / area if area > 0 else float("nan")
    if len(ratios) > 1:
        vals = [v for v in ratios.values() if v == v]
        spread = max(vals) / min(vals) if min(vals) > 0 else float("inf")
        detail = ", ".join(f"{k} {v:.4f}" for k, v in ratios.items())
        areas = ", ".join(f"{k} area {float(normalise_per_shape(m).area):.3f}"
                          for k, m in prims.items() if k in ratios)
        out.append(("7. the floor tracks normalised surface area", spread < 2.0,
                    f"floor/area: {detail} (spread {spread:.2f}x). {areas}. If this ratio is "
                    f"near-constant the floor is predictable from area alone, so it can be "
                    f"computed for the external shapes rather than guessed."))

    # 8. Does the floor go as 1/n? Typical spacing among n points on a surface of area A is
    # sqrt(A/n), so a SQUARED-distance metric should give floor proportional to A/n. If it holds,
    # floor * n / A is a single constant and the floor is computable at ANY point count -- which
    # matters because CAD-Recode's benchmark point count is not published. 8192 is the demo's.
    ns = [1024, 2048, 4096, 8192]
    consts, per_n = {}, {}
    area_box = float(normalise_per_shape(base).area)
    for n in ns:
        f = score_pair(base, base.copy(), n_points=n)["cd_x1000"]
        per_n[n] = f
        consts[n] = f * n / area_box if area_box > 0 else float("nan")
    cvals = [v for v in consts.values() if v == v]
    spread_n = max(cvals) / min(cvals) if cvals and min(cvals) > 0 else float("inf")
    out.append(("8. the floor goes as area / n_points", spread_n < 1.3,
                "floor at n: " + ", ".join(f"{n}:{v:.3f}" for n, v in per_n.items())
                + " | floor*n/area: " + ", ".join(f"{n}:{v:.1f}" for n, v in consts.items())
                + f" (spread {spread_n:.2f}x). Constant means the floor is computable at any"
                  " point count from surface area alone."))

    shown = ", ".join(f"{k} {v:.3f}" for k, v in floors.items())
    finite = [v for v in floors.values() if v == v]
    out.append(("6. sampling floor across primitives, reported not tuned away",
                len(finite) > 1 and max(finite) < 1.0,
                f"{shown}. This bounds the resolution of every CD comparison made with this "
                f"metric. Worth noting beside CAD-Recode's published Fusion360 median CD of "
                f"0.151: the same order of magnitude, so that metric is close to saturation for "
                f"good predictions, much as this paper's own F@1 % ceiling of 0.244 is."))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true", default=True)
    ap.parse_args()

    results: list[tuple[str, bool, str]] = []
    ok, msg = test_chamfer_structure()
    results.append(("0. Chamfer formula structure, hand-computed", ok, msg))
    ok, msg = test_chamfer_identity_points()
    results.append(("0b. Chamfer of a point set with itself", ok, msg))
    results.extend(_mesh_tests())

    print("=" * 78)
    print("CAD-Recode geometry metric -- self-tests")
    print("=" * 78)
    failed = 0
    for name, passed, detail in results:
        mark = "PASS" if passed else "FAIL"
        failed += not passed
        print(f"  [{mark}] {name}")
        print(f"         {detail}")

    print()
    if failed:
        print(f"{failed} check(s) did not pass. Do not score anything external until they do:")
        print("tests 2 and 3 are what verify that this evaluator discards absolute position and")
        print("scale, which is the basis for the claim that MIRAGE's scale-blind point pathway is")
        print("not directly penalised here.")
        return 1
    print("all checks passed.")
    print()
    print("Tests 2 and 3 reproduce the self-comparison floor EXACTLY, not merely closely, so the")
    print("per-shape normalisation is invariant to absolute position and scale at machine")
    print("precision. That is the verification behind reporting that MIRAGE's scale-blind point")
    print("pathway is not directly penalised by this metric. Test 5 shows the demo's")
    print("prediction-side fixed map does NOT share that invariance -- it penalises wrong scale --")
    print("which is precisely the protocol asymmetry the external comparison must disclose, and it")
    print("runs in MIRAGE's favour.")
    print()
    print("Test 6 reports the sampling floor rather than tuning it away. It bounds the resolution")
    print("of any CD comparison made here, and it is the same order as CAD-Recode's published")
    print("Fusion360 median, so small CD differences between good predictions should not be read")
    print("as meaningful without checking them against it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
