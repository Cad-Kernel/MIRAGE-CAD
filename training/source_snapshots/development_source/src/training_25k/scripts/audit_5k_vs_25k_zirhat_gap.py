"""Audit (docs/MIRAGE-CAD_experiment_results.md SS8, follow-up to SS8.2's
point/text regression): does the paired z_ir_hat gap between STEP and
point/text widen from the 5K-scale checkpoints to the 25K-scale checkpoints?

Hypothesis under test: LoRA-IR is trained on STEP's prior output only, both
at 5K and 25K, by design (see 06_train_lora_ir.sh). More 25K training data/
steps may have sharpened LoRA-IR's fit specifically to STEP's z_ir_hat
manifold, leaving point/text's z_ir_hat (produced by their OWN, different
priors) further out-of-distribution than at 5K scale -- which would help
explain why STEP improved and point/text regressed when scaling 5K->25K
(SS8.2's confirmed paired regression).

Metric: for the 500 sample_ids shared between the 5K and 25K test sets
(confirmed 100% overlap, SS8.8 Check A), encode z_m -> z_ir_hat for STEP and
for {point, text} using the SAME scale's own aligner+prior checkpoints, then
compute per-sample cosine(z_ir_hat_step, z_ir_hat_other) and average. Compare
this average between the 5K checkpoints and the 25K checkpoints.

A meaningfully LOWER 25K number supports the hypothesis (LoRA-IR's STEP-only
training became a worse fit for point/text at scale). A similar or higher
number does NOT support it -- look elsewhere (e.g. Stage 2 prior quality
itself, or Stage 3 IR-quality per SS8.4) before committing to a Stage 3b
mixed-prefix retrain.

UPDATE (2026-07-23): the STEP-relative check above came back POSITIVE
(point/text's z_ir_hat got MORE aligned with STEP's at 25K, not less),
rejecting the original hypothesis. Second check added here: does each
modality's z_ir_hat's absolute accuracy -- cosine similarity to the TRUE
reference-IR embedding (aligner.encode_ir(reference_ir_text), no modality
encoder or STEP comparison involved at all) -- regress from 5K to 25K for
point/text specifically? This isolates whether Stage 2's own prior quality
(z_m -> z_ir_hat accuracy) got worse at 25K, independent of any STEP
comparison, complementing the first (STEP-relative) check above.

No LoRA-IR/LoRA-Code involved, no training -- only Stage 1 (alignment) +
Stage 2 (prior) forward passes, run twice (5K checkpoints, 25K checkpoints).
"""
import argparse
import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, ".")
from miragecad.data import (
    collate_step_brep_batch,
    load_image,
    load_step_brep_tensors,
    read_jsonl,
    read_text,
)
from miragecad.latent_prior import LatentPrior, LatentPriorConfig
from miragecad.models import load_alignment_checkpoint
from miragecad.point_sampling import load_point_cloud_sampled


def encode_query(aligner, modality, row, device, point_count=1024, seed=42):
    if modality == "text":
        return aligner.encode_text([row.get("text", "")], device)
    if modality == "image":
        return aligner.encode_image([load_image(row["iso_image_path"])], device)
    if modality == "point":
        pts = load_point_cloud_sampled(row["point_path"], point_count=point_count, sampling="fps", seed=seed)
        return aligner.encode_point(torch.tensor(pts[None], dtype=torch.float32).to(device))
    if modality == "step":
        tensors = load_step_brep_tensors(row["step_feature_path"], strict=True)
        batch = collate_step_brep_batch([tensors])
        return aligner.encode_step({k: v.to(device) for k, v in batch.items()})
    raise ValueError(f"Unknown modality: {modality!r}")


