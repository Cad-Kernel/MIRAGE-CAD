"""V2-Lite pipeline: prior_rag mode (clean refactor of generate_latent_prior.py)."""
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
from miragecad.gen_prompts import get_observation_text
from miragecad.latent_prior import LatentPrior, LatentPriorConfig
from miragecad.models import load_alignment_checkpoint
from miragecad.point_sampling import load_point_cloud_sampled


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="V2-Lite prior_rag generation.")
    p.add_argument("--pipeline", default="prior_rag", choices=["prior_rag"], help="V2-Lite pipeline mode.")
    p.add_argument("--model-name", default="Qwen/Qwen2.5-Coder-1.5B")
    p.add_argument("--adapter-dir", type=Path, required=True)
    p.add_argument("--alignment-checkpoint", type=Path, required=True)
    p.add_argument("--prior-checkpoint", type=Path, required=True)
    p.add_argument("--retrieval-index", type=Path, required=True)
    p.add_argument("--input-jsonl", type=Path, required=True)
    p.add_argument("--output-jsonl", type=Path, required=True)
    p.add_argument("--modality", choices=["text", "image", "point", "step"], default="step")
    p.add_argument("--retrieval-mode", choices=["direct", "prior", "rerank"], default="prior")
    p.add_argument("--candidate-pool", type=int, default=128)
    p.add_argument("--retrieval-top-k", type=int, default=3)
    p.add_argument("--point-count", type=int, default=1024)
    p.add_argument("--eval-point-sampling", choices=["random", "fps", "hybrid"], default="fps")
    p.add_argument("--max-length", type=int, default=2048)
    p.add_argument("--max-new-tokens", type=int, default=1024)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--top-p", type=float, default=1.0)
    p.add_argument("--bf16", action="store_true")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def load_prior(path: Path, device: torch.device) -> LatentPrior:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    cfg = payload["config"]
    if "modality" not in cfg:
        raise ValueError(f"Prior checkpoint {path} missing 'modality' in config.")
    config = LatentPriorConfig(**cfg)
    prior = LatentPrior(config)
    prior.load_state_dict(payload["state_dict"], strict=True)
    return prior.to(device).eval()


@torch.no_grad()
def encode_query(row: dict, modality: str, aligner, prior: LatentPrior, args: argparse.Namespace, device: torch.device) -> tuple[np.ndarray, np.ndarray]:
    if modality == "text":
        z_m = aligner.encode_text([row.get("text", "")], device)
    elif modality == "image":
        z_m = aligner.encode_image([load_image(row["iso_image_path"])], device)
    elif modality == "step":
        tensors = load_step_brep_tensors(row["step_feature_path"])
        batch = {k: torch.tensor(v[None], dtype=torch.float32).to(device) for k, v in tensors.items()}
        z_m = aligner.encode_step(batch)
    elif modality == "point":
        pts = load_point_cloud_sampled(row["point_path"], point_count=args.point_count, sampling=args.eval_point_sampling, seed=args.seed)
        z_m = aligner.encode_point(torch.tensor(pts[None], dtype=torch.float32).to(device))
    else:
        raise ValueError(modality)
    z_ir_hat = prior(z_m)
    return z_m.cpu().numpy()[0], z_ir_hat.cpu().numpy()[0]


def retrieve(index, z_direct: np.ndarray, z_prior: np.ndarray, args: argparse.Namespace) -> tuple[list[int], list[str]]:
    embeddings = index["embeddings"]
    if args.retrieval_mode == "direct":
        scores = embeddings @ z_direct
        order = list(np.argsort(-scores)[: args.retrieval_top_k])
    elif args.retrieval_mode == "prior":
        scores = embeddings @ z_prior
        order = list(np.argsort(-scores)[: args.retrieval_top_k])
    else:
        direct_scores = embeddings @ z_direct
        pool = np.argsort(-direct_scores)[: args.candidate_pool]
        prior_scores = embeddings[pool] @ z_prior
        order = list(pool[np.argsort(-prior_scores)[: args.retrieval_top_k]])
    return order, [str(index["sample_ids"][i]) for i in order]


def build_retrieved_examples(index, order: list[int], row: dict) -> list[dict]:
    dataset_root = Path(row.get("dataset_root", "."))
    out: list[dict] = []
    for i in order:
        relpath = str(index["relpaths"][i])
        sample_dir = dataset_root / relpath
        out.append({
            "sample_id": str(index["sample_ids"][i]),
            "text": str(index["texts"][i]) if "texts" in index else "",
            "ir": read_text(sample_dir / "training_ir.txt"),
            "program": read_text(sample_dir / "program.py"),
        })
    return out


def main() -> int:
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dtype = torch.bfloat16 if args.bf16 else None

    aligner, _, _, _ = load_alignment_checkpoint(args.alignment_checkpoint, map_location="cpu")
    aligner.to(device).eval()
    prior = load_prior(args.prior_checkpoint, device)
    index = np.load(args.retrieval_index, allow_pickle=True)

    model_kwargs: dict = {"trust_remote_code": True}
    if dtype is not None:
        model_kwargs["torch_dtype"] = dtype
    base = AutoModelForCausalLM.from_pretrained(args.model_name, **model_kwargs)
    model = PeftModel.from_pretrained(base, args.adapter_dir)
    model.to(device).eval()
    tokenizer = AutoTokenizer.from_pretrained(args.adapter_dir, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    rows = read_jsonl(args.input_jsonl)
    if args.limit:
        rows = rows[: args.limit]
    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)

    with open(args.output_jsonl, "w", encoding="utf-8", newline="\n") as f_out:
        for row in tqdm(rows, desc="lite-prior-rag"):
            z_direct, z_prior = encode_query(row, args.modality, aligner, prior, args, device)
            order, retrieved_ids = retrieve(index, z_direct, z_prior, args)
            retrieved = build_retrieved_examples(index, order, row)

            prompt_row = dict(row)
            prompt_row["target_observation"] = get_observation_text(args.modality)
            prompt = build_generation_prompt(prompt_row, target="program", retrieved=retrieved)

            inputs = tokenizer(prompt, truncation=True, max_length=args.max_length, return_tensors="pt").to(device)
            do_sample = args.temperature > 0
            with torch.no_grad():
                gen = model.generate(
                    **inputs,
                    max_new_tokens=args.max_new_tokens,
                    do_sample=do_sample,
                    temperature=args.temperature if do_sample else None,
                    top_p=args.top_p if do_sample else None,
                    pad_token_id=tokenizer.eos_token_id,
                )
            prediction = tokenizer.decode(gen[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()

            out = {
                "sample_id": row.get("sample_id", ""),
                "modality": args.modality,
                "pipeline": "prior_rag",
                "predicted_ir": None,
                "prediction": prediction,
                "all_candidates": [prediction],
                "reference": read_text(row.get("program_path", "")),
                "retrieved": retrieved_ids,
                "retrieval_mode": args.retrieval_mode,
            }
            f_out.write(json.dumps(out, ensure_ascii=False) + "\n")

    print(f"Wrote predictions: {args.output_jsonl}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
