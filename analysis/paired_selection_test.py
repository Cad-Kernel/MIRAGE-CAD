"""Paired test for the best-of-N selection gain.

Comparing two independent Wilson intervals is the wrong test here and it
understates the evidence: N=1 and N=10 are evaluated on the SAME 100 parts, so the
comparison is paired. The marginal intervals for STEP (67.0 [57.3,75.4] and
82.0 [73.3,88.3]) barely overlap, which would invite the reader to call the gain
inconclusive; McNemar's exact test on the discordant pairs is the appropriate
statistic and answers it cleanly.

Selection is also monotone by construction: enlarging the candidate pool cannot
lower the furthest gate any candidate reaches, so a part that builds at N=1 must
build at N=10. That makes every discordant pair one-directional, which the test
below confirms rather than assumes.

    python src/scratch/paired_selection_test.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

SCRATCH = Path(r"C:\Workspace\Project\Paper\MIRAGE-V2\scratch")
GATES = ["syntax_ok", "exec_ok", "build_ok", "solid_valid", "step_export_ok"]


def best_gate_reached(cand: dict) -> int:
    """How far this candidate got: 0 = failed parse, 5 = exported STEP."""
    lvl = 0
    for i, g in enumerate(GATES, start=1):
        if cand.get(g):
            lvl = i
        else:
            break
    return lvl


def builds_at(cands: list[dict], n: int) -> bool:
    """Does the best of the first n candidates build? Candidate 0 is greedy."""
    return any(best_gate_reached(c) >= 3 for c in cands[:n])


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value on discordant counts b, c."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


for modality in ("step", "point"):
    f = SCRATCH / f"geometry_nbest_random100_{modality}" / "geometry_nbest_rows.jsonl"
    rows = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"=== {modality}: {len(rows)} parts ===")
    for hi in (3, 5, 10):
        b = c = both = neither = 0
        for r in rows:
            cands = r.get("candidate_results") or []
            lo_ok, hi_ok = builds_at(cands, 1), builds_at(cands, hi)
            if lo_ok and hi_ok:
                both += 1
            elif lo_ok and not hi_ok:
                b += 1          # lost by adding candidates -- should be impossible
            elif hi_ok and not lo_ok:
                c += 1          # gained
            else:
                neither += 1
        p = mcnemar_exact(b, c)
        note = "" if b == 0 else f"  <<< {b} part(s) LOST, monotonicity violated"
        print(f"  N=1 vs N={hi:<2}: both={both:>3} neither={neither:>3} "
              f"gained={c:>3} lost={b:>2}  McNemar exact p={p:.3g}{note}")
    print()
