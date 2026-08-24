"""CAD-Recode's input pipeline: STEP -> mesh -> 8192 surface samples -> FPS 256. Frozen and checked.

RUNS IN cadrecode_env. No checkpoint, no model. This is the last component of the input protocol,
and it is built before the download so that when inference misbehaves the cause can be attributed
to the model or the environment rather than to the data reaching it.

THE PIPELINE, from demo.ipynb cells 3 and 5:

    mesh = load(step)
    mesh.apply_translation(-(bounds[0] + bounds[1]) / 2)     # centre on the bbox midpoint
    mesh.apply_scale(2.0 / max(mesh.extents))                # largest extent becomes 2.0
    np.random.seed(0)
    verts = trimesh.sample.sample_surface(mesh, 8192)        # consumes the GLOBAL numpy RNG
    idx = sample_farthest_points(verts, K=256)
    points = verts[idx]

FOUR THINGS FROZEN ABOUT THE FPS, because this constructs a model input rather than measuring
something, so "the points are nicely spread" is not the standard:

  1. START POINT. pytorch3d's signature is sample_farthest_points(points, lengths=None, K=50,
     random_start_point=False), and the demo passes only K -- so the documented default applies and
     the first selected point is INDEX 0. Recorded as a documented default, NOT as verified: only
     an index-level comparison against a real pytorch3d run settles it, and until that exists this
     implementation is a "compatible deterministic FPS", not an exact replacement.
  2. DISTANCE. Squared Euclidean. Monotone in Euclidean distance, so argmax and argmin agree, and
     it avoids a sqrt over 8192 x 256 comparisons.
  3. TIE-BREAKING. numpy argmax returns the FIRST maximum. Whether pytorch3d's CUDA reduction does
     the same is unverified, which matters only for point sets with exact ties -- rare in sampled
     surface points and constructed deliberately in the synthetic tests below.
  4. INPUT ORDER. The 8192 points are passed in exactly the order trimesh produced them. No
     sorting, no deduplication: FPS output depends on input order through both the start point and
     tie-breaking, so reordering silently changes the model's input.

THE RANDOMNESS LIVES IN THE 8192 SAMPLE, NOT IN THE FPS. FPS is deterministic given its input, so
if the 8192-point cloud is not reproduced, the 256 differ regardless. trimesh.sample.sample_surface
draws from the GLOBAL numpy RNG, so any code that consumes random numbers earlier in the process
silently changes CAD-Recode's input. The seed is therefore set immediately before each sample and
never relied upon from further away, and `--check-determinism` asserts that two runs agree and that
processing order does not matter.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

N_PRE_POINTS = 8192      # demo cell 3
K_POINTS = 256           # demo cell 3
DEMO_SEED = 0            # demo cell 3, np.random.seed(0)
TARGET_EXTENT = 2.0      # demo cell 3, apply_scale(2.0 / max(extents))


# ---------------------------------------------------------------------------
# FPS
# ---------------------------------------------------------------------------
def sample_farthest_points_np(points: np.ndarray, k: int,
                              start_index: int = 0) -> np.ndarray:
    """Farthest-point sampling, returning INDICES into `points` in selection order.

    Greedy: having chosen S, the next point maximises the distance to its nearest member of S.
    Squared distances throughout, which is order-equivalent. Ties go to the lowest index, matching
    numpy argmax.

    DEGENERATE CASE, DOCUMENTED RATHER THAN PATCHED. If k exceeds the number of DISTINCT positions,
    every remaining point coincides with a selected one, the running distances are all zero, and
    argmax returns an already-selected index -- so the output repeats. pytorch3d is also a greedy
    argmax over a running distance array and does not track selected-ness, so masking selected
    indices here would be a deviation from the implementation this replicates, and no reference run
    exists yet to say which behaviour is theirs. Inventing a difference to satisfy a test would look
    correct and diverge silently.

    The real pipeline cannot reach this: 8192 surface samples of a solid hold far more than 256
    distinct positions. `build_input` asserts uniqueness anyway, so the premise is checked rather
    than assumed.
    """
    p = np.asarray(points, dtype=np.float64)
    n = len(p)
    if k <= 0 or n == 0:
        return np.empty(0, dtype=np.int64)
    k = min(k, n)
    idx = np.empty(k, dtype=np.int64)
    idx[0] = start_index
    # Running nearest-squared-distance to the selected set; updated, not recomputed.
    d = ((p - p[start_index]) ** 2).sum(axis=1)
    for i in range(1, k):
        nxt = int(np.argmax(d))
        idx[i] = nxt
        np.minimum(d, ((p - p[nxt]) ** 2).sum(axis=1), out=d)
    return idx


def verify_greedy_property(points: np.ndarray, idx: np.ndarray) -> tuple[bool, str]:
    """Recompute the criterion at every step: each pick must be the argmax of nearest-distance.

    This is the check that matters. A plausible-looking spread of points can come from a subtly
    wrong update rule; only replaying the criterion proves the traversal is farthest-point.
    """
    p = np.asarray(points, dtype=np.float64)
    if len(idx) == 0:
        return True, "empty selection"
    d = ((p - p[idx[0]]) ** 2).sum(axis=1)
    for i in range(1, len(idx)):
        best = float(d.max())
        got = float(d[idx[i]])
        if not np.isclose(got, best, rtol=0, atol=1e-12):
            return False, (f"step {i}: chose index {idx[i]} at nearest-distance^2 {got:.6e}, "
                           f"but {best:.6e} was available")
        np.minimum(d, ((p - p[idx[i]]) ** 2).sum(axis=1), out=d)
    return True, f"all {len(idx)} picks are the argmax of nearest-distance at their step"


# ---------------------------------------------------------------------------
# the pipeline
# ---------------------------------------------------------------------------
def normalise_for_model(mesh):
    """Centre on the bbox midpoint and scale the largest extent to 2.0. The demo's convention."""
    m = mesh.copy()
    lo, hi = m.bounds
    m.apply_translation(-(lo + hi) / 2.0)
    ext = float(max(m.extents))
    if ext > 0:
        m.apply_scale(TARGET_EXTENT / ext)
    return m


