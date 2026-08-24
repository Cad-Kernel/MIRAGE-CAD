"""Evaluate direct modality retrieval against MIRAGE-CAD predicted-IR retrieval."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from tqdm import tqdm

from miragecad.data import load_image, load_step_brep_tensors, read_jsonl, read_text
from miragecad.gen_prompts import extract_operation_types
from miragecad.models import load_alignment_checkpoint
from miragecad.latent_prior import LatentPrior, LatentPriorConfig
from miragecad.point_sampling import load_point_cloud_sampled


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Evaluate MIRAGE-CAD latent-prior retrieval.")
    p.add_argument("--alignment-checkpoint", type=Path, required=True)
    p.add_argument("--prior-checkpoint", type=Path, required=True)
    p.add_argument("--retrieval-index", type=Path, required=True)
    p.add_argument("--test-jsonl", type=Path, required=True)
    p.add_argument("--output-json", type=Path, required=True)
    p.add_argument("--modality", choices=["text", "image", "point", "step"], default="step")
    p.add_argument("--point-count", type=int, default=1024)
    p.add_argument("--eval-point-sampling", choices=["random", "fps", "hybrid"], default="fps")
    p.add_argument("--candidate-pools", nargs="+", type=int, default=[10, 128, 1024])
    p.add_argument("--corpus-jsonl", type=Path, default=None,
                   help="Train-split JSONL used to build the index. When provided, computes "
                        "same-family-rate@10 and same-op-rate@10 (architecture §18.1).")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def load_prior(path: Path, device: torch.device) -> LatentPrior:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    prior = LatentPrior(LatentPriorConfig(**payload["config"]))
    prior.load_state_dict(payload["state_dict"], strict=True)
    return prior.to(device).eval()


def reciprocal_rank(order: np.ndarray, target_sample_id: str, sample_ids: np.ndarray, k: int) -> float:
    for rank, idx in enumerate(order[:k], start=1):
        if str(sample_ids[idx]) == target_sample_id:
            return 1.0 / rank
    return 0.0


def hit(order: np.ndarray, target_sample_id: str, sample_ids: np.ndarray, k: int) -> float:
    top = {str(sample_ids[i]) for i in order[:k]}
    return 1.0 if target_sample_id in top else 0.0


def same_family_rate(
    order: np.ndarray,
    query_template: str,
    sample_ids: np.ndarray,
    corpus_meta: dict[str, dict],
    k: int = 10,
) -> float:
    """Fraction of top-k retrieved candidates that share the query's template family."""
    if not query_template:
        return float("nan")
    top_k = [str(sample_ids[i]) for i in order[:k]]
    if not top_k:
        return float("nan")
    matches = sum(1 for sid in top_k if corpus_meta.get(sid, {}).get("template", "") == query_template)
    return matches / len(top_k)


def same_op_rate(
    order: np.ndarray,
    query_ops: frozenset,
    sample_ids: np.ndarray,
    corpus_meta: dict[str, dict],
    k: int = 10,
) -> float:
    """Fraction of top-k retrieved candidates whose operation set exactly matches the query's."""
    if not query_ops:
        return float("nan")
    top_k = [str(sample_ids[i]) for i in order[:k]]
    if not top_k:
        return float("nan")
    matches = sum(1 for sid in top_k if corpus_meta.get(sid, {}).get("op_set") == query_ops)
    return matches / len(top_k)


def build_corpus_meta(corpus_jsonl: Path) -> dict[str, dict]:
    """Build {sample_id: {template, op_set}} from train-split JSONL.

    op_set is a frozenset of operation type strings extracted from training_ir.txt.
    Rows with missing ir_path or unreadable IR are stored with op_set=frozenset().
    """
    rows = read_jsonl(corpus_jsonl)
    meta: dict[str, dict] = {}
    for row in tqdm(rows, desc="build-corpus-meta"):
        sid = str(row.get("sample_id", ""))
        template = str(row.get("template", "")).strip()
        ir_text = read_text(row.get("ir_path", ""))
        op_set = frozenset(extract_operation_types(ir_text)) if ir_text else frozenset()
        meta[sid] = {"template": template, "op_set": op_set}
    return meta


