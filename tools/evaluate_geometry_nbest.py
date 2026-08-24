"""Table 4: geometry-conditioned N-best evaluation via Flluma/OpenCASCADE.

For each sample, evaluates every candidate in `all_candidates` through the
same 5 gates as evaluate_execution.py, then (for candidates that reach
step_export_ok) samples the generated STEP as a point cloud and scores it
against the query's own ground-truth geometry: symmetric Chamfer Distance,
bbox error, and F-score@1% (precision/recall at a threshold of 1% of the
target's bounding-box diagonal). Raw per-candidate results are written out;
N=1/3/5/10 selection/aggregation happens in a separate, torch-free,
non-FllumaCLI script (aggregate_geometry_nbest.py) so this script only needs
to run once regardless of how many N values are analyzed.

Must be run through FllumaCLI.exe (embedded Python with the native `flluma`
module) — the plain WSL/conda environment cannot import `flluma`.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import shlex
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

_GATE_NAMES = ["syntax_ok", "exec_ok", "build_ok", "solid_valid", "step_export_ok"]


def as_windows_path(path: str | Path) -> Path:
    text = str(path).replace("\\", "/")
    if text.startswith("/mnt/") and len(text) > 6:
        drive = text[5].upper()
        rest = text[7:]
        return Path(f"{drive}:/{rest}")
    return Path(path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def flluma_exec_namespace() -> dict[str, Any]:
    import flluma  # type: ignore

    return {name: getattr(flluma, name) for name in dir(flluma) if not name.startswith("_")}


def read_ply_ascii_xyz(path: str) -> np.ndarray:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    header_end = next(i for i, line in enumerate(lines) if line.strip() == "end_header")
    coords = [
        [float(v) for v in line.split()[:3]]
        for line in lines[header_end + 1 :]
        if line.strip()
    ]
    return np.asarray(coords, dtype=np.float64)


def sample_part_points(part: Any, n: int) -> np.ndarray | None:
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "sampled.ply")
        try:
            part.export_pointcloud(out_path, point_count=n, normals=False, face_ids=False)
            pts = read_ply_ascii_xyz(out_path)
            return pts if len(pts) > 0 else None
        except Exception:
            return None


def load_point_npz(point_path: str, n: int = 1024, seed: int = 42) -> np.ndarray | None:
    try:
        data = np.load(point_path)
        key = "points" if "points" in data else list(data.keys())[0]
        pts = np.asarray(data[key], dtype=np.float64)
        if pts.ndim != 2 or pts.shape[0] == 0:
            return None
        rng = np.random.RandomState(seed)
        if pts.shape[0] > n:
            idx = rng.choice(pts.shape[0], n, replace=False)
            pts = pts[idx]
        return pts
    except Exception:
        return None


def symmetric_chamfer(P: np.ndarray, Q: np.ndarray) -> float:
    try:
        from scipy.spatial import cKDTree
        d_PQ, _ = cKDTree(Q).query(P)
        d_QP, _ = cKDTree(P).query(Q)
    except ImportError:
        d2_PQ = ((P[:, None, :] - Q[None, :, :]) ** 2).sum(-1)
        d2_QP = ((Q[:, None, :] - P[None, :, :]) ** 2).sum(-1)
        d_PQ = np.sqrt(d2_PQ.min(1))
        d_QP = np.sqrt(d2_QP.min(1))
    return float(0.5 * np.mean(d_PQ ** 2) + 0.5 * np.mean(d_QP ** 2)), d_PQ, d_QP


def bbox_error(P: np.ndarray, Q: np.ndarray) -> float:
    return float(np.mean(np.abs((P.max(0) - P.min(0)) - (Q.max(0) - Q.min(0)))))


def f_score_at_threshold(d_PQ: np.ndarray, d_QP: np.ndarray, threshold: float) -> float:
    if threshold <= 0:
        return 0.0
    precision = float(np.mean(d_PQ < threshold))
    recall = float(np.mean(d_QP < threshold))
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def evaluate_one(code: str, P_target: np.ndarray | None, point_count: int) -> dict[str, Any]:
    result: dict[str, Any] = {k: False for k in _GATE_NAMES}
    result["error"] = ""
    result["cd"] = None
    result["bbox_err"] = None
    result["f_score_1pct"] = None
    result["target_bbox_diag"] = None
    result["gen_bbox_diag"] = None
    result["bbox_ratio_to_gt"] = None

    try:
        ast.parse(code)
    except SyntaxError as exc:
        result["error"] = f"SyntaxError: {exc}"
        return result
    result["syntax_ok"] = True

    try:
        ns = flluma_exec_namespace()
    except ImportError as exc:
        raise RuntimeError(f"requires native flluma module: {exc}") from exc

    try:
        exec(compile(code, "<candidate>", "exec"), ns)  # noqa: S102
        part = ns.get("part")
        if part is None:
            result["error"] = "no `part` variable after execution"
            return result
    except Exception as exc:
        result["error"] = f"exec error: {exc}"
        return result
    result["exec_ok"] = True

    try:
        part.build()
    except Exception as exc:
        result["error"] = f"build error: {exc}"
        return result
    result["build_ok"] = True

    try:
        if part.validate() is False:
            result["error"] = "part failed geometric validity check"
            return result
    except Exception as exc:
        result["error"] = f"validity check error: {exc}"
        return result
    result["solid_valid"] = True

    with tempfile.TemporaryDirectory() as tmpdir:
        step_out = os.path.join(tmpdir, "candidate.step")
        try:
            part.export_step(step_out)
        except Exception as exc:
            result["error"] = f"STEP export error: {exc}"
            return result
        result["step_export_ok"] = True

        if P_target is None:
            return result
        P_gen = sample_part_points(part, point_count)
        if P_gen is None or len(P_gen) == 0:
            result["error"] = "point cloud sampling failed on generated part"
            return result
        cd, d_PQ, d_QP = symmetric_chamfer(P_gen, P_target)
        target_bbox_diag = float(np.linalg.norm(P_target.max(0) - P_target.min(0)))
        gen_bbox_diag = float(np.linalg.norm(P_gen.max(0) - P_gen.min(0)))
        threshold = 0.01 * target_bbox_diag
        result["cd"] = cd
        result["bbox_err"] = bbox_error(P_gen, P_target)
        result["f_score_1pct"] = f_score_at_threshold(d_PQ, d_QP, threshold)
        # Diagnostic only (not used by selection): flags candidates whose
        # generated geometry is wildly larger than the query's own bbox --
        # e.g. a kernel-valid but geometrically-exploded solid from a
        # mis-computed "through" depth. See aggregate_geometry_nbest.py.
        result["target_bbox_diag"] = target_bbox_diag
        result["gen_bbox_diag"] = gen_bbox_diag
        result["bbox_ratio_to_gt"] = gen_bbox_diag / target_bbox_diag if target_bbox_diag > 0 else None

    return result


def load_target(row: dict, point_count: int) -> np.ndarray | None:
    # Ground truth is always the dataset's precomputed point_path npz (sampled
    # once from the reference model.step at dataset-build time) -- both point
    # and step modality rows carry the same point_path for the same object, so
    # there is no need to resample the reference STEP file here.
    point_path = as_windows_path(row.get("point_path", "")).as_posix()
    if point_path and Path(point_path).exists():
        return load_point_npz(point_path, n=point_count)
    return None


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--input-jsonl", type=Path, required=True)
    p.add_argument("--output-jsonl", type=Path, required=True)
    p.add_argument("--point-count", type=int, default=1024)
    p.add_argument("--limit", type=int, default=None)
    env_args = os.environ.get("MIRAGE_STEP_FEATURE_ARGS") or os.environ.get("KCADGEN_STEP_FEATURE_ARGS")
    if env_args:
        return p.parse_args(shlex.split(env_args))
    return p.parse_args(sys.argv[1:])


def main() -> int:
    args = parse_args()
    rows = read_jsonl(args.input_jsonl)
    if args.limit:
        rows = rows[: args.limit]

    # Incremental and resumable, for the same reason the execution scorer is: a generated
    # program can take the whole process down. One candidate raised an access violation
    # (0xC0000005) inside the kernel during the execution pass, and with results held in
    # memory and written once at the end, a crash loses every row and a plain re-run walks
    # into the same candidate and dies again -- so "just run it twice" never converges.
    #
    # Rows are appended and flushed as they are scored; a marker is written before each row
    # executes. A sample_id in the marker but not in the results killed the process, and is
    # recorded as such on the next attempt instead of being retried.
    inflight_path = args.output_jsonl.with_suffix(".inflight")
    done: dict[str, dict[str, Any]] = {}
    if args.output_jsonl.is_file():
        for line in args.output_jsonl.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                done[r.get("sample_id", "")] = r
    crashed = set()
    if inflight_path.is_file():
        for sid in inflight_path.read_text(encoding="utf-8").split():
            if sid and sid not in done:
                crashed.add(sid)
    if done or crashed:
        print(f"resuming: {len(done)} already scored, {len(crashed)} previously crashed the "
              f"kernel", flush=True)

    out_rows: list[dict[str, Any]] = []
    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_jsonl, "a", encoding="utf-8", newline="\n") as out:
        for i, row in enumerate(rows, start=1):
            sid = row.get("sample_id", "")
            if sid in done:
                rec = done[sid]
            elif sid in crashed:
                rec = {"sample_id": sid, "modality": row.get("modality", ""),
                       "has_target": None, "candidate_results": [],
                       "error": "kernel access violation (0xC0000005) -- the process died "
                                "scoring this candidate; recorded on resume, not retried"}
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out.flush()
                done[sid] = rec
            else:
                with open(inflight_path, "a", encoding="utf-8", newline="\n") as fl:
                    fl.write(sid + "\n")
                    fl.flush()
                    os.fsync(fl.fileno())
                P_target = load_target(row, args.point_count)
                rec = {
                    "sample_id": sid,
                    "modality": row.get("modality", ""),
                    "has_target": P_target is not None,
                    "candidate_results": [evaluate_one(code, P_target, args.point_count)
                                          for code in row.get("all_candidates", [])],
                }
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out.flush()
                done[sid] = rec
            out_rows.append(rec)
            if i % 25 == 0 or i == len(rows):
                print(f"  {i}/{len(rows)} scored", flush=True)

    n_with_target = sum(1 for r in out_rows if r.get("has_target"))
    n_crash = sum(1 for r in out_rows if str(r.get("error", "")).startswith("kernel access"))
    if n_with_target == 0 and out_rows:
        # The failure this project has already produced once: point_path pointed somewhere
        # the scorer could not read, every target came back None, and the analysis reported a
        # confident "scored 0, no overlap" as though it were a measurement.
        print("** WARNING: not one row had a readable reference cloud. Check point_path -- "
              "as_windows_path only converts /mnt/<drive>, so a WSL-native path silently "
              "yields no target and every score becomes a failure. **", flush=True)
    print(json.dumps({"rows": len(out_rows), "rows_with_target": n_with_target,
                      "kernel_crash_count": n_crash}, indent=2))
    return 0


if __name__ == "__main__":
    main()
