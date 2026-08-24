"""MIRAGE-CAD Phase 2 -- retrieval-augmented CAD program generation.

For each test query, encodes the input modality, retrieves top-k construction-similar
training examples from the IR index, and prompts the LoRA-adapted Qwen2.5-Coder-1.5B
model to generate an executable Flluma Python program.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from peft import PeftModel
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer

from miragecad.data import (
    build_generation_prompt,
    load_image,
    load_step_brep_tensors,
    read_jsonl,
    read_text,
)
from miragecad.models import load_alignment_checkpoint
from miragecad.point_sampling import load_point_cloud_sampled


def parse_args():
    p = argparse.ArgumentParser(description="Generate Flluma programs or training IR from prepared prompts.")
    p.add_argument("--model-name", default="Qwen/Qwen2.5-Coder-1.5B")
    p.add_argument("--adapter-dir", type=Path, required=True)
    p.add_argument("--input-jsonl", type=Path, required=True)
    p.add_argument("--output-jsonl", type=Path, required=True)
    p.add_argument("--target", choices=["program", "ir"], default="program")
    p.add_argument("--max-new-tokens", type=int, default=1024)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--top-p", type=float, default=1.0)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--bf16", action="store_true")
    p.add_argument("--fp16", action="store_true")
    p.add_argument("--retrieval-index", type=Path, default=None)
    p.add_argument("--retrieval-checkpoint", type=Path, default=None)
    p.add_argument("--retrieval-top-k", type=int, default=0)
    p.add_argument(
        "--retrieval-query-modality",
        choices=["text", "image", "point", "step", "ir"],
        default="text",
        help="Modality used to query the construction-aware retrieval index.",
    )
    p.add_argument(
        "--hide-target-text",
        action="store_true",
        help="Do not include the target natural-language description in the generation prompt.",
    )
    p.add_argument("--point-count", type=int, default=1024)
    p.add_argument("--eval-point-sampling", choices=["random", "fps", "hybrid"], default="fps")
    p.add_argument("--max-length", type=int, default=2048)
    return p.parse_args()


def load_retriever(checkpoint: Path | None, index_path: Path | None, top_k: int, device: torch.device):
    if not checkpoint or not index_path or top_k <= 0:
        return None
    model, config, modalities, extra = load_alignment_checkpoint(checkpoint, map_location="cpu")
    model.to(device).eval()
    index = np.load(index_path, allow_pickle=True)
    return {"model": model, "index": index, "top_k": top_k, "args": None}


@torch.no_grad()
def encode_query(row, retriever, device: torch.device, modality: str, point_count: int):
    model = retriever["model"]
    if modality == "text":
        return model.encode_text([row.get("text", "")], device).cpu().numpy()[0]
    if modality == "ir":
        return model.encode_ir([read_text(row["ir_path"])], device).cpu().numpy()[0]
    if modality == "image":
        return model.encode_image([load_image(row["iso_image_path"])], device).cpu().numpy()[0]
    if modality == "point":
        rargs = retriever.get("args")
        points_np = load_point_cloud_sampled(row["point_path"], point_count=point_count, sampling=getattr(rargs, "eval_point_sampling", "fps"), seed=0)
        points = torch.tensor(points_np[None, ...], dtype=torch.float32)
        return model.encode_point(points.to(device)).cpu().numpy()[0]
    if modality == "step":
        features = load_step_brep_tensors(row["step_feature_path"])
        features = {key: torch.tensor(array[None, ...], dtype=torch.float32, device=device) for key, array in features.items()}
        return model.encode_step(features).cpu().numpy()[0]
    raise ValueError(f"Unsupported retrieval query modality: {modality}")


@torch.no_grad()
def retrieve_for_row(row, retriever, device: torch.device, query_modality: str, point_count: int):
    if retriever is None:
        return []
    idx = retriever["index"]
    top_k = retriever["top_k"]
    q = encode_query(row, retriever, device, query_modality, point_count)
    scores = idx["embeddings"] @ q
    top = np.argsort(-scores)[: top_k]
    rows = []
    for i in top:
        rel = str(idx["relpaths"][i])
        dataset_root = Path(row["dataset_root"])
        sample_dir2 = dataset_root / rel
        rows.append(
            {
                "sample_id": str(idx["sample_ids"][i]),
                "text": str(idx["texts"][i]),
                "ir": read_text(sample_dir2 / "training_ir.txt"),
                "program": read_text(sample_dir2 / "program.py"),
            }
        )
    return rows


def observation_label(modality: str) -> str:
    return {
        "text": "Natural-language description.",
        "image": "Canonical CAD rendering encoded by the image branch.",
        "point": "Surface point cloud encoded by the point-cloud branch.",
        "step": "Kernel-extracted STEP/B-Rep descriptors encoded by the Global-Local-Relation STEP branch.",
        "ir": "Construction IR encoded by the IR branch.",
    }[modality]


def main() -> int:
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dtype = torch.bfloat16 if args.bf16 else torch.float16 if args.fp16 else None

    tokenizer = AutoTokenizer.from_pretrained(args.adapter_dir, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model_kwargs = {"trust_remote_code": True}
    if dtype is not None:
        model_kwargs["torch_dtype"] = dtype
    base = AutoModelForCausalLM.from_pretrained(args.model_name, **model_kwargs)
    model = PeftModel.from_pretrained(base, args.adapter_dir)
    model.to(device).eval()
    retriever = load_retriever(args.retrieval_checkpoint, args.retrieval_index, args.retrieval_top_k, device)
    if retriever is not None:
        retriever["args"] = args

    rows = read_jsonl(args.input_jsonl)
    if args.limit:
        rows = rows[: args.limit]
    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)

    with open(args.output_jsonl, "w", encoding="utf-8", newline="\n") as f:
        for row in tqdm(rows, desc="generate"):
            retrieved = retrieve_for_row(
                row,
                retriever,
                device,
                args.retrieval_query_modality,
                args.point_count,
            )
            prompt_row = dict(row)
            prompt_row["target_observation"] = observation_label(args.retrieval_query_modality)
            if args.hide_target_text:
                prompt_row["prompt_text"] = ""
            prompt = build_generation_prompt(prompt_row, target=args.target, retrieved=retrieved)
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
                "target": args.target,
                "prompt": prompt,
                "prediction": text.strip(),
                "reference": read_text(row["program_path"] if args.target == "program" else row["ir_path"]),
                "relpath": row.get("relpath", ""),
                "retrieved": [x.get("sample_id") for x in retrieved],
                "retrieval_query_modality": args.retrieval_query_modality,
                "hide_target_text": bool(args.hide_target_text),
            }
            f.write(json.dumps(out, ensure_ascii=False) + "\n")
    print(f"Wrote predictions: {args.output_jsonl}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

