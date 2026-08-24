"""Calibrate the CD sampling floor for the OCCT sampler, and compare it with trimesh's.

RUNS IN external_eval, on the clouds occt_floor_sample.py wrote from inside FllumaCLI. No model,
no GPU, no CAD kernel.

THE QUESTION. The floor relation established earlier -- about 623 * normalised_area / n -- was
calibrated on trimesh surface sampling, which is what CAD-Recode's released demo uses. The
external MIRAGE pathway samples through OCCT surface_uv instead. If the two samplers share a floor
constant, the observation that CAD-Recode's published median sits near the 8192-point floor gains
cross-sampler support. If they do not, that observation must stay confined to their released
implementation and must NOT be restated as a property of our external evaluation.

WHY THE HEADLINE QUANTITY IS SPACING AND NOT AREA. Expressing the floor as area/n assumes the
sampler spreads points uniformly by area. OCCT surface_uv distributes points per face in UV space,
which need not be area-uniform at all, and no amount of care in the evaluator would fix that. So
the primary statistic here is

    floor / (mean within-cloud nearest-neighbour distance)^2

which is measured rather than assumed: it uses the density the sampler actually produced. If a
sampler over-samples small faces, the observed spacing reflects it and this ratio stays stable,
where floor*n/area would drift. Both are reported, and which one holds is the finding.

The instruction taken from the plan, and honoured: if the ratio fails, record that the floor is
sampler-dependent. Do not adjust the sampler to preserve a constant.
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from external_geometry_eval import (CD_FLOOR_CONST, chamfer_x1000,  # noqa: E402
                                    normalise_per_shape)


def normalise_cloud(p: np.ndarray) -> np.ndarray:
    """The same per-shape map the evaluator applies, expressed on points.

    Centre on the bounding-box midpoint and scale the largest extent to 1.0. Identical in intent
    to normalise_per_shape for meshes, so floors from the two samplers are on one scale.
    """
    lo, hi = p.min(axis=0), p.max(axis=0)
    q = p - (lo + hi) / 2.0
    ext = float((hi - lo).max())
    if ext > 0:
        q = q / ext
    return q + 0.5


def mean_nn_within(p: np.ndarray) -> float:
    """Mean nearest-neighbour distance inside one cloud: the density the sampler produced."""
    from scipy.spatial import cKDTree
    d, _ = cKDTree(p).query(p, k=2)      # k=1 is the point itself
    return float(np.mean(d[:, 1]))


def resolve_npz(rec: dict, sample_dir: Path) -> Path | None:
    r"""Locate a cloud without trusting the path recorded in the log.

    The sampler runs inside FllumaCLI on Windows, so the log records `C:\...` paths, and this
    analyzer runs in a WSL conda environment where those do not exist. Rather than translate
    between path conventions, prefer the directory the caller passed plus the recorded basename:
    whoever invoked this knows where the clouds are, and the naming convention is fixed at
    {sample_id}__n{n}__s{seed}.npz.
    """
    recorded = str(rec.get("npz", ""))
    base = recorded.replace("\\", "/").rsplit("/", 1)[-1]
    for cand in (sample_dir / base, Path(recorded)):
        if cand.exists():
            return cand
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample-dir", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    d = Path(args.sample_dir)
    log = d / "sampling_log.jsonl"
    if not log.exists():
        print(f"FAIL no sampling_log.jsonl in {d}", file=sys.stderr)
        return 1

    by_key: dict[tuple[str, int], list[dict]] = defaultdict(list)
    diags: dict[str, dict] = {}
    for line in log.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("status") != "ok":
            continue
        by_key[(r["sample_id"], r["n"])].append(r)
        if "points_per_face_imbalance" in r:
            diags[r["sample_id"]] = r

    rows, missing = [], []
    for (sid, n), recs in sorted(by_key.items()):
        if len(recs) < 2:
            continue                      # one draw compared with itself measures nothing
        pa_path, pb_path = resolve_npz(recs[0], d), resolve_npz(recs[1], d)
        if pa_path is None or pb_path is None:
            missing.append((sid, n))
            continue
        a = np.load(pa_path)["points"].astype(np.float64)
        b = np.load(pb_path)["points"].astype(np.float64)
        na, nb = normalise_cloud(a), normalise_cloud(b)
        floor = chamfer_x1000(na, nb)
        sp = (mean_nn_within(na) + mean_nn_within(nb)) / 2.0
        rows.append({"sample_id": sid, "n": n, "floor": floor, "spacing": sp,
                     "floor_over_spacing_sq": floor / (sp * sp) if sp > 0 else float("nan"),
                     "floor_times_n": floor * n,
                     "implied_area": n * sp * sp})
    if missing:
        print(f"note: {len(missing)} (shape, n) pair(s) had log entries but no readable npz, "
              f"e.g. {missing[:2]}. Skipped rather than counted as zero.", file=sys.stderr)
    if not rows:
        print("FAIL no shape has two independent draws with readable clouds. If the log records "
              "Windows paths and this is running under WSL, pass --sample-dir pointing at the "
              "clouds; the recorded paths are not trusted.", file=sys.stderr)
        return 1

    print("=" * 78)
    print("OCCT surface_uv sampling floor")
    print("=" * 78)

    shapes = sorted({r["sample_id"] for r in rows})
    ns = sorted({r["n"] for r in rows})
    print(f"\n{len(shapes)} shape(s), point counts {ns}\n")

    # ---- 1. across shapes at the largest common point count -----------------------
    n_top = ns[-1]
    at_top = [r for r in rows if r["n"] == n_top]
    if len(at_top) > 1:
        k = [r["floor_over_spacing_sq"] for r in at_top]
        kn = [r["floor_times_n"] for r in at_top]
        print(f"--- across shapes at n = {n_top} ---")
        print(f"  floor                    min {min(r['floor'] for r in at_top):.4f}  "
              f"median {st.median(r['floor'] for r in at_top):.4f}  "
              f"max {max(r['floor'] for r in at_top):.4f}")
        print(f"  floor / spacing^2        min {min(k):.1f}  median {st.median(k):.1f}  "
              f"max {max(k):.1f}   spread {max(k)/min(k):.2f}x")
        print(f"  floor * n                spread {max(kn)/min(kn):.2f}x  "
              f"(expected to vary: shapes differ in area)")

    # ---- 2. across point counts, per shape ---------------------------------------
    print(f"\n--- across point counts ---")
    for sid in shapes:
        rs = sorted([r for r in rows if r["sample_id"] == sid], key=lambda r: r["n"])
        if len(rs) < 2:
            continue
        ks = [r["floor_over_spacing_sq"] for r in rs]
        print(f"  {sid}")
        print("    " + "  ".join(f"n{r['n']}:{r['floor']:.3f}" for r in rs))
        print(f"    floor/spacing^2: " + "  ".join(f"{k:.1f}" for k in ks)
              + f"   spread {max(ks)/min(ks):.2f}x")

    # ---- 3. the trimesh constant, on the same footing ----------------------------
    print(f"\n--- the same statistic for trimesh sampling, for comparison ---")
    tri = {}
    try:
        import trimesh
        from external_geometry_eval import sample_surface
        prims = {
            "box 2x1x0.5": trimesh.creation.box(extents=(2.0, 1.0, 0.5)),
            "cylinder r0.5 h2": trimesh.creation.cylinder(radius=0.5, height=2.0),
            "sphere r1": trimesh.creation.icosphere(subdivisions=3, radius=1.0),
        }
        for name, m in prims.items():
            mn = normalise_per_shape(m)
            pa, pb = sample_surface(mn, n_top, 0), sample_surface(mn, n_top, 1)
            f = chamfer_x1000(pa, pb)
            sp = (mean_nn_within(pa) + mean_nn_within(pb)) / 2.0
            tri[name] = (f, f / (sp * sp), f * n_top / float(mn.area))
            print(f"  {name:20s} floor {f:.4f}  floor/spacing^2 {f/(sp*sp):.1f}  "
                  f"floor*n/area {f*n_top/float(mn.area):.1f}")
    except Exception as e:
        print(f"  unavailable: {type(e).__name__}: {e}")

    # ---- 4. sampler distribution diagnostics ------------------------------------
    if diags:
        imb = [v["points_per_face_imbalance"] for v in diags.values()]
        nf = [v.get("n_faces_hit", 0) for v in diags.values()]
        print(f"\n--- sampler distribution, from face_ids ---")
        print(f"  faces hit            min {min(nf)}  median {st.median(nf):.0f}  max {max(nf)}")
        print(f"  points-per-face max/min  min {min(imb):.1f}  median {st.median(imb):.1f}  "
              f"max {max(imb):.1f}")
        print(f"  A large imbalance means surface_uv is not area-uniform, which is exactly why")
        print(f"  the headline statistic is spacing-based rather than area-based.")

    # ---- verdict ----------------------------------------------------------------
    print("\n" + "=" * 78)
    if len(at_top) > 1:
        k = [r["floor_over_spacing_sq"] for r in at_top]
        spread = max(k) / min(k)
        occt_k = st.median(k)
        print(f"OCCT floor / spacing^2  =  {occt_k:.1f}   (spread {spread:.2f}x across shapes)")
        if tri:
            tri_k = st.median(v[1] for v in tri.values())
            print(f"trimesh same statistic  =  {tri_k:.1f}")
            ratio = occt_k / tri_k if tri_k else float("nan")
            print(f"ratio                   =  {ratio:.2f}x")
            if 0.8 < ratio < 1.25:
                print("\nThe two samplers share a floor law once it is expressed in terms of the")
                print("spacing they actually produce. The observation about CAD-Recode's published")
                print("median therefore has cross-sampler support and may be stated for the")
                print("external evaluation as a whole.")
            else:
                print("\nThe constants DIFFER. The floor is sampler-dependent, so the observation")
                print("about CAD-Recode's published median must stay confined to their released")
                print("implementation and must not be restated as a property of our external")
                print("evaluation. Record this rather than adjusting the sampler.")
        print(f"\nFor reference, the area-based constant calibrated on trimesh was "
              f"{CD_FLOOR_CONST:.0f}; it is not assumed to transfer.")

    if args.out:
        Path(args.out).write_text(
            json.dumps({"rows": rows, "trimesh": {k: list(v) for k, v in tri.items()},
                        "diagnostics": diags}, indent=2),
            encoding="utf-8", newline="\n")
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
