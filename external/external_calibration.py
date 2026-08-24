"""What can the geometry metrics express on the external set, at the density we score at?

The build phase printed a calibration computed from two 4,096-point halves, which is not
what evaluation does. evaluate_geometry_nbest.py defaults to --point-count 1024 and
subsamples both the target npz and the generated part to that, so the ceiling that matters
is what two independent 1,024-point samplings of ONE shape score against each other. This
recomputes it under the scorer's own protocol, which is also the protocol the internal
ceiling of 0.244 was measured under -- so the two become comparable.

It also answers a question the inventory raised. FllumaOne bbox diagonals run 9 to 134 mm
with a p99 of 128; the external median is 167. Since the STEP descriptor carries bbox,
area and volume under log1p as ABSOLUTE quantities, parts beyond the corpus range are
extrapolation for the encoder, and a failure there says nothing about whether the index
holds compatible construction history. The set is not filtered -- trimming the published
test split would both spoil the sampling frame and look like dropping the hard cases -- so
instead every part is tagged and the calibration is reported for each stratum.

And Chamfer in mm^2 does not survive the crossing. It scales with the square of part size,
and external parts reach 1,780 mm against a corpus maximum of 134, so absolute Chamfer is
not comparable between the two sets in either direction. Both raw and bbox-normalized
figures are printed; the normalized one is what an external table can carry.

    python src/scratch/external_calibration.py
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "training_25k" / "scripts"))

SEED = 20260810
N_EVAL = 1024                       # evaluate_geometry_nbest.py --point-count default
CORPUS_MAX = 134.30                 # measured over 400 released FllumaOne clouds
CORPUS_P99 = 127.75

CANDIDATES = [
    Path(r"\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\data\external\fusion360"),
    Path("/home/jizong/workspace/MIRAGE/src/data/external/fusion360"),
    Path("/mnt/c/Workspace/Project/Paper/MIRAGE-V2/scratch/ext_build"),
]


def find_dir() -> Path | None:
    for c in CANDIDATES:
        if (c / "queries.jsonl").is_file():
            return c
    return None


def pairwise_min(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Nearest-neighbour distance from every a to the closest b, in chunks.

    1024x1024 is small, but the chunking keeps this honest if the density is raised.
    """
    out = np.empty(len(a))
    step = 512
    for i in range(0, len(a), step):
        chunk = a[i:i + step]
        d = ((chunk[:, None, :] - b[None, :, :]) ** 2).sum(-1)
        out[i:i + step] = np.sqrt(d.min(1))
    return out


def calibrate(rows: list[dict], label: str) -> dict | None:
    """Two disjoint N_EVAL-point draws from one cloud: the best any reconstruction can do."""
    rng = np.random.RandomState(SEED)
    f_at = {0.01: [], 0.02: [], 0.05: []}
    cd_raw, cd_norm, spacing = [], [], []
    skipped = 0

    for r in rows:
        try:
            pts = np.asarray(np.load(r["point_path"])["points"], dtype=np.float64)
        except Exception:
            skipped += 1
            continue
        if len(pts) < 2 * N_EVAL:
            skipped += 1
            continue
        idx = rng.permutation(len(pts))
        A, B = pts[idx[:N_EVAL]], pts[idx[N_EVAL:2 * N_EVAL]]
        dAB, dBA = pairwise_min(A, B), pairwise_min(B, A)

        diag = r["bbox_diag"]
        cd = 0.5 * (dAB ** 2).mean() + 0.5 * (dBA ** 2).mean()
        cd_raw.append(cd)
        cd_norm.append(cd / (diag ** 2))
        spacing.append(float(np.median(dAB)) / diag)
        for t in f_at:
            thr = t * diag
            p, rc = float((dAB < thr).mean()), float((dBA < thr).mean())
            f_at[t].append(0.0 if p + rc == 0 else 2 * p * rc / (p + rc))

    if not cd_raw:
        print(f"\n--- {label}: nothing usable ({skipped} skipped) ---")
        return None

    med = statistics.median
    print(f"\n--- {label}: n={len(cd_raw)}"
          + (f", {skipped} skipped" if skipped else "") + " ---")
    print(f"  bbox diagonal            median {med(r['bbox_diag'] for r in rows):.4g}")
    print(f"  nn spacing / diagonal    median {med(spacing):.5f}")
    for t in sorted(f_at):
        print(f"  F@{100*t:.0f}% ceiling          median {med(f_at[t]):.3f}   "
              f"mean {statistics.fmean(f_at[t]):.3f}")
    print(f"  Chamfer floor, raw mm^2  median {med(cd_raw):.4g}   "
          f"(p90 {sorted(cd_raw)[int(0.9*len(cd_raw))]:.4g})")
    print(f"  Chamfer floor / diag^2   median {med(cd_norm):.3g}")
    return {"n": len(cd_raw), "f1": med(f_at[0.01]), "cd_raw": med(cd_raw),
            "cd_norm": med(cd_norm)}


def main() -> int:
    d = find_dir()
    if d is None:
        print("queries.jsonl not found. Tried:")
        for c in CANDIDATES:
            print(f"  {c}")
        return 1
    print(f"=== {d} ===")

    rows = [json.loads(l) for l in (d / "queries.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"  {len(rows)} queries")

    # ---- scale, against the corpus the encoder was trained on -----------------
    diags = sorted(r["bbox_diag"] for r in rows)
    n = len(diags)
    print("\n=== scale distribution ===")
    for p in (0, 5, 25, 50, 75, 95, 100):
        print(f"  p{p:3d}  {diags[min(n - 1, int(p / 100 * n))]:9.2f}")
    inside = [r for r in rows if r["bbox_diag"] <= CORPUS_MAX]
    beyond = [r for r in rows if r["bbox_diag"] > CORPUS_MAX]
    print(f"\n  corpus range is 9.18 to {CORPUS_MAX} mm (p99 {CORPUS_P99})")
    print(f"  within it   {len(inside):4d}  ({100*len(inside)/n:.1f}%)")
    print(f"  beyond it   {len(beyond):4d}  ({100*len(beyond)/n:.1f}%)"
          f"   up to {diags[-1]:.0f} mm, {diags[-1]/CORPUS_MAX:.0f}x the corpus maximum")
    print()
    print("  The STEP descriptor carries bbox, area and volume under log1p as absolute")
    print("  quantities, so the parts beyond that range are extrapolation for the encoder.")
    print("  A failure there is a scale result, not an index result -- which is why the")
    print("  A-vs-B discriminator can only be read on the within-range stratum.")

    # ---- the ceilings, at the density the scorer uses -------------------------
    print(f"\n=== calibration at {N_EVAL} vs {N_EVAL} points (the scorer's default) ===")
    calibrate(rows, "all 400")
    if inside:
        calibrate(inside, f"within corpus scale (<= {CORPUS_MAX} mm)")
    if beyond:
        calibrate(beyond, f"beyond corpus scale (> {CORPUS_MAX} mm)")

    print("\n=== how to use these ===")
    print("  The internal ceiling is F@1% = 0.244 and the internal noise floor is")
    print("  1.963 mm^2, both measured at 1024 points on FllumaOne parts. The F@1%")
    print("  numbers above ARE comparable with 0.244, since the density and the")
    print("  threshold rule now match. The raw Chamfer figures are NOT comparable with")
    print("  1.963: Chamfer grows with the square of part size and these parts are")
    print("  larger, so external tables should carry the bbox-normalized column.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
