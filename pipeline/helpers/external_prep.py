"""Turn Fusion 360 Gallery into queries the MIRAGE-CAD pipeline can consume.

    inventory   scan and report -- the official split, file presence, and how external
                geometry compares with the corpus -- and write nothing
    build       sample reference clouds, emit the query manifest, calibrate the metrics

REFERENCE CLOUDS COME FROM THE STEP, THROUGH FLLUMA. occt_file_to_pointcloud (added to
BindCSG.cpp for this) imports the file with Core::CADAsset::ImportFromSTEP and hands the
shape to PointCloudExporter -- the same exporter, sampler and options that produce clouds
from generated parts. Both sides of every geometry comparison therefore come out of one
code path, and no sampler-asymmetry caveat is needed.

That equivalence is measured, not assumed. probe_step_pointcloud.py sampled a corpus
model.step and compared it against the point_cloud.npz released for the same sample, which
was sampled from the program instead: identical bounding boxes, and median nearest-neighbour
distances of 0.78 and 0.80 against an 89.55 diagonal -- sampling noise at 2,048 points.

THE SAMPLING FRAME IS THE DATASET'S OWN. train_test.json lists 6,900 train and 1,725 test
designs, and those 8,625 names match exactly the 8,625 stems with three underscore-separated
fields; the other 19,333 files are per-extrude intermediates of the same designs. Scoring an
intermediate would treat a partial solid as a target, so the frame is the published test
split and nothing else. This replaces an earlier guess at the naming convention that had the
rule backwards -- <design>_<uuid>_<index> is the finished model, and it is the four-field
<...>_<seq> names that are partial.

ON UNITS. Fusion 360's API works in centimetres and FllumaOne in millimetres, which would
matter because the STEP descriptor compresses bbox, area and volume under log1p: a tenfold
error does not rescale the input, it moves the query outside the space the encoder was
trained on, and the STEP arm would fail for a reason unrelated to cross-source
generalisation. Measured, the concern is handled for us, though not in the way it first
looked. The STEP files declare CENTIMETRE and OpenCASCADE converts on read, so what reaches
us is correct millimetres -- external bbox diagonals of 119-121 against a corpus median of
82.7, with extents on exact inch multiples (25.4, 38.1). The factor is exactly 10.00 against
the sibling .obj on every file checked, large and small alike, so no correction is applied.
The distinction matters for anyone reading these files with a parser that ignores the unit
declaration: they would be ten times too small.

The geometry phases need FllumaCLI, which hosts the only Python that can import flluma and
which does NOT forward argv -- hence the environment variable, matching what
extract_step_features.py already does.

  WSL or any python, counts only:
    python training_25k/scripts/external_prep.py --root <dir> --output-dir <dir> --mode inventory

  Windows, with geometry:
    $env:MIRAGE_EXTERNAL_PREP_ARGS = '--root "..." --output-dir "..." --mode build --limit 400'
    & "...\\FllumaCLI.exe" "...\\external_prep.py"
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import shlex
import statistics
import sys
from pathlib import Path

import numpy as np

SEED = 20260810
REPORT: list[str] = []


def say(msg: str = "") -> None:
    REPORT.append(msg)
    print(msg, flush=True)


def flush_report(path: Path) -> None:
    """FllumaCLI swallows stdout, so anything worth reading also goes to a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(chr(10).join(REPORT) + chr(10), encoding="utf-8")
    print(f"[report] {path}", flush=True)


# ------------------------------------------------------------------ the frame
def load_split(root: Path) -> tuple[list[str], list[str]]:
    j = root / "train_test.json"
    if not j.is_file():
        return [], []
    d = json.loads(j.read_text(encoding="utf-8"))
    return list(d.get("train", [])), list(d.get("test", []))


def resolve(root: Path, names: list[str]) -> list[tuple[str, Path, Path | None]]:
    """(stem, step, obj) for the names whose files are actually present."""
    rec = root / "reconstruction"
    out = []
    for n in names:
        step, obj = rec / f"{n}.step", rec / f"{n}.obj"
        if step.is_file():
            out.append((n, step, obj if obj.is_file() else None))
    return out


# ------------------------------------------------------------------- sampling
def get_flluma():
    try:
        from flluma.api import evaluation as ev
    except Exception:
        return None
    return ev if hasattr(ev, "extract_step_pointcloud") else None


