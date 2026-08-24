"""Build the Stage 4c-mini continued-training set: a much gentler version of
the failed Stage 4c experiment (see docs/Todo.md "P2 / Stage 4c results" and
docs/MIRAGE-CAD_debug_report.md 8.5 for the failure this is reacting to).

Key differences from the failed Stage 4c run:
  - Target-op share of the corpus is configurable and defaults to 10%
    (was an implicit 50% before, via 3x duplication + equal-sized general
    sample -- that ratio jump from the natural 7.14% is what's suspected to
    have caused the catastrophic forgetting).
  - No duplication of target rows by default (oversample_factor=1): all 357
    unique face-feature GT-IR rows are used at most once, so the model sees
    diverse examples instead of a small set repeated verbatim. Duplication
    is still supported via --oversample-factor if a future run wants it,
    but the default avoids it.
  - Pure GT-IR only. A predicted_ir-mixing arm was considered (as in Stage
    4b) but rejected for -this- experiment: only 8 grammar-valid rare-op
    predicted_ir training rows exist (checked empirically against
    outputs/qwen25_coder_1_5b_program_5k/predicted_ir_train_subset.jsonl),
    far too few to reach a meaningful 5% share without harmful duplication
    of the same 8 rows. Isolating "more GT-IR exposure to this op family"
    as the only new variable also matches the project's one-variable-at-
    a-time methodology.

Usage:
  python scratch/build_stage4c_mini_train.py --target-ratio 0.10 --oversample-factor 1
"""
import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, ".")
from miragecad.data import read_jsonl, read_text
from miragecad.gen_prompts import OP_TOKEN_PATTERN

TARGET_OPS = {"OP_SKETCH_ON_FACE", "OP_FACE_EXTRUDE_ADD", "OP_FACE_EXTRUDE_CUT"}
SEED = 42


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-jsonl", type=Path, default=Path("data/smoke5k/train.jsonl"))
    ap.add_argument("--target-ratio", type=float, default=0.10, help="target family's share of the final corpus")
    ap.add_argument("--oversample-factor", type=int, default=1, help="how many times to repeat each target row (1 = no duplication)")
    ap.add_argument("--out", type=Path, default=Path("data/smoke5k/train_stage4c_mini.jsonl"))
    args = ap.parse_args()

    rows = list(read_jsonl(args.train_jsonl))
    target_rows, general_rows = [], []
    for row in rows:
        ir = read_text(Path(row["ir_path"]))
        ops = set(OP_TOKEN_PATTERN.findall(ir.upper()))
        (target_rows if ops & TARGET_OPS else general_rows).append(row)

    print(f"total train rows: {len(rows)}, target (face-feature) rows: {len(target_rows)}, general rows: {len(general_rows)}")

    oversampled_target = target_rows * args.oversample_factor
    n_target = len(oversampled_target)
    # total corpus size implied by wanting n_target to be exactly target_ratio of the total
    total = round(n_target / args.target_ratio)
    n_general = total - n_target
    if n_general > len(general_rows):
        raise SystemExit(
            f"not enough general rows ({len(general_rows)}) to hit target-ratio={args.target_ratio} "
            f"with {n_target} target rows (would need {n_general}); lower --target-ratio or raise --oversample-factor"
        )

    rng = random.Random(SEED)
    general_sample = rng.sample(general_rows, n_general)

    out_rows = oversampled_target + general_sample
    rng.shuffle(out_rows)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        for row in out_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"target rows in corpus: {n_target} (oversample_factor={args.oversample_factor}, unique={len(target_rows)})")
    print(f"general rows in corpus: {n_general}")
    print(f"total corpus size: {len(out_rows)}")
    print(f"actual target ratio: {n_target/len(out_rows):.1%}")
    print("wrote", args.out)


if __name__ == "__main__":
    main()
