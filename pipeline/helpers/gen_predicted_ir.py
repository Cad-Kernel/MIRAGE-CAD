"""Stage 3 inference: generate predicted_ir for a set of rows, any modality
(text/image/point/step). Fully CLI-parameterized generalization of
scratch/gen_predicted_ir_500.py (which supported only text/image/point) --
used for both the Stage 4b train-subset generation and the final test-set
generation, so there is one script instead of several near-duplicate
hardcoded ones. No behavior change versus the validated 5K recipe: same
prompt construction (build_ir_prompt, no retrieval), same soft-prefix
handling, N=1 greedy decoding.
"""
import argparse
import json
import sys
from pathlib import Path

import torch
from peft import PeftModel
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, ".")
from miragecad.data import (
    collate_step_brep_batch,
    load_image,
    load_step_brep_tensors,
    read_jsonl,
    read_text,
)
from miragecad.gen_prompts import build_ir_prompt
from miragecad.soft_prefix import load_soft_prefix_adapter, resolve_soft_prefix_path
from miragecad.latent_prior import LatentPrior, LatentPriorConfig
from miragecad.models import load_alignment_checkpoint
from miragecad.point_sampling import load_point_cloud_sampled


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--modality", choices=["text", "image", "point", "step"], required=True)
    p.add_argument("--alignment-checkpoint", type=Path, required=True)
    p.add_argument("--prior-checkpoint", type=Path, required=True)
    p.add_argument("--lora-ir-dir", type=Path, required=True)
    p.add_argument("--input-jsonl", type=Path, required=True,
                    help="train.jsonl (Stage 4b mix generation) or test.jsonl (formal eval)")
    p.add_argument("--output-jsonl", type=Path, required=True)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--start", type=int, default=0, help="Skip the first N rows (for train-subset sampling).")
    p.add_argument("--require-split", choices=["train", "val", "test"], default=None,
                    help="If set, abort if any selected row's manifest split does not match "
                         "(safety gate for the Stage 4b train-subset case -- never accidentally "
                         "generate 'training' predicted_ir from val/test rows).")
    p.add_argument("--point-count", type=int, default=1024)
    p.add_argument("--max-length", type=int, default=2048)
    p.add_argument("--max-new-tokens", type=int, default=1536)
    p.add_argument("--seed", type=int, default=42)
    # --- N1: where the prefix comes from -------------------------------------
    # Default `prior` reproduces the deployed pipeline bit-for-bit; nothing below
    # changes behaviour unless a non-default value is passed.
    p.add_argument("--prefix-source",
                   choices=["prior", "oracle_ir", "zero_prefix", "zero_latent", "shuffled"],
                   default="prior",
                   help="prior: pi_m(z_m), the deployed path. "
                        "oracle_ir: f_ir(reference IR) -- upper bound on the prefix path, "
                        "READS GROUND TRUTH so its output must never enter training. "
                        "zero_prefix: bypass Psi entirely, feed K all-zero embeddings. "
                        "zero_latent: Psi(0), which is NOT zero -- Psi starts with a "
                        "LayerNorm, so a zero input yields a learned constant prefix. "
                        "shuffled: another sample's Psi(pi_m(z_m)) -- a wrong but "
                        "same-distribution signal, the strongest control.")
    p.add_argument("--shuffle-seed", type=int, default=1234,
                   help="Permutation seed for --prefix-source shuffled.")
    # --- N1b: sample several plans per query ---------------------------------
    p.add_argument("--num-plans", type=int, default=1,
                   help="1 = greedy, bit-identical to previous behaviour. >1 switches to "
                        "temperature sampling and emits one output row per plan.")
    p.add_argument("--temperature", type=float, default=1.0,
                   help="Only used when --num-plans > 1.")
    p.add_argument("--top-p", type=float, default=0.95,
                   help="Only used when --num-plans > 1.")
    p.add_argument("--batch-size", type=int, default=1,
                    help="Generate this many rows per model.generate() call instead of one at a time. "
                         "Default 1 reproduces the original, unmodified sequential behavior exactly.")
    # --- point-cloud observation block ---------------------------------------
    # This script has always built the prompt with point_xyz=None, so for the point
    # modality get_query_evidence() falls back to the constant string "Point cloud
    # query." instead of the point_count/bbox/ratios/centroid/std/PCA block. Stage 3
    # and 3b TRAINING populate that block (train_soft_prefix_ir.py:190), and so does
    # the sibling program-generation script (gen_code_from_predicted_ir.py:79) -- so
    # this is a train/inference mismatch specific to the plan stage, and the points
    # are already loaded a few lines below in encode_query().
    #
    # Default stays `off` on purpose: every published 25K point-cloud number was
    # produced that way, and silently changing it would invalidate PROVENANCE.md.
    # Use `on` to match training; 27_point_evidence_fix.sh runs the A/B.
    p.add_argument("--point-evidence", choices=["off", "on"], default="off",
                   help="off (default): reproduce all published runs -- point prompts get the "
                        "constant placeholder. on: populate c_obs from the sampled points, "
                        "matching what Stage 3/3b training saw. No effect for other modalities.")
    # E1, the observation-bypass ablation. Suppressing here is NOT the same as
    # --point-evidence off: that one silences the point statistics only, while this
    # drops the whole "Query-derived evidence" block for every modality, exactly as
    # happens naturally for image queries, whose evidence string is empty.
    #
    # It must be paired with the same flag on gen_code_from_predicted_ir.py. The block
    # enters BOTH prompts (gen_prompts.py:192 and :241), so suppressing one side leaves
    # a plan that was still generated with the observation present, which is not a
    # plan-only condition at all.
    #
    # Default off, so every path in PROVENANCE.md keeps reproducing its published run.
    p.add_argument("--suppress-evidence", action="store_true",
                   help="E1: drop the query-derived evidence block from the PLAN prompt. "
                        "Pair with the same flag on the code-generation script.")
    return p.parse_args()


