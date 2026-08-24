"""Does the new occt_file_to_pointcloud binding actually work, and is it trustworthy?

Two questions, and the first one answers the second for free.

  1. Corpus STEP.  FllumaOne ships, for every sample, a program.py, a model.step exported
     from it, and a point_cloud.npz sampled from the same CSG shape. So the released cloud
     and a cloud sampled from the STEP are two views of ONE part produced by two different
     routes. If they agree, the binding is right AND sampling a STEP is equivalent to
     sampling the program -- which is the assumption the whole external evaluation rests on.
     Nothing else in the repository has ever tested that equivalence, because until now
     there was no way to sample a STEP.

  2. External STEP.  A Fusion 360 Gallery file, authored by another tool entirely. Passing
     (1) but failing (2) would mean the binding works only on STEP that Flluma itself wrote.

Run it through FllumaCLI, which hosts the only Python that can import flluma:

  & "C:\\Workspace\\Project\\Flluma\\build\\Desktop_Qt_6_8_3_MSVC2022_64bit-Release\\bin\\FllumaCLI.exe" `
    "C:\\Workspace\\Project\\Paper\\MIRAGE-V2\\src\\scratch\\probe_step_pointcloud.py"

Everything goes to a report file and main() never raises SystemExit: FllumaCLI swallows
stdout on a non-zero exit and prints "Execution failed" for ANY SystemExit, zero included.
"""
import os
import sys
import tempfile
from pathlib import Path

CORPUS = Path(r"C:\Workspace\Project\FllumaOne\FllumaOne-100K\shard_0094\flluma_0094017")
EXTERNAL_DIR = Path(r"C:\Workspace\Project\Dataset\Fusion360Gallery\r1.0.1\reconstruction")
REPORT = Path(r"C:\Workspace\Project\Paper\MIRAGE-V2\scratch\probe_step_pointcloud.txt")

_LINES: list[str] = []


def say(msg: str = "") -> None:
    _LINES.append(msg)
    print(f"[probe] {msg}", flush=True)


def read_xyz(path: Path):
    """Parse the ascii xyz the exporter writes: one 'x y z' per line."""
    import numpy as np
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        p = line.split()
        if len(p) >= 3:
            try:
                rows.append((float(p[0]), float(p[1]), float(p[2])))
            except ValueError:
                continue                      # header or comment
    return np.asarray(rows, dtype=np.float64)


def describe(name, pts):
    import numpy as np
    lo, hi = pts.min(0), pts.max(0)
    say(f"    {name}: {len(pts)} points")
    say(f"      bbox min  {np.array2string(lo, precision=3)}")
    say(f"      bbox max  {np.array2string(hi, precision=3)}")
    say(f"      diagonal  {float(np.linalg.norm(hi - lo)):.4f}")
    say(f"      centroid  {np.array2string(pts.mean(0), precision=3)}")


def chamfer(a, b):
    """Symmetric Chamfer, plus the one-sided medians that say WHERE they disagree."""
    import numpy as np
    d_ab = np.sqrt(((a[:, None, :] - b[None, :, :]) ** 2).sum(-1).min(1))
    d_ba = np.sqrt(((b[:, None, :] - a[None, :, :]) ** 2).sum(-1).min(1))
    return (0.5 * (d_ab ** 2).mean() + 0.5 * (d_ba ** 2).mean(),
            float(np.median(d_ab)), float(np.median(d_ba)))


def sample(ev, step_path: Path, out: Path, n: int):
    """Call the new binding; return the cloud or None, saying why if it failed."""
    if out.exists():
        out.unlink()
    try:
        ev.extract_step_pointcloud(str(step_path), str(out), point_count=n,
                                   sampling="surface_uv", binary=False, random_seed=1337)
    except Exception as exc:
        say(f"    FAILED: {type(exc).__name__}: {str(exc)[:200]}")
        return None
    if not out.exists() or not out.stat().st_size:
        say("    returned without error but wrote nothing")
        return None
    say(f"    wrote {out.name} ({out.stat().st_size} bytes)")
    pts = read_xyz(out)
    if len(pts) == 0:
        say("    ** file is non-empty but parsed to zero points -- not the xyz layout **")
        say(f"    first 200 bytes: {out.read_bytes()[:200]!r}")
        return None
    return pts