def load_prior(path, device):
    payload = torch.load(path, map_location="cpu", weights_only=False)
    prior = LatentPrior(LatentPriorConfig(**payload["config"]))
    prior.load_state_dict(payload["state_dict"], strict=True)
    return prior.to(device).eval()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--shared-ids-jsonl", type=Path, default=Path("data/smoke5k/test.jsonl"),
                     help="jsonl whose sample_ids define the shared subset to audit (the 5K test set).")
    ap.add_argument("--rows-jsonl", type=Path, default=Path("data/25k/test.jsonl"),
                     help="jsonl to pull full row data from (25K test set is a confirmed superset).")
    ap.add_argument("--limit", type=int, default=None, help="Default: use all 500 shared samples.")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    shared_ids = [json.loads(l)["sample_id"] for l in open(args.shared_ids_jsonl, encoding="utf-8")]
    if args.limit:
        shared_ids = shared_ids[: args.limit]
    shared_set = set(shared_ids)
    rows_by_id = {r["sample_id"]: r for r in read_jsonl(args.rows_jsonl) if r["sample_id"] in shared_set}
    rows = [rows_by_id[sid] for sid in shared_ids if sid in rows_by_id]
    print(f"Auditing {len(rows)} shared sample_ids (requested {len(shared_ids)}).")

    scales = {
        "5K": dict(align="outputs/align_smoke5k_ep10/best.pt",
                   priors={"step": "outputs/prior_step_5k/best.pt",
                           "point": "outputs/prior_point_5k/best.pt",
                           "text": "outputs/prior_text_5k/best.pt"}),
        "25K": dict(align="outputs/align_25k/best.pt",
                    priors={"step": "outputs/prior_step_25k/best.pt",
                            "point": "outputs/prior_point_25k/best.pt",
                            "text": "outputs/prior_text_25k/best.pt"}),
    }

    results = {}
    for scale_name, cfg in scales.items():
        print(f"=== loading {scale_name} checkpoints ===", flush=True)
        aligner, _, _, _ = load_alignment_checkpoint(Path(cfg["align"]), map_location="cpu")
        aligner.to(device).eval()
        priors = {m: load_prior(Path(p), device) for m, p in cfg["priors"].items()}

        z_ir_hat = {m: [] for m in priors}
        z_ir_true = []
        with torch.no_grad():
            for i, row in enumerate(rows):
                for m in priors:
                    z_m = encode_query(aligner, m, row, device, seed=args.seed)
                    z_hat = priors[m](z_m)
                    z_ir_hat[m].append(z_hat.squeeze(0).cpu())
                ir_text = read_text(row.get("ir_path", ""))
                z_true = aligner.encode_ir([ir_text], device)
                z_ir_true.append(z_true.squeeze(0).cpu())
                if (i + 1) % 100 == 0:
                    print(f"  {i+1}/{len(rows)} encoded", flush=True)

        for m in priors:
            z_ir_hat[m] = torch.stack(z_ir_hat[m])
        z_ir_true = torch.stack(z_ir_true)

        pair_cos = {}
        for m in ["point", "text"]:
            cos = torch.nn.functional.cosine_similarity(z_ir_hat["step"], z_ir_hat[m], dim=-1)
            pair_cos[m] = (cos.mean().item(), cos.std().item())

        truth_cos = {}
        for m in ["step", "point", "text"]:
            cos = torch.nn.functional.cosine_similarity(z_ir_hat[m], z_ir_true, dim=-1)
            truth_cos[m] = (cos.mean().item(), cos.std().item())

        results[scale_name] = dict(pair_cos=pair_cos, truth_cos=truth_cos)
        print(f"{scale_name} (vs STEP): " + ", ".join(f"step-vs-{m} mean_cos={v[0]:.4f} (std={v[1]:.4f})" for m, v in pair_cos.items()))
        print(f"{scale_name} (vs TRUE reference-IR embedding): " + ", ".join(f"{m} mean_cos={v[0]:.4f} (std={v[1]:.4f})" for m, v in truth_cos.items()))

        del aligner, priors
        if device.type == "cuda":
            torch.cuda.empty_cache()

    print()
    print("=== Check 1: paired z_ir_hat cosine similarity to STEP (same shared samples) ===")
    print(f"{'modality':<10}{'5K mean':>12}{'25K mean':>12}{'delta':>10}")
    for m in ["point", "text"]:
        v5 = results["5K"]["pair_cos"][m][0]
        v25 = results["25K"]["pair_cos"][m][0]
        print(f"{m:<10}{v5:>12.4f}{v25:>12.4f}{v25-v5:>10.4f}")
    print("(already run 2026-07-22: came back positive for both -- rejects the 'LoRA-IR overfit to STEP' hypothesis)")

    print()
    print("=== Check 2 (NEW): z_ir_hat cosine similarity to the TRUE reference-IR embedding (no STEP involved) ===")
    print(f"{'modality':<10}{'5K mean':>12}{'25K mean':>12}{'delta':>10}")
    for m in ["step", "point", "text"]:
        v5 = results["5K"]["truth_cos"][m][0]
        v25 = results["25K"]["truth_cos"][m][0]
        print(f"{m:<10}{v5:>12.4f}{v25:>12.4f}{v25-v5:>10.4f}")
    print()
    print("Interpretation of Check 2: this measures each modality's OWN prior accuracy (does z_ir_hat actually predict")
    print("the true construction's IR embedding), independent of STEP. If point/text's delta here is clearly negative")
    print("(25K worse than 5K) while STEP's is flat/positive, that points at Stage 2 (prior) quality regressing for")
    print("point/text specifically at 25K scale -- a different, more direct culprit than the Check-1 hypothesis,")
    print("and would argue for re-examining Stage 2 prior training (data mix, epochs, rare-op sampling) rather than")
    print("Stage 3b LoRA-IR retraining, since Stage 3b would not fix a Stage-2-level accuracy problem.")


if __name__ == "__main__":
    main()