def build_input(step_path: str, seed: int = DEMO_SEED) -> dict:
    """One part, all the way to the 256 points the model consumes, with hashes at each stage."""
    import trimesh
    from probe_cadrecode_mesh import tessellate_step, to_trimesh

    v, f = tessellate_step(step_path)
    mesh = normalise_for_model(to_trimesh(v, f, merge=True))

    # Seeded immediately before sampling, never from further away: sample_surface draws on the
    # GLOBAL numpy RNG, so anything that consumed randomness earlier would change this cloud.
    np.random.seed(seed)
    pre, _ = trimesh.sample.sample_surface(mesh, N_PRE_POINTS)
    pre = np.asarray(pre, dtype=np.float64)

    idx = sample_farthest_points_np(pre, K_POINTS, start_index=0)
    # The premise checked rather than assumed. Repetition means fewer than K distinct positions
    # among the pre-samples, which would mean a degenerate mesh -- and would feed the model 256
    # points that are not 256 places. Free when the premise holds, unmissable if it stops.
    if len(set(idx.tolist())) != len(idx):
        raise ValueError(
            f"FPS repeated an index for {step_path}: only {len(set(idx.tolist()))} distinct "
            f"positions among {len(pre)} pre-samples. The mesh is degenerate; this part cannot "
            f"supply a valid model input and must be reported, not silently sampled.")
    pts = pre[idx]

    def h(a: np.ndarray) -> str:
        return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()[:16]

    return {
        "step_path": step_path,
        "mesh_vertices": int(len(mesh.vertices)),
        "mesh_faces": int(len(mesh.faces)),
        "mesh_hash": h(np.asarray(mesh.vertices)) + "/" + h(np.asarray(mesh.faces)),
        "seed": seed,
        "pre_hash": h(pre),
        "fps_index_hash": h(idx),
        "points_hash": h(pts),
        "n_points": int(len(pts)),
        "max_extent": float(max(mesh.extents)),
        "points_centre": np.asarray(pts).mean(axis=0).round(9).tolist(),
        "points_bbox_min": np.asarray(pts).min(axis=0).round(9).tolist(),
        "points_bbox_max": np.asarray(pts).max(axis=0).round(9).tolist(),
        "_points": pts,
        "_pre": pre,
        "_idx": idx,
    }


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------
def synthetic_tests() -> list[tuple[str, bool, str]]:
    """Cases that expose the start point and tie-breaking, which a spread-out cloud cannot."""
    out = []

    # 1D equidistant. From index 0, FPS must take the far end next, then bisect.
    line = np.stack([np.arange(9.0), np.zeros(9), np.zeros(9)], axis=1)
    idx = sample_farthest_points_np(line, 3)
    out.append(("1D equidistant: 0 then the far end then the midpoint",
                idx.tolist() == [0, 8, 4], f"got {idx.tolist()}, expected [0, 8, 4]"))

    # Cube corners: after the start, the antipode is uniquely farthest.
    cube = np.array([[x, y, z] for x in (0.0, 1.0) for y in (0.0, 1.0) for z in (0.0, 1.0)])
    idx = sample_farthest_points_np(cube, 2)
    out.append(("cube corners: second pick is the antipode of index 0",
                idx.tolist() == [0, 7], f"got {idx.tolist()}, expected [0, 7]"))

    # Duplicates: distinct positions are reached first, and once they are exhausted the greedy
    # repeats rather than erroring. That repetition is faithful to a greedy argmax over a running
    # distance array -- which is what pytorch3d does -- so it is asserted, not patched away. The
    # real pipeline is guarded against it in build_input instead.
    dup = np.array([[0.0, 0, 0], [0.0, 0, 0], [1.0, 0, 0], [1.0, 0, 0]])
    idx2 = sample_farthest_points_np(dup, 2)
    out.append(("duplicates: both distinct positions are reached while k allows",
                idx2.tolist() == [0, 2], f"k=2 gave {idx2.tolist()}, expected [0, 2]"))
    idx3 = sample_farthest_points_np(dup, 3)
    out.append(("duplicates: k beyond the distinct count repeats, and that is documented",
                len(idx3) == 3 and len(set(idx3.tolist())) == 2,
                f"k=3 gave {idx3.tolist()} -- only 2 distinct positions exist, so a greedy argmax "
                f"over a zeroed distance array must repeat. build_input asserts against this."))

    # Exact ties resolve to the lowest index, matching numpy argmax. Documented because
    # pytorch3d's reduction order is not verified.
    tie = np.array([[0.0, 0, 0], [1.0, 0, 0], [-1.0, 0, 0]])
    idx = sample_farthest_points_np(tie, 2)
    out.append(("exact tie goes to the lower index (numpy argmax semantics)",
                idx.tolist() == [0, 1], f"got {idx.tolist()}, expected [0, 1]"))

    # K == N returns a permutation; K > N is clamped rather than erroring.
    small = np.random.RandomState(0).rand(7, 3)
    idx = sample_farthest_points_np(small, 7)
    out.append(("K == N returns a permutation", sorted(idx.tolist()) == list(range(7)),
                f"got {sorted(idx.tolist())}"))
    idx = sample_farthest_points_np(small, 99)
    out.append(("K > N is clamped to N", len(idx) == 7, f"got {len(idx)} indices"))

    # The greedy property, replayed on a random cloud of realistic size.
    cloud = np.random.RandomState(1).rand(2000, 3)
    idx = sample_farthest_points_np(cloud, 128)
    ok, detail = verify_greedy_property(cloud, idx)
    out.append(("greedy criterion replayed on 2000 points, K=128", ok, detail))

    # Start point is index 0, and changing it changes the result -- so the choice is not cosmetic.
    a = sample_farthest_points_np(cloud, 16, start_index=0)
    b = sample_farthest_points_np(cloud, 16, start_index=5)
    out.append(("start point matters: index 0 is a real convention, not a formality",
                a[0] == 0 and b[0] == 5 and a.tolist() != b.tolist(),
                f"from 0: {a[:4].tolist()}..., from 5: {b[:4].tolist()}..."))
    return out


