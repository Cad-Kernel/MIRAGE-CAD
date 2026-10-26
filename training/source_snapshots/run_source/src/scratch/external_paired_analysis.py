"""The external comparison, in three layers. WRITTEN BEFORE ANY MIRAGE GEOMETRY NUMBER EXISTS.

That is the only reason the sign conventions below are worth anything. They are constants in this
file, not choices made while looking at a table, and if MIRAGE loses on every one of them the
script prints exactly the same thing with the sign flipped.

WHY THREE LAYERS AND NOT ONE SCORE. Coverage and fidelity answer different questions and move
independently -- this paper has already documented a case where the validity gate and the fidelity
metric point opposite ways on the same rows (docs 9.20, step modality: retrieval gains 30 points of
Build and loses fidelity at p = 4e-13). A blended "geometry score" would average those two
readings into a number that describes neither.

  LAYER 1  Coverage, all 400 inputs, genuinely paired. Who more often produces executable,
           exportable geometry at all? Immune to survivorship, because nothing is conditioned on.
  LAYER 2  Conditional fidelity, on the ids where BOTH systems produced geometry. Paired median
           difference with a paired bootstrap CI. CD and IoU get SEPARATE paired n, because
           CAD-Recode alone already has 392 and 379.
  LAYER 3  Winner counts plus a sign test. A median difference can be carried by a few extreme
           parts; the winner count says whether most parts lean slightly one way or a handful lean
           hugely.

FROZEN SIGN CONVENTIONS. Lower CD is better; higher IoU is better. Both deltas are
MIRAGE minus CAD-Recode:

    dCD  = CD_MIRAGE  - CD_CADR     dCD  > 0 means CAD-Recode is closer   (CAD-Recode better)
    dIoU = IoU_MIRAGE - IoU_CADR    dIoU > 0 means MIRAGE overlaps more   (MIRAGE better)

So the two metrics disagree in sign about who is winning, on purpose: each keeps its own natural
direction rather than being silently negated to make a table read uniformly.

SECONDARY, NOT A REPLACEMENT: floor-normalised CD, r = CD / that part's own sampling floor, and
dr = r_MIRAGE - r_CADR. The floor varies about fiftyfold across these shapes and CAD-Recode's own
400 land at a median r of 1.243 with 261/392 inside 2x floor, so a raw CD difference can be real
and still be below the resolution of the metric on that part. r says whether it is. It is a
diagnostic of ours and it does NOT replace the published CD definition.

THE SURVIVORSHIP CAVEAT, WHICH THE PAIRING DOES NOT REMOVE. point_genplan exports 232 of 400 and
CAD-Recode 392, so their intersection is about 230 parts -- and those are not a random 230, they
are disproportionately the parts MIRAGE found tractable. Layer 2 is therefore conditioned on
MIRAGE succeeding and tilts MIRAGE's way by construction. The permitted phrasing is "among parts
successfully reconstructed by both systems"; the forbidden phrasing is "MIRAGE has better external
geometry fidelity". Stated once here and once in the caption, not repeated beside every number.

INFORMATION CONDITIONS ARE NOT INTERCHANGEABLE. point_nnir retrieves a nearest-neighbour plan from
the training index at inference. It will have the cleaner statistics -- roughly 390 paired parts
against genplan's 230 -- and that is not a reason to promote it. It answers a different question:
where is the ceiling if construction information may be retrieved from the corpus? The headline
pairing stays CAD-Recode against the autonomous point_genplan.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics as st
import sys
from pathlib import Path

import numpy as np

# ---- frozen constants -----------------------------------------------------
BOOTSTRAP_B = 10000
BOOTSTRAP_SEED = 20260820
CI = (2.5, 97.5)
HEADLINE_ARM = "point_genplan"
ARMS = ["point_genplan", "point_nnir"]
CONDITION = {"point_genplan": "autonomous point->plan->code",
             "point_nnir": "retrieval-assisted (training-index NN plan at inference)"}


def exact_binom_two_sided(k: int, n: int) -> float:
    """Two-sided exact binomial p at q = 0.5. Used for McNemar and for the sign test.

    No scipy: this runs in whichever environment has the manifests, and a dependency that only
    exists to compute sum(C(n,i)) is a dependency that can be absent at the wrong moment.
    """
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(0, min(k, n - k) + 1))
    return min(1.0, 2.0 * tail / (2.0 ** n))


def paired_bootstrap_median(d: list[float]) -> tuple[float, float, float]:
    """Median of the paired differences, with a percentile CI over resampled PAIRS."""
    a = np.asarray(d, dtype=np.float64)
    if len(a) == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    idx = rng.integers(0, len(a), size=(BOOTSTRAP_B, len(a)))
    meds = np.median(a[idx], axis=1)
    lo, hi = np.percentile(meds, CI)
    return float(np.median(a)), float(lo), float(hi)


# ---------------------------------------------------------------------------
# loading
# ---------------------------------------------------------------------------
def load_cadrecode(run_dir: Path) -> dict[str, dict]:
    out = {}
    for p in sorted(run_dir.glob("*/run_manifest.json")):
        m = json.loads(p.read_text(encoding="utf-8"))
        ev = m.get("evaluation") or {}
        out[m["sample_id"]] = {
            "has_geometry": m.get("pipeline_status") == "SUCCESS",
            "cd": ev.get("cd_x1000") if m.get("cd_status") == "ok" else None,
            "floor": ev.get("cd_floor_gt"),
            "iou": ev.get("iou") if m.get("iou_status") == "ok" else None,
        }
    return out


def load_mirage(run_dir: Path, arm: str) -> dict[str, dict]:
    out = {}
    for p in sorted((run_dir / arm).glob("*/score_manifest.json")):
        m = json.loads(p.read_text(encoding="utf-8"))
        ev = m.get("evaluation") or {}
        out[m["sample_id"]] = {
            "has_geometry": m.get("pipeline_status") == "SUCCESS",
            "cd": ev.get("cd_x1000") if m.get("cd_status") == "ok" else None,
            "floor": ev.get("cd_floor_gt"),
            "iou": ev.get("iou") if m.get("iou_status") == "ok" else None,
            "gt_verified": m.get("gt_verified"),
        }
    return out


# ---------------------------------------------------------------------------
# the three layers
# ---------------------------------------------------------------------------
def layer1(cadr: dict, mir: dict, ids: list[str], arm: str) -> list[str]:
    """Coverage over every input. Nothing conditioned on, so no survivorship."""
    both = only_c = only_m = neither = 0
    for s in ids:
        c, m = cadr[s]["has_geometry"], mir[s]["has_geometry"]
        both += c and m
        only_c += c and not m
        only_m += m and not c
        neither += (not c) and (not m)
    p = exact_binom_two_sided(min(only_c, only_m), only_c + only_m)
    return [f"  CAD-Recode vs {arm}",
            f"    n paired                {len(ids)}",
            f"    CAD-Recode produced     {sum(1 for s in ids if cadr[s]['has_geometry'])}/{len(ids)}",
            f"    {arm:<21s} {sum(1 for s in ids if mir[s]['has_geometry'])}/{len(ids)}",
            f"    both                    {both}",
            f"    CAD-Recode only         {only_c}",
            f"    {arm} only{' ' * max(1, 13 - len(arm))}{only_m}",
            f"    neither                 {neither}",
            f"    McNemar exact p         {p:.4g}  (on the {only_c + only_m} discordant pairs)"]


def layer23(cadr: dict, mir: dict, ids: list[str], arm: str) -> list[str]:
    """Conditional fidelity and winner counts, each metric on its OWN paired denominator."""
    L = [f"  CAD-Recode vs {arm}"]
    for name, key, better_when_positive in (("CD", "cd", False), ("IoU", "iou", True)):
        pairs = [(s, mir[s][key], cadr[s][key]) for s in ids
                 if mir[s][key] is not None and cadr[s][key] is not None]
        d = [m - c for _, m, c in pairs]
        L.append(f"    --- {name} ---")
        L.append(f"    paired n                {len(pairs)}")
        if not pairs:
            L.append("    (no paired parts, nothing computed)")
            continue
        med, lo, hi = paired_bootstrap_median(d)
        L += [f"    median {name}_MIRAGE      {st.median([m for _, m, _ in pairs]):.6f}",
              f"    median {name}_CAD-Recode  {st.median([c for _, _, c in pairs]):.6f}",
              f"    median d{name}            {med:+.6f}   95% CI [{lo:+.6f}, {hi:+.6f}]",
              f"    excludes zero           {'yes' if (lo > 0 or hi < 0) else 'no'}"]
        # direction, spelled out so the sign cannot be misread
        if med > 0:
            who = "MIRAGE" if better_when_positive else "CAD-Recode"
        elif med < 0:
            who = "CAD-Recode" if better_when_positive else "MIRAGE"
        else:
            who = "neither"
        L.append(f"    median favours          {who}"
                 f"   (d{name} = {name}_MIRAGE - {name}_CADR; "
                 f"{'higher' if better_when_positive else 'lower'} is better)")

        # Layer 3: winner counts and a sign test.
        mw = sum(1 for x in d if (x > 0) == better_when_positive and x != 0)
        cw = sum(1 for x in d if x != 0 and (x > 0) != better_when_positive)
        tie = sum(1 for x in d if x == 0)
        L += [f"    MIRAGE better on        {mw}/{len(pairs)}",
              f"    CAD-Recode better on    {cw}/{len(pairs)}",
              f"    exact ties              {tie}",
              f"    sign test p             {exact_binom_two_sided(min(mw, cw), mw + cw):.4g}"]

        if key == "cd":
            # How many differences are smaller than the metric can resolve on that part. NOT
            # counted as ties -- the sign test above is untouched -- but a difference below the
            # larger of the two sampling floors is not a difference the protocol can see.
            unres = sum(1 for (s, m, c) in pairs
                        if (fl := max(mir[s]["floor"] or 0.0, cadr[s]["floor"] or 0.0))
                        and abs(m - c) < fl)
            L.append(f"    |dCD| below the larger sampling floor: {unres}/{len(pairs)}"
                     f"  (diagnostic; not treated as ties)")
            # Secondary, floor-normalised.
            rp = [(m / mir[s]["floor"], c / cadr[s]["floor"]) for (s, m, c) in pairs
                  if mir[s]["floor"] and cadr[s]["floor"]]
            if rp:
                dr = [a - b for a, b in rp]
                med_r, lo_r, hi_r = paired_bootstrap_median(dr)
                L += [f"    SECONDARY r = CD/own floor, n {len(rp)}",
                      f"      median r_MIRAGE       {st.median([a for a, _ in rp]):.3f}",
                      f"      median r_CAD-Recode   {st.median([b for _, b in rp]):.3f}",
                      f"      median dr             {med_r:+.3f}   95% CI [{lo_r:+.3f}, {hi_r:+.3f}]",
                      "      Diagnostic only. It does NOT replace the published CD definition."]
    return L


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cadrecode-runs", required=True)
    ap.add_argument("--mirage-runs", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    cadr = load_cadrecode(Path(args.cadrecode_runs))
    if not cadr:
        print("no CAD-Recode manifests found", file=sys.stderr)
        return 1

    L = ["=" * 78, "External comparison: coverage, then conditional fidelity, then winner counts",
         "=" * 78, "",
         "Sign conventions were frozen in this script BEFORE any MIRAGE geometry existed:",
         "  dCD  = CD_MIRAGE  - CD_CADR    ; lower CD is better, so dCD  > 0 favours CAD-Recode",
         "  dIoU = IoU_MIRAGE - IoU_CADR   ; higher IoU is better, so dIoU > 0 favours MIRAGE",
         "No overall geometry score is computed: coverage and fidelity answer different questions",
         "and this paper has already documented them pointing opposite ways on the same rows.", ""]

    present = []
    for arm in ARMS:
        mir = load_mirage(Path(args.mirage_runs), arm)
        if not mir:
            L.append(f"[{arm}] no score manifests yet -- run mirage_score_batch.py first.")
            continue
        ids = sorted(set(cadr) & set(mir))
        if set(cadr) != set(mir):
            L += [f"[{arm}] ** id sets differ: CAD-Recode {len(cadr)}, {arm} {len(mir)}, "
                  f"common {len(ids)}. The comparison is restricted to the common ids and this "
                  f"is reported, not silently absorbed. **"]
        bad = [s for s in ids if mir[s].get("gt_verified") is False]
        if bad:
            L.append(f"[{arm}] ** {len(bad)} parts have UNVERIFIED ground truth and are excluded: "
                     f"{bad[:4]} **")
            ids = [s for s in ids if s not in set(bad)]
        present.append((arm, mir, ids))

    if not present:
        L.append("")
        L.append("Nothing to compare yet. This script is deliberately written and frozen ahead of")
        L.append("the MIRAGE numbers so the statistics cannot be chosen to suit them.")
    for label, fn in (("LAYER 1 -- COVERAGE, all inputs, nothing conditioned on", layer1),
                      ("LAYER 2/3 -- CONDITIONAL FIDELITY and WINNER COUNTS, common-success only",
                       layer23)):
        if not present:
            break
        L += ["", "=" * 78, label, "=" * 78]
        for arm, mir, ids in present:
            L += fn(cadr, mir, ids, arm)
            L.append("")

    if present:
        L += ["=" * 78, "READING THIS TABLE", "=" * 78,
              f"HEADLINE pairing is CAD-Recode vs {HEADLINE_ARM} ({CONDITION[HEADLINE_ARM]}).",
              f"point_nnir is {CONDITION['point_nnir']} -- CAD-Recode has no such information",
              "source, so it is a retrieval-assisted reference answering a different question,",
              "not MIRAGE's entry in a like-for-like contest. It will have the cleaner statistics",
              "and that is not a reason to promote it.",
              "",
              "SURVIVORSHIP. Layer 2 is conditioned on BOTH systems succeeding, so for an arm with",
              "low coverage the surviving parts are disproportionately the ones it found tractable.",
              "Permitted: 'among parts successfully reconstructed by both systems, ...'.",
              "Not permitted: 'MIRAGE has better external geometry fidelity'. Layer 1 carries the",
              "system-level reading and must be quoted alongside Layer 2, never replaced by it.",
              "",
              "Neither layer may be combined into one number."]

    text = "\n".join(L) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8", newline="\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
