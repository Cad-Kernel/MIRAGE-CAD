"""MIRAGE-CAD Phase 1b -- build the IR retrieval index.

Encodes all training samples with the trained IR encoder and saves a compressed
numpy array (.npz) for fast cosine-similarity lookup at generation time.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

from miragecad.data import collate_step_brep_batch, load_image, load_step_brep_tensors, read_jsonl, read_text
from miragecad.point_sampling import load_point_cloud_sampled
from miragecad.models import load_alignment_checkpoint


class IndexDataset(Dataset):
    def __init__(self, rows, modality: str, point_count: int = 1024):
        self.rows = rows
        self.modality = modality
        self.point_count = point_count

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx):
        row = self.rows[idx]
        item = {"sample_id": row["sample_id"], "row": row}
        if self.modality == "ir":
            item["value"] = read_text(row["ir_path"])
        elif self.modality == "text":
            item["value"] = row.get("text", "")
        elif self.modality == "image":
            item["value"] = load_image(row["iso_image_path"])
        elif self.modality == "point":
            item["value"] = load_point_cloud_sampled(row["point_path"], point_count=self.point_count, sampling="fps", seed=0)
        elif self.modality == "step":
            item["value"] = load_step_brep_tensors(row["step_feature_path"])
        else:
            raise ValueError(self.modality)
        return item


def collate(batch):
    values = [x["value"] for x in batch]
    if isinstance(values[0], dict):
        values = collate_step_brep_batch(values)
    elif isinstance(values[0], np.ndarray):
        values = torch.tensor(np.stack(values, axis=0), dtype=torch.float32)
    return {
        "sample_id": [x["sample_id"] for x in batch],
        "value": values,
        "row": [x["row"] for x in batch],
    }


def parse_args():
    p = argparse.ArgumentParser(description="Build a numpy retrieval index for MIRAGE-CAD.")
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--jsonl", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--index-modality", choices=["ir", "text", "image", "point", "step"], default="ir")
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--point-count", type=int, default=1024)
    return p.parse_args()


@torch.no_grad()
def main() -> int:
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, config, modalities, extra = load_alignment_checkpoint(args.checkpoint, map_location="cpu")
    model.to(device).eval()
    rows = read_jsonl(args.jsonl)
    ds = IndexDataset(rows, args.index_modality, point_count=args.point_count)
    loader = DataLoader(ds, batch_size=args.batch_size, shuffle=False, num_workers=0, collate_fn=collate)

    embeddings = []
    sample_ids = []
    relpaths = []
    texts = []
    for batch in tqdm(loader, desc="index"):
        z = model.encode_modality(args.index_modality, batch["value"], device)
        embeddings.append(z.cpu().numpy().astype(np.float32))
        sample_ids.extend(batch["sample_id"])
        relpaths.extend([r["relpath"] for r in batch["row"]])
        texts.extend([r.get("text", "") for r in batch["row"]])

    emb = np.concatenate(embeddings, axis=0)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.output,
        embeddings=emb,
        sample_ids=np.array(sample_ids),
        relpaths=np.array(relpaths),
        texts=np.array(texts),
        modality=np.array([args.index_modality]),
        checkpoint=np.array([str(args.checkpoint)]),
    )
    meta = {"rows": len(rows), "embedding_dim": int(emb.shape[1]), "modality": args.index_modality}
    with open(args.output.with_suffix(".json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"Wrote index: {args.output} rows={len(rows)} dim={emb.shape[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

