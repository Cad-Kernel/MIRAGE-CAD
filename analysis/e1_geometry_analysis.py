"""E1 geometry: does removing the observation cost fidelity, or only build success?

Every E1 and E1b number so far is Build, and Build is a gate. Section 6.2 already showed the
two can move independently -- the shuffled prefix cost 2.8 points of Build and took median
Chamfer from 2.84 to 22.11 mm^2 -- so "plan-only builds 58.0 % against 71.4 %" says nothing
yet about whether the programs that do build reconstruct the queried part any less well.

Four cells, the same crossed design as E1b:

                          observation present     observation suppressed
      plan correct        C3                      C2
      plan shuffled       S3                      S2

C3 and S3 reuse geom_n1_step_prior and geom_n1_step_shuffled: E1's C3 programs are
byte-identical to N1's prior arm and S3 was staged from N1's shuffled arm unchanged. The
prep script verifies both identities by SHA-256 before this is relied on.

MEDIAN, NOT MEAN, AND A SIGN TEST. The distribution is heavy-tailed -- the deployed arm runs
to 1,404.66 mm^2 against a median of 2.84 -- so a mean would be set by a handful of
degenerate parts. The protocol makes the median the headline statistic for that reason, and
the paired comparison is a two-sided sign test over the parts both arms exported rather than
a t-test on values with no finite variance to speak of.

CONDITIONAL BY CONSTRUCTION. A Chamfer distance exists only where a program built and
exported, so every pairwise comparison here is over the intersection of two arms. That
favours whichever arm builds less, and the count is printed alongside each comparison so the
reader can see how much of each arm is being compared.

Run:  python src/scratch/e1_geometry_analysis.py
"""
from __future__ import annotations

import argparse
import json
import statistics as st
from math import comb
from pathlib import Path

# cell -> directory holding geometry_nbest_rows.jsonl
SOURCES = {
    "step_C3": "geom_n1_step_prior",       # reused: byte-identical to E1's C3
    "step_C2": "geom_e1_step_C2",
    "step_S3": "geom_n1_step_shuffled",    # reused: S3 was staged from this unchanged
    "step_S2": "geom_e1_step_S2",
    "text_C3": "geom_e1_text_C3",
    "text_C2": "geom_e1_text_C2",
    "step_A1": "geom_e1_step_A1",     # B1, 3 epochs, 9375 updates
    "step_A1E": "geom_e1_step_A1E",   # B1, 1 epoch, 3125 updates -- budget-conservative
    # B2P: predicted plan text, trained on predicted plans. Same 25,000 rows, same one epoch,
    # same grad-accum, so the SAME 3,125 updates as A1E. Exactly matched, not approximately.
    "step_B2P": "geom_e1_step_B2P",
}
LABEL = {
    "step_C3": "STEP  plan + observation",
    "step_C2": "STEP  plan only",
    "step_S3": "STEP  shuffled + observation",
    "step_S2": "STEP  shuffled, no observation",
    "text_C3": "text  plan + observation",
    "text_C2": "text  plan only",
    "step_A1": "STEP  latent only, 3 epochs",
    "step_A1E": "STEP  latent only, 1 epoch",
    "step_B2P": "STEP  predicted plan, exposure-matched",
}
COMPARISONS = [
    ("step_C3", "step_C2", "does removing the observation cost fidelity, not just Build?"),
    ("step_C3", "step_S3", "the published prefix intervention, as a reference point"),
    ("step_C2", "step_S2", "the same intervention with the bypass closed"),
    ("text_C3", "text_C2", "the modality contrast: Build showed no effect on text"),
    ("step_C3", "step_A1", "B1 at 3 epochs: does the latent alone match the plan?"),
    ("step_C3", "step_A1E", "B1 at 1 epoch, FEWER updates than deployed: the budget test"),
    ("step_C3", "step_B2P", "does exposure matching alone lift the plan-mediated arm?"),
    # The decisive one. Both arms saw exactly 3,125 updates on the same 25,000 rows, and each
    # trained on precisely the conditioning it meets at inference. Budget and exposure are both
    # controlled, so what is left is representation form: continuous latent against plan text.
    ("step_A1E", "step_B2P", "DECISIVE: latent vs predicted plan text, budget AND exposure matched"),
]


