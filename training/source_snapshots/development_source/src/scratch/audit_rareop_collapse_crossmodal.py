"""Cross-modality rare-op latent collapse audit.

Replicates the STEP-only audit_stage3_latent_collapse_rareop.py methodology
(pairwise cosine of z_m/z_ir_hat on the OP_SWEEP_TUBE/OP_CIRCULAR_PATTERN
subset vs. a random contrast group) for point/text/image, to determine whether
the representation-collapse diagnosis is STEP-encoder-specific or shared
across modalities -- directly informs the Stage 3 rare-op A/B/C decision.
"""
import argparse
import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, ".")
from miragecad.data import read_jsonl, read_text, load_image
from miragecad.gen_prompts import extract_operation_types
from miragecad.latent_prior import LatentPrior, LatentPriorConfig
from miragecad.models import load_alignment_checkpoint
from miragecad.point_sampling import load_point_cloud_sampled


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--modality", choices=["text", "image", "point"], required=True)
    p.add_argument("--prior-checkpoint", type=Path, required=True)
    p.add_argument("--alignment-checkpoint", type=Path, default=Path("outputs/align_smoke5k_ep10/best.pt"))
    p.add_argument("--input-jsonl", type=Path, default=Path("data/smoke5k/test.jsonl"))
    p.add_argument("--point-count", type=int, default=1024)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def pairwise_cos(z):
    zn = z / z.norm(dim=-1, keepdim=True)
    sim = zn @ zn.T
    n = sim.shape[0]
    mask = ~torch.eye(n, dtype=torch.bool, device=sim.device)
    return sim[mask].mean().item(), sim[mask].std().item()


def encode_batch(rows, modality, aligner, prior, args, device):
    if modality == "text":
        z_m = aligner.encode_text([r.get("text", "") for r in rows], device)
    elif modality == "image":
        z_m = aligner.encode_image([load_image(r["iso_image_path"]) for r in rows], device)
    elif modality == "point":
        pts = torch.stack([
            torch.tensor(load_point_cloud_sampled(r["point_path"], point_count=args.point_count, sampling="fps", seed=args.seed))
            for r in rows
        ]).float().to(device)
        z_m = aligner.encode_point(pts)
    with torch.no_grad():
        z_hat = prior(z_m)
    return z_m, z_hat


def main():
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    aligner, _, _, _ = load_alignment_checkpoint(args.alignment_checkpoint, map_location="cpu")
    aligner.to(device).eval()

    payload = torch.load(args.prior_checkpoint, map_location="cpu", weights_only=False)
    prior = LatentPrior(LatentPriorConfig(**payload["config"])).to(device).eval()
    prior.load_state_dict(payload["state_dict"], strict=True)

    rows = read_jsonl(args.input_jsonl)
    sweep_rows, circ_rows, other_rows = [], [], []
    for r in rows:
        ref_ir = read_text(r.get("ir_path", ""))
        ops = set(extract_operation_types(ref_ir))
        if "OP_SWEEP_TUBE" in ops:
            sweep_rows.append(r)
        elif "OP_CIRCULAR_PATTERN" in ops:
            circ_rows.append(r)
        else:
            other_rows.append(r)

    import random
    random.seed(args.seed)
    contrast_rows = random.sample(other_rows, min(20, len(other_rows)))

    results = {"modality": args.modality, "n_sweep": len(sweep_rows), "n_circ": len(circ_rows)}
    for name, group in [("sweep_tube", sweep_rows), ("circular_pattern", circ_rows), ("contrast", contrast_rows)]:
        if not group:
            continue
        z_m, z_hat = encode_batch(group, args.modality, aligner, prior, args, device)
        zm_mean, zm_std = pairwise_cos(z_m)
        zh_mean, zh_std = pairwise_cos(z_hat)
        results[name] = {"n": len(group), "z_m_cos_mean": zm_mean, "z_m_cos_std": zm_std,
                          "z_hat_cos_mean": zh_mean, "z_hat_cos_std": zh_std}

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
