"""Re-export MIRAGE's predicted STEP for the 400 external Fusion 360 parts, RETAINING the file.

RUNS INSIDE FllumaCLI.exe ON WINDOWS. The native `flluma` module cannot be imported from any of
the three WSL conda environments, so this half of the comparison runs where the kernel lives and
the scoring half runs in `cadrecode_env`. They meet on disk under /mnt/c.

WHY THIS SCRIPT EXISTS AT ALL. C-EXT1-min already built and exported these parts, but
`evaluate_geometry_nbest.evaluate_one` exports into a `tempfile.TemporaryDirectory()` and scores
inside it, so every STEP was destroyed microseconds after being written. The common external
evaluator consumes STEP. Nothing about the model needs re-running -- only the file needs keeping.

IT DOES NOT REIMPLEMENT THE GATES; IT CALLS THE PUBLISHED ONES. The five gates are
`evaluate_geometry_nbest.evaluate_one` verbatim, invoked with `P_target=None` so it returns the
moment `step_export_ok` is set and never enters the scoring path. The only thing changed is WHERE
the export lands: the module's `tempfile` is redirected for the duration of one call to a directory
that persists. A hand-written copy of the gate sequence would mean the numbers in the paper's
external table came from code that merely resembles the code that produced its Build column --
which is the exact shape of error that has already cost this project three separate runs.

THE REDIRECT IS NARROW AND CHECKED, NOT ASSUMED. `evaluate_geometry_nbest` calls
`TemporaryDirectory()` in two places: `sample_part_points`, reached only when scoring, and
`evaluate_one`, which is what we want. Passing `P_target=None` should mean exactly one call per
sample, so the shim RAISES on a second call rather than quietly handing the point-cloud sampler a
directory it will fill with .ply files. The assumption is therefore enforced, not documented.

EVERY SAMPLE IS CHECKED AGAINST ITS OWN PUBLISHED GATE OUTCOME, not against the totals. The
published rows survive per sample, so a re-export that lands 232 exports is not good enough if they
are a different 232. Any sample whose gates differ is recorded as a MISMATCH and reported; the
kernel is not promised to be deterministic and if it is not, that is a finding rather than
something to average away.

RESUME AND CRASH. One generated program in the point/generated-plan arm takes the process down
with an access violation, which is why the published harness retries and appends. This script
appends and flushes after every sample for the same reason, so each attempt advances past at least
one crashing candidate and the loop terminates.

STDOUT IS NOT A CHANNEL HERE. FllumaCLI does not forward the embedded interpreter's stdout
reliably, so the report file is the evidence and prints are a convenience. Anything that matters is
written to disk before it is printed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

GATES = ["syntax_ok", "exec_ok", "build_ok", "solid_valid", "step_export_ok"]


class _PersistentDir:
    """Stands in for TemporaryDirectory for exactly one call, and does not delete anything."""

    def __init__(self, path: Path, owner: "_ShimState"):
        self.path = str(path)
        self.owner = owner

    def __enter__(self) -> str:
        return self.path

    def __exit__(self, *exc) -> bool:
        return False


class _ShimState:
    """Single-use-per-sample redirect of the module's tempfile, with the limit enforced."""

    def __init__(self):
        self.target: Path | None = None
        self.calls = 0

    def TemporaryDirectory(self, *a, **kw):
        self.calls += 1
        if self.calls > 1:
            raise RuntimeError(
                "evaluate_one asked for a second temporary directory. With P_target=None it "
                "should return at step_export_ok and never reach sample_part_points, so this "
                "means the call path changed and the redirect is no longer narrow.")
        assert self.target is not None
        return _PersistentDir(self.target, self)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def read_jsonl(p: Path) -> list[dict]:
    rows = []
    with open(p, encoding="utf-8-sig") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def published_gates(path: Path) -> dict[str, dict | None]:
    """sample_id -> the published candidate's gate dict, or None where the kernel crashed."""
    out: dict[str, dict | None] = {}
    for r in read_jsonl(path):
        cr = r.get("candidate_results") or []
        out[r["sample_id"]] = ({g: bool(cr[0].get(g)) for g in GATES} if cr else None)
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--input-jsonl", type=Path, required=True,
                   help="the PUBLISHED geom_input_<arm>.jsonl, so the code is the scored code")
    p.add_argument("--published-rows", type=Path, required=True,
                   help="geometry_nbest_rows.jsonl for this arm, for the per-sample gate check")
    p.add_argument("--step-root", type=Path, required=True)
    p.add_argument("--output-jsonl", type=Path, required=True)
    p.add_argument("--arm", required=True)
    p.add_argument("--limit", type=int, default=0)
    # FllumaCLI passes no argv to the embedded interpreter; the published scripts take their
    # arguments through this variable and so does this one.
    env = os.environ.get("MIRAGE_STEP_FEATURE_ARGS") or os.environ.get("KCADGEN_STEP_FEATURE_ARGS")
    return p.parse_args(shlex.split(env) if env else sys.argv[1:])