def two_sided_sign(k: int, n: int) -> float:
    if n == 0:
        return 1.0
    k = min(k, n - k)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def load(root: Path, cell: str) -> dict[str, dict]:
    """sample_id -> {cd, f1} for rows that actually produced a scorable solid."""
    p = root / SOURCES[cell] / "geometry_nbest_rows.jsonl"
    if not p.exists():
        return {}
    out = {}
    with p.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            cands = r.get("candidate_results") or []
            if not cands:
                continue
            c = cands[0]
            if not c.get("step_export_ok") or c.get("cd") is None:
                continue
            out[r["sample_id"]] = {"cd": c["cd"], "f1": c.get("f_score_1pct")}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path,
                    default=Path(r"C:\Workspace\Project\Paper\MIRAGE-V2\scratch"))
    ap.add_argument("--ceiling", type=float, default=0.244,
                    help="Attainable F@1%% on the internal set; see sec:geom_calibration.")
    args = ap.parse_args()

    arms = {c: load(args.root, c) for c in SOURCES}
    absent = [c for c, v in arms.items() if not v]
    if absent:
        print("")
        print("not scored yet: " + ", ".join(absent))
        print("run 41_e1_geometry_prep.sh, then the PowerShell loop it prints.")
    if not any(arms.values()):
        return 2
    # Everything below still runs on whatever exists. Showing the reusable cells before the
    # new ones are scored is the point: C3 vs S3 must reproduce the published 2.84 and 22.11,
    # and if it does not, the reuse claim is wrong and nothing else here can be trusted.

    print(f"\n{'=' * 78}\nE1 geometry   median Chamfer, mm^2   F@1 % against a ceiling of "
          f"{args.ceiling}\n{'=' * 78}\n")
    print(f"{'cell':<32}{'scored':>8}{'median CD':>12}{'median F@1%':>13}{'% of ceiling':>14}")
    for c in SOURCES:
        d = arms[c]
        if not d:
            print(f"{LABEL[c]:<32}{'--':>8}")
            continue
        cds = [v["cd"] for v in d.values()]
        f1s = [v["f1"] for v in d.values() if v["f1"] is not None]
        mf1 = st.median(f1s) if f1s else float("nan")
        print(f"{LABEL[c]:<32}{len(d):>8}{st.median(cds):>12.3f}{mf1:>13.3f}"
              f"{100 * mf1 / args.ceiling:>13.1f} %")

    print(f"\n{'-' * 78}\nPaired, over the parts both arms exported. Sign test, two-sided.\n"
          f"{'-' * 78}")
    for a, b, why in COMPARISONS:
        A, B = arms[a], arms[b]
        if not (A and B):
            print(f"\n  {a} vs {b}: not both scored")
            continue
        both = sorted(A.keys() & B.keys())
        if not both:
            print(f"\n  {a} vs {b}: no overlap")
            continue
        ma, mb = st.median([A[i]["cd"] for i in both]), st.median([B[i]["cd"] for i in both])
        wins = sum(1 for i in both if A[i]["cd"] < B[i]["cd"])   # lower Chamfer is better
        ties = sum(1 for i in both if A[i]["cd"] == B[i]["cd"])
        p = two_sided_sign(wins, len(both) - ties)
        print(f"\n  {a} vs {b}   n = {len(both)} both exported")
        print(f"    median CD   {ma:8.3f}  vs {mb:8.3f}    "
              f"{'first is closer' if ma < mb else 'second is closer'}")
        print(f"    {a} nearer on {wins} of {len(both) - ties} non-tied pairs, "
              f"p = {p:.4g}   {'separable' if p < 0.05 else 'NOT separable'}")
        print(f"    {why}")

    print(f"\n{'-' * 78}\nHow to read it\n{'-' * 78}")
    print("  Chamfer exists only where a program built and exported, so every row above is")
    print("  conditional on both arms succeeding. That favours whichever arm builds less, and")
    print("  it is why the n is printed for each comparison rather than once at the top.")
    print("  Median, not mean: the deployed arm's values reach 1,404.66 mm^2 against a median")
    print("  of 2.84, so a mean would be a statement about a few degenerate parts.")
    print("  F@1 % is shown against its attainable ceiling because a perfect self-match")
    print("  scores 0.244, not 1.0.")
    print("  No repair was applied and decoding was batched, so these cells are comparable to")
    print("  each other and not to the main tables.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