@torch.no_grad()
def encode(aligner, prior, row, modality: str, args, device: torch.device) -> tuple[np.ndarray, np.ndarray]:
    if modality == "text":
        z_direct = aligner.encode_text([row.get("text", "")], device)
    elif modality == "image":
        z_direct = aligner.encode_image([load_image(row["iso_image_path"])], device)
    elif modality == "step":
        value = load_step_brep_tensors(row["step_feature_path"])
        value = {key: torch.tensor(array[None, ...], dtype=torch.float32, device=device) for key, array in value.items()}
        z_direct = aligner.encode_step(value)
    elif modality == "point":
        points = load_point_cloud_sampled(
            row["point_path"],
            point_count=args.point_count,
            sampling=args.eval_point_sampling,
            seed=args.seed,
        )
        value = torch.tensor(points[None, ...], dtype=torch.float32)
        z_direct = aligner.encode_point(value.to(device))
    else:
        raise ValueError(modality)
    z_prior = prior(z_direct)
    return z_direct.cpu().numpy()[0], z_prior.cpu().numpy()[0]


@torch.no_grad()
def main() -> int:
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    aligner, _, _, _ = load_alignment_checkpoint(args.alignment_checkpoint, map_location="cpu")
    aligner.to(device).eval()
    prior = load_prior(args.prior_checkpoint, device)
    index = np.load(args.retrieval_index, allow_pickle=True)
    rows = read_jsonl(args.test_jsonl)
    if args.limit:
        rows = rows[: args.limit]

    embeddings = index["embeddings"]
    sample_ids = index["sample_ids"]

    # Load corpus metadata for same-family and same-op metrics if corpus JSONL provided.
    corpus_meta: dict[str, dict] = {}
    has_corpus = args.corpus_jsonl is not None and args.corpus_jsonl.exists()
    if has_corpus:
        corpus_meta = build_corpus_meta(args.corpus_jsonl)

    metrics: dict[str, list] = {}
    for prefix in ["direct", "prior"]:
        for k in [1, 5, 10]:
            metrics[f"{prefix}_r@{k}"] = []
        metrics[f"{prefix}_mrr@10"] = []
        if has_corpus:
            metrics[f"{prefix}_same_family@10"] = []
            metrics[f"{prefix}_same_op@10"] = []
    for pool in args.candidate_pools:
        for k in [1, 5, 10]:
            if k <= pool:
                metrics[f"rerank_pool{pool}_r@{k}"] = []

    for row in tqdm(rows, desc="retrieval-eval"):
        target = str(row["sample_id"])
        z_direct, z_prior = encode(aligner, prior, row, args.modality, args, device)
        direct_scores = embeddings @ z_direct
        prior_scores = embeddings @ z_prior
        direct_order = np.argsort(-direct_scores)
        prior_order = np.argsort(-prior_scores)

        # Query metadata for same-family / same-op (read from test row itself).
        if has_corpus:
            query_template = str(row.get("template", "")).strip()
            query_ir = read_text(row.get("ir_path", ""))
            query_ops = frozenset(extract_operation_types(query_ir)) if query_ir else frozenset()

        for prefix, order in [("direct", direct_order), ("prior", prior_order)]:
            for k in [1, 5, 10]:
                metrics[f"{prefix}_r@{k}"].append(hit(order, target, sample_ids, k))
            metrics[f"{prefix}_mrr@10"].append(reciprocal_rank(order, target, sample_ids, 10))
            if has_corpus:
                metrics[f"{prefix}_same_family@10"].append(
                    same_family_rate(order, query_template, sample_ids, corpus_meta, k=10)
                )
                metrics[f"{prefix}_same_op@10"].append(
                    same_op_rate(order, query_ops, sample_ids, corpus_meta, k=10)
                )

        for pool in args.candidate_pools:
            candidates = direct_order[:pool]
            reranked = candidates[np.argsort(-(embeddings[candidates] @ z_prior))]
            for k in [1, 5, 10]:
                if k <= pool:
                    metrics[f"rerank_pool{pool}_r@{k}"].append(hit(reranked, target, sample_ids, k))

    summary: dict = {
        "modality": args.modality,
        "count": len(rows),
        "retrieval_index": str(args.retrieval_index),
        "corpus_jsonl": str(args.corpus_jsonl) if has_corpus else None,
    }
    for key, values in metrics.items():
        if not values:
            summary[key] = 0.0
        else:
            arr = np.array(values, dtype=float)
            valid = arr[~np.isnan(arr)]
            summary[key] = float(np.mean(valid)) if valid.size else float("nan")

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