def read_xyz(path: Path) -> np.ndarray:
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        p = line.split()
        if len(p) >= 3:
            try:
                rows.append((float(p[0]), float(p[1]), float(p[2])))
            except ValueError:
                continue
    return np.asarray(rows, dtype=np.float64)


def sample_step(ev, step: Path, tmp: Path, n: int) -> np.ndarray | None:
    """Flluma's own sampler. Returns None with a reason rather than raising."""
    out = tmp / f"{step.stem}.xyz"
    try:
        if out.exists():
            out.unlink()
        ev.extract_step_pointcloud(str(step), str(out), point_count=n,
                                   sampling="surface_uv", binary=False, random_seed=SEED)
    except Exception as exc:
        say(f"    {step.stem}: {type(exc).__name__}: {str(exc)[:120]}")
        return None
    if not out.exists() or not out.stat().st_size:
        say(f"    {step.stem}: wrote nothing")
        return None
    pts = read_xyz(out)
    out.unlink()
    return pts if len(pts) >= 32 else None


def bbox_diag(p: np.ndarray) -> float:
    return float(np.linalg.norm(p.max(0) - p.min(0)))


def corpus_bbox_sample(n: int = 120) -> list[float]:
    """Bbox diagonals from the released FllumaOne shards.

    Read from the shards rather than via test.jsonl, whose point_path is WSL-absolute and
    resolves on only one OS -- which would silently skip the comparison on the side where
    the data actually lives.
    """
    roots = [Path(r"C:\Workspace\Project\FllumaOne\FllumaOne-100K"),
             Path("/mnt/c/Workspace/Project/FllumaOne/FllumaOne-100K")]
    out: list[float] = []
    for root in roots:
        if not root.is_dir():
            continue
        for f in root.glob("shard_*/flluma_*/point_cloud.npz"):
            try:
                d = np.load(f)
                k = "points" if "points" in d else list(d.keys())[0]
                out.append(bbox_diag(np.asarray(d[k], dtype=np.float64)))
            except Exception:
                continue
            if len(out) >= n:
                return out
        if out:
            return out
    return out


# ------------------------------------------------------------------ inventory
def inventory(root: Path, limit: int, point_count: int) -> int:
    train, test = load_split(root)
    say(f"=== {root} ===")
    if not test:
        say("  ** train_test.json missing or unreadable. That file is the sampling frame;")
        say("     without it the finished models cannot be told from per-extrude")
        say("     intermediates, and scoring an intermediate scores a partial solid. **")
        return 1
    say(f"  official split: {len(train)} train, {len(test)} test")

    rt, rs = resolve(root, train), resolve(root, test)
    say(f"  present on disk: {len(rt)}/{len(train)} train, {len(rs)}/{len(test)} test")
    say(f"  test entries with no sibling .obj: {sum(1 for _, _, o in rs if o is None)}"
        f"   (unused -- clouds come from the .step -- but a sign of a partial extract)")
    if not rs:
        say("  ** no test model resolved. Is reconstruction/ where the files landed? **")
        return 1
    say(f"  example: {rs[0][0]}")

    ev = get_flluma()
    say()
    if ev is None:
        say("=== geometry: SKIPPED ===")
        say("  flluma is not importable here, which is expected outside FllumaCLI, so")
        say("  nothing was sampled. Re-run this phase through FllumaCLI for the unit")
        say("  comparison; the counts above are already trustworthy.")
        say(f"\n  would build {min(limit, len(rs))} of {len(rs)} test models")
        return 0

    say(f"=== geometry: sampling {min(24, len(rs))} test models through Flluma ===")
    tmp = Path(os.environ.get("TEMP", "/tmp")) / "mirage_ext_prep"
    tmp.mkdir(parents=True, exist_ok=True)
    diags, counts, bad = [], [], 0
    for stem, step, _ in rs[:24]:
        pts = sample_step(ev, step, tmp, point_count)
        if pts is None:
            bad += 1
            continue
        diags.append(bbox_diag(pts))
        counts.append(len(pts))
    if not diags:
        say("  ** nothing sampled. Stop here -- the build phase cannot work either. **")
        return 1
    say(f"  sampled {len(diags)}, failed {bad}")
    say(f"  points returned   median {statistics.median(counts):.0f}   "
        f"min {min(counts)}   max {max(counts)}   (requested {point_count})")
    say(f"  bbox diagonal     median {statistics.median(diags):.4g}   "
        f"min {min(diags):.4g}   max {max(diags):.4g}")

    say()
    say("=== units, against the corpus ===")
    corpus = corpus_bbox_sample()
    if not corpus:
        say("  could not read FllumaOne shards; compare by hand before building")
    else:
        cm, em = statistics.median(corpus), statistics.median(diags)
        say(f"  corpus   median bbox diagonal {cm:.4g}   (FllumaOne, millimetres)")
        say(f"  external median bbox diagonal {em:.4g}")
        r = cm / em if em else float("nan")
        say(f"  ratio corpus/external = {r:.3g}")
        if 0.3 < r < 3:
            say("  -> same order. No scale correction; the STEP is already in millimetres.")
        elif 5 < r < 20:
            say(f"  -> external ~{r:.0f}x smaller, the centimetre/millimetre signature.")
            say(f"     Re-run build with --scale {round(r)}.")
        else:
            say("  -> an unexpected factor. Do not guess a correction; find out why first.")

    say(f"\n  would build {min(limit, len(rs))} of {len(rs)} test models")
    say("  nothing written. Re-run with --mode build when the above looks right.")
    return 0