def reference_check(ref_dir: str | None) -> list[tuple[str, bool, str]]:
    """Index-level comparison against a real pytorch3d run, if one has been captured.

    Without this the implementation is a COMPATIBLE deterministic FPS, not an exact replacement,
    and the distinction is kept rather than blurred. Capture the reference wherever pytorch3d does
    install -- CAD-Recode's own Docker image is the obvious place -- as two files:
      fps_reference_input.npy    (N, 3) float
      fps_reference_indices.npy  (K,)   int, from sample_farthest_points(..., K=K)
    """
    if not ref_dir:
        return [("index-level reference against pytorch3d", None,
                 "NOT RUN. No --reference-dir given, so this implementation is a compatible "
                 "deterministic FPS rather than a verified exact replacement. Capture "
                 "fps_reference_input.npy and fps_reference_indices.npy from a real pytorch3d "
                 "environment to settle it.")]
    ri = Path(ref_dir) / "fps_reference_input.npy"
    rx = Path(ref_dir) / "fps_reference_indices.npy"
    if not (ri.exists() and rx.exists()):
        return [("index-level reference against pytorch3d", None,
                 f"NOT RUN. Expected {ri.name} and {rx.name} in {ref_dir}.")]
    pts = np.load(ri)
    want = np.load(rx).astype(np.int64).ravel()
    got = sample_farthest_points_np(pts, len(want), start_index=0)
    exact = np.array_equal(got, want)
    same_set = set(got.tolist()) == set(want.tolist())
    if exact:
        detail = f"all {len(want)} indices identical, in order"
    elif same_set:
        detail = (f"same SET of {len(want)} indices, different order. Compatible, not exact; "
                  f"first divergence at position "
                  f"{int(np.argmax(got != want))}")
    else:
        n_shared = len(set(got.tolist()) & set(want.tolist()))
        detail = (f"differs: {n_shared}/{len(want)} indices shared. Not a replacement for "
                  f"pytorch3d's implementation.")
    return [("index-level reference against pytorch3d", exact, detail)]


