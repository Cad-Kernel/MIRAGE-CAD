"""Aggregate evaluate_geometry_nbest.py's per-candidate raw results into
Table 4's N=1/3/5/10 rows. Selection matches run_miragecad.py's
select_best_candidate: among the first N candidates, prefer the lowest
(cd + 0.1*bbox_err) among those that were fully scored; else fall back to
the highest partial-validity candidate; else candidate 0.

Median CD / median F@1% are the headline Table 4 statistics. Mean CD / mean
F@1% are reported alongside as an auxiliary, outlier-sensitive statistic --
a rare kernel-valid-but-geometrically-degenerate candidate (e.g. a
mis-computed "through" depth blowing up one bbox axis) can pass every gate
and dominate the mean while median stays stable. `is_geometry_outlier` is a
diagnostic-only flag (bbox_ratio_to_gt > OUTLIER_BBOX_RATIO); it is reported
for visibility and is NOT used by select() or by any Table 4 statistic.
"""
import json
import statistics
import sys
from pathlib import Path

VALIDITY_ORDER = ["syntax_ok", "exec_ok", "build_ok", "solid_valid", "step_export_ok"]
OUTLIER_BBOX_RATIO = 10.0


def validity_level(c):
    level = 0
    for i, k in enumerate(VALIDITY_ORDER, start=1):
        if c.get(k):
            level = i
        else:
            break
    return level


def select(candidates, n):
    pool = candidates[:n]
    scored = [c for c in pool if c.get("cd") is not None]
    if scored:
        return min(scored, key=lambda c: c["cd"] + 0.1 * (c.get("bbox_err") or 0.0))
    partial = [(validity_level(c), c) for c in pool]
    partial = [c for lvl, c in partial if lvl > 0]
    if partial:
        return max(zip([validity_level(c) for c in partial], partial), key=lambda x: x[0])[1]
    return pool[0]


def is_geometry_outlier(c):
    """Diagnostic-only: does not affect select() or any Table 4 statistic."""
    ratio = c.get("bbox_ratio_to_gt")
    return ratio is not None and ratio > OUTLIER_BBOX_RATIO


def candidate_gate_breakdown(rows):
    """Per-candidate (not per-selected-N) gate funnel, across the whole pool."""
    counts = {"total": 0, "syntax_ok": 0, "exec_ok": 0, "build_ok": 0, "solid_valid": 0,
              "step_export_ok": 0, "pointcloud_scored": 0, "geometry_outlier": 0}
    export_ok_but_unscored = 0
    for r in rows:
        for c in r["candidate_results"]:
            counts["total"] += 1
            for k in ["syntax_ok", "exec_ok", "build_ok", "solid_valid", "step_export_ok"]:
                if c.get(k):
                    counts[k] += 1
            if c.get("cd") is not None:
                counts["pointcloud_scored"] += 1
                if is_geometry_outlier(c):
                    counts["geometry_outlier"] += 1
            elif c.get("step_export_ok"):
                export_ok_but_unscored += 1
    counts["step_export_ok_but_pointcloud_export_failed"] = export_ok_but_unscored
    return counts


def check_monotonicity(rows):
    """Per-sample check that the N-best selection's combined score
    (cd + 0.1*bbox_err) is non-increasing as N grows (guaranteed by
    construction since the candidate pool only grows with N -- a violation
    here means an aggregation bug, not a modeling result)."""
    violations = []
    for r in rows:
        scores = {}
        for n in [1, 3, 5, 10]:
            sel = select(r["candidate_results"], n)
            if sel.get("cd") is not None:
                scores[n] = sel["cd"] + 0.1 * (sel.get("bbox_err") or 0.0)
        ns = sorted(scores)
        for a, b in zip(ns, ns[1:]):
            if scores[b] > scores[a] + 1e-9:
                violations.append((r.get("sample_id"), a, scores[a], b, scores[b]))
    return violations