# ---------------------------------------------------------------------- build
def to_wsl(p: Path) -> str:
    r"""A Windows path as WSL sees it. Two forms, and the second one bit us.

        C:\x                            -> /mnt/c/x
        \\wsl.localhost\Ubuntu\home\... -> /home/...

    The first version handled only the drive letter, so running the build with an
    --output-dir on the UNC share -- which is the normal way to write results straight into
    WSL -- recorded every path as //wsl.localhost/... , which resolves nowhere inside WSL.
    The row builder's precondition caught all 400 before a single token was generated, but
    the manifest on disk was still wrong.
    """
    s = str(p).replace("\\", "/")
    m = re.match(r"//(?:wsl\.localhost|wsl\$)/[^/]+(/.*)$", s, re.I)
    if m:
        return m.group(1)
    if len(s) > 1 and s[1] == ":":
        return f"/mnt/{s[0].lower()}{s[2:]}"
    return s


def build(root: Path, out_dir: Path, limit: int, point_count: int, scale: float) -> int:
    ev = get_flluma()
    if ev is None:
        say("** flluma is not importable, or lacks extract_step_pointcloud. **")
        say("   The build phase must run through FllumaCLI:")
        say('   $env:MIRAGE_EXTERNAL_PREP_ARGS = \'--root "..." --output-dir "..." --mode build\'')
        say('   & "...\\FllumaCLI.exe" "...\\external_prep.py"')
        return 2

    _, test = load_split(root)
    rs = resolve(root, test)
    if not rs:
        say("no test model resolved; run --mode inventory first")
        return 1
    random.Random(SEED).shuffle(rs)

    cloud_dir = out_dir / "clouds"
    cloud_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(os.environ.get("TEMP", "/tmp")) / "mirage_ext_prep"
    tmp.mkdir(parents=True, exist_ok=True)

    rows, failed = [], 0
    for stem, step, _ in rs:
        if len(rows) >= limit:
            break
        pts = sample_step(ev, step, tmp, point_count)
        if pts is None:
            failed += 1
            continue
        if scale != 1.0:
            pts = pts * scale
        d = bbox_diag(pts)
        if not (np.isfinite(d) and d > 1e-6):
            failed += 1
            continue

        npz = cloud_dir / f"{stem}.npz"
        np.savez_compressed(npz, points=pts.astype(np.float32))
        rows.append({
            "sample_id": f"f360_{stem}",
            "source_dataset": "fusion360_gallery_r1.0.1",
            "external_id": stem,
            "split": "test",
            "step_path": str(step),
            "step_path_wsl": to_wsl(step),
            "point_path": str(npz),
            "point_path_wsl": to_wsl(npz),
            "n_points": int(len(pts)),
            "bbox_diag": d,
            "scale_applied": scale,
        })
        if len(rows) % 50 == 0:
            say(f"  {len(rows)} built, {failed} failed")

    manifest = out_dir / "queries.jsonl"
    manifest.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                        encoding="utf-8")
    say(f"wrote {len(rows)} queries -> {manifest}   ({failed} failed to sample)")

    (out_dir / "run_metadata.json").write_text(json.dumps({
        "source": str(root),
        "dataset": "Fusion 360 Gallery reconstruction r1.0.1",
        "frame": "published test split of train_test.json (1,725 designs); "
                 "per-extrude intermediates excluded",
        "n": len(rows),
        "n_failed": failed,
        "point_count_requested": point_count,
        "scale_applied": scale,
        "seed": SEED,
        "sampler": "flluma occt_file_to_pointcloud, surface_uv -- the same exporter, "
                   "sampler and options used for generated parts, so both sides of every "
                   "geometry comparison come out of one code path",
        "equivalence_check": "probe_step_pointcloud.py: a corpus model.step sampled this "
                             "way matches the released point_cloud.npz sampled from the "
                             "program instead -- identical bbox, median nearest neighbour "
                             "0.78/0.80 against an 89.55 diagonal",
    }, indent=2), encoding="utf-8")

    calibrate(rows)
    return 0


