"""Diagnostic: find which call in the editability probe kills the FllumaCLI process.

The probe wrote its STEP files and then vanished at [3/4] with no traceback, which
means a hard exit rather than a Python exception. Run this under FllumaCLI to find
the offending call. Each step prints BEFORE it runs and flushes, so the last line
printed is the call that died.

    & $FllumaCli \\wsl.localhost\...\src\scratch\diag_probe_deps.py
"""
import json
import os
import sys
import tempfile

def step(msg):
    print(f"[diag] {msg}", flush=True)

step("start")
step(f"python {sys.version}")

step("import numpy ...")
try:
    import numpy as np
    step(f"  numpy {np.__version__}")
except Exception as exc:
    step(f"  numpy FAILED: {exc}")

step("import scipy.spatial.cKDTree ...")
try:
    from scipy.spatial import cKDTree
    step("  scipy cKDTree OK")
except Exception as exc:
    step(f"  scipy FAILED: {exc}  (probe falls back to a numpy O(n^2) path)")

step("import flluma ...")
import flluma as fl
step("  flluma OK")

IN = os.environ.get("DIAG_INPUT",
                    r"\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\outputs\editability_25k\c_step.jsonl")
step(f"reading first row of {IN}")
with open(IN, encoding="utf-8") as fh:
    row = json.loads(fh.readline())
code = row["prediction"]
step(f"  sample_id {row['sample_id']}, {len(code)} chars")

ns = {"__name__": "__candidate__", "fl": fl}
for a in dir(fl):
    if not a.startswith("_"):
        ns[a] = getattr(fl, a)

step("exec program ...")
exec(compile(code, "<diag>", "exec"), ns)
part = ns.get("part")
step(f"  part = {type(part)}")

step("part.build() ...")
part.build()
step("  build OK")

step("part.validate() ...")
v = part.validate()
step(f"  validate -> {v!r}")

step("dir(part) members of interest:")
step("  " + ", ".join(sorted(a for a in dir(part) if not a.startswith('_'))))

with tempfile.TemporaryDirectory() as td:
    sp = os.path.join(td, "d.step")
    step("part.export_step(...) ...")
    part.export_step(sp)
    step(f"  export_step OK, {os.path.getsize(sp)} bytes")

    pp = os.path.join(td, "d.ply")
    step("part.export_pointcloud(point_count=512, normals=False, face_ids=False) ...")
    part.export_pointcloud(pp, point_count=512, normals=False, face_ids=False)
    step(f"  export_pointcloud OK, exists={os.path.exists(pp)}, "
         f"{os.path.getsize(pp) if os.path.exists(pp) else 0} bytes")

    step("read ply header ...")
    with open(pp, encoding="utf-8", errors="replace") as fh:
        head = [next(fh, "") for _ in range(12)]
    step("  " + " | ".join(h.strip() for h in head if h.strip()))

step("SECOND export_pointcloud on the same part (the probe does this twice) ...")
with tempfile.TemporaryDirectory() as td:
    pp2 = os.path.join(td, "d2.ply")
    part.export_pointcloud(pp2, point_count=512, normals=False, face_ids=False)
    step(f"  second export OK, {os.path.getsize(pp2)} bytes")

step("re-exec the SAME program a second time in a fresh namespace ...")
ns2 = {"__name__": "__candidate__", "fl": fl}
for a in dir(fl):
    if not a.startswith("_"):
        ns2[a] = getattr(fl, a)
exec(compile(code, "<diag2>", "exec"), ns2)
p2 = ns2.get("part")
p2.build()
step("  second full execution OK  <- if the probe dies before here, re-execution is the problem")

step("ALL DIAGNOSTICS PASSED")
