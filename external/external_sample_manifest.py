"""Build the paired sample manifest for the CAD-Recode external comparison.

WHY THIS RUNS BEFORE ANY MODEL. A side-by-side percentage is meaningless unless both arms were
scored on the same rows, and "both produced 400 numbers" is not the same statement as "both
produced numbers for the same 400 ids". This builds the row-level record that every later paired
analysis is read against, and it aborts rather than warns on the three conditions that would make
a paired analysis a lie.

IT ALSO REPORTS WHAT DOES NOT EXIST YET, which today is most of it: there are no meshes on disk,
for the ground truth or for either arm's predictions. That is not an error, it is the work list,
and printing it as a work list is the point of running this now.

TWO ACCOUNTINGS, ALWAYS BOTH. The manifest never reduces itself to the rows where both methods
succeeded. Every summary reports:

  * unconditional -- the denominator is every common input id, and a failure to produce geometry
    counts as a failure of the system, not as a missing data point;
  * paired-valid -- only rows where both arms produced usable geometry, which is the only basis on
    which CD and IoU can be compared at all.

Taking each method's successful subset and comparing those is the mistake this project already
made once, when a conditional median got printed beside a paired sign test and read as the same
quantity. Reporting both is how that stops happening.

PER-SAMPLE RESOLUTION, NOT A GLOBAL ONE. `expected_cd_floor_8192` is computed for each row from
its own ground-truth surface area, using the relation verified in external_geometry_eval.py:
floor is approximately CD_FLOOR_CONST * normalised_area / n_points, to about 3 % over 1024..8192
points. A CD difference smaller than a row's own floor is not a difference for that row, and a
single global 0.137 would hide that the floor varies with shape.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

N_POINTS = 8192
CD_FLOOR_CONST = 623.0   # verified in external_geometry_eval.py tests 7 and 8, +-3 %

FIELDS = [
    "sample_id",
    "gt_step_path", "gt_mesh_path", "point_cloud_path",
    "mirage_prediction_path", "mirage_exists", "mirage_exec_status", "mirage_mesh_path",
    "cadrecode_prediction_path", "cadrecode_exists", "cadrecode_exec_status",
    "cadrecode_mesh_path",
    "eligible_for_cd", "eligible_for_iou", "paired_valid_geometry",
    "gt_normalized_area", "expected_cd_floor_8192",
    "notes",
]


# ---------------------------------------------------------------------------
# Path handling. This project spans a Windows checkout and a WSL tree, and the recorded paths use
# whichever convention the writing process had. Resolving all three forms means a manifest built
# from either side agrees with one built from the other.
# ---------------------------------------------------------------------------
def resolve(path: str | None) -> str | None:
    """Return the first form of `path` that exists, or None."""
    if not path:
        return None
    cands = [path]
    p = path.replace("\\", "/")
    if p.startswith("/mnt/c/"):
        cands += ["C:/" + p[len("/mnt/c/"):]]
    if len(p) > 2 and p[1] == ":":
        cands += ["/mnt/" + p[0].lower() + "/" + p[3:]]
    if p.startswith("/home/"):
        cands += ["//wsl.localhost/Ubuntu" + p]
    if p.startswith("//wsl.localhost/Ubuntu/"):
        cands += [p[len("//wsl.localhost/Ubuntu"):]]
    for c in cands:
        try:
            if os.path.exists(c):
                return c
        except OSError:
            continue
    return None


def read_jsonl(path: str | None) -> list[dict]:
    r = resolve(path)
    if not r:
        return []
    out = []
    with open(r, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def gt_area_and_floor(mesh_path: str | None) -> tuple[float | None, float | None]:
    """Normalised surface area and the CD floor it implies. None when no mesh exists yet."""
    r = resolve(mesh_path)
    if not r:
        return None, None
    try:
        import trimesh
        from external_geometry_eval import normalise_per_shape
        m = trimesh.load_mesh(r)
        area = float(normalise_per_shape(m).area)
        return area, CD_FLOOR_CONST * area / N_POINTS
    except Exception:
        return None, None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rows", default="/mnt/c/../data/external/fusion360/rows.jsonl",
                    help="the input universe; every common id comes from here")
    ap.add_argument("--queries", default=None,
                    help="queries.jsonl, for the STEP paths rows.jsonl does not carry")
    ap.add_argument("--mirage-pred", default=None, help="MIRAGE prediction jsonl")
    ap.add_argument("--cadrecode-pred", default=None, help="CAD-Recode prediction jsonl")
    ap.add_argument("--gt-mesh-dir", default=None,
                    help="where tessellated ground-truth meshes are or will be")
    ap.add_argument("--mirage-mesh-dir", default=None)
    ap.add_argument("--cadrecode-mesh-dir", default=None)
    ap.add_argument("--mesh-ext", default="stl")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--require-paired", action="store_true",
                    help="abort unless both arms cover exactly the same id set")
    args = ap.parse_args()

    rows = read_jsonl(args.rows)
    if not rows:
        print(f"FAIL cannot read rows: {args.rows}", file=sys.stderr)
        return 1
    queries = {q["sample_id"]: q for q in read_jsonl(args.queries)} if args.queries else {}

    # ---- fail-fast 1: duplicate ids -------------------------------------------
    ids = [r["sample_id"] for r in rows]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        print(f"FAIL {len(dupes)} duplicate sample_id in the input universe, e.g. "
              f"{sorted(dupes)[:3]}. A duplicate silently double-weights a row in every "
              f"aggregate, so this aborts.", file=sys.stderr)
        return 1

    mirage = {r["sample_id"]: r for r in read_jsonl(args.mirage_pred)}
    cadrec = {r["sample_id"]: r for r in read_jsonl(args.cadrecode_pred)}

    # ---- fail-fast 2: paired coverage, only when pairing is requested ---------
    if args.require_paired:
        a, b = set(mirage), set(cadrec)
        if a != b:
            print(f"FAIL paired evaluation requested but the id sets differ: "
                  f"MIRAGE-only {len(a - b)}, CAD-Recode-only {len(b - a)}, shared {len(a & b)}. "
                  f"Comparing marginal rates over different rows is not a paired comparison.",
                  file=sys.stderr)
            return 1

    out_rows, notes_count = [], {}
    for r in rows:
        sid = r["sample_id"]
        q = queries.get(sid, {})
        step = resolve(q.get("step_path_wsl") or q.get("step_path") or r.get("step_path"))
        cloud = resolve(r.get("point_path") or q.get("point_path_wsl"))

        def mesh_of(d):
            return str(Path(d) / f"{sid}.{args.mesh_ext}") if d else None

        gt_mesh = mesh_of(args.gt_mesh_dir)
        mi_mesh = mesh_of(args.mirage_mesh_dir)
        cr_mesh = mesh_of(args.cadrecode_mesh_dir)
        gt_mesh_r, mi_mesh_r, cr_mesh_r = resolve(gt_mesh), resolve(mi_mesh), resolve(cr_mesh)

        area, floor = gt_area_and_floor(gt_mesh_r)

        note = []
        if not step:
            note.append("no_gt_step")
        if not cloud:
            note.append("no_point_cloud")
        if not gt_mesh_r:
            note.append("gt_mesh_not_tessellated")
        for n in note:
            notes_count[n] = notes_count.get(n, 0) + 1

        row = {
            "sample_id": sid,
            "gt_step_path": step or "",
            "gt_mesh_path": gt_mesh_r or (gt_mesh or ""),
            "point_cloud_path": cloud or "",
            "mirage_prediction_path": args.mirage_pred or "",
            "mirage_exists": sid in mirage,
            "mirage_exec_status": ("not_executed" if sid in mirage else "no_prediction")
                                  if not mi_mesh_r else "mesh_present",
            "mirage_mesh_path": mi_mesh_r or (mi_mesh or ""),
            "cadrecode_prediction_path": args.cadrecode_pred or "",
            "cadrecode_exists": sid in cadrec,
            "cadrecode_exec_status": ("not_executed" if sid in cadrec else "no_prediction")
                                     if not cr_mesh_r else "mesh_present",
            "cadrecode_mesh_path": cr_mesh_r or (cr_mesh or ""),
            "eligible_for_cd": bool(gt_mesh_r and mi_mesh_r and cr_mesh_r),
            # IoU additionally needs closed solids; unknown until the meshes exist, so it is not
            # claimed here. Left equal to CD eligibility and refined by the scorer.
            "eligible_for_iou": bool(gt_mesh_r and mi_mesh_r and cr_mesh_r),
            "paired_valid_geometry": bool(mi_mesh_r and cr_mesh_r),
            "gt_normalized_area": area if area is not None else "",
            "expected_cd_floor_8192": floor if floor is not None else "",
            "notes": ";".join(note),
        }
        out_rows.append(row)

    # ---- fail-fast 3: a scored row with no ground truth -----------------------
    scored_without_gt = [r["sample_id"] for r in out_rows
                         if r["paired_valid_geometry"] and not r["gt_mesh_path"]]
    if scored_without_gt:
        print(f"FAIL {len(scored_without_gt)} row(s) have geometry from both arms but no ground "
              f"truth to score against, e.g. {scored_without_gt[:3]}. Scoring these would "
              f"silently drop them from one metric and not the other.", file=sys.stderr)
        return 1

    out = Path(resolve(args.out_dir) or args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "manifest.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for r in out_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with (out / "manifest.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out_rows)

    n = len(out_rows)
    counts = {
        "N_total": n,
        "N_with_point_cloud": sum(bool(r["point_cloud_path"]) for r in out_rows),
        "N_with_GT_step": sum(bool(r["gt_step_path"]) for r in out_rows),
        "N_with_GT_mesh": sum(bool(resolve(r["gt_mesh_path"])) for r in out_rows),
        "N_MIRAGE_prediction": sum(r["mirage_exists"] for r in out_rows),
        "N_CADRecode_prediction": sum(r["cadrecode_exists"] for r in out_rows),
        "N_MIRAGE_valid_mesh": sum(bool(resolve(r["mirage_mesh_path"])) for r in out_rows),
        "N_CADRecode_valid_mesh": sum(bool(resolve(r["cadrecode_mesh_path"])) for r in out_rows),
        "N_paired_valid_mesh": sum(r["paired_valid_geometry"] for r in out_rows),
        "N_CD_eligible": sum(r["eligible_for_cd"] for r in out_rows),
        "N_IoU_eligible": sum(r["eligible_for_iou"] for r in out_rows),
    }

    lines = ["=" * 74, "external comparison sample manifest", "=" * 74, ""]
    for k, v in counts.items():
        lines.append(f"  {k:26s} {v}")
    lines += ["", "  the two accountings this manifest exists to keep separate:",
              f"    unconditional denominator   {counts['N_total']}  (every common input id; a "
              f"failure to produce geometry is a system failure, not a missing datum)",
              f"    paired-valid denominator    {counts['N_paired_valid_mesh']}  (the only rows on "
              f"which CD and IoU can be compared at all)"]
    if notes_count:
        lines += ["", "  missing artefacts, which are the work list rather than errors:"]
        for k, v in sorted(notes_count.items(), key=lambda kv: -kv[1]):
            lines.append(f"    {k:26s} {v}")
    if counts["N_with_GT_mesh"]:
        floors = [r["expected_cd_floor_8192"] for r in out_rows
                  if isinstance(r["expected_cd_floor_8192"], float)]
        if floors:
            floors.sort()
            lines += ["", f"  per-sample CD floor at {N_POINTS} points, from each row's own "
                          f"ground-truth area:",
                      f"    min {floors[0]:.4f}  median {floors[len(floors)//2]:.4f}  "
                      f"max {floors[-1]:.4f}",
                      "    a CD gap below a row's own floor is not a difference for that row."]
    else:
        lines += ["", "  No ground-truth meshes exist yet, so per-sample CD floors could not be",
                  "  computed. The STEP sources are present; tessellating them is the next step,",
                  "  and its tolerance is a protocol parameter because the same meshes feed BOTH",
                  "  the metric and CAD-Recode's own input pipeline."]

    text = "\n".join(lines) + "\n"
    (out / "summary.txt").write_text(text, encoding="utf-8", newline="\n")
    print(text)
    print(f"  wrote {out / 'manifest.jsonl'}")
    print(f"        {out / 'manifest.csv'}")
    print(f"        {out / 'summary.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
