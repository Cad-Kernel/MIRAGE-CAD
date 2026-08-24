"""Does it matter whether external reference clouds come from the .step or the .obj?

The case for the .step is that SurfaceUV sampling lands exact points on the analytic B-Rep
surface, while the .obj is a triangulation whose approximation error concentrates on
cylinders, holes and fillets -- the very features that separate a good reconstruction from a
bad one -- and that the generated clouds come from the same sampler, so no fixed bias enters
the comparison. The case for the .obj is independence: sampling the reference with the same
kernel that builds the candidates could be said to cancel kernel artifacts in our favour.

Rather than argue it, measure it. Both files ship for every model, so the two reference
clouds for the same part can be compared directly. If they agree to within the sampling
noise floor already calibrated on this set, the choice provably does not matter and one
sentence disposes of the question. If they disagree, the size and direction of the
disagreement is itself the answer.

The .obj is in centimetres and the .step arrives in millimetres (the file declares
CENTIMETRE and OpenCASCADE converts), so the obj is scaled by ten before comparison. That
factor is not assumed: it is verified per part against the bounding boxes, and any part
where it does not hold is reported rather than silently rescaled.

    python src/scratch/obj_vs_step_reference.py [n]
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent.parent
QUERIES = REPO / "scratch" / "ext_queries.jsonl"
SEED = 20260810
N_EVAL = 1024                      # evaluate_geometry_nbest.py --point-count default
OBJ_TO_STEP = 10.0                 # cm -> mm

# Calibrated on this set, same 1024-vs-1024 protocol (docs 9.19)
FLOOR_ALL = 1.958
FLOOR_WITHIN = 0.660
CORPUS_MAX_DIAG = 134.30


def read_obj(path: Path):
    verts, tris = [], []
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith("v "):
                p = line.split()
                verts.append((float(p[1]), float(p[2]), float(p[3])))
            elif line.startswith("f "):
                idx = [int(t.split("/")[0]) for t in line.split()[1:]]
                idx = [i - 1 if i > 0 else len(verts) + i for i in idx]
                for k in range(1, len(idx) - 1):
                    tris.append((idx[0], idx[k], idx[k + 1]))
    if len(verts) < 3 or not tris:
        return None
    return np.asarray(verts, float), np.asarray(tris, int)


def sample_surface(v, f, n, seed):
    """Area-weighted uniform surface sampling, verified on a unit cube (six faces 0.165-0.169)."""
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    areas = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    tot = areas.sum()
    if not np.isfinite(tot) or tot <= 0:
        return None
    rng = np.random.RandomState(seed)
    pick = rng.choice(len(f), size=n, p=areas / tot)
    u, w = rng.random_sample((n, 1)), rng.random_sample((n, 1))
    su = np.sqrt(u)
    return (1 - su) * a[pick] + su * (1 - w) * b[pick] + su * w * c[pick]


def nn(a, b):
    out = np.empty(len(a))
    for i in range(0, len(a), 512):
        ch = a[i:i + 512]
        out[i:i + 512] = np.sqrt(((ch[:, None, :] - b[None, :, :]) ** 2).sum(-1).min(1))
    return out


def main() -> int:
    n_parts = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    rows = [json.loads(l) for l in QUERIES.read_text(encoding="utf-8").splitlines() if l.strip()]
    rng = np.random.RandomState(SEED)

    cds, cds_norm, scale_bad, skipped = [], [], [], 0
    within, beyond = [], []

    for r in rows[:n_parts]:
        obj = Path(r["step_path"]).with_suffix(".obj")
        if not obj.is_file():
            skipped += 1
            continue
        m = read_obj(obj)
        if m is None:
            skipped += 1
            continue
        po = sample_surface(*m, 8192, SEED)
        if po is None:
            skipped += 1
            continue
        po = po * OBJ_TO_STEP
        try:
            ps = np.asarray(np.load(r["point_path"])["points"], float)
        except Exception:
            skipped += 1
            continue

        do = float(np.linalg.norm(po.max(0) - po.min(0)))
        ds = float(np.linalg.norm(ps.max(0) - ps.min(0)))
        if not (0.98 < do / ds < 1.02):
            scale_bad.append((r["external_id"], do, ds))
            continue

        i1, i2 = rng.permutation(len(po))[:N_EVAL], rng.permutation(len(ps))[:N_EVAL]
        A, B = po[i1], ps[i2]
        dAB, dBA = nn(A, B), nn(B, A)
        cd = 0.5 * (dAB ** 2).mean() + 0.5 * (dBA ** 2).mean()
        cds.append(cd)
        cds_norm.append(cd / ds ** 2)
        (within if r["bbox_diag"] <= CORPUS_MAX_DIAG else beyond).append(cd)

    if not cds:
        print("nothing comparable")
        return 1

    med = statistics.median
    print(f"compared {len(cds)} parts, skipped {skipped}, scale mismatch {len(scale_bad)}")
    for pid, do, ds in scale_bad[:5]:
        print(f"  ** {pid}: obj*10 diag {do:.1f} vs step diag {ds:.1f} -- not a factor of ten **")
    print()
    print("obj-sampled reference vs step-sampled reference, same part, 1024 vs 1024:")
    print(f"  Chamfer   median {med(cds):.4g}   p90 {sorted(cds)[int(0.9*len(cds))]:.4g}")
    print(f"  / diag^2  median {med(cds_norm):.3g}")
    if within:
        print(f"  within corpus scale (n={len(within)})  median {med(within):.4g}")
    if beyond:
        print(f"  beyond corpus scale (n={len(beyond)})  median {med(beyond):.4g}")
    print()
    print("against the sampling noise floor calibrated on this set (docs 9.19):")
    print(f"  floor, all 400            {FLOOR_ALL}")
    print(f"  floor, within corpus scale {FLOOR_WITHIN}")
    print()
    r_all = med(cds) / FLOOR_ALL
    print(f"  obj-vs-step disagreement is {r_all:.2f}x the noise floor")
    if r_all < 1.5:
        print("  ==> Within sampling noise. The choice of source file does not measurably")
        print("      change the reference cloud, so the .step is preferred on the other")
        print("      grounds -- exact surface points and one sampler on both sides -- with")
        print("      nothing riding on it.")
    elif r_all < 5:
        print("  ==> Distinguishable from noise but small. Report which source was used and")
        print("      this ratio; do not mix sources within a table.")
    else:
        print("  ==> The two references genuinely disagree. Find out where before scoring")
        print("      anything: check whether the gap tracks curved-surface content, which")
        print("      would confirm the tessellation explanation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
