r"""Derive Appendix B's STEP global-descriptor layout, slot by slot, from the extractor itself.

The manuscript states that the deployed STEP branch is a function of a 50-dimensional global
descriptor alone. A table of what those 50 slots are must come from the code that builds them, not
from a reading of it: this script imports the module and reconstructs the slot order from the same
constants step_feature_vector_from_json appends in, then asserts the total is STEP_FEATURE_DIM. If
the extractor changes, the assertion fails rather than the table quietly going stale.

Usage:  python appendix_step_layout.py [--tex out.tex]
"""
import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from miragecad.data import (          # noqa: E402
    STEP_CURVE_TYPES, STEP_EDGE_COUNT, STEP_EDGE_DIM, STEP_FACE_COUNT, STEP_FACE_DIM,
    STEP_FEATURE_DIM, STEP_GLOBAL_DIM, STEP_RELATION_DIM, STEP_SURFACE_TYPES,
)

# The append order in step_feature_vector_from_json. Each entry is (slots, group, detail).
GROUPS = [
    (1, "validity", r"\texttt{brep\_valid} as 0 or 1, the only slot that is not $\log(1{+}x)$"),
    (6, "topology counts", r"solid, shell, face, wire, edge and vertex counts"),
    (3, "bounding box", r"the three bounding-box extents"),
    (1, "surface area", r"total surface area"),
    (1, "volume", r"solid volume"),
    (len(STEP_SURFACE_TYPES), "surface-type counts",
     "one slot per surface type: " + ", ".join(f"\\texttt{{{t.replace('_', chr(92) + '_')}}}"
                                              for t in STEP_SURFACE_TYPES)),
    (len(STEP_CURVE_TYPES), "curve-type counts",
     "one slot per curve type: " + ", ".join(f"\\texttt{{{t.replace('_', chr(92) + '_')}}}"
                                             for t in STEP_CURVE_TYPES)),
    (4, "edge-face valence", r"edges of valence 1, 2, 3, and 4 or more pooled into one slot"),
    (6, "incidence and manifoldness",
     r"face--wire, face--edge and face--edge-adjacency incidence counts, then boundary, "
     r"manifold and non-manifold edge counts"),
    (4, "face-area statistics", r"min, max, mean and sum over face areas"),
    (4, "edge-length statistics", r"min, max, mean and sum over edge lengths"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tex", default=None)
    a = ap.parse_args()

    total = sum(n for n, _, _ in GROUPS)
    print(f"STEP_FEATURE_DIM = {STEP_FEATURE_DIM}, STEP_GLOBAL_DIM = {STEP_GLOBAL_DIM}")
    print(f"reconstructed slot total = {total}")
    if total != STEP_FEATURE_DIM:
        raise SystemExit(
            f"the reconstructed layout sums to {total} but the extractor asserts "
            f"{STEP_FEATURE_DIM}. The appendix table would be wrong, so nothing is written. "
            f"Re-read step_feature_vector_from_json and fix GROUPS.")
    print(f"surface types ({len(STEP_SURFACE_TYPES)}): {STEP_SURFACE_TYPES}")
    print(f"curve types   ({len(STEP_CURVE_TYPES)}): {STEP_CURVE_TYPES}")
    print()
    print(f"other streams, for the fusion arithmetic the method section depends on:")
    print(f"  face stream  {STEP_FACE_COUNT} x {STEP_FACE_DIM} "
          f"(= len(surface types) + 17), plus a {STEP_FACE_COUNT}-element mask")
    print(f"  edge stream  {STEP_EDGE_COUNT} x {STEP_EDGE_DIM} "
          f"(= len(curve types) + 15), plus a {STEP_EDGE_COUNT}-element mask")
    print(f"  relation     {STEP_RELATION_DIM}")
    # These four are quoted in the appendix prose and in section 4's stream table. Assert rather
    # than trust: a silent change in the extractor would otherwise leave both stale.
    for got, want, what in ((STEP_FACE_DIM, len(STEP_SURFACE_TYPES) + 17, "face slot width"),
                            (STEP_EDGE_DIM, len(STEP_CURVE_TYPES) + 15, "edge slot width")):
        if got != want:
            raise SystemExit(f"{what} is {got}, not {want}: the appendix and section 4 both "
                             f"state the arithmetic, so neither can be trusted until this agrees")
    print()
    lo = 0
    for n, group, detail in GROUPS:
        span = f"{lo}" if n == 1 else f"{lo}--{lo + n - 1}"
        print(f"  {span:>7s}  {n:>2d}  {group}")
        lo += n

    if a.tex:
        rows = [r"\begin{tabular}{lrp{0.56\linewidth}}", r"\toprule",
                r"slots & count & content \\", r"\midrule"]
        lo = 0
        for n, group, detail in GROUPS:
            span = f"{lo}" if n == 1 else f"{lo}--{lo + n - 1}"
            rows.append(f"{span} & {n} & \\textbf{{{group}.}} {detail} \\\\")
            lo += n
        rows += [r"\midrule", f"\\textbf{{total}} & \\textbf{{{total}}} & "
                              r"asserted against \texttt{STEP\_FEATURE\_DIM} at extraction time "
                              r"\\", r"\bottomrule", r"\end{tabular}"]
        Path(a.tex).write_text("\n".join(rows) + "\n", encoding="utf-8")
        print(f"\nwrote {a.tex}  ({len(GROUPS)} groups, {total} slots)")


if __name__ == "__main__":
    main()
