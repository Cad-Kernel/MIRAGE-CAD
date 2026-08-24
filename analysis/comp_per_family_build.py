"""B10, second half: per-family build rate on the compositional split.

The coverage table (heldout_family_op_coverage.py) shows the four held-out families
differ sharply in how well their constituent operations are represented in the
retained partition -- from 18.8% of rows down to 4.95%. If variant C's failures track
that, then the split is partly measuring operation rarity rather than compositional
novelty, which is the confound the paper flags but has not quantified.

Joins the per-row execution results to each row's family (CAT field of its reference
IR) and reports build rate per family per variant.

    python src/scratch/comp_per_family_build.py
"""
from __future__ import annotations

import json
import os
import re
from collections import defaultdict

WSL = "//wsl.localhost/Ubuntu/home/jizong/workspace/MIRAGE/src"
SCRATCH = r"C:\Workspace\Project\Paper\MIRAGE-V2\scratch"
BS = chr(92)
# rarest-constituent-operation coverage, from heldout_family_op_coverage.py
COVERAGE = {"cross_tab_profile_mount": 18.77, "stepped_profile_mount": 22.27,
            "face_recursive_mount": 4.95, "sweep_tube": 6.72}
N_OPS = {"cross_tab_profile_mount": 6, "stepped_profile_mount": 4,
         "face_recursive_mount": 6, "sweep_tube": 1}


def win(p: str) -> str:
    t = str(p).replace(BS, "/")
    if t.startswith("/mnt/") and len(t) > 6:
        return t[5].upper() + ":/" + t[7:]
    return t


def read_jsonl(path):
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


# sample_id -> family
fam_of = {}
for row in read_jsonl(f"{WSL}/data/25k_comp/comp_test.jsonl"):
    p = win(row.get("ir_path", ""))
    if not os.path.exists(p):
        continue
    m = re.search(r"^PART\s+\S+\s+CAT\s+(\S+)", open(p, encoding="utf-8",
                                                     errors="replace").read(), re.M)
    if m:
        fam_of[row["sample_id"]] = m.group(1)
print(f"resolved family for {len(fam_of)} held-out rows")

VARIANTS = [("C: Generated IR", "exec_ours_comp_{m}"),
            ("A: Direct-NN-IR", "exec_nnir_comp_direct_{m}"),
            ("B: Prior-NN-IR", "exec_nnir_comp_prior_{m}")]

for modality in ("step", "point", "text", "image"):
    print(f"\n=== {modality} ===")
    header = f"  {'family':<28}{'ops':>4}{'cov%':>7}"
    per_variant = {}
    for label, pat in VARIANTS:
        f = os.path.join(SCRATCH, pat.format(m=modality), "execution_rows.jsonl")
        if not os.path.exists(f):
            continue
        agg = defaultdict(lambda: [0, 0])   # family -> [built, total]
        for r in read_jsonl(f):
            fam = fam_of.get(r.get("sample_id"))
            if fam is None:
                continue
            ok = r.get("build_ok", r.get("exec_ok"))
            agg[fam][1] += 1
            agg[fam][0] += int(bool(ok))
        per_variant[label] = agg
        header += f"{label.split(':')[0]:>9}"
    if not per_variant:
        print("  (no execution rows found)")
        continue
    print(header)
    for fam in sorted(COVERAGE, key=lambda k: -COVERAGE[k]):
        line = f"  {fam:<28}{N_OPS[fam]:>4}{COVERAGE[fam]:>6.1f}%"
        for label in per_variant:
            built, tot = per_variant[label].get(fam, [0, 0])
            line += f"{(100.0*built/tot if tot else float('nan')):>8.1f}%"
        print(line)
