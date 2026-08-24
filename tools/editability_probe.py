"""B7: measure delta-editability of generated Flluma programs by perturbing
declared parameters and re-executing.

RUNS UNDER FllumaCLI ON WINDOWS (it needs `import flluma`), driven by
src/scripts/editability_probe.ps1. Args arrive via MIRAGE_STEP_FEATURE_ARGS, the
same convention as evaluate_execution_nbest.py and evaluate_geometry_nbest.py.

WHAT THIS MEASURES, AND WHY IT IS NOT THE SAME AS "BUILD RATE"
--------------------------------------------------------------
Section 3.2 defines a program as delta-editable when changing a declared parameter
changes the built solid correspondingly, rather than breaking it or being ignored.
Generated programs declare parameters explicitly:

    params.add('thickness', 4.8, min=2.0, max=15.0, semantic_type='thickness')
    solid = part.extrude(..., height=params['thickness'], ...)

so the property is directly testable: rewrite the declared value, re-execute, and
see what happens. Three outcomes matter and they are different failures:

  RE-BUILT AND MOVED    the solid rebuilds and its geometry changed  -> editable
  RE-BUILT, NO CHANGE   rebuilds but geometry is bit-identical       -> parameter
                        is declared but never actually consumed (dead parameter);
                        an edit silently does nothing, which is worse for a user
                        than an error
  BROKE                 no longer builds / fails a later gate        -> brittle

The third is the one people expect; the second is the one that is easy to miss and
is why this probe reports geometry change rather than only build success.

It also reports PARAMETRIC COVERAGE: the fraction of numeric literals in the program
that reach the kernel through a `params[...]` reference rather than inlined. This
matters because the generated programs inline sketch coordinates and offsets --
`points=[[-12.31, -28.8], ...]`, `offset=[0.0, 0.0, 3.25]` -- so a part can pass
every editability test on its declared parameters while its profile geometry is
frozen. Coverage bounds what editability can be worth.

VARIANT COMPARISON
------------------
Run this on variant C and on the NN-IR baselines A/B over the same sample ids.
A and B substitute *another part's* construction plan, so their parameter names and
semantics need not match the query -- variant C has a structural reason to do better
here, and this is the one dimension where that is plausible. Reporting C alone would
waste the experiment.

Usage (via the .ps1 wrapper; these are the args it forwards):
    --input-jsonl   programs to probe: {sample_id, modality, prediction}
    --output-jsonl  per-perturbation records
    --summary-json  aggregate
    --deltas        comma-separated relative perturbations, default -0.25,-0.1,0.1,0.25
    --limit         cap rows (0 = all)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
import tempfile
from pathlib import Path
from typing import Any

# `params.add('name', <value>, ...)` -- captures the literal we rewrite.
PARAM_ADD = re.compile(
    r"""(?P<head>params\.add\(\s*['"](?P<name>[^'"]+)['"]\s*,\s*)
        (?P<value>-?\d+(?:\.\d+)?)
        (?P<tail>\s*[,)])""",
    re.VERBOSE,
)
PARAM_REF = re.compile(r"params\[\s*['\"]([^'\"]+)['\"]\s*\]")
NUMERIC_LITERAL = re.compile(r"(?<![\w.])-?\d+\.\d+|(?<![\w.])-?\d+(?![\w.])")
MIN_KW = re.compile(r"min\s*=\s*(-?\d+(?:\.\d+)?)")
MAX_KW = re.compile(r"max\s*=\s*(-?\d+(?:\.\d+)?)")


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


# ---------------------------------------------------------------------------
# static analysis: which parameters exist, which are referenced, coverage
# ---------------------------------------------------------------------------
def declared_params(code: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for m in PARAM_ADD.finditer(code):
        line_start = code.rfind("\n", 0, m.start()) + 1
        line_end = code.find("\n", m.end())
        line = code[line_start: line_end if line_end != -1 else len(code)]
        lo = MIN_KW.search(line)
        hi = MAX_KW.search(line)
        out[m.group("name")] = {
            "value": float(m.group("value")),
            "min": float(lo.group(1)) if lo else None,
            "max": float(hi.group(1)) if hi else None,
        }
    return out


def parametric_coverage(code: str) -> dict[str, Any]:
    """How much of the program's numbers are reachable through a parameter."""
    decl = declared_params(code)
    referenced = set(PARAM_REF.findall(code))
    # Numeric literals outside the params.add block are inlined constants.
    body_lines = [l for l in code.splitlines() if "params.add(" not in l]
    inlined = sum(len(NUMERIC_LITERAL.findall(l)) for l in body_lines)
    n_refs = len(PARAM_REF.findall(code))
    total = inlined + n_refs
    return {
        "n_declared": len(decl),
        "n_declared_referenced": len(referenced & set(decl)),
        "n_declared_unreferenced": len(set(decl) - referenced),
        "unreferenced_names": sorted(set(decl) - referenced),
        "n_param_references": n_refs,
        "n_inlined_literals": inlined,
        "parametric_coverage": (n_refs / total) if total else 0.0,
    }


