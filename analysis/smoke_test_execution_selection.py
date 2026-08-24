"""Self-contained smoke test for the corrected execution-selection gate logic
(no gen_scripts import — that module pulls in torch/transformers, which
FllumaCLI's embedded Python doesn't have). Mirrors the fixed
_evaluate_one/select_best_candidate logic in run_miragecad.py using the real
Part.build()/validate()/export_step() instance API.
"""
import ast
import json
import os
import tempfile


def flluma_exec_namespace():
    import flluma  # type: ignore

    return {name: getattr(flluma, name) for name in dir(flluma) if not name.startswith("_")}


def evaluate_one(code):
    result = {"syntax_ok": False, "exec_ok": False, "build_ok": False, "solid_valid": False, "step_export_ok": False, "validity": 0, "error": ""}
    try:
        ast.parse(code)
    except SyntaxError as exc:
        result["error"] = f"SyntaxError: {exc}"
        return result
    result["syntax_ok"] = True
    result["validity"] = 1

    ns = flluma_exec_namespace()
    try:
        exec(compile(code, "<candidate>", "exec"), ns)
        part = ns.get("part")
        if part is None:
            result["error"] = "no `part` variable after execution"
            return result
    except Exception as exc:
        result["error"] = f"exec error: {exc}"
        return result
    result["exec_ok"] = True
    result["validity"] = 2

    try:
        part.build()
    except Exception as exc:
        result["error"] = f"build error: {exc}"
        return result
    result["build_ok"] = True
    result["validity"] = 3

    try:
        if part.validate() is False:
            result["error"] = "part failed geometric validity check"
            return result
    except Exception as exc:
        result["error"] = f"validity check error: {exc}"
        return result
    result["solid_valid"] = True
    result["validity"] = 4

    with tempfile.TemporaryDirectory() as tmpdir:
        step_out = os.path.join(tmpdir, "candidate.step")
        try:
            part.export_step(step_out)
        except Exception as exc:
            result["error"] = f"STEP export error: {exc}"
            return result
    result["step_export_ok"] = True
    result["validity"] = 5
    return result


def select_best(candidates):
    results = [evaluate_one(c) for c in candidates]
    partial = [(i, r) for i, r in enumerate(results) if r["validity"] > 0]
    if partial:
        best_idx, _ = max(partial, key=lambda ir: ir[1]["validity"])
    else:
        best_idx = 0
    return best_idx, results


GOOD = """
params = Parameters()
params.add('height', 45.6, min=12, max=80, semantic_type='overall_height')
params.add('thickness', 11, min=3, max=25, semantic_type='thickness')
params.add('width', 78.0, min=20, max=120, semantic_type='overall_width')
part = Part('smoke_test_good', category='electronics_enclosure', parameters=params, seed=1, sample_id='smoke_test_good', units='mm')
plate = part.plate(name='floor_plate', width=params['width'], height=params['height'], thickness=params['thickness'], semantic_type='base_plate')
__all__ = ['part']
"""

BAD_API = """
params = Parameters()
params.add('height', 45.6, min=12, max=80, semantic_type='overall_height')
part = Part('smoke_test_bad_api', category='electronics_enclosure', parameters=params, seed=1, sample_id='smoke_test_bad_api', units='mm')
plate = part.plate(name='floor_plate', size=[10, 10, 10])
__all__ = ['part']
"""

BROKEN_SYNTAX = """
params = Parameters(
part = Part('smoke_test_broken'
"""

best_idx, results = select_best([GOOD, BAD_API, BROKEN_SYNTAX])
out = {"best_idx": best_idx, "results": results}
with open(r"C:\tmp\MIRAGE\exec_eval\smoke_test_result.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2)
print(json.dumps(out, indent=2))
