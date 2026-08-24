"""Execute one CAD-Recode-generated program in an isolated subprocess. Never imported.

RUN AS A SUBPROCESS ONLY, by cadrecode_stage2.py:

    python cadrecode_generated_runner.py --code code.py --out-step out.step --result result.json

WHY A SUBPROCESS AND NOT exec() IN THE EVALUATOR. This is arbitrary Python produced by a language
model, and the released demo runs it with a bare `exec(py_string, globals())`. Three things go wrong
in-process and none of them can be recovered from there: a `while True` hangs the whole run, an OCCT
segfault takes the evaluator's loaded model down with it, and anything the code writes lands in
whatever directory the evaluator happened to be in. A subprocess gives a timeout, a crash boundary,
and a working directory of its own -- and over 400 samples any of the three will eventually happen.

THE CONTRACT, from demo.ipynb cell 6. The generated program assigns a CadQuery Workplane to the
global name `r`; the demo then takes `globals()['r'].val()`. So this looks for exactly that name and
reports RESULT_R_MISSING when it is absent, rather than searching the namespace for something
plausible.

THE STEP IS THE ONLY GEOMETRY IT PRODUCES. The demo also tessellates here, at (0.001, 0.1), and
that mesh is deliberately NOT used for scoring: the frozen protocol re-tessellates every arm's STEP
through one common operator at alpha = 1e-6. The demo's mesh is released-behaviour reference, not a
measurement.

IT REPORTS, IT DOES NOT REPAIR. A failure to extract, execute, or export is a result about the
model, and rewriting the program to get past it would measure the rewrite instead.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import traceback
from contextlib import redirect_stdout
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--code", required=True)
    ap.add_argument("--out-step", required=True)
    ap.add_argument("--result", required=True)
    args = ap.parse_args()

    res: dict = {"status": "UNKNOWN"}

    def finish(status: str, **kw):
        res["status"] = status
        res.update(kw)
        Path(args.result).write_text(json.dumps(res, indent=2, default=str),
                                     encoding="utf-8", newline="\n")
        return 0 if status == "SUCCESS" else 1

    try:
        code = Path(args.code).read_text(encoding="utf-8")
    except Exception as e:
        return finish("EXECUTION_FAILED", error=f"cannot read code: {type(e).__name__}: {e}")

    try:
        import cadquery as cq
    except Exception as e:
        return finish("EXECUTION_FAILED", error=f"cadquery import: {type(e).__name__}: {e}")

    # The generated program's own prints are captured rather than interleaved with this report.
    ns: dict = {"cq": cq, "__name__": "__cadrecode__"}
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            exec(compile(code, "<generated>", "exec"), ns)
    except Exception as e:
        return finish("EXECUTION_FAILED",
                      error=f"{type(e).__name__}: {e}",
                      traceback=traceback.format_exc()[-4000:],
                      generated_stdout=buf.getvalue()[-4000:])
    res["generated_stdout"] = buf.getvalue()[-4000:]

    if "r" not in ns:
        return finish("RESULT_R_MISSING",
                      defined_names=sorted(k for k in ns
                                           if not k.startswith("__") and k != "cq")[:40])

    try:
        compound = ns["r"].val()
        res["shape_type"] = type(compound).__name__
        res["is_valid"] = bool(getattr(compound, "isValid", lambda: True)())
        bb = compound.BoundingBox()
        res["bbox"] = [bb.xlen, bb.ylen, bb.zlen]
    except Exception as e:
        return finish("CADQUERY_OBJECT_FAILED", error=f"{type(e).__name__}: {e}",
                      traceback=traceback.format_exc()[-4000:])

    try:
        cq.exporters.export(compound, args.out_step)
        p = Path(args.out_step)
        if not p.exists() or p.stat().st_size == 0:
            return finish("STEP_EXPORT_FAILED",
                          error=f"export returned without error but the file is "
                                f"{'missing' if not p.exists() else 'empty'}")
        res["step_bytes"] = p.stat().st_size
    except Exception as e:
        return finish("STEP_EXPORT_FAILED", error=f"{type(e).__name__}: {e}",
                      traceback=traceback.format_exc()[-4000:])

    return finish("SUCCESS")


if __name__ == "__main__":
    raise SystemExit(main())