# ---------------------------------------------------------------- calibration
def calibrate(rows: list[dict]) -> None:
    """What can the geometry metrics express on THIS set?

    Two disjoint halves of one reference cloud differ only by sampling, so whatever they
    score bounds a perfect reconstruction. The internal ceiling of 0.244 and floor of
    1.963 mm^2 were measured at 1,024 points on FllumaOne parts and transfer to neither the
    density nor the part sizes here, so they must not be quoted beside external numbers.
    """
    if not rows:
        return
    rng = np.random.RandomState(SEED)
    f_at = {0.01: [], 0.02: [], 0.05: []}
    cds, spacings = [], []

    for r in rows[:200]:
        try:
            pts = np.asarray(np.load(r["point_path"])["points"], dtype=np.float64)
        except Exception:
            continue
        half = len(pts) // 2
        if half < 64:
            continue
        idx = rng.permutation(len(pts))
        A, B = pts[idx[:half]], pts[idx[half:2 * half]]
        dAB = np.sqrt(((A[:, None, :] - B[None, :, :]) ** 2).sum(-1).min(1))
        dBA = np.sqrt(((B[:, None, :] - A[None, :, :]) ** 2).sum(-1).min(1))
        cds.append(0.5 * (dAB ** 2).mean() + 0.5 * (dBA ** 2).mean())
        spacings.append(float(np.median(dAB)))
        diag = r["bbox_diag"]
        for t in f_at:
            thr = t * diag
            p, rc = float((dAB < thr).mean()), float((dBA < thr).mean())
            f_at[t].append(0.0 if p + rc == 0 else 2 * p * rc / (p + rc))

    if not cds:
        say("\ncalibration: no usable clouds")
        return
    say(f"\n=== metric calibration on this set ({len(cds)} parts, half-cloud vs half-cloud) ===")
    say(f"  median nearest-neighbour spacing  {statistics.median(spacings):.4g}")
    say(f"  median bbox diagonal              "
        f"{statistics.median(r['bbox_diag'] for r in rows[:200]):.4g}")
    for t in sorted(f_at):
        say(f"  F@{100*t:.0f}% ceiling   median {statistics.median(f_at[t]):.3f}   "
            f"mean {statistics.fmean(f_at[t]):.3f}")
    say(f"  Chamfer noise floor  median {statistics.median(cds):.4g}")
    say("\n  Quote these beside any external geometry figure, not the internal 0.244.")


def parse_args() -> argparse.Namespace:
    # FllumaCLI does not forward argv, so arguments arrive by environment variable --
    # the convention extract_step_features.py already uses.
    argv = sys.argv[1:]
    env = os.environ.get("MIRAGE_EXTERNAL_PREP_ARGS")
    if not argv and env:
        argv = [a.strip('"') for a in shlex.split(env, posix=False)]

    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--mode", choices=["inventory", "build"], default="inventory")
    ap.add_argument("--limit", type=int, default=400)
    ap.add_argument("--point-count", type=int, default=8192)
    ap.add_argument("--scale", type=float, default=float(os.environ.get("EXT_SCALE", 1.0)))
    ap.add_argument("--report", type=Path, default=None)
    return ap.parse_args(argv)


def main() -> int:
    args = parse_args()
    if args.mode == "inventory":
        rc = inventory(args.root, args.limit, args.point_count)
    else:
        rc = build(args.root, args.output_dir, args.limit, args.point_count, args.scale)
    flush_report(args.report or (args.output_dir / f"external_prep_{args.mode}.txt"))
    return rc


if __name__ == "__main__":
    # No SystemExit at all: FllumaCLI reports "Execution failed" for any SystemExit,
    # including zero, which reads as an error when nothing went wrong.
    try:
        main()
    except Exception:
        import traceback
        say("UNCAUGHT")
        say(traceback.format_exc())
        try:
            flush_report(Path(os.environ.get("TEMP", "/tmp")) / "external_prep_crash.txt")
        except Exception:
            pass