def perturb(code: str, name: str, new_value: float) -> str:
    def repl(m: re.Match) -> str:
        if m.group("name") != name:
            return m.group(0)
        return f"{m.group('head')}{new_value:g}{m.group('tail')}"
    return PARAM_ADD.sub(repl, code)


# ---------------------------------------------------------------------------
# execution
# ---------------------------------------------------------------------------
def flluma_namespace() -> dict:
    """Namespace for exec()ing a candidate. Mirrors the evaluation harness."""
    import flluma as fl
    from flluma import Parameters, Part  # noqa: F401
    ns = {"__name__": "__candidate__", "fl": fl}
    for attr in dir(fl):
        if not attr.startswith("_"):
            ns[attr] = getattr(fl, attr)
    return ns


def read_ply_ascii_xyz(path: str):
    """Same reader the geometry harness uses (evaluate_geometry_nbest.py)."""
    import numpy as np
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().splitlines()
    header_end = next(i for i, l in enumerate(lines) if l.strip() == "end_header")
    coords = [[float(v) for v in l.split()[:3]] for l in lines[header_end + 1:] if l.strip()]
    return np.asarray(coords, dtype=np.float64)


def sample_part_points(part: Any, n: int):
    """Point-cloud fingerprint. This is the ONLY geometry read that is known to
    exist on a Flluma Part -- `volume` and `bounding_box` do not, which an earlier
    version of this script assumed and consequently classified every perturbation as
    `change_unknown`. Mirrors evaluate_geometry_nbest.sample_part_points.
    """
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "fp.ply")
        try:
            part.export_pointcloud(out, point_count=n, normals=False, face_ids=False)
            pts = read_ply_ascii_xyz(out)
            return pts if len(pts) > 0 else None
        except Exception:
            return None


def chamfer(P, Q) -> float:
    """Symmetric mean-squared nearest-neighbour distance, same convention as
    evaluate_geometry_nbest.symmetric_chamfer (both halves carry the 1/2)."""
    import numpy as np
    try:
        from scipy.spatial import cKDTree
        d_pq, _ = cKDTree(Q).query(P)
        d_qp, _ = cKDTree(P).query(Q)
    except ImportError:
        d_pq = np.sqrt(((P[:, None, :] - Q[None, :, :]) ** 2).sum(-1).min(1))
        d_qp = np.sqrt(((Q[:, None, :] - P[None, :, :]) ** 2).sum(-1).min(1))
    return float(0.5 * np.mean(d_pq ** 2) + 0.5 * np.mean(d_qp ** 2))


