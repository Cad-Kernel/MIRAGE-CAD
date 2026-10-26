"""B1 inference: generate a program from the construction latent, with no plan text.

WHY A SEPARATE SCRIPT. Training reuses train_soft_prefix_ir.py with --target program,
because the machinery there is identical and only the prompt and target differ. Inference
cannot reuse either sibling as cleanly:

  * gen_code_from_predicted_ir.py has no soft-prefix support at all -- the deployed code
    decoder never receives one.
  * gen_predicted_ir.py has the prefix logic but its output schema is IR-shaped
    (predicted_ir / reference_ir), and the gate and geometry harnesses downstream read
    `prediction`. Bending it would leave one script emitting two incompatible schemas.

So this mirrors gen_predicted_ir.py's prefix path exactly -- same encode_query, same
adapter loading, same concat-in-embedding-space, same attention-mask extension -- and emits
gen_code_from_predicted_ir.py's schema, so evaluate_execution.ps1 and
evaluate_geometry_nbest.ps1 consume it unchanged.

WHAT B1 IS. The latent conditions the CODE decoder through a soft prefix; the plan block and
its instruction line are both absent; the query-derived observation block is present exactly
as the deployed decoder receives it. B1 therefore differs from the deployed arm in one
respect only, which is what makes A1-versus-A3 interpretable.

GREEDY, N = 1, no repair, to match every arm it will be compared against.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from miragecad.data import (
    collate_step_brep_batch,
    load_image,
    load_step_brep_tensors,
    read_jsonl,
    read_text,
)
from miragecad.gen_prompts import build_program_prompt
from miragecad.latent_prior import LatentPrior, LatentPriorConfig
from miragecad.models import load_alignment_checkpoint
from miragecad.point_sampling import load_point_cloud_sampled
from miragecad.soft_prefix import load_soft_prefix_adapter, resolve_soft_prefix_path


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--modality", choices=["text", "image", "point", "step"], required=True)
    p.add_argument("--alignment-checkpoint", type=Path, required=True)
    p.add_argument("--prior-checkpoint", type=Path, required=True)
    p.add_argument("--b1-dir", type=Path, required=True,
                   help="Output directory of the --target program run: LoRA adapter plus "
                        "soft_prefix.pt.")
    p.add_argument("--input-jsonl", type=Path, required=True)
    p.add_argument("--output-jsonl", type=Path, required=True)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--point-count", type=int, default=1024)
    p.add_argument("--max-length", type=int, default=1536)
    p.add_argument("--max-new-tokens", type=int, default=1536)
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--model-name", default="Qwen/Qwen2.5-Coder-1.5B")
    # Kept for parity with the sibling scripts: every published point-cloud run passed the
    # plan prompt a constant rather than the statistics. B1 has no plan prompt, so this only
    # affects whether the CODE prompt sees the point statistics -- which the deployed code
    # decoder always does, hence the default.
    p.add_argument("--point-evidence", choices=["off", "on"], default="on",
                   help="on (default): populate the point statistics, matching what the "
                        "deployed code decoder receives.")
    return p.parse_args()


def encode_query(aligner, modality: str, row: dict, args, device):
    """Identical to gen_predicted_ir.py's, so the latent B1 sees is the latent A3 sees."""
    if modality == "text":
        return aligner.encode_text([row.get("text", "")], device), None
    if modality == "image":
        return aligner.encode_image([load_image(row["iso_image_path"])], device), None
    if modality == "point":
        pts = load_point_cloud_sampled(row["point_path"], point_count=args.point_count,
                                       sampling="fps", seed=args.seed)
        return aligner.encode_point(
            torch.tensor(pts[None], dtype=torch.float32).to(device)), pts
    if modality == "step":
        tensors = load_step_brep_tensors(row["step_feature_path"], strict=True)
        batch = collate_step_brep_batch([tensors])
        return aligner.encode_step({k: v.to(device) for k, v in batch.items()}), None
    raise ValueError(f"Unknown modality: {modality!r}")


def main() -> int:
    args = parse_args()
    torch.manual_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    aligner, _, _, _ = load_alignment_checkpoint(args.alignment_checkpoint, map_location="cpu")
    aligner.to(device).eval()

    payload = torch.load(args.prior_checkpoint, map_location="cpu", weights_only=False)
    prior = LatentPrior(LatentPriorConfig(**payload["config"]))
    prior.load_state_dict(payload["state_dict"], strict=True)
    prior = prior.to(device).eval()

    base = AutoModelForCausalLM.from_pretrained(args.model_name, trust_remote_code=True)
    lora_model = PeftModel.from_pretrained(base, args.b1_dir).to(device).eval()
    prefix_adapter = load_soft_prefix_adapter(
        resolve_soft_prefix_path(args.b1_dir, None), device=device, dtype=None)
    tokenizer = AutoTokenizer.from_pretrained(args.b1_dir, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"       # generation with a batch needs left padding

    rows = read_jsonl(args.input_jsonl)
    if args.limit:
        rows = rows[: args.limit]
    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)

    n_empty_program = 0
    with open(args.output_jsonl, "w", encoding="utf-8", newline="\n") as f_out:
        for start in tqdm(range(0, len(rows), args.batch_size),
                          desc=f"gen_b1[{args.modality}]"):
            batch_rows = rows[start: start + args.batch_size]

            zs, pts_all = [], []
            for row in batch_rows:
                z_m, pts = encode_query(aligner, args.modality, row, args, device)
                zs.append(z_m)
                pts_all.append(pts)
            with torch.no_grad():
                z_ir_hat = prior(torch.cat(zs, dim=0))

            pts_for_prompt = (pts_all if args.point_evidence == "on"
                              else [None] * len(batch_rows))
            # No plan block, no plan instruction line, observation block present.
            prompts = [build_program_prompt(row, args.modality, "", point_xyz=pts,
                                            include_plan=False)
                       for row, pts in zip(batch_rows, pts_for_prompt)]

            inputs = tokenizer(prompts, truncation=True, max_length=args.max_length,
                               padding=True, return_tensors="pt").to(device)
            text_embeds = lora_model.get_input_embeddings()(inputs["input_ids"])
            with torch.no_grad():
                soft_prefix = prefix_adapter(z_ir_hat.detach())
            soft_prefix = soft_prefix.to(device=text_embeds.device, dtype=text_embeds.dtype)

            inputs_embeds = torch.cat([soft_prefix, text_embeds], dim=1)
            prefix_mask = torch.ones(inputs["attention_mask"].shape[0],
                                     soft_prefix.shape[1],
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
            for row, gen_row in zip(batch_rows, gen):
                prediction = tokenizer.decode(gen_row, skip_special_tokens=True).strip()
                if not prediction:
                    n_empty_program += 1
                f_out.write(json.dumps({
                    "sample_id": row.get("sample_id", ""),
                    "modality": args.modality,
                    # Schema matches gen_code_from_predicted_ir.py so the gate and geometry
                    # harnesses read it unchanged. predicted_ir is empty BY CONSTRUCTION:
                    # B1 produces no plan, and an empty string here is the honest record of
                    # that rather than a missing field.
                    "predicted_ir": "",
                    "prediction": prediction,
                    "reference": read_text(row.get("program_path", "")),
                    "arm": "B1_direct_latent",
                }, ensure_ascii=False) + "\n")

    print(f"Wrote {args.output_jsonl}")
    if n_empty_program:
        print(f"WARNING: {n_empty_program} rows produced an empty program.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
