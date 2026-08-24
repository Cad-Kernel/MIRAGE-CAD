"""Can Flluma sample a point cloud from an EXTERNAL STEP file?

This gates the whole cross-source diagnostic and takes half a minute to answer, so it
runs before any of that pipeline is written. Everywhere in this repository that produces
a point cloud does it from a part the kernel just BUILT from generated code
(`part.export_pointcloud`, evaluate_geometry_nbest.py:81). Nothing imports a STEP file
and samples it. The external evaluation needs exactly that: reference clouds for models
we did not author, to score generated geometry against.

Three possible answers, and each sends the work a different way:

  Flluma imports STEP and exposes the result as a part
      -> the reference clouds come from the same kernel that scores the generated ones,
         so sampling is consistent on both sides. Best case; write the prep pipeline.
  Flluma reads STEP only as B-Rep features, not as a part
      -> extract_step_brep_features still works for the STEP *input* modality, but the
         reference clouds need another sampler (pythonocc-core, trimesh on a mesh export).
         Consistency between the two sides then has to be argued rather than assumed.
  Neither
      -> the external set must ship its own point clouds, which changes the dataset choice.

Run it through FllumaCLI, which hosts the only Python that can import flluma:

  & "C:\\Workspace\\Project\\Flluma\\build\\Desktop_Qt_6_8_3_MSVC2022_64bit-Release\\bin\\FllumaCLI.exe" `
    "C:\\Workspace\\Project\\Paper\\MIRAGE-V2\\src\\scratch\\probe_step_import.py"

Override the test file with PROBE_STEP=<path>. The default is a corpus STEP, on the
principle that if it fails there it will not work on an external one either.
"""
import os
import sys
import tempfile
from pathlib import Path

DEFAULT_STEP = r"C:\Workspace\Project\FllumaOne\FllumaOne-100K\shard_0094\flluma_0094017\model.step"


# FllumaCLI swallows stdout on a non-zero exit -- the first run of this probe printed
# nothing at all and reported only "SystemExit: 1", losing the API listing that was the
# entire point. PROVENANCE.md already notes its stdout is awkward. So everything goes to
# a file, and main() always returns 0 so the CLI has no reason to hide anything.
REPORT = Path(r"C:\Workspace\Project\Paper\MIRAGE-V2\scratch\probe_step_import.txt")
_LINES: list[str] = []


def say(msg: str) -> None:
    _LINES.append(msg)
    print(f"[probe] {msg}", flush=True)


def flush_report() -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(chr(10).join(_LINES) + chr(10), encoding="utf-8")


