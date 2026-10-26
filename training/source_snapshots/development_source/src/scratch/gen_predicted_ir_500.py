"""Stage 3: generate predicted_ir for 500 held-out test samples, any modality.

500-sample formal-eval version of gen_predicted_ir_{point,text,image}100.py.
Fixed config, no changes from the validated 100-sample recipe: same
alignment/prior checkpoints, same lora_ir_5k, same max_new_tokens=1536, N=1 greedy.
"""
import argparse
import json
import sys
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, ".")
from miragecad.data import read_jsonl, read_text, load_image
from miragecad.gen_prompts import build_ir_prompt
from miragecad.soft_prefix import load_soft_prefix_adapter, resolve_soft_prefix_path
from miragecad.latent_prior import LatentPrior, LatentPriorConfig
from miragecad.models import load_alignment_checkpoint
from miragecad.point_sampling import load_point_cloud_sampled


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--modality", choices=["text", "image", "point"], required=True)
    p.add_argument("--prior-checkpoint", type=Path, required=True)
    p.add_argument("--output-jsonl", type=Path, required=True)
    p.add_argument("--limit", type=int, default=500)
    p.add_argument("--alignment-checkpoint", type=Path, default=Path("outputs/align_smoke5k_ep10/best.pt"))
    p.add_argument("--lora-ir-dir", type=Path, default=Path("outputs/lora_ir_5k"))
    p.add_argument("--input-jsonl", type=Path, default=Path("data/smoke5k/test.jsonl"))
    p.add_argument("--point-count", type=int, default=1024)
    p.add_argument("--max-length", type=int, default=2048)
    p.add_argument("--max-new-tokens", type=int, default=1536)
    return p.parse_args()


def main():
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    aligner, _, _, _ = load_alignment_checkpoint(args.alignment_checkpoint, map_location="cpu")
    aligner.to(device).eval()

    payload = torch.load(args.prior_checkpoint, map_location="cpu", weights_only=False)
    prior = LatentPrior(LatentPriorConfig(**payload["config"]))
    prior.load_state_dict(payload["state_dict"], strict=True)
    prior = prior.to(device).eval()

    base = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-Coder-1.5B", trust_remote_code=True)
    lora_model = PeftModel.from_pretrained(base, args.lora_ir_dir).to(device).eval()
    prefix_adapter = load_soft_prefix_adapter(resolve_soft_prefix_path(args.lora_ir_dir, None), device=device, dtype=None)
    tokenizer = AutoTokenizer.from_pretrained(args.lora_ir_dir, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    rows = read_jsonl(args.input_jsonl)[: args.limit]
    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)

    with open(args.output_jsonl, "w", encoding="utf-8", newline="\n") as f:
        for i, row in enumerate(rows):
            if args.modality == "text":
                z_m = aligner.encode_text([row.get("text", "")], device)
            elif args.modality == "image":
                z_m = aligner.encode_image([load_image(row["iso_image_path"])], device)
            elif args.modality == "point":
                pts = load_point_cloud_sampled(row["point_path"], point_count=args.point_count, sampling="fps", seed=42)
                z_m = aligner.encode_point(torch.tensor(pts[None], dtype=torch.float32).to(device))
            with torch.no_grad():
                z_ir_hat = prior(z_m)
            prompt = build_ir_prompt(row, args.modality, retrieved_ir=None, point_xyz=None)

            inputs = tokenizer(prompt, truncation=True, max_length=args.max_length, return_tensors="pt").to(device)
            text_embeds = lora_model.get_input_embeddings()(inputs["input_ids"])
            soft_prefix = prefix_adapter(z_ir_hat.detach()).to(device=text_embeds.device, dtype=text_embeds.dtype)
            inputs_embeds = torch.cat([soft_prefix, text_embeds], dim=1)
            prefix_mask = torch.ones(inputs["attention_mask"].shape[0], soft_prefix.shape[1],
                                      dtype=inputs["attention_mask"].dtype, device=device)
            attention_mask = torch.cat([prefix_mask, inputs["attention_mask"]], dim=1)
            with torch.no_grad():
                gen = lora_model.generate(
                    inputs_embeds=inputs_embeds,
                    attention_mask=attention_mask,
                    max_new_tokens=args.max_new_tokens,
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id,
                )
            predicted_ir = tokenizer.decode(gen[0], skip_special_tokens=True).strip()

            out = {
                "sample_id": row.get("sample_id", ""),
                "predicted_ir": predicted_ir,
                "reference_ir": read_text(row.get("ir_path", "")),
                "program_path": row.get("program_path", ""),
            }
            f.write(json.dumps(out, ensure_ascii=False) + "\n")
            if (i + 1) % 50 == 0:
                print(f"{i+1}/{len(rows)} done", flush=True)

    print("Wrote", args.output_jsonl)


if __name__ == "__main__":
    main()
