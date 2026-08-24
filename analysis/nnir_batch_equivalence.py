"""Does batching change what the NN-IR baseline generates?

It matters for two reasons at once. The external NN-IR arm takes 25 seconds a row
unbatched -- 2.8 hours per arm, 5.6 for both -- while the generated-plan arms already run at
--batch-size 16. And the published internal NN-IR numbers were produced unbatched, so if
batching moved the outputs, the external figure could not be set beside the internal one.

Greedy decoding should be batch-invariant in exact arithmetic. It is not guaranteed in
floating point: left-padding changes the numerics enough to flip an occasional token. So
this is an empirical question, and the failed first attempt at arm B happens to have left
exactly the artifact needed to answer it -- 20 rows generated one at a time, preserved as
_batchcheck_b1.jsonl because the runner overwrites gen_step_nnir.jsonl.

Run the same 20 rows batched, then compare:

    # WSL, ~1 minute
    python scratch/gen_nn_ir_baseline.py \\
      --modality step --retrieval-mode prior \\
      --alignment-checkpoint outputs/align_25k/best.pt \\
      --prior-checkpoint outputs/prior_step_25k/best.pt \\
      --retrieval-index outputs/align_25k/train_ir_index.npz \\
      --lora-code-dir outputs/qwen25_coder_1_5b_program_25k_stage4b \\
      --input-jsonl data/external/fusion360/rows.jsonl \\
      --output-jsonl outputs/external_fusion360/_batchcheck_b16.jsonl \\
      --limit 20 --batch-size 16 --max-length 1536 --max-new-tokens 1536

    python scratch/nnir_batch_equivalence.py

Identical means take the sixteenfold speedup and set the external number beside the
internal one without qualification. Nearly identical means take the speedup and say so.
Substantially different means run unbatched and pay the 5.6 hours.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

CANDIDATES = [
    Path("outputs/external_fusion360"),
    Path("/home/jizong/workspace/MIRAGE/src/outputs/external_fusion360"),
    Path(r"\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\outputs\external_fusion360"),
]


def load(p: Path) -> dict[str, dict]:
    return {r["sample_id"]: r
            for r in (json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip())}


def main() -> int:
    root = next((c for c in CANDIDATES if (c / "gen_step_nnir.jsonl").is_file()), None)
    if root is None:
        print("gen_step_nnir.jsonl not found in any of:")
        for c in CANDIDATES:
            print(f"  {c}")
        return 1
    b1_path, b16_path = root / "_batchcheck_b1.jsonl", root / "_batchcheck_b16.jsonl"
    if not b16_path.is_file():
        print(f"{b16_path} not found -- run the batched generation first (see this file's docstring)")
        return 1

    b1, b16 = load(b1_path), load(b16_path)
    shared = sorted(set(b1) & set(b16))
    print(f"unbatched {len(b1)} rows, batched {len(b16)} rows, {len(shared)} in common")
    if not shared:
        return 1

    same_pred = same_ir = 0
    diffs = []
    for sid in shared:
        p1 = (b1[sid].get("prediction") or "").strip()
        p2 = (b16[sid].get("prediction") or "").strip()
        i1 = (b1[sid].get("predicted_ir") or b1[sid].get("retrieved_ir") or "").strip()
        i2 = (b16[sid].get("predicted_ir") or b16[sid].get("retrieved_ir") or "").strip()
        same_ir += (i1 == i2)
        if p1 == p2:
            same_pred += 1
        else:
            diffs.append((sid, p1, p2))

    n = len(shared)
    print(f"  retrieved plan identical : {same_ir}/{n}")
    print(f"  generated program identical: {same_pred}/{n}")
    if diffs:
        print("\n  first difference:")
        sid, p1, p2 = diffs[0]
        print(f"    {sid}")
        for a, b in zip(p1.splitlines(), p2.splitlines()):
            if a != b:
                print(f"      unbatched: {a[:100]}")
                print(f"      batched  : {b[:100]}")
                break
        else:
            print(f"      lengths differ: {len(p1)} vs {len(p2)} chars")

    print()
    if same_pred == n:
        print("  ==> Batching changes nothing here. Take the sixteenfold speedup, and the")
        print("      external number sits beside the published internal one unqualified.")
    elif same_pred >= 0.9 * n:
        print(f"  ==> {n - same_pred} of {n} differ. Padding numerics, as expected. Take the")
        print("      speedup and state the batch size beside the external result; do not")
        print("      claim byte-identical decoding against the unbatched internal run.")
    else:
        print(f"  ==> {n - same_pred} of {n} differ, which is too many to wave through.")
        print("      Run the external NN-IR arms unbatched and pay the 5.6 hours, or find")
        print("      out what padding is doing before trusting either number.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
