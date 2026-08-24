"""MIRAGE-CAD Phase 1 -- star-topology multimodal alignment training.

Trains the IR-anchored contrastive alignment stage described in Section 4.2.
Each input modality (text, image, point cloud, STEP/B-Rep) is aligned to the
Construction IR anchor via symmetric InfoNCE.  The resulting shared 512-d
embedding space is used to build the retrieval index for Phase 2 (LoRA generation).
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from tqdm import tqdm

# Operations confirmed to fail at 80-92% across all four modalities in the 5K
# validation round (docs/MIRAGE-CAD_experiment_results.md SS4.5) due to a collapsed
# shared IR anchor space, not any single modality encoder. --rare-op-boost
# upweights training rows containing these ops via WeightedRandomSampler; it does
# NOT change the loss function or add hard negatives -- see the 25K plan doc for
# why hard-negative mining is deferred to a later iteration.
DEFAULT_RARE_OP_TOKENS = [
    "OP_SWEEP_TUBE",
    "OP_CIRCULAR_PATTERN",
    "OP_SKETCH_ON_FACE",
    "OP_FACE_EXTRUDE_ADD",
    "OP_FACE_EXTRUDE_CUT",
    "OP_PROFILE_CUT",
]

from miragecad.data import (
    STEP_EDGE_DIM,
    STEP_FACE_DIM,
    STEP_FEATURE_DIM,
    STEP_RELATION_DIM,
    collate_step_brep_batch,
    load_image,
    load_step_brep_tensors,
    read_jsonl,
    read_text,
)
from miragecad.losses import retrieval_accuracy, symmetric_info_nce
from miragecad.models import MIRAGECADConfig, MIRAGECADAligner, save_alignment_checkpoint
from miragecad.point_sampling import load_point_cloud_sampled


class AlignmentDataset(Dataset):
    def __init__(
        self,
        rows: list[dict[str, Any]],
        modalities: list[str],
        image_mode: str = "iso",
        point_count: int = 1024,
        point_sampling: str = "fps",
        seed: int = 42,
    ):
        self.rows = rows
        self.modalities = set(modalities)
        self.image_mode = image_mode
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
        ir = read_text(row["ir_path"])
        item = {
            "sample_id": row["sample_id"],
            "text": row.get("text", ""),
            "ir": ir,
        }
        if "image" in self.modalities:
            if self.image_mode == "8view":
                paths = row.get("image_paths", [])
                item["images"] = [load_image(p) for p in paths[:8]]
            else:
                item["image"] = load_image(row["iso_image_path"])
        if "point" in self.modalities:
            item["point"] = load_point_cloud_sampled(row["point_path"], point_count=self.point_count, sampling=self.point_sampling, seed=self.seed + self.epoch * len(self.rows) + idx)
        if "step" in self.modalities:
            item["step"] = load_step_brep_tensors(row["step_feature_path"], strict=True)
        return item


def collate(batch: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "sample_id": [x["sample_id"] for x in batch],
        "text": [x["text"] for x in batch],
        "ir": [x["ir"] for x in batch],
    }
    if "point" in batch[0]:
        out["point"] = torch.from_numpy(np.stack([x["point"] for x in batch], axis=0)).float()
    if "step" in batch[0]:
        out["step"] = collate_step_brep_batch([x["step"] for x in batch])
    if "images" in batch[0]:
        out["images"] = [x["images"] for x in batch]
    elif "image" in batch[0]:
        out["image"] = [x["image"] for x in batch]
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train the MIRAGE-CAD star-topology multimodal alignment model.")
    p.add_argument("--train-jsonl", type=Path, required=True)
    p.add_argument("--val-jsonl", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--modalities", nargs="+", default=["text", "image", "point", "step", "ir"], choices=["text", "image", "point", "step", "ir"])
    p.add_argument("--text-model", default="distilbert-base-uncased")
    p.add_argument("--image-model", default="openai/clip-vit-base-patch32")
    p.add_argument("--embed-dim", type=int, default=512)
    p.add_argument("--max-text-length", type=int, default=128)
    p.add_argument("--max-ir-length", type=int, default=256)
    p.add_argument("--train-text-backbone", action="store_true")
    p.add_argument("--train-image-backbone", action="store_true")
    p.add_argument("--freeze-ir-backbone", action="store_true")
    p.add_argument("--image-mode", choices=["iso", "8view"], default="iso")
    p.add_argument("--point-count", type=int, default=1024)
    p.add_argument("--train-point-sampling", choices=["random", "fps", "hybrid"], default="hybrid")
    p.add_argument("--eval-point-sampling", choices=["random", "fps", "hybrid"], default="fps")
    p.add_argument("--epochs", type=int, default=1)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--grad-accum", type=int, default=1)
    p.add_argument("--learning-rate", type=float, default=1e-4)
    p.add_argument("--weight-decay", type=float, default=1e-4)
    p.add_argument("--temperature", type=float, default=0.07)
    p.add_argument("--num-workers", type=int, default=0)
    p.add_argument("--bf16", action="store_true")
    p.add_argument("--fp16", action="store_true")
    p.add_argument("--log-steps", type=int, default=20)
    p.add_argument("--eval-steps", type=int, default=200)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument(
        "--rare-op-boost", type=float, default=1.0,
        help="Sampling weight multiplier for training rows whose reference IR contains "
             "a rare operation token (see --rare-op-tokens). 1.0 = disabled (plain shuffle). "
             "Recommended range 2.0-3.0; do not exceed 5.0 (risks overfitting the boosted rows).",
    )
    p.add_argument(
        "--rare-op-tokens", nargs="+", default=DEFAULT_RARE_OP_TOKENS,
        help="Operation tokens (as they appear in training_ir.txt) treated as rare for "
             "--rare-op-boost. Only used if --rare-op-boost > 1.0.",
    )
    return p.parse_args()


def compute_rare_op_sample_weights(rows: list[dict[str, Any]], rare_op_tokens: list[str], boost: float) -> list[float]:
    """One weight per training row: `boost` if its reference IR contains any of
    `rare_op_tokens`, else 1.0. Reads training_ir.txt directly (same source the
    rare-op audit scripts use), not a cached field, so this stays correct even if
    upstream manifest fields change."""
    pattern = re.compile("|".join(re.escape(tok) for tok in rare_op_tokens))
    weights = []
    n_boosted = 0
    for row in rows:
        text = read_text(row["ir_path"])
        if pattern.search(text):
            weights.append(boost)
            n_boosted += 1
        else:
            weights.append(1.0)
    print(f"[rare-op-boost] {n_boosted}/{len(rows)} training rows contain a rare op "
          f"({rare_op_tokens}); sampling weight={boost}x for those rows.")
    return weights


def encode_batch(model: MIRAGECADAligner, batch: dict[str, Any], modalities: list[str], device: torch.device, image_mode: str) -> dict[str, torch.Tensor]:
    z: dict[str, torch.Tensor] = {}
    if "ir" in modalities:
        z["ir"] = model.encode_ir(batch["ir"], device)
    if "text" in modalities:
        z["text"] = model.encode_text(batch["text"], device)
    if "point" in modalities:
        z["point"] = model.encode_point(batch["point"].to(device))
    if "step" in modalities:
        z["step"] = model.encode_step({k: v.to(device) for k, v in batch["step"].items()})
    if "image" in modalities:
        if image_mode == "8view":
            # Flatten B x V images, encode, then average views.
            bsz = len(batch["images"])
            views = len(batch["images"][0])
            flat = [img for item in batch["images"] for img in item]
            emb = model.encode_image(flat, device).view(bsz, views, -1).mean(dim=1)
            z["image"] = torch.nn.functional.normalize(emb, dim=-1)
        else:
            z["image"] = model.encode_image(batch["image"], device)
    return z


@torch.no_grad()
def evaluate(model: MIRAGECADAligner, loader: DataLoader, modalities: list[str], device: torch.device, args: argparse.Namespace) -> dict[str, float]:
    model.eval()
    total_loss = 0.0
    count = 0
    acc_sums: dict[str, float] = {}
    for batch in tqdm(loader, desc="eval", leave=False):
        z = encode_batch(model, batch, modalities, device, args.image_mode)
        if "ir" not in z:
            continue
        loss = torch.zeros([], device=device)
        pairs = 0
        for modality, emb in z.items():
            if modality == "ir":
                continue
            pair_loss = symmetric_info_nce(emb, z["ir"], args.temperature)
            loss = loss + pair_loss
            pairs += 1
            acc = retrieval_accuracy(emb, z["ir"])
            for k, v in acc.items():
                acc_sums[f"{modality}_{k}"] = acc_sums.get(f"{modality}_{k}", 0.0) + v
        if pairs:
            loss = loss / pairs
            total_loss += loss.item()
            count += 1
    out = {"loss": total_loss / max(count, 1)}
    for k, v in acc_sums.items():
        out[k] = v / max(count, 1)
    model.train()
    return out


def main() -> int:
    args = parse_args()
    torch.manual_seed(args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dtype = torch.bfloat16 if args.bf16 else torch.float16 if args.fp16 else None

    train_rows = read_jsonl(args.train_jsonl)
    val_rows = read_jsonl(args.val_jsonl)
    train_ds = AlignmentDataset(train_rows, args.modalities, image_mode=args.image_mode, point_count=args.point_count, point_sampling=args.train_point_sampling, seed=args.seed)
    val_ds = AlignmentDataset(val_rows, args.modalities, image_mode=args.image_mode, point_count=args.point_count, point_sampling=args.eval_point_sampling, seed=args.seed + 100000)
    if args.rare_op_boost > 1.0:
        weights = compute_rare_op_sample_weights(train_rows, args.rare_op_tokens, args.rare_op_boost)
        sampler = WeightedRandomSampler(weights, num_samples=len(train_rows), replacement=True)
        train_loader = DataLoader(train_ds, batch_size=args.batch_size, sampler=sampler, num_workers=args.num_workers, collate_fn=collate)
    else:
        train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=args.num_workers, collate_fn=collate)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers, collate_fn=collate)

    config = MIRAGECADConfig(
        text_model=args.text_model,
        image_model=args.image_model,
        embed_dim=args.embed_dim,
        max_text_length=args.max_text_length,
        max_ir_length=args.max_ir_length,
        step_feature_dim=STEP_FEATURE_DIM,
        step_encoder_type="global_local_relation",
        step_face_dim=STEP_FACE_DIM,
        step_edge_dim=STEP_EDGE_DIM,
        step_relation_dim=STEP_RELATION_DIM,
        train_text_backbone=args.train_text_backbone,
        train_image_backbone=args.train_image_backbone,
        train_ir_backbone=not args.freeze_ir_backbone,
    )
    model = MIRAGECADAligner(config, args.modalities).to(device)
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=args.learning_rate, weight_decay=args.weight_decay)
    scaler = torch.amp.GradScaler("cuda", enabled=args.fp16)

    best_loss = math.inf
    step = 0
    running = 0.0
    report_args = {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()}
    report = {"args": report_args, "steps": []}

    model.train()
    for epoch in range(args.epochs):
        train_ds.set_epoch(epoch)
        pbar = tqdm(train_loader, desc=f"epoch {epoch + 1}/{args.epochs}")
        optimizer.zero_grad(set_to_none=True)
        for batch in pbar:
            step += 1
            with torch.autocast(device_type="cuda", dtype=dtype, enabled=(dtype is not None and device.type == "cuda")):
                z = encode_batch(model, batch, args.modalities, device, args.image_mode)
                if "ir" not in z:
                    # IR is the star-topology anchor; all other modalities align to it.
                    raise ValueError("The alignment anchor 'ir' must be included in --modalities.")
                loss = torch.zeros([], device=device)
                pairs = 0
                for modality, emb in z.items():
                    if modality == "ir":
                        continue
                    loss = loss + symmetric_info_nce(emb, z["ir"], args.temperature)
                    pairs += 1
                loss = loss / max(pairs, 1)
                loss = loss / args.grad_accum

            scaler.scale(loss).backward()
            running += loss.item() * args.grad_accum
            if step % args.grad_accum == 0:
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad(set_to_none=True)

            if step % args.log_steps == 0:
                pbar.set_postfix(loss=f"{running / args.log_steps:.4f}")
                running = 0.0

            if step % args.eval_steps == 0:
                metrics = evaluate(model, val_loader, args.modalities, device, args)
                metrics["step"] = step
                metrics["epoch"] = epoch + 1
                report["steps"].append(metrics)
                print(json.dumps(metrics, indent=2))
                if metrics["loss"] < best_loss:
                    best_loss = metrics["loss"]
                    save_alignment_checkpoint(args.output_dir / "best.pt", model, config, args.modalities, extra={"best_loss": best_loss, "step": step})

        metrics = evaluate(model, val_loader, args.modalities, device, args)
        metrics["step"] = step
        metrics["epoch"] = epoch + 1
        report["steps"].append(metrics)
        if metrics["loss"] < best_loss:
            best_loss = metrics["loss"]
            save_alignment_checkpoint(args.output_dir / "best.pt", model, config, args.modalities, extra={"best_loss": best_loss, "step": step})

    save_alignment_checkpoint(args.output_dir / "last.pt", model, config, args.modalities, extra={"best_loss": best_loss, "step": step})
    with open(args.output_dir / "training_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Best checkpoint: {args.output_dir / 'best.pt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

