"""How far outside the corpus does the external STEP descriptor actually land?

The bbox check said 35.5% of the external parts are larger than anything in FllumaOne. But
bbox is one number and the encoder reads fifty, so that fraction neither bounds nor
characterises the shift. This computes the real descriptor
(miragecad.data.step_feature_vector_from_json, the same function the model is fed) for both
sets and compares them dimension by dimension.

The split that matters is inside the descriptor itself. Thirteen of the fifty dimensions are
absolute magnitudes -- the three bbox extents, surface area, volume, and the four-way min /
max / mean / sum summaries of face area and edge length -- and those move when a part is
simply scaled. The other thirty-seven are counts and topology, and a scaled part gives
identical values. So if the external set is out of range mainly on the thirteen, the problem
is scale and says nothing about whether the corpus holds compatible construction history; if
the thirty-seven are also out of range, the geometry itself is unfamiliar and that is the
finding C-EXT1 exists to report.

Out-of-range is measured against the corpus p1-p99 per dimension rather than min-max, so a
single odd corpus part cannot widen a range to cover everything.

    python src/scratch/external_descriptor_shift.py
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from miragecad.data import STEP_FEATURE_DIM, step_feature_vector_from_json  # noqa: E402

CORPUS_INDEX = REPO.parent / "scratch" / "corpus_step_train.jsonl"
EXT_FEATURES = REPO.parent / "scratch" / "ext_step" / "features"
EXT_QUERIES = REPO.parent / "scratch" / "ext_queries.jsonl"
CORPUS_MAX_DIAG = 134.30

# Index positions of the magnitude dimensions, in the order data.py appends them:
#   0            brep_valid
#   1-6          solid/shell/face/wire/edge/vertex counts
#   7,8,9        bbox size x,y,z          <- magnitude
#   10           surface_area             <- magnitude
#   11           volume                   <- magnitude
# then surface-type counts, curve-type counts, valences, incidences, and finally
#   last 8       face_area min/max/mean/sum, edge_length min/max/mean/sum  <- magnitude
SCALE_DIMS = [7, 8, 9, 10, 11] + list(range(STEP_FEATURE_DIM - 8, STEP_FEATURE_DIM))


def corpus_vectors(start: int = 0, limit: int = 3000) -> np.ndarray:
    """Read the corpus descriptors through their per-sample feature files.

    The start offset exists so a second, disjoint slice can serve as an in-distribution
    CONTROL. Without one, "19% of external parts are fully inside the corpus range" cannot
    be read at all: fifty dimensions each at p1-p99 will put plenty of ordinary corpus parts
    outside too, and how many is not something to estimate -- the dimensions are strongly
    correlated, so the independent-coordinate guess of 0.98^50 is far too pessimistic. The
    measured control is 84.7%.
    """
    out = []
    with open(CORPUS_INDEX, encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if i < start:
                continue
            if len(out) >= limit:
                break
            row = json.loads(line)
            p = row.get("step_feature_path", "")
            # the index stores WSL-absolute paths; this may run on either side
            for cand in (Path(p), Path(p.replace("/mnt/c/", "C:/"))):
                if cand.is_file():
                    try:
                        out.append(step_feature_vector_from_json(
                            json.loads(cand.read_text(encoding="utf-8"))))
                    except Exception:
                        pass
                    break
    return np.asarray(out) if out else np.empty((0, STEP_FEATURE_DIM))


def external_vectors() -> tuple[np.ndarray, list[str]]:
    vecs, ids = [], []
    for f in sorted(EXT_FEATURES.glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            vecs.append(step_feature_vector_from_json(d))
            ids.append(d.get("sample_id", f.stem))
        except Exception:
            continue
    return (np.asarray(vecs) if vecs else np.empty((0, STEP_FEATURE_DIM))), ids


def report(ext: np.ndarray, lo: np.ndarray, hi: np.ndarray, label: str) -> None:
    if not len(ext):
        print(f"\n--- {label}: empty ---")
        return
    below, above = ext < lo, ext > hi
    outside = below | above

    scale_mask = np.zeros(STEP_FEATURE_DIM, dtype=bool)
    scale_mask[SCALE_DIMS] = True
    shape_mask = ~scale_mask

    print(f"\n--- {label}: n={len(ext)} ---")
    print(f"  dims outside corpus p1-p99, per part (median of {STEP_FEATURE_DIM}):")
    print(f"    all dims          {np.median(outside.sum(1)):.0f}")
    print(f"    magnitude ({scale_mask.sum():2d})    {np.median(outside[:, scale_mask].sum(1)):.0f}")
    print(f"    count/topo ({shape_mask.sum():2d})   {np.median(outside[:, shape_mask].sum(1)):.0f}")
    print(f"  parts fully inside the corpus range: "
          f"{100 * float((outside.sum(1) == 0).mean()):.1f}%")
    print(f"  parts inside on every count/topo dim: "
          f"{100 * float((outside[:, shape_mask].sum(1) == 0).mean()):.1f}%")

    worst = np.argsort(-outside.mean(0))[:8]
    print("  most-often-outside dimensions:")
    for d in worst:
        if not outside[:, d].any():
            break
        kind = "magnitude" if scale_mask[d] else "count/topo"
        print(f"    dim {d:2d} ({kind:10s})  {100 * float(outside[:, d].mean()):5.1f}% outside"
              f"   corpus p1-p99 [{lo[d]:.3g}, {hi[d]:.3g}]"
              f"   external median {np.median(ext[:, d]):.3g}")


def main() -> int:
    if not EXT_FEATURES.is_dir():
        print(f"external features not found at {EXT_FEATURES}")
        return 1
    if not CORPUS_INDEX.is_file():
        print(f"corpus index not found at {CORPUS_INDEX}")
        return 1

    corpus = corpus_vectors()
    print(f"corpus descriptors: {corpus.shape}")
    if not len(corpus):
        print("  ** could not read any corpus feature file; check step_feature_path **")
        return 1

    ext, ids = external_vectors()
    print(f"external descriptors: {ext.shape}")
    if not len(ext):
        return 1

    lo = np.percentile(corpus, 1, axis=0)
    hi = np.percentile(corpus, 99, axis=0)

    control = corpus_vectors(start=3000, limit=3000)
    if len(control):
        report(control, lo, hi, "CONTROL: held-out corpus, in-distribution")
    else:
        print("\n  ** no control slice; the external rows below are uncalibrated **")

    diag = {}
    if EXT_QUERIES.is_file():
        for line in EXT_QUERIES.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                diag[r["sample_id"]] = r["bbox_diag"]

    report(ext, lo, hi, "all external")
    if diag:
        inside_idx = [i for i, s in enumerate(ids) if diag.get(s, 1e9) <= CORPUS_MAX_DIAG]
        beyond_idx = [i for i, s in enumerate(ids) if diag.get(s, 1e9) > CORPUS_MAX_DIAG]
        if inside_idx:
            report(ext[inside_idx], lo, hi, f"within corpus scale (<= {CORPUS_MAX_DIAG} mm)")
        if beyond_idx:
            report(ext[beyond_idx], lo, hi, "beyond corpus scale")

    print("\n=== how to read this ===")
    print("  If the magnitude dimensions are the ones outside and the count/topology")
    print("  dimensions sit inside, the external parts are structurally familiar and only")
    print("  differently sized -- a STEP-arm failure would then be a scale result. If the")
    print("  count/topology dimensions are also outside, the geometry itself is unfamiliar,")
    print("  and that is a genuine cross-source finding rather than a units artifact.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
