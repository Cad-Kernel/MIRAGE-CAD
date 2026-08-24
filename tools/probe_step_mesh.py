"""Can Flluma turn a STEP into a controllable mesh, and can it do B-Rep booleans? Ask, don't infer.

RUNS INSIDE FllumaCLI, via scripts/run_probe_step_mesh.ps1. Reads one STEP, writes nothing except
a report.

WHY A PROBE RATHER THAN READING MORE SOURCE. The Python API in flluma/api exposes
kernel_load_from_file, kernel_compute_volume and kernel_compute_surface_area, but no
kernel_tessellate and no kernel-level boolean -- while bindings.py DOES bind
TessellationParameters, BooleanOperation, BooleanOperationResult and Mesh as raw types. So the
capability may exist on the C++ objects with no Python wrapper in front of it. Reading further
would only let me guess; calling dir() on the real objects settles it.

The rule this follows, set out before the work started: if a key fact can only be guessed, stop
and build an explicit STEP-to-mesh pipeline in the CAD-Recode environment instead. A second,
auditable mesher beats an unauditable "it is probably the same OCCT underneath".

FOUR QUESTIONS, in the order that decides the architecture:

  1. Does a STEP load, and what is the loaded object?
  2. Is there a route to a triangle mesh, with vertices and indices reachable?
  3. Is the tessellation tolerance settable and the result deterministic? Without this, the mesh
     cannot be called part of the frozen operator -- only "the same OCCT stack", which is weaker.
  4. Can volumes and booleans be computed on the B-Rep directly? If yes, IoU needs no mesh at
     all, is more accurate than a mesh boolean, and stays inside the frozen stack -- which would
     dissolve half the mesh debt rather than paying it.

Question 4 carries its own correctness check: intersection(A, A) and union(A, A) must both have
A's volume, so IoU(A, A) must be exactly 1. A known answer, in the spirit of pinning the Chamfer
formula with a hand-computed 1520.
"""
from __future__ import annotations

import json
import os
import shlex
import sys
import traceback


def names(obj, *keywords) -> list[str]:
    """Public attribute names on obj whose name contains any keyword."""
    out = []
    for a in dir(obj):
        if a.startswith("_"):
            continue
        low = a.lower()
        if not keywords or any(k in low for k in keywords):
            out.append(a)
    return sorted(out)


def say(*a):
    """Courtesy only. FllumaCLI does not forward the embedded interpreter's stdout, so nothing
    here is load-bearing -- the report file is the channel that works."""
    print(*a, flush=True)


REPORT: dict = {}
REPORT_PATH = os.environ.get("MIRAGE_PROBE_OUT") or ""


def record(**kw) -> None:
    """Add findings and rewrite the report immediately.

    Immediately, because the previous runs produced no artefact at all: a failed kernel call
    returned before the single write at the end of main(), which is indistinguishable on disk from
    the script never having run. Flushing after every finding means whatever stage breaks, the
    facts gathered before it survive.
    """
    REPORT.update(kw)
    if not REPORT_PATH:
        return
    try:
        with open(REPORT_PATH, "w", encoding="utf-8", newline="\n") as f:
            json.dump(REPORT, f, indent=2, default=str)
    except Exception:
        pass


def note(msg: str) -> None:
    """A human-readable line that survives to the report as well as the invisible stdout."""
    say(msg)
    REPORT.setdefault("log", []).append(msg)
    record()


