#!/usr/bin/env python3
"""Collect existing Stage 3/3b/4/4b provenance; never starts training."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def file_record(path: Path) -> dict:
    return {"path": str(path), "exists": path.is_file(),
            "bytes": path.stat().st_size if path.is_file() else None,
            "sha256": sha256(path) if path.is_file() else None}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-root", type=Path, required=True)
    ap.add_argument("--out-json", type=Path, required=True)
    ap.add_argument("--inspect-trusted-torch-metadata", action="store_true",
                    help="Read this project's own small torch metadata/prefix files on CPU.")
    args = ap.parse_args()
    source = args.source_root.resolve()
    result = {
        "purpose": "Review/04 pre-training mapping audit of historical checkpoints",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_root": str(source), "training_started": False,
        "scripts": {}, "datasets": {}, "components": {}, "historical_evaluation_files": {},
    }
    for rel in (
        "gen_scripts/train_soft_prefix_ir.py", "train_program_lora.py",
        "training_25k/06_train_lora_ir.sh", "training_25k/06b_train_lora_ir_stage3b.sh",
        "training_25k/07_gen_predicted_ir_train_subset.sh", "training_25k/08_build_stage4b_mix.sh",
        "training_25k/09_train_lora_code_stage4.sh", "training_25k/10_train_lora_code_stage4b.sh",
        "training_25k/scripts/build_stage4b_mix.py", "training_25k/scripts/gen_predicted_ir.py",
        "training_25k/scripts/gen_code_from_predicted_ir.py",
        "training_25k/scripts/run_full_stage3b_pipeline.sh",
    ):
        result["scripts"][rel] = file_record(source / rel)
    for rel in ("data/25k/train.jsonl", "data/25k/val.jsonl", "data/25k/test.jsonl",
                "data/25k/train_stage4b_mix.jsonl"):
        path = source / rel
        data = rows(path)
        result["datasets"][rel] = {
            **file_record(path), "rows": len(data),
            "unique_ids": len({r["sample_id"] for r in data}),
            "predicted_plan_rows": sum("ir_text_for_program" in r for r in data),
            "id_sequence_sha256": hashlib.sha256(
                ("\n".join(r["sample_id"] for r in data) + "\n").encode()).hexdigest(),
        }
    for name in (
        "align_25k", "prior_step_25k", "prior_point_25k", "prior_text_25k", "prior_image_25k",
        "lora_ir_25k", "lora_ir_25k_stage3b", "qwen25_coder_1_5b_program_25k",
        "qwen25_coder_1_5b_program_25k_stage4b",
    ):
        path = source / "outputs" / name
        info = {"path": str(path), "files": {}, "reports": {}, "checkpoints": {}}
        for fname in ("best.pt", "last.pt", "adapter_model.safetensors", "soft_prefix.pt",
                      "adapter_config.json", "training_args.bin"):
            if (path / fname).is_file():
                info["files"][fname] = file_record(path / fname)
        for report in path.glob("*training_report.json"):
            data = read_json(report)
            info["reports"][report.name] = {
                **file_record(report),
                "content": data if "steps" not in data else {
                    "args": data.get("args"), "logged_evaluations": len(data["steps"]),
                    "last_evaluation": data["steps"][-1] if data["steps"] else None,
                },
            }
        for ckpt in sorted(path.glob("checkpoint-*")):
            state = ckpt / "trainer_state.json"
            meta = read_json(state) if state.exists() else None
            if meta and "global_step" in meta:
                meta = {k: meta.get(k) for k in ("global_step", "max_steps", "epoch",
                                                "num_train_epochs", "best_model_checkpoint")}
            info["checkpoints"][ckpt.name] = {
                "state": meta, "files": {f: file_record(ckpt / f)
                    for f in ("adapter_model.safetensors", "soft_prefix.pt") if (ckpt / f).exists()},
            }
        result["components"][name] = info
    test_ids = [r["sample_id"] for r in rows(source / "data/25k/test.jsonl")]
    for modality in ("step", "point", "text", "image"):
        result["historical_evaluation_files"][modality] = {}
        for label, rel in {
            "plan_stage3b_raw": f"outputs/lora_ir_25k_stage3b/predicted_ir_test_{modality}.jsonl",
            "code_stage3b_raw": f"outputs/qwen25_coder_1_5b_program_25k_stage4b/gen_test_{modality}_stage3b.jsonl",
            "code_stage3b_repaired": f"outputs/qwen25_coder_1_5b_program_25k_stage4b/gen_test_{modality}_stage3b_repaired_p0.jsonl",
        }.items():
            path = source / rel
            data = rows(path) if path.exists() else []
            result["historical_evaluation_files"][modality][label] = {
                **file_record(path), "rows": len(data),
                "ids_equal_frozen_test_order": [r["sample_id"] for r in data] == test_ids,
            }
    if args.inspect_trusted_torch_metadata:
        import torch
        import transformers

        result["metadata_runtime"] = {"torch": torch.__version__, "transformers": transformers.__version__}
        fields = ("seed", "data_seed", "num_train_epochs", "max_steps", "learning_rate",
                  "warmup_ratio", "lr_scheduler_type", "optim", "gradient_accumulation_steps",
                  "per_device_train_batch_size", "load_best_model_at_end")
        for name in ("qwen25_coder_1_5b_program_25k", "qwen25_coder_1_5b_program_25k_stage4b"):
            path = source / "outputs" / name / "training_args.bin"
            data = torch.load(path, map_location="cpu", weights_only=False)
            result["components"][name]["saved_training_args"] = {
                k: getattr(data, k, None) for k in fields}
        root = source / "outputs/lora_ir_25k"
        state = torch.load(root / "soft_prefix.pt", map_location="cpu", weights_only=False)["state_dict"]
        comparisons = {}
        for label in ("checkpoint-4500", "checkpoint-4689"):
            other = torch.load(root / label / "soft_prefix.pt", map_location="cpu", weights_only=False)["state_dict"]
            changed = [k for k in state if not torch.equal(state[k], other[k])]
            comparisons[label] = {"tensor_count": len(state), "changed_tensors": changed,
                                  "all_tensors_equal_to_root": not changed}
        result["stage3_root_prefix_tensor_comparison"] = comparisons
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(result, indent=2, ensure_ascii=True, default=str) + "\n",
                             encoding="utf-8")
    print(f"Mapping snapshot saved: {args.out_json}")
    print("Historical plan updates: 4689 + 500 = 5189")
    print("Training started: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
