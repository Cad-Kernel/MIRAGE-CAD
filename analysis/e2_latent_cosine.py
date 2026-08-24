"""E2 step 1: the one diagnostic that was never stored -- cos(z_ir_hat, z_ir).

WHY THIS EXISTS. E2 asks whether the explicit plan is a more informative diagnostic of downstream
failure than the continuous latent already is. That needs the latent's own diagnostic, and it does
not exist in any output file. What `outputs/tab_ir_quality_step_C.json` stores as `ir_cosine` is
cos(E_ir(predicted plan text), E_ir(reference plan text)) -- see gen_scripts/evaluate_ir_quality.py,
which encodes both plan texts and never touches the prior. It is a plan-level metric, and using it
as the latent baseline would compare the plan against itself.

WHAT THIS COMPUTES. For each of the 500 STEP rows the B2-Pred arm was evaluated on:

    z_m       = aligner.encode_step(step features)        the observation embedding
    z_ir_hat  = prior(z_m)                                the predicted construction latent
    z_ir      = aligner.encode_ir(read_text(ir_path))     the encoded reference plan
    lat_cos   = cos(z_ir_hat, z_ir)

The target is the RAW IR file text, because that is exactly what the prior was trained against
(train_latent_prior.py:68). It is deliberately not normalize_ir_text(...): that normalisation
belongs to the plan-text metric, and scoring the prior against a target it never saw would
understate it. Both vectors are L2 normalised onto the unit sphere, which the script asserts rather
than assumes, and the final mean is checked against the prior's own training-time cosine so a
wrong target fails loudly instead of passing as a weak prior.

Use `data/25k/test.jsonl` as --rows-jsonl. `data/25k/step_features_test.jsonl` carries the same
rows but stores Windows paths (C:\\tmp\\...) that WSL cannot open.

READ-ONLY. No checkpoint is written, no model is trained, nothing under outputs/ is modified. One
forward pass per row.

RUN (WSL, ai_dev):

    cd ~/workspace/MIRAGE/src
    PYTHONPATH=. python scratch/e2_latent_cosine.py \
        --alignment-checkpoint outputs/align_25k/best.pt \
        --prior-checkpoint outputs/prior_step_25k/best.pt \
        --rows-jsonl data/25k/test.jsonl \
        --arm-jsonl outputs/e1_observation_bypass/gen_code_step_B2P.jsonl \
        --out /mnt/c/Workspace/Project/Paper/MIRAGE-V2/scratch/e2_latent_cosine.jsonl
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from miragecad.data import load_step_brep_tensors, read_jsonl, read_text
from miragecad.latent_prior import LatentPrior, LatentPriorConfig
from miragecad.models import load_alignment_checkpoint

# The prior's own training log records the cosine LOSS, which is 1 - cos (latent_prior.py:87).
# prior_step_25k finished at 0.0455, so its mean cosine against the training target was ~0.955.
# A run here that lands far below that is measuring the wrong target, not a weak prior -- the
# first version of this script normalised the reference text and got a median of 0.008.
EXPECTED_MEAN_COS = 0.955
EXPECTED_TOLERANCE = 0.25


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--alignment-checkpoint", type=Path, required=True)
    p.add_argument("--prior-checkpoint", type=Path, required=True)
    p.add_argument("--rows-jsonl", type=Path, required=True,
                   help="Split file carrying step_feature_path per sample_id.")
    p.add_argument("--arm-jsonl", type=Path, required=True,
                   help="The arm's generation file; supplies sample order and reference_ir.")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--batch-size", type=int, default=16)
    return p.parse_args()


def load_prior(path: Path, device: torch.device) -> LatentPrior:
    """Load a prior checkpoint.

    The weights key is `state_dict`, matching generate_latent_prior.py and
    training_25k/scripts/audit_5k_vs_25k_zirhat_gap.py, which are the scripts that read the
    prior_*_25k checkpoints this analysis uses. gen_scripts/generate_predicted_ir.py reads a
    `model` key instead; both spellings are accepted here so a format difference is reported
    rather than raising a bare KeyError.
    """
    payload = torch.load(path, map_location="cpu", weights_only=False)
    cfg = payload["config"]
    if "modality" not in cfg:
        raise ValueError(f"Prior checkpoint {path} missing 'modality' in config.")
    weights = payload.get("state_dict", payload.get("model"))
    if weights is None:
        raise SystemExit(f"{path} has neither 'state_dict' nor 'model'; payload keys are "
                         f"{sorted(payload)}")
    prior = LatentPrior(LatentPriorConfig(**cfg))
    prior.load_state_dict(weights, strict=True)
    print(f"prior: {path.name}, modality {cfg['modality']}")
    return prior.to(device).eval()


@torch.no_grad()
def main() -> int:
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device: {device}")

    aligner, _, _, _ = load_alignment_checkpoint(args.alignment_checkpoint, map_location="cpu")
    aligner.to(device).eval()
    prior = load_prior(args.prior_checkpoint, device)

    arm = read_jsonl(args.arm_jsonl)
    feats = {r["sample_id"]: r for r in read_jsonl(args.rows_jsonl)}
    missing = [r["sample_id"] for r in arm if r["sample_id"] not in feats]
    if missing:
        raise SystemExit(f"{len(missing)} arm rows have no features row, first {missing[:3]}")
    print(f"{len(arm)} rows from {args.arm_jsonl.name}")

    out = []
    for i in range(0, len(arm), args.batch_size):
        chunk = arm[i: i + args.batch_size]

        # observation -> z_m -> z_ir_hat, one row at a time because the STEP loader is per-sample
        z_hats = []
        for row in chunk:
            # strict=True is load-bearing. The default returns all-zero descriptors when the
            # JSON cannot be read, and data/25k/step_features_test.jsonl stores Windows paths
            # (C:\tmp\...) that WSL cannot open -- so the first run of this script encoded 500
            # identical zero vectors and produced a near-zero cosine that looked like a weak
            # prior. Every training and generation script in this repo already passes strict=True,
            # which is why none of the paper's results could have come from zeros.
            tensors = load_step_brep_tensors(
                feats[row["sample_id"]]["step_feature_path"], strict=True)
            batch = {k: torch.tensor(v[None], dtype=torch.float32).to(device)
                     for k, v in tensors.items()}
            z_hats.append(prior(aligner.encode_step(batch)))
        z_ir_hat = torch.cat(z_hats, dim=0)

        # The target must be exactly what the prior was trained against, which is
        # train_latent_prior.py:68 -- read_text(row["ir_path"]), the RAW IR file text. It is
        # deliberately NOT normalize_ir_text(...): that normalisation belongs to the plan-text
        # metric, and applying it here would score the prior against a target it never saw.
        refs = [read_text(feats[r["sample_id"]]["ir_path"]) for r in chunk]
        if not all(refs):
            raise SystemExit(f"empty reference IR in batch starting at row {i}")
        z_ir = aligner.encode_ir(refs, device)

        # Both heads end in L2 normalisation, so a dot product is the cosine. Checked, not assumed:
        # a silent normalisation change upstream would otherwise turn cosines into inner products.
        for name, z in (("z_ir_hat", z_ir_hat), ("z_ir", z_ir)):
            norms = z.norm(dim=-1)
            if not torch.allclose(norms, torch.ones_like(norms), atol=1e-3):
                raise SystemExit(f"{name} is not unit-norm (min {norms.min():.4f}, "
                                 f"max {norms.max():.4f}); a dot product would not be a cosine")

        cos = torch.sum(z_ir_hat * z_ir, dim=-1).cpu().tolist()
        for row, c in zip(chunk, cos):
            out.append({"sample_id": row["sample_id"], "lat_cos": float(c)})
        print(f"  {len(out)}/{len(arm)}", flush=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")

    vals = sorted(r["lat_cos"] for r in out)
    n = len(vals)
    mean = sum(vals) / n
    print(f"\nwrote {n} rows to {args.out}")
    print(f"  lat_cos: min {vals[0]:.4f}  median {vals[n // 2]:.4f}  "
          f"mean {mean:.4f}  max {vals[-1]:.4f}")

    # Sanity, not a result: does this reproduce the prior's own training-time alignment?
    delta = abs(mean - EXPECTED_MEAN_COS)
    print(f"  prior's training-time mean cosine was ~{EXPECTED_MEAN_COS:.3f} "
          f"(1 - 0.0455); here {mean:.3f}, off by {delta:.3f}")
    if delta > EXPECTED_TOLERANCE:
        raise SystemExit(
            "\nSTOP. This is too far from the prior's own training-time cosine to be a weak\n"
            "prior; it is far more likely the wrong target. Check that the reference text is\n"
            "read_text(ir_path) -- the raw IR file -- and not a normalised or re-serialised\n"
            "version. A near-zero baseline here would make every plan diagnostic look strong\n"
            "for a reason that has nothing to do with the plan.")
    print("\nThis is a diagnostic input, not an E2 outcome. Run scratch/e2_analysis.py next.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