def paired_subset_analysis(rows):
    """Isolates whether a median-CD trend across N is a real per-sample effect
    or an artifact of the scored-sample set changing composition as N grows
    (larger N reaches step_export on previously-unscored, often harder,
    samples). Restricts to the subset of samples that have a scored candidate
    (cd is not None) at every one of N=1/3/5/10, so the same denominator is
    compared across N."""
    per_sample = {}
    for r in rows:
        sid = r.get("sample_id")
        cds = {}
        for n in [1, 3, 5, 10]:
            sel = select(r["candidate_results"], n)
            if sel.get("cd") is not None:
                cds[n] = sel["cd"]
        per_sample[sid] = cds

    paired_ids = [sid for sid, cds in per_sample.items() if all(n in cds for n in [1, 3, 5, 10])]
    print(f"--- paired-subset analysis (samples scored at ALL of N=1/3/5/10): {len(paired_ids)}/{len(rows)} ---")
    if not paired_ids:
        print("  No samples scored at every N -- cannot compare trends on a fixed denominator.")
        return
    for n in [1, 3, 5, 10]:
        vals = [per_sample[sid][n] for sid in paired_ids]
        print(f"  N={n:2d}: paired-subset median CD = {statistics.median(vals):.6f}  (n={len(vals)})")
    violations = 0
    for sid in paired_ids:
        cds = per_sample[sid]
        ns = [1, 3, 5, 10]
        for a, b in zip(ns, ns[1:]):
            if cds[b] > cds[a] + 1e-9:
                violations += 1
    print(f"  per-sample CD non-increasing across N: {len(paired_ids) * 3 - violations}/{len(paired_ids) * 3} step-pairs hold "
          f"({violations} step-pairs where CD increased despite a larger candidate pool -- "
          f"expected occasionally since selection optimizes cd + 0.1*bbox_err, not cd alone)")


def main():
    in_path = Path(sys.argv[1])
    rows = [json.loads(l) for l in open(in_path, encoding="utf-8") if l.strip()]
    rows = [r for r in rows if r.get("has_target")]

    print(f"=== {in_path} ===")
    print(f"rows (samples) with target: {len(rows)}")

    gates = candidate_gate_breakdown(rows)
    print("--- candidate-level gate funnel (across all candidates in pool) ---")
    total = gates["total"]
    print(f"  total candidates evaluated: {total}")
    for k in ["syntax_ok", "exec_ok", "build_ok", "solid_valid", "step_export_ok", "pointcloud_scored"]:
        v = gates[k]
        pct = v / total * 100 if total else 0.0
        print(f"  {k:35s}: {v}/{total} = {pct:.1f}%")
    print(f"  step_export_ok but pointcloud export/CD failed: {gates['step_export_ok_but_pointcloud_export_failed']}")
    print(f"  geometry_outlier (bbox_ratio_to_gt > {OUTLIER_BBOX_RATIO:g}x, diagnostic only, NOT filtered): "
          f"{gates['geometry_outlier']}/{gates['pointcloud_scored']} scored candidates")

    violations = check_monotonicity(rows)
    print("--- N=1/3/5/10 monotonicity check (selection score = cd + 0.1*bbox_err) ---")
    if violations:
        print(f"  VIOLATIONS FOUND ({len(violations)}):")
        for sid, n1, s1, n2, s2 in violations:
            print(f"    {sid}: N={n1} score={s1:.6f}  ->  N={n2} score={s2:.6f} (should be <=)")
    else:
        print("  OK: no violations (selection score non-increasing for every sample)")

    print("--- Table 4 headline: Median CD / Median F@1% (mean shown as auxiliary, outlier-sensitive) ---")
    for n in [1, 3, 5, 10]:
        build_ok = 0
        solid_valid = 0
        cds, fscores = [], []
        selected_outliers = 0
        for r in rows:
            sel = select(r["candidate_results"], n)
            if sel.get("build_ok"):
                build_ok += 1
            if sel.get("solid_valid"):
                solid_valid += 1
            if sel.get("cd") is not None:
                cds.append(sel["cd"])
                fscores.append(sel["f_score_1pct"])
                if is_geometry_outlier(sel):
                    selected_outliers += 1
        total = len(rows)
        print(f"--- N={n} (n_samples={total}) ---")
        print(f"  Build:      {build_ok}/{total} = {build_ok/total*100:.1f}%")
        print(f"  STEP Valid: {solid_valid}/{total} = {solid_valid/total*100:.1f}%")
        if cds:
            print(f"  Median CD:      {statistics.median(cds):.6f}   <- headline")
            print(f"  Median F@1%:    {statistics.median(fscores)*100:.1f}%   <- headline")
            print(f"  Mean CD:        {statistics.mean(cds):.6f}  (n_scored={len(cds)}/{total})  [auxiliary, outlier-sensitive]")
            print(f"  Mean F@1%:      {statistics.mean(fscores)*100:.1f}%  [auxiliary, outlier-sensitive]")
            if selected_outliers:
                print(f"  NOTE: {selected_outliers} selected candidate(s) flagged geometry_outlier "
                      f"(diagnostic only, still included in the stats above)")
        else:
            print("  No scored candidates (0 samples reached step_export with a target).")

    print()
    paired_subset_analysis(rows)


if __name__ == "__main__":
    main()
