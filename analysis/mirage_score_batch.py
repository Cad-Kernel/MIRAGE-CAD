"""Score MIRAGE's re-exported STEP through the COMMON external evaluator. Runs in cadrecode_env.

THE POINT OF THIS SCRIPT IS THAT IT ADDS NO METRIC. It calls `cadrecode_stage2.evaluate`, the same
function that produced every CAD-Recode number, on the same ground truth, with the same frozen
mesh operator at alpha = 1e-6. If the two arms were scored by two functions that agree in
principle, the paired table would be measuring the agreement of two implementations as much as the
difference between two systems.

WHY MIRAGE'S EXISTING GEOMETRY NUMBERS CANNOT BE REUSED. C-EXT1-min already reports Chamfer and
F@1% for these exact 400 parts, but through `evaluate_geometry_nbest.py`: 1,024 points subsampled
from precomputed 8,192-point clouds, raw millimetre-squared Chamfer, F-score at 1% of the target's
bbox diagonal. CAD-Recode's metric is a different quantity -- both shapes into the unit cube, 8,192
surface samples, bidirectional mean of SQUARED nearest-neighbour distances, summed, times 1000.
Those two numbers are not convertible into each other, and putting them in one table would be the
same category of error as comparing the internal Chamfer floor of 1.963 mm^2 against an external
one, which docs 9.20 already warns about in the other direction.

GROUND TRUTH IDENTITY IS PROVEN, NOT ASSUMED. For each part the CAD-Recode manifest recorded
`source_step_sha256` and `canonical_mesh_sha256` -- the hash of the GT file and of the tessellated,
normalised GT mesh actually scored against. This script rebuilds the GT through the same
`build_input` and REFUSES to score the sample if either hash differs. So "both systems were
measured against the same ground truth" is a checked claim about bytes rather than a statement
about intent.

GT IS BUILT ONCE AND USED FOR BOTH ARMS. Sample-major, not arm-major: tessellating each GT part
twice would cost the same as the whole CAD-Recode batch again and, worse, would give the two arms
two separately-derived GT meshes that only ought to be identical.

A PART THAT DID NOT BUILD IS NOT A PART THAT SCORED ZERO. MIRAGE's point/generated-plan arm
exports 232 of 400. Those 168 are coverage failures and appear in the coverage table; they never
enter a CD or IoU distribution as zeros, in either direction. Same contract as the CAD-Recode
side: coverage over all 400, geometry conditional on what produced geometry, every table carrying
its own n, evaluator failures named rather than dropped.

NOTHING HERE MAY RETUNE ANYTHING. The CAD-Recode arm is frozen and so is the protocol. If MIRAGE
scores badly that is a result; if it scores well that is a result. The one thing this script is
allowed to conclude is that a hash did not match, in which case it stops.
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ARMS = ["point_genplan", "point_nnir"]


def to_wsl(p: str) -> str:
    """C:\\x -> /mnt/c/x. The export half runs on Windows because that is where Flluma is."""
    t = str(p).replace("\\", "/")
    if len(t) > 2 and t[1] == ":":
        return f"/mnt/{t[0].lower()}{t[2:]}"
    return t


def read_jsonl(p: Path) -> list[dict]:
    rows = []
    with open(p, encoding="utf-8-sig") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def cadrecode_gt(run_dir: Path) -> dict[str, dict]:
    """sample_id -> the GT facts the CAD-Recode run recorded, which we must reproduce exactly."""
    out = {}
    for m in sorted(run_dir.glob("*/run_manifest.json")):
        d = json.loads(m.read_text(encoding="utf-8"))
        inp = d.get("input") or {}
        if not inp.get("canonical_mesh_sha256"):
            continue
        out[d["sample_id"]] = {"step_path": d["step_path"],
                               "source_step_sha256": inp["source_step_sha256"],
                               "canonical_mesh_sha256": inp["canonical_mesh_sha256"],
                               "mesh_triangle_count": inp["mesh_triangle_count"]}
    return out


def summarise(per_arm: dict[str, list[dict]], n_total: int, out: Path) -> None:
    L = ["=" * 78, "MIRAGE through the COMMON external evaluator -- facts only", "=" * 78,
         "Same evaluate(), same GT meshes (hash-verified), same alpha = 1e-6 as CAD-Recode.", ""]
    for arm in ARMS:
        rows = per_arm.get(arm) or []
        L += [f"--- {arm} ---", f"  rows                    {len(rows)} of {n_total}"]
        c = Counter(r.get("pipeline_status", "MISSING") for r in rows)
        for k, v in c.most_common():
            L.append(f"    {k:24s} {v}")
        L.append("  Coverage denominator is all "
                 f"{n_total}; a part that did not build is NOT a zero.")

        cds = [(r["sample_id"], r["evaluation"]["cd_x1000"], r["evaluation"].get("cd_floor_gt"))
               for r in rows if r.get("cd_status") == "ok"
               and (r.get("evaluation") or {}).get("cd_x1000") is not None]
        L.append(f"  CD   n = {len(cds)} of {n_total}")
        if cds:
            v = sorted(x for _, x, _ in cds)
            L += [f"    median {st.median(v):.4f}   mean {st.fmean(v):.4f}"
                  f"   p25 {v[len(v)//4]:.4f}   p75 {v[3*len(v)//4]:.4f}"]
            rt = sorted(x / fl for _, x, fl in cds if fl)
            if rt:
                L += [f"    CD / own floor: median {st.median(rt):.3f}   p25 {rt[len(rt)//4]:.3f}"
                      f"   p75 {rt[3*len(rt)//4]:.3f}",
                      f"    at or below 1x floor {sum(1 for x in rt if x <= 1.0)}/{len(rt)}"
                      f"   2x {sum(1 for x in rt if x <= 2.0)}/{len(rt)}"]
        ious = [r["evaluation"]["iou"] for r in rows if r.get("iou_status") == "ok"
                and (r.get("evaluation") or {}).get("iou") is not None]
        fails = [(r["sample_id"], r.get("iou_status")) for r in rows
                 if r.get("pipeline_status") == "SUCCESS" and r.get("iou_status") != "ok"]
        L.append(f"  IoU  n = {len(ious)} of {n_total}")
        if ious:
            v = sorted(ious)
            L += [f"    median {st.median(v):.6f}   mean {st.fmean(v):.6f}"
                  f"   p25 {v[len(v)//4]:.6f}   p75 {v[3*len(v)//4]:.6f}"]
        L.append(f"    IoU evaluator failures among scored parts: {len(fails)} "
                 f"(named, never set to 0)")
        for sid, why in fails[:10]:
            L.append(f"      {sid}  {why}")
        if len(fails) > 10:
            L.append(f"      ... and {len(fails) - 10} more")
        L.append("")
    L += ["CD and IoU have different denominators BY DESIGN, and so do the two arms.",
          "No cross-system comparison is computed here: that is a separate, paired analysis",
          "over the ids where the relevant arms both produced a number."]
    text = "\n".join(L) + "\n"
    out.write_text(text, encoding="utf-8", newline="\n")
    print(text)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mirage-runs", required=True, help="scratch/mirage_runs")
    ap.add_argument("--cadrecode-runs", required=True, help="scratch/cadrecode_runs, for the GT")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--summary-only", action="store_true")
    ap.add_argument("--timeout", type=int, default=600,
                    help="per (sample, arm); a 640k-triangle boolean is slow, not hung")
    ap.add_argument("--mem-mb", type=int, default=8192,
                    help="per-child address-space cap, so a huge boolean fails as a recordable "
                         "MemoryError instead of as an OOM kill of the whole batch")
    args = ap.parse_args()

    root = Path(args.mirage_runs)
    gt_facts = cadrecode_gt(Path(args.cadrecode_runs))
    print(f"GT facts recovered for {len(gt_facts)} parts from the CAD-Recode run")

    exports: dict[str, dict[str, dict]] = {}
    for arm in ARMS:
        f = root / arm / "export_rows.jsonl"
        if not f.exists():
            print(f"  {arm}: no export_rows.jsonl yet, skipping")
            continue
        exports[arm] = {r["sample_id"]: r for r in read_jsonl(f)}
        print(f"  {arm}: {len(exports[arm])} export rows, "
              f"{sum(1 for r in exports[arm].values() if r.get('step_path'))} with STEP")

    sids = sorted(set().union(*[set(v) for v in exports.values()])) if exports else []
    if args.limit:
        sids = sids[: args.limit]

    if not args.summary_only:
        worker = Path(__file__).resolve().parent / "mirage_score_one.py"
        if not worker.exists():
            print(f"missing worker {worker}", file=sys.stderr)
            return 1

        for i, sid in enumerate(sids, 1):
            g = gt_facts.get(sid)
            for arm in ARMS:
                r = (exports.get(arm) or {}).get(sid)
                if r is None:
                    continue
                mp = root / arm / sid / "score_manifest.json"
                if mp.exists():
                    try:
                        if json.loads(mp.read_text(encoding="utf-8")).get("terminal"):
                            continue
                    except Exception:
                        pass
                mp.parent.mkdir(parents=True, exist_ok=True)

                def stub(status: str, reason: str) -> dict:
                    m = {"sample_id": sid, "arm": arm, "terminal": True,
                         "pipeline_status": status, "reason": reason,
                         "gt_verified": None, "cd_status": None, "iou_status": None,
                         "gates": r.get("gates"), "gate_check": r.get("gate_check")}
                    mp.write_text(json.dumps(m, indent=2, default=str),
                                  encoding="utf-8", newline="\n")
                    return m

                # A part that produced no STEP is a coverage failure. It carries NO metric at
                # all -- not a zero, not a worst-case value - and it costs no subprocess.
                if not r.get("step_path"):
                    m = stub("NO_GEOMETRY", "this arm produced no STEP for this part: "
                             + (r.get("error") or r.get("status") or "gate failure"))
                elif g is None:
                    m = stub("NO_GT_RECORD", "no CAD-Recode GT record for this sample_id")
                else:
                    pred = to_wsl(r["step_path"])
                    if not Path(pred).exists():
                        m = stub("PRED_STEP_MISSING", pred)
                    else:
                        cmd = [sys.executable, str(worker),
                               "--gt-step", g["step_path"],
                               "--expect-source-sha", g["source_step_sha256"],
                               "--expect-mesh-sha", g["canonical_mesh_sha256"],
                               "--pred-step", pred, "--sample-id", sid, "--arm", arm,
                               "--out", str(mp), "--mem-mb", str(args.mem_mb)]
                        t0 = time.time()
                        try:
                            p = subprocess.run(cmd, capture_output=True, text=True,
                                               timeout=args.timeout)
                            rc, tout = p.returncode, False
                        except subprocess.TimeoutExpired:
                            rc, tout = None, True

                        # The child writes its own terminal manifest. If there is none, the child
                        # died -- OOM kill, segfault, timeout -- and the parent records THAT,
                        # because a part the evaluator could not measure must never be silently
                        # absent from the coverage table.
                        ok = False
                        if mp.exists():
                            try:
                                m = json.loads(mp.read_text(encoding="utf-8"))
                                ok = bool(m.get("terminal"))
                            except Exception:
                                ok = False
                        if not ok:
                            if tout:
                                m = stub("EVAL_TIMEOUT",
                                         f"no result within {args.timeout}s")
                            elif rc is not None and rc < 0:
                                m = stub("EVAL_KILLED",
                                         f"child killed by signal {-rc}"
                                         + (" (SIGKILL: almost certainly the OOM killer)"
                                            if -rc == 9 else ""))
                            else:
                                m = stub("EVAL_NO_MANIFEST",
                                         f"child exited {rc} without writing a manifest; "
                                         f"stderr tail: {(p.stderr or '')[-300:]}")
                        else:
                            # graft on what only the parent knows
                            m["gates"] = r.get("gates")
                            m["gate_check"] = r.get("gate_check")
                            m["seconds"] = round(time.time() - t0, 2)
                            mp.write_text(json.dumps(m, indent=2, default=str),
                                          encoding="utf-8", newline="\n")

                ev = m.get("evaluation") or {}
                print(f"  [{i}/{len(sids)}] {arm:14s} {sid:26s} "
                      f"{str(m.get('pipeline_status'))[:22]:22s} "
                      f"cd={ev.get('cd_x1000')} tri={ev.get('pred_mesh_triangles')}", flush=True)

    per_arm: dict[str, list[dict]] = {}
    for arm in ARMS:
        rows = []
        for sid in (exports.get(arm) or {}):
            mp = root / arm / sid / "score_manifest.json"
            if mp.exists():
                try:
                    rows.append(json.loads(mp.read_text(encoding="utf-8")))
                except Exception:
                    pass
        per_arm[arm] = rows
    n_total = len(gt_facts) or len(sids)
    summarise(per_arm, n_total, root / "score_summary.txt")
    print(f"wrote {root / 'score_summary.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
