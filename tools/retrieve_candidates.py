"""MIRAGE-CAD interactive retrieval utility.

Given a single query (text, image, point cloud, STEP features, or raw IR),
encodes it with the trained MIRAGE-CAD aligner and returns the top-k
construction-similar samples from a pre-built IR index.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import torch

from miragecad.data import load_image, load_step_brep_tensors
from miragecad.point_sampling import load_point_cloud_sampled
from miragecad.models import load_alignment_checkpoint


def parse_args():
    p = argparse.ArgumentParser(description="Retrieve similar CAD samples using a MIRAGE-CAD alignment checkpoint.")
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--index", type=Path, required=True)
    p.add_argument("--query-modality", choices=["text", "image", "point", "step", "ir"], required=True)
    p.add_argument("--query-text", default=None)
    p.add_argument("--query-image", type=Path, default=None)
    p.add_argument("--query-point", type=Path, default=None)
    p.add_argument("--query-step-features", type=Path, default=None)
    p.add_argument("--query-ir", type=Path, default=None)
    p.add_argument("--top-k", type=int, default=5)
    p.add_argument("--point-count", type=int, default=1024)
    return p.parse_args()


@torch.no_grad()
def main() -> int:
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, config, modalities, extra = load_alignment_checkpoint(args.checkpoint, map_location="cpu")
    model.to(device).eval()

    if args.query_modality == "text":
        if not args.query_text:
            raise ValueError("--query-text is required for text queries")
        query_value = [args.query_text]
    elif args.query_modality == "ir":
        if not args.query_ir:
            raise ValueError("--query-ir is required for IR queries")
        query_value = [args.query_ir.read_text(encoding="utf-8")]
    elif args.query_modality == "image":
        if not args.query_image:
            raise ValueError("--query-image is required for image queries")
        query_value = [load_image(args.query_image)]
    elif args.query_modality == "point":
        if not args.query_point:
            raise ValueError("--query-point is required for point queries")
        query_points = load_point_cloud_sampled(args.query_point, point_count=args.point_count, sampling="fps", seed=0)
        query_value = torch.tensor(query_points[None, ...], dtype=torch.float32)
    else:
        if not args.query_step_features:
            raise ValueError("--query-step-features is required for STEP feature queries")
        step = load_step_brep_tensors(args.query_step_features)
        query_value = {key: torch.tensor(array[None, ...], dtype=torch.float32) for key, array in step.items()}

    z = model.encode_modality(args.query_modality, query_value, device).cpu().numpy()[0]
    idx = np.load(args.index, allow_pickle=True)
    embeddings = idx["embeddings"]
    scores = embeddings @ z
    top = np.argsort(-scores)[: args.top_k]
    for rank, i in enumerate(top, start=1):
        print(f"{rank}\t{scores[i]:.5f}\t{idx['sample_ids'][i]}\t{idx['relpaths'][i]}")
        text = str(idx["texts"][i])
        if text:
            print(f"  {text[:240].replace(chr(10), ' ')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