def determinism_test(step_path: str) -> list[tuple[str, bool, str]]:
    """Two builds must agree, and processing another part in between must not matter."""
    out = []
    a = build_input(step_path)
    # Deliberately consume global randomness between the two, which is the failure mode: if the
    # seed were set anywhere but immediately before sampling, this would change the cloud.
    np.random.rand(1000)
    b = build_input(step_path)
    keys = ("mesh_hash", "pre_hash", "fps_index_hash", "points_hash")
    same = all(a[k] == b[k] for k in keys)
    out.append(("two builds agree, with global randomness consumed in between", same,
                " ".join(f"{k}={'=' if a[k] == b[k] else 'DIFFERS'}" for k in keys)))
    out.append((f"exactly {K_POINTS} points, all finite", a["n_points"] == K_POINTS
                and bool(np.isfinite(a["_points"]).all()),
                f"n={a['n_points']}, finite={bool(np.isfinite(a['_points']).all())}"))
    ext = a["max_extent"]
    out.append((f"mesh max extent is {TARGET_EXTENT} under the demo's convention",
                abs(ext - TARGET_EXTENT) < 1e-9, f"max extent {ext:.12f}"))
    span = float(np.max(np.asarray(a["_points"]).max(axis=0)
                        - np.asarray(a["_points"]).min(axis=0)))
    out.append(("the 256 points span no more than the mesh", span <= TARGET_EXTENT + 1e-9,
                f"point-cloud span {span:.9f} against extent {TARGET_EXTENT}"))
    ok, detail = verify_greedy_property(a["_pre"], a["_idx"])
    out.append(("greedy criterion holds on the real 8192-point cloud", ok, detail))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--step", default=None, help="a STEP for the determinism and pipeline checks")
    ap.add_argument("--reference-dir", default=None,
                    help="directory holding fps_reference_{input,indices}.npy from pytorch3d")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    print("=" * 78)
    print("CAD-Recode input pipeline: FPS and the 8192 -> 256 path")
    print("=" * 78)
    print(f"  pre-sample points     {N_PRE_POINTS}")
    print(f"  FPS output            {K_POINTS}")
    print(f"  start index           0 (pytorch3d's documented random_start_point=False default; "
          f"NOT verified against a real run)")
    print(f"  distance              squared Euclidean")
    print(f"  tie-breaking          lowest index (numpy argmax); pytorch3d's order unverified")
    print(f"  input order           trimesh order preserved, no sort, no dedup")
    print(f"  seed                  np.random.seed({DEMO_SEED}) immediately before each sample")
    print(f"  mesh normalisation    centre on bbox midpoint, max extent -> {TARGET_EXTENT}")
    print()

    results = synthetic_tests()
    results += reference_check(args.reference_dir)
    if args.step and os.path.exists(args.step):
        results += determinism_test(args.step)
    else:
        results.append(("pipeline determinism on a real STEP", None,
                        "NOT RUN. Pass --step; the synthetic tests cover the algorithm but not "
                        "the 8192-sample reproducibility that the model input depends on."))

    # Three states, not two. `None` means the check could not run because its input does not
    # exist yet, which is different from failing: a script that is permanently red trains people
    # to stop reading it, and calling an unrun check a PASS would hide an unverified assumption.
    failed = sum(1 for _, ok, _ in results if ok is False)
    not_run = [r for r in results if r[1] is None]
    for name, ok, detail in results:
        tag = "PASS" if ok is True else ("FAIL" if ok is False else "NOT RUN")
        print(f"  [{tag}] {name}")
        print(f"         {detail}")

    print()
    print(f"{sum(1 for _, ok, _ in results if ok is True)} passed, {failed} failed, "
          f"{len(not_run)} not run")
    if not_run:
        print()
        print("STANDING GAPS -- not failures, but not verified either:")
        for name, _, detail in not_run:
            print(f"  * {name}")
            print(f"    {detail.splitlines()[0]}")
    print()
    if failed:
        print("A genuine failure means the model's input is not reproducible. Fix it before a")
        print("checkpoint is downloaded, or an inference anomaly cannot be attributed to the")
        print("model rather than to the data reaching it.")
    elif not_run:
        print("Everything that could be checked here passes. The gaps above are honest: until the")
        print("pytorch3d reference exists this is a COMPATIBLE deterministic FPS, not a verified")
        print("exact replacement, and the paper must use those words.")
    else:
        print("Input pipeline frozen and reproducible. The only thing left before inference is")
        print("the checkpoint itself.")

    if args.out:
        Path(args.out).write_text(json.dumps({
            "frozen": {"n_pre_points": N_PRE_POINTS, "k_points": K_POINTS, "seed": DEMO_SEED,
                       "target_extent": TARGET_EXTENT, "start_index": 0,
                       "distance": "squared euclidean",
                       "tie_breaking": "lowest index (numpy argmax)",
                       "input_order": "trimesh order, no sort, no dedup",
                       "start_index_status": "pytorch3d documented default, not verified"},
            "checks": [{"name": n,
                        "state": "pass" if p is True else ("fail" if p is False else "not_run"),
                        "detail": d} for n, p, d in results],
        }, indent=2), encoding="utf-8", newline="\n")
        print(f"\nwrote {args.out}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
