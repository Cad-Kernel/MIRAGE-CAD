"""Run CAD-Recode over all 400 external Fusion360 parts. Phase 2 data generation, not a trial.

RUNS IN cadrecode_env. Stage 2 was the trial and it passed; this produces the numbers. Nothing here
tunes anything: the protocol -- alpha = 1e-6 relative, angular 0.3, 8192 samples at seed 0, FPS to
256 from index 0, greedy at max_new_tokens 768 -- was frozen before any CAD-Recode output was seen,
and a poor result is a result.

IT ORCHESTRATES AND DOES NOT REIMPLEMENT. Every sample goes through cadrecode_stage2.run_one, the
same function validated on one part. A batch runner with its own copy of that logic would mean the
code checked on one sample and the code producing the paper's numbers were two things that merely
resemble each other -- which is exactly how this project lost eight hours to a stale script that ran
and reported success.

THE MODEL IS LOADED ONCE; THE GENERATED CODE NEVER IS. Reusing a 1.5B checkpoint across 400 samples
is the point of a batch. Reusing a process to exec 400 model-written programs is not: each one gets
a fresh subprocess, a fresh directory and a timeout, because over 400 samples something will hang or
segfault.

RESUME LOOKS AT `terminal`, NOT AT WHETHER A FILE EXISTS. run_one writes a RUNNING manifest before
it starts and a terminal one when it finishes. A sample interrupted between generation and execution
leaves a manifest that exists and is unfinished; treating that as done is the same mistake as
accepting a truncated 416-of-500 output because the file was non-empty.

FOUR KINDS OF NUMBER, AND NO INVENTED AGGREGATE. Coverage over all 400; CD conditional on the parts
that scored one, with the CD/floor distribution because the floor varies fiftyfold across shapes;
IoU conditional on the parts where the boolean is trustworthy, with evaluator failures counted
rather than silently set to zero; and the audits that catch a batch going wrong -- missing ids,
duplicate work, timing drift. No single "geometry score" is computed: coverage plus conditional
geometry says what happened, and a blended number would hide which half moved.

EXAMPLE SELECTION IS FIXED HERE, BEFORE THE RESULTS EXIST. Any qualitative figure uses the
median-IoU part, the 25th-percentile part, and a failure case, chosen by rank. Picking the
prettiest reconstruction after the fact would make the figure an illustration of nothing.
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def load_queries(path: str, limit: int = 0) -> list[tuple[str, str]]:
    rows = []
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            p = r.get("step_path_wsl") or r.get("step_path")
            if p and Path(p).exists():
                rows.append((r["sample_id"], p))
    ids = [s for s, _ in rows]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        raise ValueError(f"duplicate sample_id in the queries file: {sorted(dupes)[:5]}. A "
                         f"duplicate double-weights a row in every aggregate.")
    return rows[:limit] if limit else rows


def read_manifest(run_dir: Path, sid: str) -> dict | None:
    p = run_dir / sid / "run_manifest.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def summarise(mans: list[dict], n_total: int, out: Path) -> None:
    """Facts only. Whether this is good or bad is not decided here."""
    lines = ["=" * 78, "CAD-Recode over the external Fusion360 set -- factual summary", "=" * 78, ""]

    # ---- 1. coverage, over every common input ---------------------------------
    def n(pred) -> int:
        return sum(1 for m in mans if pred(m))

    got_gen = n(lambda m: "generation" in m)
    got_code = n(lambda m: m.get("extracted_code_sha256"))
    got_exec = n(lambda m: (m.get("execution", {}).get("runner_result", {}).get("status")
                            == "SUCCESS"))
    got_step = n(lambda m: m.get("artifacts", {}).get("prediction_step_sha256"))
    got_remesh = n(lambda m: m.get("evaluation", {}).get("remesh_status") == "ok")
    lines += ["1. COVERAGE, denominator = every common input id",
              f"   N total                     {n_total}",
              f"   manifests present           {len(mans)}",
              f"   generation completed        {got_gen}",
              f"   code extracted              {got_code}",
              f"   isolated execution ok       {got_exec}",
              f"   STEP exported               {got_step}",
              f"   common remesh ok            {got_remesh}", ""]

    from collections import Counter
    st_counts = Counter(m.get("pipeline_status", "MISSING") for m in mans)
    lines.append("   pipeline_status distribution, failures NOT dropped from the denominator:")
    for k, v in st_counts.most_common():
        lines.append(f"     {k:26s} {v}")
    lines.append("")

    # ---- 2. CD, conditional, against each part's own floor --------------------
    cds = [(m["sample_id"], m["evaluation"]["cd_x1000"], m["evaluation"].get("cd_floor_gt"))
           for m in mans
           if m.get("cd_status") == "ok" and m.get("evaluation", {}).get("cd_x1000") is not None]
    lines.append(f"2. CD, conditional.  n = {len(cds)} of {n_total}")
    if cds:
        vals = sorted(c for _, c, _ in cds)
        lines += [f"   median {st.median(vals):.4f}   mean {st.fmean(vals):.4f}",
                  f"   p25 {vals[len(vals)//4]:.4f}   p75 {vals[3*len(vals)//4]:.4f}"]
        ratios = sorted(c / fl for _, c, fl in cds if fl)
        if ratios:
            lines += [f"   CD / that part's own sampling floor:",
                      f"     median {st.median(ratios):.3f}   p25 {ratios[len(ratios)//4]:.3f}   "
                      f"p75 {ratios[3*len(ratios)//4]:.3f}",
                      f"     at or below 1x floor  {sum(1 for r in ratios if r <= 1.0)}/{len(ratios)}",
                      f"     at or below 2x floor  {sum(1 for r in ratios if r <= 2.0)}/{len(ratios)}",
                      "   The ratio matters more than the raw median: the floor varies about",
                      "   fiftyfold across these shapes, so one global figure would not say",
                      "   whether a CD is near the metric's resolution or far from it."]
    lines.append("")

    # ---- 3. IoU, conditional, with evaluator failures counted ----------------
    ious = [(m["sample_id"], m["evaluation"]["iou"]) for m in mans
            if m.get("iou_status") == "ok" and m.get("evaluation", {}).get("iou") is not None]
    iou_fail = [(m["sample_id"], m.get("iou_status")) for m in mans
                if m.get("pipeline_status") == "SUCCESS" and m.get("iou_status") != "ok"]
    lines.append(f"3. IoU, conditional.  n = {len(ious)} of {n_total}")
    if ious:
        vals = sorted(v for _, v in ious)
        lines += [f"   median {st.median(vals):.6f}   mean {st.fmean(vals):.6f}",
                  f"   p25 {vals[len(vals)//4]:.6f}   p75 {vals[3*len(vals)//4]:.6f}"]
    lines += [f"   IoU evaluator failures among otherwise-successful parts: {len(iou_fail)}",
              "   Never set to zero: a boolean failure is not a reconstruction of volume 0."]
    for sid, why in iou_fail[:10]:
        lines.append(f"     {sid}  {why}")
    if len(iou_fail) > 10:
        lines.append(f"     ... and {len(iou_fail) - 10} more")
    lines += ["", "   CD and IoU have DIFFERENT DENOMINATORS by design (frozen contract). Any",
              "   table must state each metric's own n.", ""]

    # ---- 4. audits that catch a batch going wrong ----------------------------
    lines.append("4. AUDITS")
    seen = [m["sample_id"] for m in mans]
    lines.append(f"   duplicate manifests         {len(seen) - len(set(seen))}")
    lines.append(f"   non-terminal manifests      "
                 f"{sum(1 for m in mans if not m.get('terminal'))}  (should be 0)")
    gens = [m.get("generation", {}).get("seconds") for m in mans]
    gens = [g for g in gens if g]
    if len(gens) > 20:
        half = len(gens) // 2
        lines += [f"   generation seconds          median {st.median(gens):.2f}, "
                  f"max {max(gens):.2f}",
                  f"   first half vs second half   {st.median(gens[:half]):.2f} vs "
                  f"{st.median(gens[half:]):.2f}",
                  "   A large drift between halves would suggest thermal or driver trouble"]
    lines.append("")

    # ---- example selection, by the rule fixed in advance ---------------------
    if ious:
        ranked = sorted(ious, key=lambda kv: kv[1])
        lines += ["5. QUALITATIVE EXAMPLES, chosen by the rule fixed before these results existed",
                  f"   median IoU        {ranked[len(ranked)//2][0]}  "
                  f"({ranked[len(ranked)//2][1]:.4f})",
                  f"   25th percentile   {ranked[len(ranked)//4][0]}  "
                  f"({ranked[len(ranked)//4][1]:.4f})"]
        fails = [m["sample_id"] for m in mans if m.get("pipeline_status") != "SUCCESS"]
        lines.append(f"   failure case      {fails[0] if fails else '(none)'}")
        lines.append("   Not the prettiest reconstruction: a figure chosen after the fact")
        lines.append("   illustrates the choosing, not the method.")
    lines.append("")
    lines.append("No aggregate 'geometry score' is computed. Coverage plus conditional geometry")
    lines.append("says what happened; a blended number would hide which half moved.")

    text = "\n".join(lines) + "\n"
    out.write_text(text, encoding="utf-8", newline="\n")
    print(text)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--queries", required=True)
    ap.add_argument("--cadrecode-repo", required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--summary-only", action="store_true",
                    help="re-summarise existing manifests without running anything")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    rows = load_queries(args.queries, args.limit)
    run_dir = Path(args.run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    out = Path(args.out) if args.out else run_dir / "batch_summary.txt"

    print(f"=== {len(rows)} samples, run dir {run_dir} ===")

    if not args.summary_only:
        from cadrecode_stage2 import load_model, run_one

        todo, done = [], 0
        for sid, path in rows:
            m = read_manifest(run_dir, sid)
            # Terminal, not merely present. A manifest written before an interrupted run exists
            # and is unfinished; skipping it would silently drop the sample.
            if m and m.get("terminal"):
                done += 1
            else:
                todo.append((sid, path))
        print(f"    {done} already terminal, {len(todo)} to run")

        if todo:
            t0 = time.time()
            model, tok, meta = load_model(args.cadrecode_repo, args.device)
            print(f"    model loaded in {time.time() - t0:.1f}s, reused for every sample")
            for i, (sid, path) in enumerate(todo, 1):
                t = time.time()
                try:
                    man = run_one(path, sid, str(run_dir), model, tok, meta,
                                  args.device, args.timeout, verbose=False)
                    status = man.get("pipeline_status")
                except Exception as e:
                    # One sample must never end the batch.
                    status = f"BATCH_EXCEPTION: {type(e).__name__}: {e}"
                print(f"  [{i}/{len(todo)}] {sid[:34]:34s} {status:22s} {time.time() - t:5.1f}s",
                      flush=True)

    mans = [m for m in (read_manifest(run_dir, sid) for sid, _ in rows) if m]
    summarise(mans, len(rows), out)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