def main() -> int:
    say(f"python {sys.version.split()[0]}")

    try:
        import numpy as np
    except Exception as exc:
        say(f"numpy unavailable ({exc}); cannot compare clouds")
        np = None

    try:
        from flluma.api import evaluation as ev
    except Exception as exc:
        say(f"import flluma FAILED: {exc}")
        return 2
    say("import flluma OK")

    have = hasattr(ev, "occt_file_to_pointcloud"), hasattr(ev, "extract_step_pointcloud")
    say(f"occt_file_to_pointcloud present: {have[0]}   extract_step_pointcloud: {have[1]}")
    if not all(have):
        say("  ** the new wrapper is missing. Wrong build, or evaluation.py not the one on disk. **")
        say(f"     evaluation.py in use: {getattr(ev, '__file__', '?')}")
        return 2

    tmp = Path(tempfile.gettempdir())
    verdict = {}

    # ---- 1. corpus STEP against the released reference cloud -------------------
    say()
    say("=" * 68)
    say("1. CORPUS STEP vs the released point_cloud.npz")
    say("=" * 68)
    step, npz = CORPUS / "model.step", CORPUS / "point_cloud.npz"
    if not step.is_file() or not npz.is_file():
        say(f"  sample incomplete at {CORPUS}; skipping")
        verdict["corpus"] = "skipped"
    else:
        ref = None
        if np is not None:
            d = np.load(npz)
            key = "points" if "points" in d else list(d.keys())[0]
            ref = np.asarray(d[key], dtype=np.float64)
            say(f"  released cloud key '{key}', {ref.shape}")
        n = len(ref) if ref is not None else 2048
        say(f"  sampling the STEP at the same {n} points")
        got = sample(ev, step, tmp / "probe_corpus.xyz", n)
        verdict["corpus"] = "ok" if got is not None else "failed"
        if got is not None and ref is not None:
            describe("released (from program)", ref)
            describe("sampled  (from STEP)", got)
            k = min(len(ref), len(got), 2048)          # keep the O(n^2) honest
            cd, m_ab, m_ba = chamfer(got[:k], ref[:k])
            diag = float(np.linalg.norm(ref.max(0) - ref.min(0)))
            say()
            say(f"  symmetric Chamfer      {cd:.6g}   ({cd / diag**2:.3g} of bbox diag^2)")
            say(f"  median nearest, sampled->released  {m_ab:.5f}")
            say(f"  median nearest, released->sampled  {m_ba:.5f}")
            say(f"  reference bbox diagonal            {diag:.5f}")
            say()
            if m_ab < 0.02 * diag and m_ba < 0.02 * diag:
                say("  ==> The two routes agree to within sampling noise. Sampling a STEP")
                say("      is equivalent to sampling the program it came from.")
            else:
                say("  ==> They DISAGREE. Before using this, find out why -- candidates are")
                say("      a unit or transform difference on STEP export, or the released")
                say("      cloud having been produced by different options.")

    # ---- 2. external STEP, authored by another tool ---------------------------
    say()
    say("=" * 68)
    say("2. EXTERNAL STEP (Fusion 360 Gallery)")
    say("=" * 68)
    ext = sorted(EXTERNAL_DIR.glob("*.step"))[:3] if EXTERNAL_DIR.is_dir() else []
    if not ext:
        say(f"  no .step under {EXTERNAL_DIR}; skipping")
        verdict["external"] = "skipped"
    else:
        oks = 0
        for f in ext:
            say(f"  {f.name}")
            pts = sample(ev, f, tmp / f"probe_ext_{f.stem}.xyz", 2048)
            if pts is not None:
                oks += 1
                if np is not None:
                    describe("sampled", pts)
                obj = f.with_suffix(".obj")
                if obj.is_file():
                    say(f"      (.obj ships beside it: {obj.stat().st_size} bytes)")
            say()
        verdict["external"] = f"{oks}/{len(ext)} ok"

    say("=" * 68)
    for k, v in verdict.items():
        say(f"  {k}: {v}")
    say("=" * 68)
    return 0


if __name__ == "__main__":
    try:
        rc = main()
    except Exception as exc:
        import traceback
        say(f"UNCAUGHT {type(exc).__name__}: {exc}")
        say(traceback.format_exc())
        rc = 3
    say()
    say(f"verdict code: {rc}")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(chr(10).join(_LINES) + chr(10), encoding="utf-8")
    print(f"[probe] report written to {REPORT}", flush=True)
