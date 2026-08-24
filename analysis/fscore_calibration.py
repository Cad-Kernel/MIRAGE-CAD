"""What is the highest F@1% a perfect reconstruction could score?

F@1% counts the fraction of sampled points on one surface that lie within 1% of the
target's bounding-box diagonal of some point on the other. Both sides are point SAMPLES,
so even two samplings of the *identical* surface disagree: nearest-neighbour spacing is
set by sampling density, not by geometric error. If that spacing exceeds the threshold,
the metric cannot reach 1 no matter how good the reconstruction is.

This measures that ceiling with no execution, no GPU and no kernel. Each reference cloud
in FllumaOne-100K holds exactly 2,048 points and the evaluation subsamples 1,024 from it,
so drawing two DISJOINT 1,024-point subsets reproduces the evaluation's density on both
sides while holding geometry exactly constant. Whatever F@1% those two halves score is
the best any reconstruction of that part could achieve.

It matters because docs SS9.13 and SS9.14 report F@1% around 0.20 and the paper reads
that as "far from geometric accuracy". If the ceiling is near 0.26, as review item B6
asserts without evidence, then 0.20 is roughly three quarters of what is attainable and
the paper's characterisation is wrong. This settles which.

Note that the target side cannot be made denser: 2,048 points is all the corpus stores.
B6's suggestion of sampling at 8,192-16,384 would require re-sampling the reference STEP
files, not merely changing a flag.

    python src/scratch/fscore_calibration.py [--limit 500]
"""
from __future__ import annotations

import argparse
import json
import statistics
import subprocess
from pathlib import Path

import numpy as np

TEST = "//wsl.localhost/Ubuntu/home/jizong/workspace/MIRAGE/src/data/25k/test.jsonl"
THRESHOLDS = [0.01, 0.02, 0.05, 0.10]


def to_local(p: str) -> Path:
    """point_path is a WSL path into the Windows drive (/mnt/c/...)."""
    p = p.replace("\\", "/")
    if p.startswith("/mnt/") and len(p) > 6:
        return Path(f"{p[5].upper()}:/{p[7:]}")
    return Path(p)


def read_rows(limit: int) -> list[dict]:
    # The UNC share is intermittently unreadable from python but fine through the shell.
    out = subprocess.run(["head", "-n", str(limit), TEST], capture_output=True, text=True)
    if out.returncode != 0 or not out.stdout.strip():
        raise SystemExit(f"could not read {TEST}\n{out.stderr}")
    return [json.loads(l) for l in out.stdout.splitlines() if l.strip()]


def f_at(dPQ: np.ndarray, dQP: np.ndarray, thr: float) -> float:
    p = float(np.mean(dPQ < thr))
    r = float(np.mean(dQP < thr))
    return 0.0 if p + r == 0 else 2 * p * r / (p + r)


def nn(P: np.ndarray, Q: np.ndarray) -> np.ndarray:
    d = ((P[:, None, :] - Q[None, :, :]) ** 2).sum(-1)
    return np.sqrt(d.min(1))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=500)
    ap.add_argument("--n", type=int, default=1024, help="points per side, as evaluated")
    args = ap.parse_args()

    rows = read_rows(args.limit)
    rng = np.random.RandomState(20260809)
    per_thr: dict[float, list[float]] = {t: [] for t in THRESHOLDS}
    cds, spacings, diags, skipped = [], [], [], 0

    for r in rows:
        f = to_local(r.get("point_path", ""))
        if not f.is_file():
            skipped += 1
            continue
        d = np.load(f)
        k = "points" if "points" in d else list(d.keys())[0]
        pts = np.asarray(d[k], dtype=np.float64)
        if pts.shape[0] < 2 * args.n:
            skipped += 1
            continue
        idx = rng.permutation(pts.shape[0])
        A, B = pts[idx[:args.n]], pts[idx[args.n:2 * args.n]]

        diag = float(np.linalg.norm(pts.max(0) - pts.min(0)))
        diags.append(diag)
        dAB, dBA = nn(A, B), nn(B, A)
        cds.append(float(0.5 * (dAB ** 2).mean() + 0.5 * (dBA ** 2).mean()))
        spacings.append(float(np.median(dAB)))
        for t in THRESHOLDS:
            per_thr[t].append(f_at(dAB, dBA, t * diag))

    n = len(cds)
    if not n:
        print("no usable rows"); return 1
    print(f"=== ceiling from {n} parts ({skipped} skipped), {args.n} points per side, "
          f"two disjoint subsets of the same reference cloud ===\n")
    print(f"  median bbox diagonal            {statistics.median(diags):8.2f} mm")
    print(f"  median nearest-neighbour spacing{statistics.median(spacings):8.4f} mm")
    print(f"  1% threshold (median part)      {0.01*statistics.median(diags):8.4f} mm")
    print(f"  -> spacing / threshold          {statistics.median(spacings)/(0.01*statistics.median(diags)):8.2f}"
          f"   (>1 means the sampling grid alone defeats the threshold)\n")
    print(f"  {'threshold':>10}{'median F':>11}{'mean F':>10}{'p10':>9}{'p90':>9}")
    for t in THRESHOLDS:
        v = sorted(per_thr[t])
        print(f"  {100*t:>9.0f}%{statistics.median(v):>11.3f}{statistics.fmean(v):>10.3f}"
              f"{v[int(0.1*len(v))]:>9.3f}{v[int(0.9*len(v))]:>9.3f}")
    print(f"\n  Chamfer between two samplings of the SAME surface: median "
          f"{statistics.median(cds):.4g} mm^2  (this is the CD noise floor)")

    ceil = statistics.median(per_thr[0.01])
    print("\n=== what this means for the reported numbers ===")
    print(f"  A perfect reconstruction scores about F@1% = {ceil:.3f} at this density.")
    for label, obs in [("prior / K=4 (docs 9.13)", 0.218), ("K=8 (docs 9.14)", 0.204),
                       ("shuffled prefix (docs 9.13)", 0.027)]:
        print(f"    {label:<28}{obs:.3f}  = {100*obs/ceil:5.1f}% of the ceiling"
              if ceil > 0 else "")
    ok = next((t for t in THRESHOLDS if statistics.median(per_thr[t]) >= 0.95), None)
    print(f"\n  Median F reaches 0.95 at a threshold of "
          + (f"{100*ok:.0f}% of the diagonal." if ok else
             "none of the thresholds tried -- the ceiling is a density limit, and the "
             "target side cannot be densified because the corpus stores only 2,048 points."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