def main() -> int:
    args = parse_args()
    import evaluate_geometry_nbest as EG

    rows = read_jsonl(args.input_jsonl)
    if args.limit:
        rows = rows[: args.limit]
    pub = published_gates(args.published_rows)

    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if args.output_jsonl.exists():
        done = {r["sample_id"] for r in read_jsonl(args.output_jsonl)}

    # A sample_id written here but absent from the results killed the process. It is recorded as
    # a crash on the next attempt instead of being retried, which is what makes the retry loop
    # terminate: without it, the arm containing a kernel-killing candidate walks into the same
    # candidate every attempt and never advances. Copied from the published harness, which needed
    # it for this exact arm.
    inflight = args.output_jsonl.with_suffix(".inflight")
    crashed = set()
    if inflight.is_file():
        for s in inflight.read_text(encoding="utf-8").split():
            if s and s not in done:
                crashed.add(s)

    shim = _ShimState()
    real_tempfile = EG.tempfile
    log = args.output_jsonl.with_suffix(".report.txt")

    def note(msg: str) -> None:
        with open(log, "a", encoding="utf-8", newline="\n") as f:
            f.write(msg + "\n")
        print(msg, flush=True)

    note(f"=== {args.arm}: {len(rows)} rows, {len(done)} already exported, "
         f"{len(crashed)} previously crashed the kernel ===")

    for i, row in enumerate(rows, 1):
        sid = row["sample_id"]
        if sid in done:
            continue
        cands = row.get("all_candidates") or []
        out: dict = {"sample_id": sid, "arm": args.arm}

        if sid in crashed:
            out["status"] = "KERNEL_CRASH"
            out["error"] = ("the process died building this candidate; recorded on resume and "
                            "not retried, so the run advances")
            out["step_path"] = None
        elif not cands:
            out["status"] = "NO_CANDIDATE"
        else:
            with open(inflight, "a", encoding="utf-8", newline="\n") as fl:
                fl.write(sid + "\n")
                fl.flush()
                os.fsync(fl.fileno())   # useless unless it reaches the disk before the crash
            d = args.step_root / args.arm / sid
            d.mkdir(parents=True, exist_ok=True)
            shim.target, shim.calls = d, 0
            EG.tempfile = shim                      # narrow: one call, then restored
            t0 = time.time()
            try:
                # The PUBLISHED gate implementation, unmodified. P_target=None means it returns
                # at step_export_ok and never scores, so no reference cloud is needed here.
                res = EG.evaluate_one(cands[0], None, 1024)
                out["gates"] = {g: bool(res.get(g)) for g in GATES}
                out["error"] = res.get("error") or ""
                out["status"] = "OK"
            except Exception as e:                  # noqa: BLE001 - a result, not a crash
                out["status"] = f"GATE_CALL_FAILED: {type(e).__name__}: {e}"
            finally:
                EG.tempfile = real_tempfile
            out["seconds"] = round(time.time() - t0, 2)
            out["tempdir_calls"] = shim.calls

            step = d / "candidate.step"
            if step.exists() and step.stat().st_size > 0:
                out["step_path"] = str(step)
                out["step_bytes"] = step.stat().st_size
                out["step_sha256"] = sha256_file(step)
            else:
                out["step_path"] = None

        # The per-sample check: same gates as the published run, or a named mismatch.
        exp = pub.get(sid, "ABSENT")
        got = out.get("gates")
        if exp == "ABSENT":
            out["gate_check"] = "NOT_IN_PUBLISHED_ROWS"
        elif exp is None:
            out["gate_check"] = "published row was a kernel crash; nothing to compare"
        elif got is None:
            out["gate_check"] = "MISMATCH: no gates produced this time"
        else:
            out["gate_check"] = "match" if got == exp else f"MISMATCH: published {exp}, now {got}"

        with open(args.output_jsonl, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(out, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())     # a kernel crash must not lose the row that caused it

        note(f"  [{i}/{len(rows)}] {sid:26s} {out.get('status','')[:22]:22s} "
             f"step={'yes' if out.get('step_path') else 'no ':3s} {out['gate_check'][:34]}")

    # ---- summary, written before it is printed ------------------------------
    all_rows = read_jsonl(args.output_jsonl)
    n_step = sum(1 for r in all_rows if r.get("step_path"))
    mism = [r["sample_id"] for r in all_rows if r.get("gate_check", "").startswith("MISMATCH")]
    n_crash = sum(1 for r in all_rows if r.get("status") == "KERNEL_CRASH")
    note("")
    note(f"rows {len(all_rows)}   STEP retained {n_step}   gate mismatches {len(mism)}"
         f"   kernel crashes {n_crash}")
    if n_crash:
        note("  crashed candidates (recorded, not retried -- this is how the loop terminates):")
        for r in all_rows:
            if r.get("status") == "KERNEL_CRASH":
                note(f"    {r['sample_id']}")
    for g in GATES:
        note(f"  {g:16s} {sum(1 for r in all_rows if (r.get('gates') or {}).get(g))}")
    if mism:
        note("  MISMATCHED sample_ids (the kernel did not repeat itself; this is a finding):")
        for s in mism[:20]:
            note(f"    {s}")
    note(f"report -> {log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
