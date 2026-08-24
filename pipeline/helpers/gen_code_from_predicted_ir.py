"""Stage 4/4b inference: generate program.py from predicted_ir (or ground-truth
IR), any modality (text/image/point/step). Fully CLI-parameterized
generalization of scratch/gen_code_500_from_predicted_ir.py (which supported
only text/image/point) -- adds step, otherwise unchanged from the validated
5K recipe: same prompt construction (build_program_prompt), N=1 greedy
decoding, max_new_tokens=1536.
"""
import argparse
import json
import sys
from pathlib import Path

import torch
from tqdm import tqdm

sys.path.insert(0, ".")
from miragecad.data import read_jsonl, read_text
from miragecad.gen_prompts import build_program_prompt
from miragecad.point_sampling import load_point_cloud_sampled
from gen_scripts.run_miragecad import load_lm, load_tokenizer, generate_text, generate_text_batch


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--modality", choices=["text", "image", "point", "step"], required=True)
    # --- no-plan ablation ---------------------------------------------------
    # With --no-plan the prompt carries no Construction IR block, so there is no IR
    # file to iterate: rows come from --input-jsonl directly and --ir-jsonl is unused.
    # Pair it with a checkpoint trained the same way (train_program_lora.py --no-plan);
    # pointing it at the published Stage 4b checkpoint measures only that the model
    # expects a plan it is not being given.
    p.add_argument("--no-plan", action="store_true",
                   help="omit the plan block; iterate --input-jsonl instead of --ir-jsonl")
    p.add_argument("--ir-jsonl", type=Path, required=False,
                    help="predicted_ir jsonl (P1a-repaired) with a 'predicted_ir' field per row, "
                         "OR ground-truth IR eval (pass --use-ground-truth-ir instead).")
    p.add_argument("--use-ground-truth-ir", action="store_true",
                    help="Ignore --ir-jsonl's predicted_ir field and use each row's own "
                         "ir_path (ground-truth IR) instead -- for the Stage 4 upper-bound check.")
    p.add_argument("--output-jsonl", type=Path, required=True)
    p.add_argument("--lora-code-dir", type=Path, required=True)
    p.add_argument("--input-jsonl", type=Path, required=True)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--point-count", type=int, default=1024)
    p.add_argument("--max-length", type=int, default=1536)
    p.add_argument("--max-new-tokens", type=int, default=1536)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--repetition-penalty", type=float, default=None,
                    help="Passed to model.generate() to discourage greedy-decoding repetition loops "
                         "(e.g. degenerate repeated coordinate-list generations seen in point-cloud outputs). "
                         "Default None reproduces the original, unmodified generation behavior.")
    # E1, the observation-bypass ablation. See the note on the sibling plan script: the
    # evidence block enters both prompts, so this flag is only meaningful when the plans
    # were themselves generated with it. Default off keeps every published run intact.
    p.add_argument("--suppress-evidence", action="store_true",
                   help="E1: drop the query-derived evidence block from the CODE prompt.")
    p.add_argument("--batch-size", type=int, default=1,
                    help="Generate this many rows per model.generate() call instead of one at a time. "
                         "Default 1 reproduces the original, unmodified sequential behavior exactly.")
    args = p.parse_args()
    # --ir-jsonl became optional when --no-plan was added; without this the flag's
    # absence would surface much later as a confusing NoneType error.
    if args.ir_jsonl is None and not (args.no_plan or args.use_ground_truth_ir):
        p.error("--ir-jsonl is required unless --no-plan or --use-ground-truth-ir is given")
    return args


def main():
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    lora_code = load_lm("Qwen/Qwen2.5-Coder-1.5B", args.lora_code_dir, torch.bfloat16, device)
    lora_code_tok = load_tokenizer(args.lora_code_dir)

    test_rows = {r["sample_id"]: r for r in read_jsonl(args.input_jsonl)}
    if args.no_plan:
        # No plan means no IR file to walk; the test set itself is the row source.
        print("[NO-PLAN] plan block omitted; iterating --input-jsonl. Results are an "
              "ablation baseline, not a system result.")
        ir_rows = [{"sample_id": sid, "predicted_ir": None, "reference_ir": ""}
                   for sid in test_rows]
        if args.limit is not None:
            ir_rows = ir_rows[: args.limit]
    elif args.use_ground_truth_ir:
        ir_rows = [{"sample_id": sid, "predicted_ir": None, "reference_ir": ""} for sid in test_rows]
        if args.limit is not None:
            ir_rows = ir_rows[: args.limit]
    else:
        ir_rows = read_jsonl(args.ir_jsonl)
        if args.limit is not None:
            ir_rows = ir_rows[: args.limit]

    # Build the (sid, prompt, out_stub) list up front so batching just slices
    # this list -- identical prompt construction to the original per-row loop,
    # only the generation call is grouped.
    items = []
    for ir_row in ir_rows:
        sid = ir_row["sample_id"]
        row = test_rows.get(sid)
        if row is None:
            continue
        if args.no_plan:
            ir_text = None
        elif args.use_ground_truth_ir:
            if "ir_path" not in row:
                raise SystemExit(
                    f"--use-ground-truth-ir needs a reference plan, and row {sid} has no "
                    f"ir_path. External data has no reference plan at all, so this flag "
                    f"does not apply to it.")
            ir_text = read_text(row["ir_path"])
        else:
            ir_text = ir_row["predicted_ir"]
        point_xyz = None
        if args.modality == "point":
            point_xyz = load_point_cloud_sampled(row["point_path"], point_count=args.point_count, sampling="fps", seed=args.seed)
        prompt = build_program_prompt(row, args.modality, ir_text or "", point_xyz=point_xyz,
                                      include_plan=not args.no_plan,
                                      evidence_text="" if args.suppress_evidence else None)
        out_stub = {
            "sample_id": sid,
            "modality": args.modality,
            "predicted_ir": ir_text,
            # External rows carry no reference plan, and reference_ir only ever feeds
            # metrics that compare against one. Missing is a legitimate state, not an
            # error -- the line below already treats program_path that way.
            "reference_ir": ir_row.get("reference_ir", "") or read_text(row.get("ir_path", "")),
            "reference": read_text(row.get("program_path", "")),
        }
        items.append((prompt, out_stub))

    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_jsonl, "w", encoding="utf-8", newline="\n") as f:
        for batch_start in tqdm(range(0, len(items), args.batch_size), desc=f"gen_code[{args.modality}]"):
            batch = items[batch_start: batch_start + args.batch_size]
            prompts = [prompt for prompt, _ in batch]
            if args.batch_size == 1:
                predictions = [generate_text(lora_code, lora_code_tok, prompts[0], args.max_length, args.max_new_tokens, 0.0, 1.0, device, repetition_penalty=args.repetition_penalty)]
            else:
                predictions = generate_text_batch(lora_code, lora_code_tok, prompts, args.max_length, args.max_new_tokens, 0.0, 1.0, device, repetition_penalty=args.repetition_penalty)
            for (_, out_stub), prediction in zip(batch, predictions):
                out = dict(out_stub)
                out["prediction"] = prediction
                f.write(json.dumps(out, ensure_ascii=False) + "\n")
            f.flush()
    print("Wrote", args.output_jsonl)


if __name__ == "__main__":
    main()