def execute(code: str, fingerprint_points: int = 512) -> dict:
    """Run one program through the five gates, then take a geometry fingerprint.

    Gate calls match evaluate_geometry_nbest.py exactly: part.build() is called for
    effect, part.validate() returns False on failure, part.export_step(path) writes.
    """
    res: dict[str, Any] = {
        "syntax_ok": False, "exec_ok": False, "build_ok": False,
        "solid_valid": False, "step_export_ok": False,
        "points": None, "error": "",
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

    pts = sample_part_points(part, fingerprint_points)
    res["points"] = None if pts is None else pts.tolist()
    return res


def fingerprint_changed(base: dict, pert: dict, noise_floor: float) -> bool | None:
    """Did the geometry move?

    Compared by Chamfer distance between the two sampled clouds, against a noise
    floor measured by sampling the *baseline* twice. This matters because
    export_pointcloud is not seeded: two samples of the identical solid do not give
    identical points, so an exact comparison would call every perturbation a change.
    Conversely a bounding-box comparison would miss edits that change interior
    geometry only -- a fillet radius, say -- and report them as silently ignored.

    Threshold is 10x the measured noise floor, with an absolute lower bound so that a
    part whose resampling happens to be very stable does not get a threshold of ~0.
    """
    import numpy as np
    if not base.get("points") or not pert.get("points"):
        return None
    P = np.asarray(base["points"], dtype=np.float64)
    Q = np.asarray(pert["points"], dtype=np.float64)
    if len(P) == 0 or len(Q) == 0:
        return None
    return chamfer(P, Q) > max(10.0 * noise_floor, 1e-6)


def classify(base: dict, pert: dict, noise_floor: float) -> str:
    if not pert["step_export_ok"]:
        for gate in ("syntax_ok", "exec_ok", "build_ok", "solid_valid"):
            if not pert[gate]:
                return f"broke_at_{gate}"
        return "broke_at_step_export_ok"
    moved = fingerprint_changed(base, pert, noise_floor)
    if moved is None:
        return "rebuilt_change_unknown"
    return "rebuilt_and_moved" if moved else "rebuilt_no_change"


# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--input-jsonl", type=Path, required=True)
    p.add_argument("--output-jsonl", type=Path, required=True)
    p.add_argument("--summary-json", type=Path, required=True)
    p.add_argument("--deltas", default="-0.25,-0.1,0.1,0.25")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--program-field", default="prediction")
    env = os.environ.get("MIRAGE_STEP_FEATURE_ARGS")
    if env:
        return p.parse_args(shlex.split(env))
    return p.parse_args(sys.argv[1:])


def main() -> int:
    args = parse_args()
    deltas = [float(x) for x in args.deltas.split(",") if x.strip()]
    rows = read_jsonl(args.input_jsonl)
    if args.limit > 0:
        rows = rows[: args.limit]

    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    n_base_valid = 0
    n_probed = 0
    outcome_counts: dict[str, int] = {}
    per_delta: dict[str, dict[str, int]] = {f"{d:+.2f}": {} for d in deltas}
    cov_acc: list[float] = []
    noise_acc: list[float] = []
    dead_params = 0
    total_params = 0
    clamped = 0

    with open(args.output_jsonl, "w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            code = row.get(args.program_field, "") or ""
            sid = row.get("sample_id", "")
            cov = parametric_coverage(code)
            base = execute(code)

            rec = {"sample_id": sid, "modality": row.get("modality", ""),
                   "coverage": cov,
                   "baseline": {k: v for k, v in base.items() if k != "points"},
                   "perturbations": []}

            # Only kernel-valid baselines can be probed -- a program that never
            # built tells us nothing about whether editing it breaks it.
            if not base["step_export_ok"]:
                rec["skipped"] = "baseline not kernel-valid"
                rec["baseline"] = {k: v for k, v in base.items() if k != "points"}
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                continue
            n_base_valid += 1

            # Noise floor: re-execute the UNCHANGED program and Chamfer the two
            # samples. export_pointcloud is unseeded, so this is the resampling
            # variation we must clear before calling anything a real change.
            base2 = execute(code)
            noise = 0.0
            if base.get("points") and base2.get("points"):
                import numpy as np
                noise = chamfer(np.asarray(base["points"]), np.asarray(base2["points"]))
            rec["resample_noise_floor"] = noise
            noise_acc.append(noise)
            cov_acc.append(cov["parametric_coverage"])
            total_params += cov["n_declared"]
            dead_params += cov["n_declared_unreferenced"]

            decl = declared_params(code)
            for name, info in decl.items():
                for d in deltas:
                    target = info["value"] * (1.0 + d)
                    was_clamped = False
                    if info["min"] is not None and target < info["min"]:
                        target, was_clamped = info["min"], True
                    if info["max"] is not None and target > info["max"]:
                        target, was_clamped = info["max"], True
                    if abs(target - info["value"]) < 1e-12:
                        continue  # clamped onto its own value; no edit to test
                    pert = execute(perturb(code, name, target))
                    outcome = classify(base, pert, noise)
                    n_probed += 1
                    clamped += int(was_clamped)
                    outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
                    key = f"{d:+.2f}"
                    per_delta[key][outcome] = per_delta[key].get(outcome, 0) + 1
                    rec["perturbations"].append({
                        "param": name, "delta": d, "from": info["value"], "to": target,
                        "clamped_to_bound": was_clamped, "outcome": outcome,
                        "error": pert["error"],
                    })
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def pct(n: int) -> float:
        return round(100.0 * n / n_probed, 2) if n_probed else 0.0

    summary = {
        "n_rows": len(rows),
        "n_baseline_kernel_valid": n_base_valid,
        "n_perturbations": n_probed,
        "n_clamped_to_declared_bound": clamped,
        "outcomes": outcome_counts,
        "outcomes_pct": {k: pct(v) for k, v in outcome_counts.items()},
        "per_delta": per_delta,
        "editable_pct": pct(outcome_counts.get("rebuilt_and_moved", 0)),
        "silently_ignored_pct": pct(outcome_counts.get("rebuilt_no_change", 0)),
        "broke_pct": pct(sum(v for k, v in outcome_counts.items() if k.startswith("broke_"))),
        "mean_parametric_coverage": round(sum(cov_acc) / len(cov_acc), 4) if cov_acc else 0.0,
        "mean_resample_noise_floor": round(sum(noise_acc) / len(noise_acc), 9) if noise_acc else 0.0,
        "max_resample_noise_floor": round(max(noise_acc), 9) if noise_acc else 0.0,
        "declared_params_total": total_params,
        "declared_params_never_referenced": dead_params,
    }
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    with open(args.summary_json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(summary, fh, indent=2)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
