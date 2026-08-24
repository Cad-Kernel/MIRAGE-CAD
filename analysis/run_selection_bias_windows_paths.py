"""src/scratch/conditional_selection_bias.py's test, run against the right scratch path.

That script resolves its rows as REPO/"scratch", which does not exist on the WSL side -- the
committed scratch/ lives in the Windows repository -- so it prints "missing rows" for all four
pairs and its result has never been seen. Its logic is reproduced here verbatim rather than
patching the original, which is not mine to change.

The question it answers matters for Figure 5's Panel A caption: the conditional comparison runs on
parts BOTH arms can score, and retrieval scores almost everything, so that subset is effectively
"the parts the generated arm could handle". If those parts are simply easier, the generated arm's
conditional advantage is partly circular. Retrieval's own fidelity on the two subsets measures how
much easier, because retrieval's behaviour does not depend on the other arm.
"""
import json
import math
import pathlib
import statistics

SCRATCH = pathlib.Path(r"C:\Workspace\Project\Paper\MIRAGE-V2\scratch")

# (label, ours_dir, nnir_dir, ours_conditional, nnir_conditional) -- the last two are the
# published conditional medians the selection effect would have to explain.
PAIRS = [
    ("compositional step", "geom_comp_step_ours", "geom_comp_step_nnir", 0.162, 0.111),
    ("compositional point", "geom_comp_point_ours", "geom_comp_point_nnir", 0.022, 0.020),
    ("external step", "geom_ext_step_genplan", "geom_ext_step_nnir", 0.012, 0.006),
    ("external point", "geom_ext_point_genplan", "geom_ext_point_nnir", 0.004, 0.004),
]


def load(name: str) -> dict:
    f = SCRATCH / name / "geometry_nbest_rows.jsonl"
    if not f.is_file():
        return {}
    out = {}
    for line in f.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        c = [x for x in r.get("candidate_results", []) if x.get("cd") is not None]
        out[r["sample_id"]] = c[0] if c else None
    return out


def mann_whitney(a, b):
    merged = sorted([(v, 0) for v in a] + [(v, 1) for v in b])
    ranks = [0.0] * len(merged)
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


for label, ours_dir, nnir_dir, ours_cond, nnir_cond in PAIRS:
    O, N = load(ours_dir), load(nnir_dir)
    if not O or not N:
        print(f"{label}: missing rows ({ours_dir} / {nnir_dir})\n")
        continue
    built = [N[s]["f_score_1pct"] for s in O if O[s] and N.get(s)]
    failed = [N[s]["f_score_1pct"] for s in O if not O[s] and N.get(s)]
    if not built or not failed:
        print(f"{label}: one subset is empty\n")
        continue
    mb, mf = statistics.median(built), statistics.median(failed)
    z, p = mann_whitney(built, failed)
    bias, effect = mb - mf, ours_cond - nnir_cond
    print(label)
    print(f"  retrieval F@1% where the generated arm BUILT   n={len(built):<5} median {mb:.4f}")
    print(f"  retrieval F@1% where the generated arm FAILED  n={len(failed):<5} median {mf:.4f}")
    print(f"  difference (how much easier the subset is)     {bias:+.4f}   "
          f"Mann-Whitney z={z:.2f}, p={p:.3g}")
    print(f"  the advantage it would have to explain         {effect:+.4f}")
    if abs(bias) < 1e-9:
        v = "no measurable selection effect"
    elif effect <= 0:
        v = "no advantage to explain on this arm"
    elif abs(bias) < 0.25 * abs(effect):
        v = (f"bounded at {abs(bias) / abs(effect):.0%} of the advantage -- the advantage survives")
    else:
        v = "a substantial fraction of the advantage -- do not claim it without this"
    print(f"  -> {v}\n")