def main() -> int:
    say("start")
    say(f"python {sys.version.split()[0]}")

    try:
        import flluma as fl
    except Exception as exc:
        say(f"import flluma FAILED: {exc}")
        return 2
    say("import flluma OK")

    step_path = os.environ.get("PROBE_STEP", DEFAULT_STEP)
    say(f"test file: {step_path}")
    if not Path(step_path).is_file():
        say("  ** that file does not exist; pass PROBE_STEP=<a .step path> **")
        return 2

    # ---- 1. what does the API surface offer? ------------------------------
    say("")
    say("--- names containing 'step', 'import', 'read' or 'load' ---")
    seen = set()
    for modname in ("flluma", "flluma.api", "flluma.api.evaluation"):
        try:
            mod = __import__(modname, fromlist=["*"])
        except Exception as exc:
            say(f"  {modname}: not importable ({exc})")
            continue
        hits = [n for n in dir(mod)
                if not n.startswith("_")
                and any(k in n.lower() for k in ("step", "import", "read", "load", "open"))]
        say(f"  {modname}: {', '.join(hits) if hits else '(none)'}")
        seen.update(hits)

    say("")
    say("--- names containing 'point', 'sample', 'mesh' or 'tessel' ---")
    for modname in ("flluma", "flluma.api", "flluma.api.evaluation"):
        try:
            mod = __import__(modname, fromlist=["*"])
        except Exception:
            continue
        hits = [n for n in dir(mod)
                if not n.startswith("_")
                and any(k in n.lower() for k in ("point", "sample", "mesh", "tessel"))]
        say(f"  {modname}: {', '.join(hits) if hits else '(none)'}")

    # ---- 2. does a Part expose an import? ---------------------------------
    say("")
    part_cls = getattr(fl, "Part", None)
    if part_cls is None:
        say("flluma.Part not found; listing top-level classes instead:")
        say("  " + ", ".join(n for n in dir(fl) if n[:1].isupper())[:400])
    else:
        methods = [n for n in dir(part_cls) if not n.startswith("_")]
        say(f"Part methods ({len(methods)}):")
        for k in range(0, len(methods), 8):
            say("    " + ", ".join(methods[k:k + 8]))
        cands = [n for n in methods
                 if any(k in n.lower() for k in ("import", "load", "read", "step", "open"))]
        say(f"  import-like: {cands or '(none)'}")

    # ---- 3. signatures first, then try -------------------------------------
    # The previous two rounds guessed call shapes and misread the failures. Print what
    # the functions actually accept before calling anything.
    import inspect
    ev = __import__("flluma.api.evaluation", fromlist=["*"])
    api = __import__("flluma.api", fromlist=["*"])
    say("")
    say("--- signatures ---")
    for label, obj in (("flluma.api.import_model", getattr(api, "import_model", None)),
                       ("flluma.api.ImportModel", getattr(api, "ImportModel", None)),
                       ("evaluation.export_pointcloud", getattr(ev, "export_pointcloud", None)),
                       ("evaluation.pointcloud_options", getattr(ev, "pointcloud_options", None)),
                       ("Part.__init__", getattr(fl.Part, "__init__", None)),
                       ("Part.add", getattr(fl.Part, "add", None)),
                       ("Part.add_solid", getattr(fl.Part, "add_solid", None)),
                       ("Part.build", getattr(fl.Part, "build", None)),
                       ("Part.export_pointcloud", getattr(fl.Part, "export_pointcloud", None))):
        if obj is None:
            say(f"  {label}: absent")
            continue
        try:
            say(f"  {label}{inspect.signature(obj)}")
        except (TypeError, ValueError):
            doc = (getattr(obj, "__doc__", "") or "").strip().splitlines()
            say(f"  {label}: <no signature>  doc: {doc[0] if doc else '(none)'}")

    say("")
    say("--- round 4: follow the evaluate_node_mesh lead ---")
    # What round 3 established, so this round is targeted rather than another guess:
    #   * Part.add/add_solid take a feature NAME, not geometry -- Part is a feature-tree
    #     builder and cannot ingest an imported STEP at all. That whole branch is closed.
    #   * export_pointcloud wants a Flluma::Core::Asset. A Shape is the wrong type, but a
    #     CustomNode PASSED the type check and failed later with "OCCT build failed",
    #     which says the node is asset-like and merely unevaluated.
    # evaluation exposes evaluate_node_mesh and export_mesh_to_obj, which is exactly the
    # missing step. If this fails, stop: the .obj files Fusion 360 ships are sufficient.
    out = Path(tempfile.gettempdir()) / "probe_external_cloud.ply"
    obj_out = Path(tempfile.gettempdir()) / "probe_external_mesh.obj"
    for label, obj in (("evaluation.evaluate_node_mesh", getattr(ev, "evaluate_node_mesh", None)),
                       ("evaluation.export_mesh_to_obj", getattr(ev, "export_mesh_to_obj", None)),
                       ("flluma.api.Mesh", getattr(api, "Mesh", None))):
        if obj is None:
            say(f"  {label}: absent"); continue
        try:
            say(f"  {label}{inspect.signature(obj)}")
        except (TypeError, ValueError):
            say(f"  {label}: <no signature>")

    say("")
    node = None
    try:
        node = api.import_model(step_path)
        say(f"  import_model -> {type(node).__name__}")
    except Exception as exc:
        say(f"  import_model failed: {type(exc).__name__}: {exc}")

    if node is not None:
        for label, fn in (
            ("evaluate_node_mesh(node) then export_pointcloud",
             lambda: ev.export_pointcloud(ev.evaluate_node_mesh(node), str(out), point_count=1024)),
            ("evaluate_node_mesh(node) then export_mesh_to_obj",
             lambda: ev.export_mesh_to_obj(ev.evaluate_node_mesh(node), str(obj_out))),
            ("export_mesh_to_obj(node) directly",
             lambda: ev.export_mesh_to_obj(node, str(obj_out))),
        ):
            for f in (out, obj_out):
                if f.exists():
                    f.unlink()
            try:
                fn()
            except Exception as exc:
                say(f"  {label}: {type(exc).__name__}: {str(exc)[:160]}")
                continue
            wrote = [(f, f.stat().st_size) for f in (out, obj_out) if f.exists() and f.stat().st_size]
            if wrote:
                for f, n in wrote:
                    say(f"  {label}: OK -> {f.name} ({n} bytes)")
                say("    ==> YES. Reference clouds can come from the same kernel that")
                say("        scores generated geometry, so both sides share a sampler.")
                return 0
            say(f"  {label}: no error but wrote nothing")

    say("")
    say("==> NO import path found above. Read the API listing: if something plausible is")
    say("    listed but not tried here, add it. Otherwise the reference clouds need a")
    say("    separate sampler and that choice belongs in the design before any code.")
    return 1


def _named(fl, path, meth):
    """Part requires a name; the first probe omitted it and read the TypeError as absence."""
    part = fl.Part("probe")
    return getattr(part, meth)(path) or part


if __name__ == "__main__":
    try:
        rc = main()
    except Exception as exc:                      # never let the CLI hide the report
        import traceback
        say(f"UNCAUGHT {type(exc).__name__}: {exc}")
        say(traceback.format_exc())
        rc = 3
    say("")
    say(f"verdict code: {rc}   (0 = Flluma can import+sample, 1 = no path found)")
    flush_report()
    print(f"[probe] report written to {REPORT}", flush=True)
    # No SystemExit at all: FllumaCLI prints "Execution failed" for ANY SystemExit,
    # including zero, which reads as an error when nothing went wrong.
