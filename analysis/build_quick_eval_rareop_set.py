"""Build a fixed ~120-sample quick-eval subset of the 500-test set, so future
continued-fine-tune experiments (e.g. Stage 4c-mini) can be screened in
minutes instead of committing to a full 500-sample generate+repair+execute
cycle (~2-3 hours) before knowing if a config is even promising.

Composition:
  - ALL samples referencing the Stage 4c-mini fine-tuning target family
    (OP_SKETCH_ON_FACE / OP_FACE_EXTRUDE_ADD / OP_FACE_EXTRUDE_CUT) -- this is
    the group we're actually trying to improve.
  - A capped random subsample of samples referencing the OTHER rare ops
    (OP_SWEEP_TUBE / OP_CIRCULAR_PATTERN / OP_PROFILE_CUT) -- these are NOT
    fine-tune targets (Stage 3 generative collapse or already fixed by P0),
    included as regression canaries: Stage 4c-mini should not make these
    worse, even though it can't be expected to fix OP_SWEEP_TUBE/
    OP_CIRCULAR_PATTERN.
  - A fixed random sample of "normal" (no rare op) samples -- this is what
    actually matters for the "did we cause collateral damage" question.

Per-sample metadata recorded (used for pass/fail screening later):
  - rare_op_types: list of matched rare ops (empty for normal samples)
  - is_target_family: True if it's in the fine-tune target group
  - is_ir_valid: from validate_ir_grammar() on the P1a-repaired predicted_ir
  - baseline_success / baseline_error: from the current frozen best
    (Stage4b + repair + P0 + P1a) execution run, so every future experiment
    diffs against the same reference point.
"""
import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, ".")
from miragecad.data import read_jsonl
from miragecad.gen_prompts import OP_TOKEN_PATTERN, validate_ir_grammar

TARGET_FAMILY = {"OP_SKETCH_ON_FACE", "OP_FACE_EXTRUDE_ADD", "OP_FACE_EXTRUDE_CUT"}
OTHER_RARE = {"OP_SWEEP_TUBE", "OP_CIRCULAR_PATTERN", "OP_PROFILE_CUT"}
ALL_RARE = TARGET_FAMILY | OTHER_RARE

N_OTHER_RARE_CAP = 15
N_NORMAL = 80
SEED = 42


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--predicted-ir", type=Path, default=Path("outputs/lora_ir_5k/predicted_ir_test500_full_p1a.jsonl"))
    ap.add_argument("--baseline-exec-rows", type=Path,
                     default=Path("/mnt/c/Workspace/Project/Paper/MIRAGE-V2/scratch/exec_eval_stage4b_test500_p1a/execution_rows.jsonl"))
    ap.add_argument("--out", type=Path, default=Path("data/smoke5k/quick_eval_rareop_set.jsonl"))
    args = ap.parse_args()

    pred_rows = {r["sample_id"]: r for r in read_jsonl(args.predicted_ir)}
    baseline = {}
    for l in open(args.baseline_exec_rows, encoding="utf-8"):
        if not l.strip():
            continue
        row = json.loads(l)
        baseline[row["sample_id"]] = row

    target_ids, other_rare_ids, normal_ids = [], [], []
    tags = {}
    for sid, r in pred_rows.items():
        ref_ir = r.get("reference_ir", "")
        ops = set(OP_TOKEN_PATTERN.findall(ref_ir.upper()))
        matched = sorted(ops & ALL_RARE)
        tags[sid] = matched
        if ops & TARGET_FAMILY:
            target_ids.append(sid)
        elif ops & OTHER_RARE:
            other_rare_ids.append(sid)
        else:
            normal_ids.append(sid)

    rng = random.Random(SEED)
    other_rare_sample = rng.sample(other_rare_ids, min(N_OTHER_RARE_CAP, len(other_rare_ids)))
    normal_sample = rng.sample(normal_ids, min(N_NORMAL, len(normal_ids)))

    selected = target_ids + other_rare_sample + normal_sample
    print(f"target family (all): {len(target_ids)}")
    print(f"other rare (sampled): {len(other_rare_sample)} of {len(other_rare_ids)} available")
    print(f"normal (sampled): {len(normal_sample)} of {len(normal_ids)} available")
    print(f"total quick-eval set size: {len(selected)}")

    out_rows = []
    n_valid = n_invalid = n_base_ok = n_base_fail = 0
    for sid in selected:
        r = pred_rows[sid]
        is_valid = validate_ir_grammar(r["predicted_ir"])["valid"]
        b = baseline.get(sid, {})
        base_ok = bool(b.get("exec_ok"))
        n_valid += is_valid
        n_invalid += not is_valid
        n_base_ok += base_ok
        n_base_fail += not base_ok
        out_rows.append({
            "sample_id": sid,
            "rare_op_types": tags[sid],
            "is_target_family": sid in target_ids,
            "is_ir_valid": is_valid,
            "baseline_success": base_ok,
            "baseline_error": b.get("error", ""),
        })

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        for row in out_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print()
    print(f"IR-valid: {n_valid}, IR-invalid: {n_invalid}")
    print(f"baseline (Stage4b+P0+P1a) success: {n_base_ok}/{len(selected)} = {n_base_ok/len(selected):.1%}")
    n_target_base_ok = sum(1 for r in out_rows if r["is_target_family"] and r["baseline_success"])
    print(f"baseline success within target family: {n_target_base_ok}/{len(target_ids)}")
    print("wrote", args.out)


if __name__ == "__main__":
    main()