def encode_query(aligner, modality: str, row: dict, args, device):
    """Return (z_m, point_xyz). point_xyz is the sampled array for the point modality
    and None otherwise; the caller decides whether it reaches the prompt."""
    if modality == "text":
        return aligner.encode_text([row.get("text", "")], device), None
    if modality == "image":
        return aligner.encode_image([load_image(row["iso_image_path"])], device), None
    if modality == "point":
        pts = load_point_cloud_sampled(row["point_path"], point_count=args.point_count, sampling="fps", seed=args.seed)
        return aligner.encode_point(torch.tensor(pts[None], dtype=torch.float32).to(device)), pts
    if modality == "step":
        tensors = load_step_brep_tensors(row["step_feature_path"], strict=True)
        batch = collate_step_brep_batch([tensors])
        return aligner.encode_step({k: v.to(device) for k, v in batch.items()}), None
    raise ValueError(f"Unknown modality: {modality!r}")


def main():
    args = parse_args()
    torch.manual_seed(args.seed)
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

    all_rows = read_jsonl(args.input_jsonl)
    rows = all_rows[args.start:]
    if args.limit is not None:
        rows = rows[: args.limit]
    if args.require_split:
        bad = [r["sample_id"] for r in rows if r.get("split", args.require_split) != args.require_split]
        if bad:
            raise SystemExit(
                f"--require-split={args.require_split} but {len(bad)} selected rows have a different "
                f"split (e.g. {bad[:5]}). Refusing to continue -- check --input-jsonl/--start/--limit."
            )

    tokenizer.padding_side = "left"

    # ---------------------------------------------------------------------
    # N1 setup. Everything here is skipped in the default `prior` mode.
    # ---------------------------------------------------------------------
    if args.prefix_source != "prior":
        print(f"[ABLATION] --prefix-source={args.prefix_source}: this run does NOT "
              f"reproduce the deployed pipeline. Output rows are tagged "
              f"ablation_only=true and must not be used as generation results.")
    if args.prefix_source == "oracle_ir":
        print("[ABLATION] oracle_ir READS THE GROUND-TRUTH IR. Its output must never "
              "enter any training set.")

    shuffled_latents = None
    if args.prefix_source == "shuffled":
        # Must be a GLOBAL permutation computed up front. Permuting within a batch is
        # the identity at --batch-size 1, and at larger batch sizes only swaps among a
        # handful of adjacent rows -- either way it would silently understate the
        # control. So encode every row once, permute with a fixed seed, and assert that
        # no row kept its own latent.
        print(f"[ABLATION] pre-encoding {len(rows)} rows for a global shuffle "
              f"(seed {args.shuffle_seed}) ...")
        with torch.no_grad():
            zs = [prior(encode_query(aligner, args.modality, r, args, device)[0]) for r in rows]
        z_all = torch.cat(zs, dim=0)
        g = torch.Generator().manual_seed(args.shuffle_seed)
        n = z_all.shape[0]
        if n < 2:
            raise SystemExit("--prefix-source shuffled needs at least 2 rows.")
        perm = torch.randperm(n, generator=g)
        # Derange: rotate any fixed points so nobody receives their own latent.
        fixed = (perm == torch.arange(n)).nonzero(as_tuple=True)[0]
        for i in fixed.tolist():
            j = (i + 1) % n
            perm[i], perm[j] = perm[j].clone(), perm[i].clone()
        assert not bool((perm == torch.arange(n)).any()), "shuffle left a fixed point"
        shuffled_latents = z_all[perm]
        print(f"[ABLATION] shuffle ready; 0 of {n} rows kept their own latent.")

    if args.num_plans > 1:
        print(f"[N1b] sampling {args.num_plans} plans per query at temperature "
              f"{args.temperature}, top-p {args.top_p}. One output row per plan.")

    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_jsonl, "w", encoding="utf-8", newline="\n") as f:
        for batch_start in tqdm(range(0, len(rows), args.batch_size), desc=f"gen_predicted_ir[{args.modality}]"):
            batch_rows = rows[batch_start: batch_start + args.batch_size]

            encoded = [encode_query(aligner, args.modality, row, args, device) for row in batch_rows]
            z_m = torch.cat([z for z, _ in encoded], dim=0)
            with torch.no_grad():
                z_ir_hat = prior(z_m)

            # point_xyz reaches the prompt only under --point-evidence on; see the
            # argparse note. `off` keeps every published run reproducible.
            pts_for_prompt = ([p for _, p in encoded] if args.point_evidence == "on"
                              else [None] * len(batch_rows))
            ev = "" if args.suppress_evidence else None      # None means "derive it"
            prompts = [build_ir_prompt(row, args.modality, evidence_text=ev,
                                       retrieved_ir=None, point_xyz=pts)
                       for row, pts in zip(batch_rows, pts_for_prompt)]
            inputs = tokenizer(prompts, truncation=True, max_length=args.max_length, padding=True, return_tensors="pt").to(device)
            text_embeds = lora_model.get_input_embeddings()(inputs["input_ids"])

            # --- N1: choose what feeds the prefix ---------------------------
            with torch.no_grad():
                if args.prefix_source == "prior":
                    soft_prefix = prefix_adapter(z_ir_hat.detach())
                elif args.prefix_source == "oracle_ir":
                    ir_texts = [read_text(r.get("ir_path", "")) for r in batch_rows]
                    z_true = aligner.encode_ir(ir_texts, device)
                    soft_prefix = prefix_adapter(z_true.detach())
                elif args.prefix_source == "zero_latent":
                    # Psi(0) is a learned constant, not zero: Psi begins with a
                    # LayerNorm, whose output for an all-zero input is its own bias.
                    soft_prefix = prefix_adapter(torch.zeros_like(z_ir_hat))
                elif args.prefix_source == "shuffled":
                    idx = slice(batch_start, batch_start + len(batch_rows))
                    soft_prefix = prefix_adapter(shuffled_latents[idx].to(device))
                elif args.prefix_source == "zero_prefix":
                    # Bypass Psi altogether -- K genuinely zero embeddings. This is
                    # what "removing the latent signal" means; zero_latent is not it.
                    soft_prefix = torch.zeros(
                        text_embeds.shape[0], prefix_adapter.config.prefix_len,
                        prefix_adapter.config.hidden_size, device=device)
                else:
                    raise SystemExit(f"unhandled --prefix-source {args.prefix_source}")
            soft_prefix = soft_prefix.to(device=text_embeds.device, dtype=text_embeds.dtype)

            inputs_embeds = torch.cat([soft_prefix, text_embeds], dim=1)
            prefix_mask = torch.ones(inputs["attention_mask"].shape[0], soft_prefix.shape[1],
                                      dtype=inputs["attention_mask"].dtype, device=device)
            attention_mask = torch.cat([prefix_mask, inputs["attention_mask"]], dim=1)

            K = max(1, args.num_plans)
            gen_kwargs = dict(max_new_tokens=args.max_new_tokens,
                              pad_token_id=tokenizer.eos_token_id)
            if K > 1:
                gen_kwargs.update(do_sample=True, temperature=args.temperature,
                                  top_p=args.top_p, num_return_sequences=K)
            else:
                gen_kwargs.update(do_sample=False)
            with torch.no_grad():
                gen = lora_model.generate(inputs_embeds=inputs_embeds,
                                          attention_mask=attention_mask, **gen_kwargs)

            # generate() returns sequences GROUPED BY INPUT ROW:
            #   [row0_plan0 ... row0_planK-1, row1_plan0, ...]
            # so zip(batch_rows, gen) silently misaligns as soon as K > 1. Index
            # explicitly instead.
            assert gen.shape[0] == len(batch_rows) * K, (
                f"expected {len(batch_rows)}*{K} sequences, got {gen.shape[0]}")
            for row_i, row in enumerate(batch_rows):
                for plan_i in range(K):
                    gen_row = gen[row_i * K + plan_i]
                    predicted_ir = tokenizer.decode(gen_row, skip_special_tokens=True).strip()
                    out = {
                        "sample_id": row.get("sample_id", ""),
                        "modality": args.modality,
                        "predicted_ir": predicted_ir,
                        "reference_ir": read_text(row.get("ir_path", "")),
                        "program_path": row.get("program_path", ""),
                    }
                    if K > 1:
                        out["plan_index"] = plan_i
                        out["plan_temperature"] = args.temperature
                        out["plan_top_p"] = args.top_p
                    if args.prefix_source != "prior":
                        out["prefix_source"] = args.prefix_source
                        out["ablation_only"] = True
                    f.write(json.dumps(out, ensure_ascii=False) + "\n")
            f.flush()

    print("Wrote", args.output_jsonl)


if __name__ == "__main__":
    main()
