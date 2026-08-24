"""B7 worker: probe ONE program's parameters. Runs under FllumaCLI.

Split out from editability_probe.py because perturbing a declared parameter can push
OpenCASCADE into a state that ABORTS THE PROCESS rather than raising a catchable
exception. The main evaluation harness never sees this, because it only ever executes
unmodified model output; perturbed values leave that distribution. A single in-process
loop therefore dies partway through and loses the whole run -- observed on row 2 of a
two-row smoke test, with no traceback and no "Execution failed" banner.

So: one worker process per input row, driven by editability_probe.py. Results are
appended to --output-jsonl and FLUSHED AFTER EVERY PERTURBATION, so a crash costs at
most the perturbation that caused it. The parent notices the missing tail and records
it as a hard crash, which is itself a reportable outcome -- a dimension edit that
takes down the kernel is a stronger brittleness result than one that merely fails to
build.

Invoked as:
    FllumaCLI.exe editability_worker.py     (args via MIRAGE_STEP_FEATURE_ARGS)
      --row-json   <one row as json>
      --output-jsonl <append here>
      --deltas     -0.25,-0.1,0.1,0.25
      --fingerprint-points 512
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
import tempfile
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from editability_probe import (  # noqa: E402
    chamfer, classify, declared_params, parametric_coverage, perturb,
    read_ply_ascii_xyz,
)


def flluma_namespace() -> dict:
    import flluma as fl
    ns: dict[str, Any] = {"__name__": "__candidate__", "fl": fl}
    for attr in dir(fl):
        if not attr.startswith("_"):
            ns[attr] = getattr(fl, attr)
    return ns


def sample_points(part: Any, n: int):
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "fp.ply")
        try:
            part.export_pointcloud(out, point_count=n, normals=False, face_ids=False)
            pts = read_ply_ascii_xyz(out)
            return pts if len(pts) > 0 else None
        except Exception:
            return None


def execute(code: str, fp_points: int) -> dict:
    """Five gates, matching evaluate_geometry_nbest.py, plus a point fingerprint."""
    res: dict[str, Any] = {
        "syntax_ok": False, "exec_ok": False, "build_ok": False,
        "solid_valid": False, "step_export_ok": False, "points": None, "error": "",
    }
    import ast
    try:
        ast.parse(code)
    except SyntaxError as exc:
        res["error"] = f"SyntaxError: {exc}"
        return res
    res["syntax_ok"] = True

    ns = flluma_namespace()
    try:
        exec(compile(code, "<probe>", "exec"), ns)  # noqa: S102
    except Exception as exc:
        res["error"] = f"exec error: {exc}"
        return res
    part = ns.get("part")
    if part is None:
        res["error"] = "no `part` variable after execution"
        return res
    res["exec_ok"] = True

    try:
        part.build()
    except Exception as exc:
        res["error"] = f"build error: {exc}"
        return res
    res["build_ok"] = True

    try:
        if part.validate() is False:
            res["error"] = "part failed geometric validity check"
            return res
    except Exception as exc:
        res["error"] = f"validity check error: {exc}"
        return res
    res["solid_valid"] = True

    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "probe.step")
        try:
            part.export_step(out)
        except Exception as exc:
            res["error"] = f"STEP export error: {exc}"
            return res
        if not (os.path.exists(out) and os.path.getsize(out) > 0):
            res["error"] = "STEP export produced no file"
            return res
    res["step_export_ok"] = True

    pts = sample_points(part, fp_points)
    res["points"] = None if pts is None else pts.tolist()
    return res


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--row-json", required=True)
    p.add_argument("--output-jsonl", required=True)
    p.add_argument("--deltas", default="-0.25,-0.1,0.1,0.25")
    p.add_argument("--fingerprint-points", type=int, default=512)
    p.add_argument("--program-field", default="prediction")
    env = os.environ.get("MIRAGE_STEP_FEATURE_ARGS")
    return p.parse_args(shlex.split(env) if env else sys.argv[1:])


def emit(path: str, obj: dict) -> None:
    """Append and flush. The flush is the point: a later hard crash must not cost
    results already computed."""
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def main() -> int:
    args = parse_args()
    with open(args.row_json, encoding="utf-8") as fh:
        row = json.load(fh)
    code = row.get(args.program_field, "") or ""
    sid = row.get("sample_id", "")
    deltas = [float(x) for x in args.deltas.split(",") if x.strip()]

    cov = parametric_coverage(code)
    base = execute(code, args.fingerprint_points)

    emit(args.output_jsonl, {
        "kind": "row", "sample_id": sid, "modality": row.get("modality", ""),
        "coverage": cov,
        "baseline": {k: v for k, v in base.items() if k != "points"},
    })

    if not base["step_export_ok"]:
        emit(args.output_jsonl, {"kind": "done", "sample_id": sid,
                                 "skipped": "baseline not kernel-valid"})
        return 0

    # Noise floor: re-execute unchanged and Chamfer the two samples.
    # export_pointcloud is not seeded, so identical solids do not give identical
    # points; without this an exact comparison calls everything a change.
    base2 = execute(code, args.fingerprint_points)
    noise = 0.0
    if base.get("points") and base2.get("points"):
        import numpy as np
        noise = chamfer(np.asarray(base["points"]), np.asarray(base2["points"]))
    emit(args.output_jsonl, {"kind": "noise", "sample_id": sid, "value": noise})

    for name, info in declared_params(code).items():
        for d in deltas:
            target = info["value"] * (1.0 + d)
            clamped = False
            if info["min"] is not None and target < info["min"]:
                target, clamped = info["min"], True
            if info["max"] is not None and target > info["max"]:
                target, clamped = info["max"], True
            if abs(target - info["value"]) < 1e-12:
                continue
            # Announce BEFORE executing, so a hard crash identifies its own cause.
            emit(args.output_jsonl, {"kind": "attempt", "sample_id": sid,
                                     "param": name, "delta": d,
                                     "from": info["value"], "to": target})
            pert = execute(perturb(code, name, target), args.fingerprint_points)
            emit(args.output_jsonl, {
                "kind": "result", "sample_id": sid, "param": name, "delta": d,
                "from": info["value"], "to": target, "clamped_to_bound": clamped,
                "outcome": classify(base, pert, noise), "error": pert["error"],
            })

    emit(args.output_jsonl, {"kind": "done", "sample_id": sid})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
