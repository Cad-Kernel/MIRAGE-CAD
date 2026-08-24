"""Stage 3: generate predicted_ir for 100 held-out image-query test samples.

Mirrors scratch/gen_predicted_ir_text100.py, parameterized for image modality.
"""
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

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

aligner, _, _, _ = load_alignment_checkpoint(Path("outputs/align_smoke5k_ep10/best.pt"), map_location="cpu")
aligner.to(device).eval()

payload = torch.load(Path("outputs/prior_image_5k/best.pt"), map_location="cpu", weights_only=False)
prior = LatentPrior(LatentPriorConfig(**payload["config"]))
prior.load_state_dict(payload["state_dict"], strict=True)
prior = prior.to(device).eval()

lora_ir_dir = Path("outputs/lora_ir_5k")
base = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-Coder-1.5B", trust_remote_code=True)
lora_model = PeftModel.from_pretrained(base, lora_ir_dir).to(device).eval()
prefix_adapter = load_soft_prefix_adapter(resolve_soft_prefix_path(lora_ir_dir, None), device=device, dtype=None)
tokenizer = AutoTokenizer.from_pretrained(lora_ir_dir, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

rows = read_jsonl(Path("data/smoke5k/test.jsonl"))[:100]
out_path = Path("outputs/lora_ir_5k/predicted_ir_image100.jsonl")
max_length = 2048
max_new_tokens = 1536

with open(out_path, "w", encoding="utf-8", newline="\n") as f:
    for i, row in enumerate(rows):
        img = load_image(row["iso_image_path"])
        z_m = aligner.encode_image([img], device)
        with torch.no_grad():
            z_ir_hat = prior(z_m)
        prompt = build_ir_prompt(row, "image", retrieved_ir=None, point_xyz=None)

        inputs = tokenizer(prompt, truncation=True, max_length=max_length, return_tensors="pt").to(device)
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
                max_new_tokens=max_new_tokens,
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
        if (i + 1) % 10 == 0:
            print(f"{i+1}/{len(rows)} done", flush=True)

print("Wrote", out_path)
