"""Sample the same STEP twice with different seeds, through the frozen OCCT sampler.

RUNS INSIDE FllumaCLI. The `flluma` module cannot be imported from a plain conda environment, so
this script is handed to FllumaCLI.exe by scripts/run_occt_floor.ps1, and takes its arguments from
MIRAGE_STEP_FEATURE_ARGS -- the same convention evaluate_geometry_nbest.py uses.

WHAT IT IS FOR. The sampling floor measured so far -- roughly 623 * normalised_area / n -- was
calibrated on trimesh surface sampling, because that is what CAD-Recode's released demo uses. The
external MIRAGE pathway does not use trimesh: it uses OCCT surface_uv sampling through
occt_file_to_pointcloud. Those are different samplers and there is no reason to assume they share
a floor constant. Until this is measured, the observation that CAD-Recode's published median sits
near the 8192-point floor belongs to THEIR implementation and cannot be extended to our external
evaluation.

INDEPENDENT SEEDS ARE THE WHOLE POINT. Sampling once and comparing the cloud with itself gives
zero and measures nothing. Two independent draws from the same solid are what a perfect prediction
would look like under this metric, so their Chamfer distance IS the floor.

THE TESSELLATION CONFIGURATION IS NOT SET HERE, DELIBERATELY. linear_deflection and
angular_deflection are left at the library defaults, 0.05 and 0.3, because those are the values
external_prep.py used for all 400 Fusion360 clouds and every other external artefact in the
manuscript. Passing them explicitly would look like a choice; omitting them is the record that
nothing was chosen.

Diagnostics are collected alongside, because if the floor does not scale cleanly the reason will
be in the sampler's point distribution: face_ids gives points-per-face, which is where a
non-area-uniform sampler would show up.
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np


def read_ply_ascii_xyz(path: str) -> np.ndarray:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    header_end = next(i for i, line in enumerate(lines) if line.strip() == "end_header")
    coords = [
        [float(v) for v in line.split()[:3]]
        for line in lines[header_end + 1:]
        if line.strip()
    ]
    return np.asarray(coords, dtype=np.float64)


def read_ply_ascii_with_face_ids(path: str) -> tuple[np.ndarray, np.ndarray | None]:
    """xyz plus the trailing face id column, when the exporter wrote one."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    header = lines[:next(i for i, l in enumerate(lines) if l.strip() == "end_header")]
    props = [l.split()[-1] for l in header if l.strip().startswith("property")]
    body = [l.split() for l in lines[len(header) + 1:] if l.strip()]
    xyz = np.asarray([[float(v) for v in r[:3]] for r in body], dtype=np.float64)
    fid = None
    for name in ("face_id", "face_index", "faceid"):
        if name in props:
            j = props.index(name)
            if all(len(r) > j for r in body):
                fid = np.asarray([int(float(r[j])) for r in body], dtype=np.int64)
            break
    return xyz, fid


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--input-jsonl", required=True,
                   help="rows of {sample_id, step_path}")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--point-counts", default="1024,2048,4096,8192")
    p.add_argument("--seeds", default="20260810,20260811")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--face-id-at", type=int, default=8192,
                   help="collect the points-per-face diagnostic at this point count")
    env = os.environ.get("MIRAGE_STEP_FEATURE_ARGS") or os.environ.get("KCADGEN_STEP_FEATURE_ARGS")
    if env:
        return p.parse_args(shlex.split(env))
    return p.parse_args(sys.argv[1:])


def main() -> int:
    args = parse_args()
    import flluma
    from flluma.api import evaluation as ev

    rows = []
    # utf-8-sig, not utf-8: PowerShell 5.1's Set-Content -Encoding utf8 writes a BOM, and
    # json.loads rejects it. utf-8-sig strips a BOM when present and is identical to utf-8 when
    # absent, so reading this way costs nothing and removes a whole class of producer mismatch.
    with open(args.input_jsonl, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    if args.limit:
        rows = rows[:args.limit]

    ns = [int(x) for x in args.point_counts.split(",") if x.strip()]
    seeds = [int(x) for x in args.seeds.split(",") if x.strip()]
    if len(seeds) < 2:
        print("FAIL need at least two seeds; one draw compared with itself measures nothing.",
              file=sys.stderr)
        return 1

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "sampling_log.jsonl"
    done = set()
    if log_path.exists():
        with log_path.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    done.add((r["sample_id"], r["n"], r["seed"]))

    print(f"=== OCCT floor sampling: {len(rows)} shapes x {len(ns)} point counts x "
          f"{len(seeds)} seeds ===")
    print(f"    tessellation left at library defaults (linear 0.05, angular 0.3) on purpose")

    written = 0
    with log_path.open("a", encoding="utf-8", newline="\n") as log:
        for i, r in enumerate(rows, 1):
            sid, step = r["sample_id"], r.get("step_path") or r.get("step_path_wsl")
            if not step or not os.path.exists(step):
                log.write(json.dumps({"sample_id": sid, "status": "no_step",
                                      "step_path": step}) + "\n")
                continue
            for n in ns:
                for seed in seeds:
                    if (sid, n, seed) in done:
                        continue
                    npz = out_dir / f"{sid}__n{n}__s{seed}.npz"
                    rec: dict[str, Any] = {"sample_id": sid, "n": n, "seed": seed,
                                           "npz": str(npz)}
                    try:
                        with tempfile.TemporaryDirectory() as td:
                            ply = os.path.join(td, "s.ply")
                            want_fid = (n == args.face_id_at and seed == seeds[0])
                            ev.extract_step_pointcloud(
                                str(step), ply, point_count=n,
                                sampling="surface_uv", binary=False,
                                random_seed=seed, face_ids=want_fid)
                            if want_fid:
                                pts, fid = read_ply_ascii_with_face_ids(ply)
                            else:
                                pts, fid = read_ply_ascii_xyz(ply), None
                        if len(pts) == 0:
                            rec["status"] = "empty"
                        else:
                            payload = {"points": pts.astype(np.float32)}
                            if fid is not None:
                                payload["face_ids"] = fid
                                counts = np.bincount(fid - fid.min()) if len(fid) else np.array([])
                                counts = counts[counts > 0]
                                rec["n_faces_hit"] = int(len(counts))
                                if len(counts):
                                    rec["points_per_face_min"] = int(counts.min())
                                    rec["points_per_face_median"] = float(np.median(counts))
                                    rec["points_per_face_max"] = int(counts.max())
                                    rec["points_per_face_imbalance"] = float(
                                        counts.max() / max(counts.min(), 1))
                            np.savez_compressed(npz, **payload)
                            rec["status"] = "ok"
                            rec["n_returned"] = int(len(pts))
                            written += 1
                    except Exception as e:
                        rec["status"] = "error"
                        rec["error"] = f"{type(e).__name__}: {e}"
                    log.write(json.dumps(rec) + "\n")
                    log.flush()
            if i % 5 == 0 or i == len(rows):
                print(f"  {i}/{len(rows)} shapes, {written} clouds written")

    print(f"=== done: {written} clouds -> {out_dir} ===")
    print("    analyse in the external_eval environment: src/scratch/occt_floor_analyze.py")
    return 0


if __name__ == "__main__":
    # Plain call, no `raise SystemExit(main())`. FllumaCLI's embedded Python reports SystemExit as
    # an exception even when the code is 0, printing "Execution failed / SystemExit: 0" and
    # returning exit 2 after a fully successful run -- which makes success and failure
    # indistinguishable from the exit code alone. evaluate_geometry_nbest.py ends the same way.
    main()
