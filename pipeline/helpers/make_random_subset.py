"""Draw a reproducible random subset of a JSONL file.

Why this exists: every 100-sample table in the paper was produced with
`--limit 100`, which takes the *first* hundred rows. Those slices run roughly ten
points optimistic against the full 2,500-row test set, which is a systematic offset
rather than sampling noise (review item B5). Re-running against a seeded random
subset removes it.

The subset is written in the sampled order, and the chosen sample_ids are also
written to a sidecar `.ids.txt` so the identical subset can be reconstructed for any
other modality or variant. Pass `--ids-from` to reuse a previous selection, which is
what makes the point-cloud and STEP runs comparable to each other and lets the
NN-IR baselines be scored on exactly the same parts.

Usage:
    python training_25k/scripts/make_random_subset.py \
        --input  outputs/lora_ir_25k_stage3b/predicted_ir_test_step_p1a.jsonl \
        --output outputs/geometry_nbest_random100/ir_step.jsonl \
        --n 100 --seed 20260804
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--n", type=int, default=100)
    p.add_argument("--seed", type=int, default=20260804)
    p.add_argument("--ids-from", type=Path, default=None,
                   help="reuse the sample_ids listed in this file instead of drawing new ones")
    args = p.parse_args()

    rows = read_jsonl(args.input)
    by_id = {r["sample_id"]: r for r in rows}
    print(f"input: {len(rows)} rows ({len(by_id)} distinct sample_ids)")

    if args.ids_from:
        wanted = [ln.strip() for ln in open(args.ids_from, encoding="utf-8") if ln.strip()]
        chosen = [by_id[i] for i in wanted if i in by_id]
        missing = [i for i in wanted if i not in by_id]
        print(f"reusing {len(wanted)} ids from {args.ids_from}: "
              f"{len(chosen)} present, {len(missing)} missing")
        if missing:
            print("  missing:", ", ".join(missing[:10]) + (" ..." if len(missing) > 10 else ""))
    else:
        if args.n > len(rows):
            print(f"warning: n={args.n} exceeds available {len(rows)}; using all")
        rng = random.Random(args.seed)
        chosen = rng.sample(rows, min(args.n, len(rows)))
        print(f"drew {len(chosen)} rows with seed {args.seed}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8", newline="\n") as fh:
        for r in chosen:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    ids_path = args.output.with_suffix(args.output.suffix + ".ids.txt")
    with open(ids_path, "w", encoding="utf-8", newline="\n") as fh:
        for r in chosen:
            fh.write(r["sample_id"] + "\n")

    print(f"wrote {args.output}")
    print(f"wrote {ids_path}  <- pass this as --ids-from to match this subset elsewhere")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
