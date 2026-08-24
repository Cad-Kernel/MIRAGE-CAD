"""Stage 1 decision-gate check (STEP modality): does the rare-op latent
collapse found at 5K scale (docs/MIRAGE-CAD_experiment_results.md SS4.5) persist
at 25K? CLI-parameterized generalization of
scratch/audit_stage3_latent_collapse_rareop.py (which had every path
hardcoded to 5K literals). Computes pairwise cosine similarity of z_m (STEP
encoder output) and z_ir_hat (prior output) within OP_SWEEP_TUBE /
OP_CIRCULAR_PATTERN groups vs. a random 'normal' contrast group -- collapse
looks like op-group cosine >> contrast-group cosine (5K numbers: sweep=0.90/
0.876, circular=0.80/0.94, contrast=~0.01/0.00).

Run this AFTER Stage 2 (needs a trained step-modality prior) and a predicted_ir
file with reference_ir populated for the same test split (any predicted_ir
run works -- reference_ir, not predicted_ir, is what's used for grouping).
"""
import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, ".")
from miragecad.data import read_jsonl, load_step_brep_tensors
from miragecad.gen_prompts import OP_TOKEN_PATTERN
from miragecad.models import load_alignment_checkpoint
from gen_scripts.run_miragecad import load_prior, encode_query

TARGET_OPS = ["OP_SWEEP_TUBE", "OP_CIRCULAR_PATTERN"]


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--alignment-checkpoint", type=Path, required=True)
    p.add_argument("--prior-checkpoint", type=Path, required=True)
    p.add_argument("--test-jsonl", type=Path, required=True)
    p.add_argument("--predicted-ir-jsonl", type=Path, required=True,
                    help="Any predicted_ir run over --test-jsonl; only reference_ir is used, "
                         "to identify which samples contain the rare ops.")
    p.add_argument("--output-json", type=Path, default=None)
    p.add_argument("--n-contrast", type=int, default=20)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def mean_pairwise_cos(mat: np.ndarray):
    n = mat.shape[0]
    if n < 2:
        return None
    normed = mat / (np.linalg.norm(mat, axis=1, keepdims=True) + 1e-8)
    sim = normed @ normed.T
    return float(sim[np.triu_indices(n, k=1)].mean())


def main():
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    aligner, _, _, _ = load_alignment_checkpoint(args.alignment_checkpoint, map_location="cpu")
    aligner = aligner.to(device).eval()
    prior = load_prior(args.prior_checkpoint, device)

    test_rows = {r["sample_id"]: r for r in read_jsonl(args.test_jsonl)}
    pred_rows = {r["sample_id"]: r for r in read_jsonl(args.predicted_ir_jsonl)}

    groups = {op: [] for op in TARGET_OPS}
    normal_ids = []
    for sid, r in pred_rows.items():
        ref_ir = r.get("reference_ir", "")
        if not ref_ir:
            continue
        ops = set(OP_TOKEN_PATTERN.findall(ref_ir.upper()))
        matched = [op for op in TARGET_OPS if op in ops]
        if matched:
            for op in matched:
                groups[op].append(sid)
        else:
            normal_ids.append(sid)

    rng = random.Random(args.seed)
    normal_sample = rng.sample(normal_ids, min(args.n_contrast, len(normal_ids)))

    eval_args = argparse.Namespace(point_count=1024, eval_point_sampling="fps", seed=args.seed)

    def encode_all(sample_ids):
        z_ms, z_irs, globals_ = [], [], []
        for sid in sample_ids:
            row = test_rows[sid]
            z_m, z_ir_hat = encode_query(row, "step", aligner, prior, eval_args, device)
            z_ms.append(z_m)
            z_irs.append(z_ir_hat)
            tensors = load_step_brep_tensors(row["step_feature_path"], strict=True)
            globals_.append(tensors["global"])
        return np.stack(z_ms), np.stack(z_irs), np.stack(globals_)

    results = {}
    print(f"Encoding normal contrast group (n={len(normal_sample)})...")
    n_zm, n_zir, n_glob = encode_all(normal_sample)
    results["contrast"] = {
        "n": len(normal_sample),
        "z_m_cos": mean_pairwise_cos(n_zm),
        "z_ir_hat_cos": mean_pairwise_cos(n_zir),
        "global_feat_cos": mean_pairwise_cos(n_glob),
    }
    print(json.dumps(results["contrast"], indent=2))

    for op in TARGET_OPS:
        ids = groups[op]
        zm, zir, glob = encode_all(ids)
        results[op] = {
            "n": len(ids),
            "z_m_cos": mean_pairwise_cos(zm),
            "z_ir_hat_cos": mean_pairwise_cos(zir),
            "global_feat_cos": mean_pairwise_cos(glob),
        }
        print(f"=== {op} (n={len(ids)}) ===")
        print(json.dumps(results[op], indent=2))

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print("Wrote", args.output_json)


if __name__ == "__main__":
    main()
