"""Is "higher fidelity among successful builds" partly tautological?

The conditional comparison runs on parts BOTH arms could build. Retrieval builds close to
everything, so that subset is effectively "the parts the generated plan could build" -- selected
by the generated arm's own success. A part it can build is plausibly one whose plan it got
roughly right, so its fidelity advantage there might be partly circular.

There is a clean test that does not require a new run. Look at RETRIEVAL's fidelity on the two
subsets: the parts the generated arm built, and the parts it failed. Retrieval's behaviour does
not depend on the other arm, so any difference measures how much easier one subset is. If the
two are comparable, the subset is not selected for easiness and the generated arm's advantage is
real. If retrieval scores much better where the generated arm succeeded, those parts are simply
easier and the advantage is inflated.

What matters is the MAGNITUDE, not just the p-value: at n over a thousand, a difference far too
small to explain anything at all will still be significant.

    python src/scratch/conditional_selection_bias.py
"""
from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent

PAIRS = [
    ("compositional step", "geom_comp_step_ours", "geom_comp_step_nnir", 0.162, 0.111),
    ("compositional point", "geom_comp_point_ours", "geom_comp_point_nnir", 0.022, 0.020),
    ("external step", "geom_ext_step_genplan", "geom_ext_step_nnir", 0.012, 0.006),
    ("external point", "geom_ext_point_genplan", "geom_ext_point_nnir", 0.004, 0.004),
]


def load(name: str) -> dict[str, dict | None]:
    f = REPO / "scratch" / name / "geometry_nbest_rows.jsonl"
    if not f.is_file():
        return {}
    out: dict[str, dict | None] = {}
    for line in f.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        c = [x for x in r.get("candidate_results", []) if x.get("cd") is not None]
        out[r["sample_id"]] = c[0] if c else None
    return out


def mann_whitney(a: list[float], b: list[float]) -> tuple[float, float]:
    """Normal approximation with tie-averaged ranks. Enough to judge comparability."""
    merged = sorted([(v, 0) for v in a] + [(v, 1) for v in b])
    ranks: dict[int, float] = {}
    i = 0
    while i < len(merged):
        j = i
        while j + 1 < len(merged) and merged[j + 1][0] == merged[i][0]:
            j += 1
        r = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[k] = r
        i = j + 1
    r1 = sum(ranks[k] for k, (_, g) in enumerate(merged) if g == 0)
    n1, n2 = len(a), len(b)
    u = r1 - n1 * (n1 + 1) / 2
    mu = n1 * n2 / 2
    sd = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    z = (u - mu) / sd if sd > 0 else 0.0
    return z, 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))


def main() -> int:
    for label, ours_dir, nnir_dir, ours_cond, nnir_cond in PAIRS:
        O, N = load(ours_dir), load(nnir_dir)
        if not O or not N:
            print(f"{label}: missing rows\n")
            continue
        built = [N[s]["f_score_1pct"] for s in O if O[s] and N.get(s)]
        failed = [N[s]["f_score_1pct"] for s in O if not O[s] and N.get(s)]
        if not built or not failed:
            print(f"{label}: one subset is empty\n")
            continue
        mb, mf = statistics.median(built), statistics.median(failed)
        z, p = mann_whitney(built, failed)
        bias = mb - mf
        effect = ours_cond - nnir_cond
        print(f"{label}")
        print(f"  retrieval F@1% where the generated arm BUILT   n={len(built):<5} median {mb:.4f}")
        print(f"  retrieval F@1% where the generated arm FAILED  n={len(failed):<5} median {mf:.4f}")
        print(f"  difference (how much easier the subset is)     {bias:+.4f}   "
              f"Mann-Whitney z={z:.2f}, p={p:.3g}")
        print(f"  the advantage it would have to explain         {effect:+.4f}   "
              f"(conditional {ours_cond:.3f} vs {nnir_cond:.3f})")
        if abs(bias) < 1e-9:
            verdict = "no measurable selection effect"
        elif effect <= 0:
            verdict = "no advantage to explain on this arm"
        elif abs(bias) < 0.25 * abs(effect):
            verdict = (f"selection effect is real but bounded at {abs(bias)/abs(effect):.0%} of the "
                       f"advantage -- the advantage survives")
        else:
            verdict = ("selection effect is a substantial fraction of the advantage -- do not "
                       "claim the conditional result without it")
        print(f"  -> {verdict}\n")

    print("Read the magnitude, not the p-value. At n in the thousands a difference far too small")
    print("to account for anything is still significant, and reporting only p would turn a")
    print("bounded caveat into an apparent refutation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
