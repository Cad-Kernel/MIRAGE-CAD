"""Table 3 A/B baseline: nearest-neighbor reference-IR substitution.

Not the legacy direct_rag/prior_rag (build_generation_prompt, no IR block) —
that prompt format has no compatible 5k-scale LoRA-Code checkpoint (the only
available checkpoint, qwen25_coder_1_5b_program_5k_stage4b, was trained on
build_program_prompt's IR-conditioned format). Reusing that mismatched prompt
would reproduce the same train/inference format-mismatch bug already found
and fixed once in this project (see docs/MIRAGE-CAD_debug_report.md).

Instead: retrieve the nearest training sample's real training_ir.txt (not a
LoRA-IR generation) and feed it through the SAME build_program_prompt() +
Stage4b LoRA-Code used by the "Ours" (C/D) pipeline. This isolates exactly
one variable: does LoRA-IR's generative step help over just grabbing the
nearest real IR?

  --retrieval-mode direct : rank candidates by z_m (query embedding) dot product
  --retrieval-mode prior  : rank candidates by z_ir_hat (prior output) dot product

No P1a (input is real reference IR, not a LoRA-IR generation — no alias to fix).
P0 + extrude_on_face code-level repairs still apply post-hoc, same as "Ours".
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
from peft import PeftModel
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, ".")
from miragecad.data import read_jsonl, read_text, load_image
from miragecad.gen_prompts import build_program_prompt
from miragecad.latent_prior import LatentPrior, LatentPriorConfig
from miragecad.models import load_alignment_checkpoint
from miragecad.point_sampling import load_point_cloud_sampled
from gen_scripts.run_miragecad import load_lm, load_tokenizer, generate_text, generate_text_batch, retrieve_candidates, build_retrieved_examples


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--modality", choices=["text", "image", "point", "step"], required=True)
    p.add_argument("--retrieval-mode", choices=["direct", "prior"], required=True)
    p.add_argument("--prior-checkpoint", type=Path, required=True)
    p.add_argument("--output-jsonl", type=Path, required=True)
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--alignment-checkpoint", type=Path, default=Path("outputs/align_smoke5k_ep10/best.pt"))
    p.add_argument("--retrieval-index", type=Path, default=Path("outputs/align_smoke5k_ep10/train_ir_index.npz"))
    p.add_argument("--lora-code-dir", type=Path, default=Path("outputs/qwen25_coder_1_5b_program_5k_stage4b"))
    p.add_argument("--input-jsonl", type=Path, default=Path("data/smoke5k/test.jsonl"))
    p.add_argument("--point-count", type=int, default=1024)
    p.add_argument("--max-length", type=int, default=1536)
    p.add_argument("--max-new-tokens", type=int, default=1536)
    p.add_argument("--batch-size", type=int, default=1,
                    help="Generate this many rows per model.generate() call instead of one at a time. "
                         "Default 1 reproduces the original, unmodified sequential behavior exactly.")
    return p.parse_args()


@torch.no_grad()
def encode_query(row, modality, aligner, prior, args, device):
    if modality == "text":
        z_m = aligner.encode_text([row.get("text", "")], device)
    elif modality == "image":
        z_m = aligner.encode_image([load_image(row["iso_image_path"])], device)
    elif modality == "step":
        from miragecad.data import load_step_brep_tensors
        tensors = load_step_brep_tensors(row["step_feature_path"], strict=True)
        batch = {k: torch.tensor(v[None], dtype=torch.float32).to(device) for k, v in tensors.items()}
        z_m = aligner.encode_step(batch)
    elif modality == "point":
        pts = load_point_cloud_sampled(row["point_path"], point_count=args.point_count, sampling="fps", seed=42)
        z_m = aligner.encode_point(torch.tensor(pts[None], dtype=torch.float32).to(device))
    z_ir_hat = prior(z_m)
    return z_m.cpu().numpy()[0], z_ir_hat.cpu().numpy()[0]


def load_point_xyz(row, modality, args):
    if modality != "point":
        return None
    return load_point_cloud_sampled(row["point_path"], point_count=args.point_count, sampling="fps", seed=42)


def main():
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    aligner, _, _, _ = load_alignment_checkpoint(args.alignment_checkpoint, map_location="cpu")
    aligner.to(device).eval()

    payload = torch.load(args.prior_checkpoint, map_location="cpu", weights_only=False)
    prior = LatentPrior(LatentPriorConfig(**payload["config"])).to(device).eval()
    prior.load_state_dict(payload["state_dict"], strict=True)

    index = np.load(args.retrieval_index, allow_pickle=True)
    rows = read_jsonl(args.input_jsonl)[: args.limit]

    # A fake args namespace matching what retrieve_candidates()/retrieval-mode expects.
    class RA:
        retrieval_mode = args.retrieval_mode
        retrieval_top_k = 1
        candidate_pool = 128
    ra = RA()

    lora_code = load_lm("Qwen/Qwen2.5-Coder-1.5B", args.lora_code_dir, torch.bfloat16, device)
    lora_code_tok = load_tokenizer(args.lora_code_dir)

    # Retrieval (encode + nearest-neighbor lookup) is cheap relative to LLM
    # generation -- keep it per-row, but batch only the generate() call.
    prepared = []
    for row in tqdm(rows, desc=f"retrieve[{args.modality}/{args.retrieval_mode}]"):
        z_direct, z_ir_hat = encode_query(row, args.modality, aligner, prior, args, device)
        order, retrieved_ids = retrieve_candidates(index, z_direct, z_ir_hat, ra)
        retrieved = build_retrieved_examples(index, order, row)
        nn_ir = retrieved[0]["ir"] if retrieved else ""
        if not nn_ir.strip():
            # build_retrieved_examples resolves the neighbour's files under the QUERY row's
            # dataset_root and read_text returns "" when the path is wrong, so a missing or
            # incorrect dataset_root yields an empty plan and an empty example without any
            # error. That produced 400 programs from a prompt containing neither, and a 0%
            # build rate that read like a result about the retrieval index. Fail on the
            # first row instead: this baseline has no meaning without the retrieved plan.
            raise SystemExit(
                f"empty retrieved plan for {row.get('sample_id')} (neighbour "
                f"{retrieved[0]['sample_id'] if retrieved else 'none'}). "
                f"dataset_root is {row.get('dataset_root', '<absent, defaults to \".\">')!r}; "
                f"the neighbour's training_ir.txt must be readable beneath it.")
        point_xyz = load_point_xyz(row, args.modality, args)
        prompt = build_program_prompt(row, args.modality, nn_ir, point_xyz=point_xyz)
        prepared.append((row, nn_ir, retrieved_ids[0] if retrieved_ids else "", prompt))

    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_jsonl, "w", encoding="utf-8", newline="\n") as f:
        for batch_start in tqdm(range(0, len(prepared), args.batch_size), desc=f"generate[{args.modality}/{args.retrieval_mode}]"):
            batch = prepared[batch_start: batch_start + args.batch_size]
            prompts = [p for _, _, _, p in batch]
            if args.batch_size == 1:
                predictions = [generate_text(lora_code, lora_code_tok, prompts[0], args.max_length, args.max_new_tokens, 0.0, 1.0, device)]
            else:
                predictions = generate_text_batch(lora_code, lora_code_tok, prompts, args.max_length, args.max_new_tokens, 0.0, 1.0, device)
            for (row, nn_ir, nn_sample_id, _), prediction in zip(batch, predictions):
                out = {
                    "sample_id": row.get("sample_id", ""),
                    "modality": args.modality,
                    "baseline": f"{args.retrieval_mode}-nn-ir",
                    "nn_sample_id": nn_sample_id,
                    "predicted_ir": nn_ir,
                    "reference_ir": read_text(row.get("ir_path", "")),
                    "prediction": prediction,
                    "reference": read_text(row.get("program_path", "")),
                }
                f.write(json.dumps(out, ensure_ascii=False) + "\n")
            f.flush()
    print("Wrote", args.output_jsonl)


if __name__ == "__main__":
    main()