def main() -> int:
    env = os.environ.get("MIRAGE_STEP_FEATURE_ARGS") or ""
    argv = shlex.split(env) if env else sys.argv[1:]
    step = argv[0] if argv else ""
    if not step or not os.path.exists(step):
        note(f"FAIL no readable STEP given: {step!r}")
        return 1

    record(step=step)
    report = REPORT
    note("=" * 78)
    note("Flluma STEP -> mesh / B-Rep probe")
    note("=" * 78)

    import flluma
    from flluma.api import geometry as geo

    # ---- 1. load ------------------------------------------------------------------
    # Ask the factory what it actually has. create() returned None on the first probe, and
    # FllumaCLI's "OpenCASCADE: enabled" banner describes the build rather than a kernel
    # registered in this process, so one null is not an answer.
    note("--- 0. what kernels does the factory report? ---")
    kernel_type = None
    try:
        avail = geo.available_geometry_kernels()
        note(f"  available_geometry_kernels(): {[str(x) for x in avail]}")
        record(available_kernels=[str(x) for x in avail])
        for nm in ("OPENCASCADE", "MANIFOLD"):
            try:
                ok = geo.is_geometry_kernel_available(nm)
            except Exception as e:
                ok = f"error: {type(e).__name__}: {e}"
            note(f"  is_geometry_kernel_available({nm}) = {ok!r}")
            record(**{f"available_{nm}": str(ok)})
            if ok is True and kernel_type is None:
                kernel_type = nm
        from flluma.api import bindings as B0
        F = getattr(B0, "GeometryKernelFactory", None)
        note(f"  GeometryKernelFactory members: {names(F) if F else None}")
        record(factory_members=names(F) if F else None)
    except Exception as e:
        note(f"  FAIL {type(e).__name__}: {e}")
        record(kernel_query_error=f"{type(e).__name__}: {e}")
    if kernel_type is None:
        kernel_type = "OPENCASCADE"
        note(f"  none reported available; trying {kernel_type} anyway")
    record(kernel_type_tried=kernel_type)

    note("\n--- 1. does a STEP load, and into what? ---")
    try:
        k = geo.create_geometry_kernel(kernel_type)
        if k is None:
            other = "MANIFOLD" if kernel_type == "OPENCASCADE" else "OPENCASCADE"
            note(f"  create_geometry_kernel({kernel_type}) -> None; trying {other}")
            k = geo.create_geometry_kernel(other)
            note(f"  create_geometry_kernel({other}) -> {type(k).__name__}")
            record(kernel_fallback=other, kernel_fallback_type=type(k).__name__)
        note(f"  kernel: {type(k).__name__}")
        g = geo.kernel_load_from_file(k, step, "STEP")
        note(f"  loaded: {type(g).__name__}   truthy={bool(g)}")
        report["kernel_type"] = type(k).__name__
        report["loaded_type"] = type(g).__name__
    except Exception as e:
        note(f"  FAIL {type(e).__name__}: {e}")
        traceback.print_exc()
        report["load_error"] = f"{type(e).__name__}: {e}"
        print(json.dumps(report, indent=2))
        return 1

    # ---- 2. what can the kernel and the geometry actually do? ---------------------
    note("\n--- 2. mesh / tessellation / boolean surface, by introspection ---")
    kn = names(k, "mesh", "tessel", "triangul", "bool", "union", "inter", "volume", "area")
    gn = names(g, "mesh", "tessel", "triangul", "bool", "volume", "area", "vert", "tri", "face")
    note(f"  kernel   : {kn}")
    note(f"  geometry : {gn}")
    report["kernel_methods"] = kn
    report["geometry_methods"] = gn
    note(f"  kernel, everything public: {names(k)}")

    # ---- 3. volume and area on the B-Rep ------------------------------------------
    note("\n--- 3. volume and surface area on the loaded B-Rep ---")
    for label, fn in (("volume", geo.kernel_compute_volume),
                      ("surface_area", geo.kernel_compute_surface_area)):
        try:
            v = fn(k, g)
            note(f"  {label:12s} {v!r}")
            report[label] = v
        except Exception as e:
            note(f"  {label:12s} FAIL {type(e).__name__}: {e}")
            report[f"{label}_error"] = f"{type(e).__name__}: {e}"

    # ---- 4. TessellationParameters: does it exist and what is settable? -----------
    note("\n--- 4. TessellationParameters ---")
    try:
        from flluma.api import bindings as B
        TP = getattr(B, "TessellationParameters", None)
        if TP is None:
            note("  not bound")
        else:
            tp = TP()
            fields = names(tp)
            note(f"  {type(tp).__name__} fields: {fields}")
            report["tessellation_fields"] = fields
            for f in fields:
                try:
                    note(f"    {f} = {getattr(tp, f)!r}")
                except Exception:
                    pass
    except Exception as e:
        note(f"  FAIL {type(e).__name__}: {e}")

    # ---- 5. try to reach a mesh, twice, and check determinism --------------------
    note("\n--- 5. a triangle mesh from the loaded B-Rep? ---")
    mesh_fn = None
    for cand in ("tessellate", "to_mesh", "create_mesh", "mesh", "triangulate"):
        if hasattr(k, cand):
            mesh_fn = cand
            break
    if mesh_fn is None:
        note("  no candidate method on the kernel. Checking the geometry object.")
        for cand in ("tessellate", "to_mesh", "mesh", "triangulate"):
            if hasattr(g, cand):
                mesh_fn = f"geometry.{cand}"
                break
    note(f"  candidate: {mesh_fn!r}")
    report["mesh_method"] = mesh_fn
    if mesh_fn:
        try:
            target = g if mesh_fn.startswith("geometry.") else k
            fn = getattr(target, mesh_fn.split(".")[-1])
            m1 = fn(g) if target is k else fn()
            m2 = fn(g) if target is k else fn()
            for i, m in ((1, m1), (2, m2)):
                vc = getattr(m, "vertex_count", None)
                ic = getattr(m, "index_count", None)
                note(f"  call {i}: {type(m).__name__}  vertex_count={vc}  index_count={ic}")
                report[f"mesh_call{i}"] = {"type": type(m).__name__, "vertex_count": vc,
                                          "index_count": ic}
            same = (report.get("mesh_call1") == report.get("mesh_call2"))
            note(f"  deterministic across two calls: {same}")
            report["mesh_deterministic"] = same
            note(f"  mesh attributes: {names(m1)}")
        except Exception as e:
            note(f"  FAIL {type(e).__name__}: {e}")
            report["mesh_error"] = f"{type(e).__name__}: {e}"

    # ---- 6. B-Rep boolean, with a known answer -----------------------------------
    note("\n--- 6. B-Rep boolean, checked against a known answer ---")
    note("  intersection(A, A) and union(A, A) must both have A's volume, so IoU(A, A) = 1.")
    bool_fn = None
    for cand in ("boolean", "boolean_operation", "perform_boolean", "compute_boolean"):
        if hasattr(k, cand):
            bool_fn = cand
            break
    note(f"  candidate: {bool_fn!r}")
    report["boolean_method"] = bool_fn
    if bool_fn:
        try:
            g2 = geo.kernel_load_from_file(k, step, "STEP")
            from flluma.api import bindings as B
            BO = getattr(B, "BooleanOperation", None)
            note(f"  BooleanOperation members: {names(BO) if BO else None}")
            fn = getattr(k, bool_fn)
            for op_name in ("INTERSECTION", "INTERSECT", "UNION"):
                op = getattr(BO, op_name, None) if BO else None
                if op is None:
                    continue
                try:
                    res = fn(g, g2, op)
                    shape = getattr(res, "geometry", None) or getattr(res, "result", None) or res
                    vol = geo.kernel_compute_volume(k, shape)
                    note(f"  {op_name:13s} volume {vol!r}   (A's volume "
                        f"{report.get('volume')!r})")
                    report[f"bool_{op_name}"] = vol
                except Exception as e:
                    note(f"  {op_name:13s} FAIL {type(e).__name__}: {e}")
        except Exception as e:
            note(f"  FAIL {type(e).__name__}: {e}")

    note("\n" + "=" * 78)
    note("VERDICT INPUTS -- read these against the go/no-go rule")
    note("=" * 78)
    note(f"  STEP loads                        {'loaded_type' in report}")
    note(f"  volume on B-Rep                   {'volume' in report}")
    note(f"  a mesh method exists              {bool(report.get('mesh_method'))}")
    note(f"  mesh deterministic                {report.get('mesh_deterministic')}")
    note(f"  tessellation fields settable      {bool(report.get('tessellation_fields'))}")
    note(f"  B-Rep boolean method exists       {bool(report.get('boolean_method'))}")
    note("")
    note("  If the boolean and volume both work, IoU needs no mesh at all and stays inside the")
    note("  frozen OCCT stack. If the mesh route works AND its tolerance is settable, the mesh")
    note("  can be called part of the same operator. If either can only be guessed at, stop and")
    note("  build an explicit pipeline in the CAD-Recode environment instead.")

    record(completed=True)
    note(f"\nreport: {REPORT_PATH or '(MIRAGE_PROBE_OUT unset -- nothing written)'}")
    return 0


# Module-level marker and an UNCONDITIONAL call. The first run inside FllumaCLI printed nothing at
# all between its own [3/4] and [4/4] banners and wrote no report, while occt_floor_sample.py --
# same wrapper, same env-var convention -- printed normally. Rather than guess whether __name__
# differs or stdout is being discarded, print before anything else and call main() without the
# guard. If the marker appears, the guard was the problem; if it does not, output capture is.
# Unconditional call. Not because the __name__ guard failed -- it holds here -- but because
# nothing about this script's execution is observable from the console, so one less conditional
# between the file and its report is worth having.
record(module_reached=True, dunder_name=__name__)
main()
