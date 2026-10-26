"""Read-only CPU token audit using the real historical dataset classes.

No LM, latent encoder, Trainer, optimizer or inference is constructed. A1E's unused
latent field is a one-element dummy; only the actual dataset's token/labels path
is audited. Files are written exclusively to a new audit output directory.
"""
from __future__ import annotations

import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

import argparse
import hashlib
import importlib.util
import json
import platform
import shutil
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class RecordingTokenizer:
    def __init__(self, base):
        self.base = base
        self.calls = []

    def __getattr__(self, key):
        return getattr(self.base, key)

    def __call__(self, text, **kwargs):
        result = self.base(text, **kwargs)
        self.calls.append(result["input_ids"])
        return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=Path("__RUN_SOURCE_ROOT__"))
    parser.add_argument("--review-root", type=Path, default=Path("__EVIDENCE_SOURCE_ROOT__"))
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    root = args.source_root.resolve()
    review = args.review_root.resolve()
    out = args.out or review / "09_cpu_preparation/review01_dataset_v1"
    out = out.resolve()
    require(out.is_relative_to(review / "09_cpu_preparation"), "Output must stay inside new CPU preparation package")
    require(not out.exists(), "Do not overwrite an existing audit; choose a new version")
    os.chdir(root)
    sys.path.insert(0, str(root))

    import numpy as np
    import torch
    import transformers
    import peft
    from huggingface_hub import snapshot_download
    from transformers import AutoTokenizer
    from miragecad import data, gen_prompts

    torch.set_num_threads(2)
    require(not torch.cuda.is_initialized(), "CUDA unexpectedly initialized")
    historical = review / "07/support/review01_lineage/train_soft_prefix_ir_recorded_source.py"
    b_source = root / "train_program_lora.py"
    a_mod = load_module("review01_historical_a1e_token_audit", historical)
    b_mod = load_module("review01_historical_b2p_token_audit", b_source)
    train = root / "data/25k/train.jsonl"
    pred = root / "data/25k/train_b2pred_step.jsonl"
    source_hashes = {"A1E": sha(historical), "B2P": sha(b_source)}
    data_hashes = {"train": sha(train), "b2p_train": sha(pred)}
    recorded = []
    for seed in range(1, 5):
        p = review / f"07/support/review01_lineage/cag_seed_{seed}_actuals.json"
        rec = json.loads(p.read_text(encoding="utf-8"))
        require(rec["script_hashes"]["gen_scripts/train_soft_prefix_ir.py"] == source_hashes["A1E"], f"A1E source mismatch seed {seed}")
        require(rec["script_hashes"]["train_program_lora.py"] == source_hashes["B2P"], f"B2P source mismatch seed {seed}")
        require(rec["inputs"]["train_sha256"] == data_hashes["train"], f"train hash mismatch seed {seed}")
        require(rec["inputs"]["b2p_train_sha256"] == data_hashes["b2p_train"], f"pred train hash mismatch seed {seed}")
        recorded.append({"seed": seed, "record_sha256": sha(p), "source_and_training_hash_match": True})

    base_rows = data.read_jsonl(train)
    pred_rows = data.read_jsonl(pred)
    require(len(base_rows) == len(pred_rows) == 25000, "Unexpected training rows")
    ids = [r["sample_id"] for r in base_rows]
    require(len(set(ids)) == 25000, "Duplicate sample IDs")
    for a, b in zip(base_rows, pred_rows):
        require(a["sample_id"] == b["sample_id"], "ID/order mismatch")
        for key in a.keys() | b.keys():
            if key not in {"ir_text_for_program", "predicted_ir"}:
                require((key in a) == (key in b) and a.get(key) == b.get(key), f"Source field differs: {a['sample_id']} {key}")

    snapshot = Path(snapshot_download("Qwen/Qwen2.5-Coder-1.5B", local_files_only=True))
    tok = AutoTokenizer.from_pretrained(snapshot, local_files_only=True)
    eos_ids = tok(tok.eos_token, add_special_tokens=False)["input_ids"]
    require(eos_ids == [tok.eos_token_id], "EOS is not one token; classification must be revised")
    a_tok, b_tok = RecordingTokenizer(tok), RecordingTokenizer(tok)
    examples = []
    programs = []
    for row in base_rows:
        program = Path(row["program_path"])
        require(program.is_file(), f"Missing program: {program}")
        text = data.read_text(program).strip()
        require(bool(text), f"Empty program: {program}")
        examples.append(a_mod.IRExample(str(row["sample_id"]), a_mod.build_program_prompt(row, "step", "", point_xyz=None, include_plan=False), text, np.zeros(1, dtype=np.float32)))
        programs.append({"sample_id": row["sample_id"], "source_path": str(program), "sha256": sha(program)})
    a_ds = a_mod.SoftPrefixIRDataset(examples, a_tok, 1536)
    b_ds = b_mod.ProgramDataset(pred_rows, b_tok, target="program", max_length=1536, modality="step", include_plan=True)
    require(len(a_ds) == len(b_ds) == 25000, "Dataset row loss")

    out.mkdir(parents=True)
    snapshots = out / "source_snapshots"
    snapshots.mkdir()
    files_to_copy = {"a1e_historical.py": historical, "b2p_recorded_hash_match.py": b_source,
                     "gen_prompts.py": Path(gen_prompts.__file__), "data.py": Path(data.__file__)}
    for label, path in files_to_copy.items():
        shutil.copyfile(path, snapshots / label)
    tokenizer_dir = out / "tokenizer_snapshot"
    tokenizer_dir.mkdir()
    for name in ("tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt", "special_tokens_map.json", "added_tokens.json", "config.json"):
        p = snapshot / name
        if p.is_file():
            shutil.copyfile(p, tokenizer_dir / name)
    shutil.copyfile(train, out / "train_source.jsonl")
    shutil.copyfile(pred, out / "b2p_train_source.jsonl")
    (out / "program_source_manifest.jsonl").write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in programs), encoding="utf-8")

    stats = {arm: {"rows": 0, "complete": 0, "eos_only": 0, "partial_body": 0, "no_target": 0,
                   "body_tokens": 0, "body_lost": 0, "prompt_lengths": [], "body_losses": []} for arm in ("A1E", "B2P")}
    with (out / "per_sample_tokens_labels.jsonl").open("x", encoding="utf-8") as log:
        for i in range(25000):
            for arm, ds, recording in (("A1E", a_ds, a_tok), ("B2P", b_ds, b_tok)):
                recording.calls.clear()
                item = ds[i]  # Real unmodified class, actual __getitem__.
                require(len(recording.calls) == 2, f"Unexpected tokenizer path: {arm}")
                prompt_ids, target_ids = recording.calls
                require(target_ids[-1] == tok.eos_token_id, "Appended EOS not final")
                inp, labels = item["input_ids"].tolist(), item["labels"].tolist()
                plen, tlen = len(prompt_ids), len(target_ids)
                kept = max(0, min(tlen, 1536 - plen))
                require(inp == (prompt_ids + target_ids)[:1536], f"Input packing differs {arm}/{i}")
                require(labels == [-100] * min(plen, len(inp)) + target_ids[:kept], f"Labels differ {arm}/{i}")
                require(item["attention_mask"].tolist() == [1] * len(inp), "Unexpected attention mask")
                require(sum(v != -100 for v in labels) == kept, "Supervision count mismatch")
                body_total = tlen - 1
                body_kept = min(kept, body_total)
                body_lost = body_total - body_kept
                bucket = "no_target" if kept == 0 else "partial_body" if body_lost else "eos_only" if kept < tlen else "complete"
                s = stats[arm]
                s["rows"] += 1
                s[bucket] += 1
                s["body_tokens"] += body_total
                s["body_lost"] += body_lost
                s["prompt_lengths"].append(plen)
                if body_lost:
                    s["body_losses"].append(body_lost)
                log.write(json.dumps({"sample_id": ids[i], "index": i, "arm": arm, "bucket": bucket,
                                      "prompt_tokens": plen, "body_tokens": body_total, "target_tokens_including_eos": tlen,
                                      "supervised_tokens": kept, "body_tokens_lost": body_lost, "eos_retained": kept == tlen,
                                      "input_ids_sha256": digest(inp), "labels_sha256": digest(labels),
                                      "prompt_tokens_sha256": digest(prompt_ids), "target_tokens_sha256": digest(target_ids)}, ensure_ascii=False) + "\n")
            if (i + 1) % 1000 == 0:
                print(f"real datasets audited {i+1}/25000 paired rows; CPU only", flush=True)

    claude = json.loads((review / "08_claude/support/trunc_audit_v2_results.json").read_text(encoding="utf-8"))
    for arm, s in stats.items():
        s["median_prompt_tokens"] = statistics.median(s.pop("prompt_lengths"))
        losses = sorted(s.pop("body_losses"))
        s["body_loss_median"] = statistics.median(losses) if losses else 0
        s["body_loss_p90_nearest_rank"] = losses[max(0, int(np.ceil(len(losses) * .9)) - 1)] if losses else 0
        s["body_loss_max"] = max(losses, default=0)
        s["body_cut_including_no_target"] = s["partial_body"] + s["no_target"]
        s["incomplete_target"] = s["eos_only"] + s["body_cut_including_no_target"]
        s["body_lost_pct_of_body_tokens"] = s["body_lost"] / s["body_tokens"] * 100
        c = claude["arms"][arm]
        require((s["eos_only"], s["body_cut_including_no_target"], s["no_target"], s["body_lost"]) ==
                (c["eos_only_rows"], c["body_cut_rows"], c["no_target_rows"], c["body_tokens_lost"]), f"Disagrees with v2: {arm}")
    require(not torch.cuda.is_initialized(), "CUDA was initialized during token-only audit")
    report = {"status": "PASS_REAL_DATASET_TOKEN_LABEL_AUDIT", "created_utc": datetime.now(timezone.utc).isoformat(),
              "rows_per_arm": 25000, "arm_sample_records": 50000, "text_max_length": 1536,
              "source_hashes": source_hashes, "training_jsonl_hashes": data_hashes,
              "all_four_recorded_hash_matches": recorded, "tokenizer_snapshot_revision": snapshot.name,
              "tokenizer_files": {p.name: sha(p) for p in tokenizer_dir.iterdir()},
              "prompt_builder_sha256": sha(Path(gen_prompts.__file__)), "data_helper_sha256": sha(Path(data.__file__)),
              "runtime": {"python": sys.version, "platform": platform.platform(), "torch": torch.__version__,
                          "transformers": transformers.__version__, "peft": peft.__version__, "cuda_initialized": torch.cuda.is_initialized()},
              "scope": {"real_dataset_classes": True, "full_25000_rows": True, "latent_encoder_run": False,
                        "dummy_a1e_latent": "one float zero; not consulted by token/labels path",
                        "model_loaded": False, "trainer_or_optimizer_constructed": False,
                        "historical_prediction_weight_binding_established": False,
                        "historical_prompt_tokenizer_byte_binding_established": False,
                        "tokenizer_and_prompt_used_in_this_audit_pinned": True},
              "comparison_with_claude_v2_counts": "MATCH", "arms": stats, "audit_script_sha256": sha(__file__)}
    (out / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    artifacts = [{"relative_path": str(p.relative_to(out)), "bytes": p.stat().st_size, "sha256": sha(p)} for p in sorted(out.rglob("*")) if p.is_file()]
    (out / "artifact_manifest.json").write_text(json.dumps(artifacts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "arms": stats, "out": str(out)}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
