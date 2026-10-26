"""Generate Flluma programs with MIRAGE-CAD latent-prior retrieval."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from peft import PeftModel
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer

from miragecad.data import build_generation_prompt, load_image, load_step_brep_tensors, read_jsonl, read_text
from miragecad.models import load_alignment_checkpoint
from miragecad.latent_prior import LatentPrior, LatentPriorConfig
from miragecad.point_sampling import load_point_cloud_sampled


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate programs using MIRAGE-CAD predicted-IR latent retrieval.")
    p.add_argument("--model-name", default="Qwen/Qwen2.5-Coder-1.5B")
    p.add_argument("--adapter-dir", type=Path, required=True, help="LoRA program adapter directory.")
    p.add_argument("--alignment-checkpoint", type=Path, required=True)
    p.add_argument("--prior-checkpoint", type=Path, required=True)
    p.add_argument("--retrieval-index", type=Path, required=True)
    p.add_argument("--input-jsonl", type=Path, required=True)
    p.add_argument("--output-jsonl", type=Path, required=True)
    p.add_argument("--modality", choices=["text", "image", "point", "step"], default="step")
    p.add_argument("--retrieval-mode", choices=["direct", "prior", "rerank"], default="prior")
    p.add_argument("--candidate-pool", type=int, default=128)
    p.add_argument("--retrieval-top-k", type=int, default=3)
    p.add_argument("--include-nearest-ir", action="store_true")
    p.add_argument("--hide-target-text", action="store_true")
    p.add_argument("--point-count", type=int, default=1024)
    p.add_argument("--eval-point-sampling", choices=["random", "fps", "hybrid"], default="fps")
    p.add_argument("--max-length", type=int, default=2048)
    p.add_argument("--max-new-tokens", type=int, default=1024)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--top-p", type=float, default=1.0)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--bf16", action="store_true")
    p.add_argument("--fp16", action="store_true")
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def load_prior(path: Path, device: torch.device) -> LatentPrior:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    config = LatentPriorConfig(**payload["config"])
    prior = LatentPrior(config)
    prior.load_state_dict(payload["state_dict"], strict=True)
    return prior.to(device).eval()


def load_query_value(row: dict, modality: str, args: argparse.Namespace):
    if modality == "text":
        return row.get("text", "")
    if modality == "image":
        return load_image(row["iso_image_path"])
    if modality == "step":
        value = load_step_brep_tensors(row["step_feature_path"])
        return {key: torch.tensor(array[None, ...], dtype=torch.float32) for key, array in value.items()}
    if modality == "point":
        points = load_point_cloud_sampled(
            row["point_path"],
            point_count=args.point_count,
            sampling=args.eval_point_sampling,
            seed=args.seed,
        )
        return torch.tensor(points[None, ...], dtype=torch.float32)
    raise ValueError(modality)


@torch.no_grad()
def encode_query(aligner, prior, row: dict, args: argparse.Namespace, device: torch.device) -> tuple[np.ndarray, np.ndarray]:
    value = load_query_value(row, args.modality, args)
    if args.modality == "text":
        z_direct = aligner.encode_text([value], device)
    elif args.modality == "image":
        z_direct = aligner.encode_image([value], device)
    elif args.modality == "step":
        z_direct = aligner.encode_step({k: v.to(device) for k, v in value.items()})
    elif args.modality == "point":
        z_direct = aligner.encode_point(value.to(device))
    else:
        raise ValueError(args.modality)
    z_prior = prior(z_direct)
    return z_direct.cpu().numpy()[0], z_prior.cpu().numpy()[0]


def row_for_retrieved(rel: str, current_row: dict, sample_id: str, text: str) -> dict:
    dataset_root = Path(current_row["dataset_root"])
    sample_dir2 = dataset_root / rel
    return {
        "sample_id": sample_id,
        "text": text,
        "ir": read_text(sample_dir2 / "training_ir.txt"),
        "program": read_text(sample_dir2 / "program.py"),
    }


def retrieve(row: dict, index, z_direct: np.ndarray, z_prior: np.ndarray, args: argparse.Namespace) -> list[dict]:
    embeddings = index["embeddings"]
    if args.retrieval_mode == "direct":
        scores = embeddings @ z_direct
        order = np.argsort(-scores)[: args.retrieval_top_k]
    elif args.retrieval_mode == "prior":
        scores = embeddings @ z_prior
        order = np.argsort(-scores)[: args.retrieval_top_k]
    else:
        direct_scores = embeddings @ z_direct
        pool = np.argsort(-direct_scores)[: args.candidate_pool]
        prior_scores = embeddings[pool] @ z_prior
        order = pool[np.argsort(-prior_scores)[: args.retrieval_top_k]]

    out = []
    for i in order:
        out.append(
            row_for_retrieved(
                str(index["relpaths"][i]),
                row,
                str(index["sample_ids"][i]),
                str(index["texts"][i]),
            )
        )
    return out


def observation_text(args: argparse.Namespace, retrieved: list[dict]) -> str:
    label = {
        "text": "Natural-language query encoded into the Construction-IR latent space.",
        "image": "CAD image query encoded into the Construction-IR latent space.",
        "point": "Surface point-cloud query encoded into the Construction-IR latent space.",
        "step": "STEP/B-Rep query encoded into the Construction-IR latent space.",
    }[args.modality]
    if args.include_nearest_ir and retrieved and retrieved[0].get("ir"):
        return label + "\nNearest predicted construction IR:\n" + retrieved[0]["ir"][:1200]
    return label


@torch.no_grad()
def main() -> int:
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dtype = torch.bfloat16 if args.bf16 else torch.float16 if args.fp16 else None

    aligner, _, _, _ = load_alignment_checkpoint(args.alignment_checkpoint, map_location="cpu")
    aligner.to(device).eval()
    prior = load_prior(args.prior_checkpoint, device)
    index = np.load(args.retrieval_index, allow_pickle=True)

    tokenizer = AutoTokenizer.from_pretrained(args.adapter_dir, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model_kwargs = {"trust_remote_code": True}
    if dtype is not None:
        model_kwargs["torch_dtype"] = dtype
    base = AutoModelForCausalLM.from_pretrained(args.model_name, **model_kwargs)
    model = PeftModel.from_pretrained(base, args.adapter_dir)
    model.to(device).eval()

    rows = read_jsonl(args.input_jsonl)
    if args.limit:
        rows = rows[: args.limit]
    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)

    with open(args.output_jsonl, "w", encoding="utf-8", newline="\n") as f:
        for row in tqdm(rows, desc="generate-miragecad"):
            z_direct, z_prior = encode_query(aligner, prior, row, args, device)
            retrieved = retrieve(row, index, z_direct, z_prior, args)
            prompt_row = dict(row)
            prompt_row["target_observation"] = observation_text(args, retrieved)
            if args.hide_target_text:
                prompt_row["prompt_text"] = ""
            prompt = build_generation_prompt(prompt_row, target="program", retrieved=retrieved)
            inputs = tokenizer(prompt, truncation=True, max_length=args.max_length, return_tensors="pt").to(device)
            do_sample = args.temperature > 0
            gen = model.generate(
                **inputs,
                max_new_tokens=args.max_new_tokens,
                do_sample=do_sample,
                temperature=args.temperature if do_sample else None,
                top_p=args.top_p if do_sample else None,
                pad_token_id=tokenizer.eos_token_id,
            )
            text = tokenizer.decode(gen[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True)
            out = {
                "sample_id": row["sample_id"],
                "target": "program",
                "prediction": text.strip(),
                "reference": read_text(row["program_path"]),
                "relpath": row.get("relpath", ""),
                "retrieved": [x["sample_id"] for x in retrieved],
                "modality": args.modality,
                "retrieval_mode": args.retrieval_mode,
                "candidate_pool": args.candidate_pool,
                "include_nearest_ir": args.include_nearest_ir,
            }
            f.write(json.dumps(out, ensure_ascii=False) + "\n")
    print(f"Wrote predictions: {args.output_jsonl}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



