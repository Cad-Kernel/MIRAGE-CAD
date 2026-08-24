"""Train MIRAGE-CAD modality-to-IR latent priors."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

from miragecad.data import collate_step_brep_batch, load_image, load_step_brep_tensors, read_jsonl, read_text
from miragecad.models import load_alignment_checkpoint
from miragecad.latent_prior import LatentPrior, LatentPriorConfig, prior_losses, retrieval_metrics
from miragecad.point_sampling import load_point_cloud_sampled


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train a MIRAGE-CAD latent prior.")
    p.add_argument("--alignment-checkpoint", type=Path, required=True)
    p.add_argument("--train-jsonl", type=Path, required=True)
    p.add_argument("--val-jsonl", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--modality", choices=["text", "image", "point", "step"], default="step")
    p.add_argument("--epochs", type=int, default=5)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--learning-rate", type=float, default=1e-4)
    p.add_argument("--weight-decay", type=float, default=1e-4)
    p.add_argument("--temperature", type=float, default=0.07)
    # 1.0, not the 0.1 that prior_losses used to default to. Until this flag
    # existed the two calls below were positional, so args.lambda_cos landed in the
    # lambda_l2 slot and every released prior was trained at lambda_l2 = 1.0. The
    # default records that rather than reintroducing a value no checkpoint ever saw.
    p.add_argument("--lambda-l2", type=float, default=1.0)
    p.add_argument("--lambda-cos", type=float, default=1.0)
    p.add_argument("--lambda-nce", type=float, default=1.0)
    p.add_argument("--point-count", type=int, default=1024)
    p.add_argument("--train-point-sampling", choices=["random", "fps", "hybrid"], default="hybrid")
    p.add_argument("--eval-point-sampling", choices=["random", "fps", "hybrid"], default="fps")
    p.add_argument("--num-workers", type=int, default=0)
    p.add_argument("--limit-train", type=int, default=None)
    p.add_argument("--limit-val", type=int, default=None)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


class PriorDataset(Dataset):
    def __init__(self, rows: list[dict[str, Any]], modality: str, point_count: int, point_sampling: str, seed: int):
        self.rows = rows
        self.modality = modality
        self.point_count = point_count
        self.point_sampling = point_sampling
        self.seed = seed
        self.epoch = 0

    def set_epoch(self, epoch: int) -> None:
        self.epoch = epoch

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        row = self.rows[idx]
        item: dict[str, Any] = {
            "sample_id": row["sample_id"],
            "ir": read_text(row["ir_path"]),
        }
        if self.modality == "text":
            item["value"] = row.get("text", "")
        elif self.modality == "image":
            item["value"] = load_image(row["iso_image_path"])
        elif self.modality == "step":
            item["value"] = load_step_brep_tensors(row["step_feature_path"], strict=True)
        elif self.modality == "point":
            item["value"] = load_point_cloud_sampled(
                row["point_path"],
                point_count=self.point_count,
                sampling=self.point_sampling,
                seed=self.seed + self.epoch * len(self.rows) + idx,
            )
        else:
            raise ValueError(self.modality)
        return item


def collate(batch: list[dict[str, Any]]) -> dict[str, Any]:
    values = [x["value"] for x in batch]
    if isinstance(values[0], dict):
        values = collate_step_brep_batch(values)
    elif isinstance(values[0], np.ndarray):
        values = torch.tensor(np.stack(values, axis=0), dtype=torch.float32)
    return {
        "sample_id": [x["sample_id"] for x in batch],
        "ir": [x["ir"] for x in batch],
        "value": values,
    }


@torch.no_grad()
def encode_modality(aligner, modality: str, values, device: torch.device) -> torch.Tensor:
    if modality == "point":
        return aligner.encode_point(values.to(device))
    if modality == "step":
        return aligner.encode_step({k: v.to(device) for k, v in values.items()})
    if modality == "image":
        return aligner.encode_image(values, device)
    if modality == "text":
        return aligner.encode_text(values, device)
    raise ValueError(modality)


@torch.no_grad()
def evaluate(aligner, prior, loader, args, device: torch.device) -> dict[str, float]:
    prior.eval()
    losses = []
    direct_metrics = []
    pred_metrics = []
    for batch in tqdm(loader, desc="eval", leave=False):
        z_ir = aligner.encode_ir(batch["ir"], device)
        z_m = encode_modality(aligner, args.modality, batch["value"], device)
        z_hat = prior(z_m)
        parts = prior_losses(
            z_hat,
            z_ir,
            temperature=args.temperature,
            lambda_l2=args.lambda_l2,
            lambda_cos=args.lambda_cos,
            lambda_nce=args.lambda_nce,
        )
        losses.append({k: float(v.detach().cpu()) for k, v in parts.items()})
        direct_metrics.append(retrieval_metrics(z_m, z_ir))
        pred_metrics.append(retrieval_metrics(z_hat, z_ir))
    out: dict[str, float] = {}
    for key in ["loss", "l2", "cosine", "nce"]:
        out[key] = float(np.mean([x[key] for x in losses])) if losses else 0.0
    for prefix, rows in [("direct", direct_metrics), ("pred", pred_metrics)]:
        keys = sorted({k for row in rows for k in row})
        for key in keys:
            out[f"{prefix}_{key}"] = float(np.mean([row.get(key, 0.0) for row in rows])) if rows else 0.0
    prior.train()
    return out


def main() -> int:
    args = parse_args()
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    aligner, align_config, modalities, extra = load_alignment_checkpoint(args.alignment_checkpoint, map_location="cpu")
    aligner.to(device).eval()
    for p in aligner.parameters():
        p.requires_grad_(False)

    train_rows = read_jsonl(args.train_jsonl)
    val_rows = read_jsonl(args.val_jsonl)
    if args.limit_train:
        train_rows = train_rows[: args.limit_train]
    if args.limit_val:
        val_rows = val_rows[: args.limit_val]

    train_ds = PriorDataset(train_rows, args.modality, args.point_count, args.train_point_sampling, args.seed)
    val_ds = PriorDataset(val_rows, args.modality, args.point_count, args.eval_point_sampling, args.seed)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=args.num_workers, collate_fn=collate)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers, collate_fn=collate)

    prior = LatentPrior(LatentPriorConfig(modality=args.modality, embed_dim=int(align_config.embed_dim))).to(device)
    optimizer = torch.optim.AdamW(prior.parameters(), lr=args.learning_rate, weight_decay=args.weight_decay)

    best_loss = float("inf")
    report = {
        "args": {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
        "steps": [],
    }
    step = 0
    for epoch in range(args.epochs):
        train_ds.set_epoch(epoch)
        pbar = tqdm(train_loader, desc=f"epoch {epoch + 1}/{args.epochs}")
        for batch in pbar:
            step += 1
            with torch.no_grad():
                z_ir = aligner.encode_ir(batch["ir"], device)
                z_m = encode_modality(aligner, args.modality, batch["value"], device)
            z_hat = prior(z_m)
            loss_dict = prior_losses(
                z_hat,
                z_ir,
                temperature=args.temperature,
                lambda_l2=args.lambda_l2,
                lambda_cos=args.lambda_cos,
                lambda_nce=args.lambda_nce,
            )
            optimizer.zero_grad(set_to_none=True)
            loss_dict["loss"].backward()
            optimizer.step()
            pbar.set_postfix(loss=f"{float(loss_dict['loss'].detach().cpu()):.4f}")

        metrics = evaluate(aligner, prior, val_loader, args, device)
        metrics["epoch"] = epoch + 1
        metrics["step"] = step
        report["steps"].append(metrics)
        print(json.dumps(metrics, indent=2))
        if metrics["loss"] < best_loss:
            best_loss = metrics["loss"]
            torch.save(
                {
                    "state_dict": prior.state_dict(),
                    "config": prior.config.__dict__,
                    "alignment_checkpoint": str(args.alignment_checkpoint),
                    "modality": args.modality,
                    "best_loss": best_loss,
                },
                args.output_dir / "best.pt",
            )

    torch.save(
        {
            "state_dict": prior.state_dict(),
            "config": prior.config.__dict__,
            "alignment_checkpoint": str(args.alignment_checkpoint),
            "modality": args.modality,
            "best_loss": best_loss,
        },
        args.output_dir / "last.pt",
    )
    with open(args.output_dir / "training_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Best checkpoint: {args.output_dir / 'best.pt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



