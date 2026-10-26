#!/usr/bin/env python3
"""Prepare Review/04 manifests and CPU-only checks. Never calls Trainer.train()."""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import inspect
import json
from pathlib import Path
import random
import shutil
import sys


SEED = 42
MODALITIES = ("step", "point", "text", "image")
PHASE1_ROWS = 75024
PHASE2_IDS = 2000
ROLE_COUNTS = {"predicted": 945, "gt": 2205}
MODEL_ID = "Qwen/Qwen2.5-Coder-1.5B"
REVISION = "df3ce67c0e24480f20468b6ef2894622d69eb73b"
LORA_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def json_bytes(obj):
    return (json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":")) + "\n").encode()


def object_hash(obj):
    return hashlib.sha256(json_bytes(obj)).hexdigest()


def read_rows(path):
    with Path(path).open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def file_record(path):
    path = Path(path)
    require(path.is_file() and path.stat().st_size > 0, f"Missing/empty file: {path}")
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest(path)}


def write_once(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(path.read_bytes() == content, f"Refusing to replace different frozen content: {path}")
        return
    with path.open("xb") as f:
        f.write(content)


def check_source_ids(splits):
    ids = {}
    for split, rows in splits.items():
        values = [r["sample_id"] for r in rows]
        require(all(isinstance(x, str) and x for x in values), f"Empty ID in {split}")
        require(len(set(values)) == len(values), f"Duplicate ID in {split}")
        ids[split] = set(values)
    overlaps = {}
    for a, b in (("train", "val"), ("train", "test"), ("val", "test")):
        n = len(ids[a] & ids[b])
        require(n == 0, f"Source split leakage: {a}/{b}: {n}")
        overlaps[f"{a}_{b}"] = n
    return overlaps


def build_manifests(train, val, test):
    check_source_ids({"train": train, "val": val, "test": test})
    require(len(train) == 25000 and len(val) == len(test) == 2500, "Unexpected source counts")
    # Separate named RNG streams prevent one decision from shifting another stream.
    rng = random.Random("review04:source-order:42:v1")
    source_order = []
    while len(source_order) < PHASE1_ROWS:
        order = list(range(len(train)))
        rng.shuffle(order)
        source_order.extend(order)
    source_order = source_order[:PHASE1_ROWS]
    labels = [m for m in MODALITIES for _ in range(PHASE1_ROWS // 4)]
    random.Random("review04:phase1-modalities:42:v1").shuffle(labels)
    manifests = {}
    for arm in ("A", "B"):
        manifests[f"phase1_{arm}.jsonl"] = [
            {"case_index": i, "source_row": row, "sample_id": train[row]["sample_id"],
             "modality": "step" if arm == "A" else labels[i], "source_split": "train"}
            for i, row in enumerate(source_order)
        ]
    manifests["phase2_shared.jsonl"] = [
        {"case_index": k * PHASE2_IDS + i, "source_row": i,
         "sample_id": r["sample_id"], "modality": m, "source_split": "train"}
        for k, m in enumerate(MODALITIES) for i, r in enumerate(train[:PHASE2_IDS])
    ]
    role_order = list(range(len(train)))
    random.Random("review04:stage4b-roles:42:v1").shuffle(role_order)
    manifests["stage4b_roles.jsonl"] = [
        {"case_index": i, "source_row": row, "sample_id": train[row]["sample_id"],
         "role": "predicted" if i < ROLE_COUNTS["predicted"] else "gt",
         "modality": "step", "source_split": "train"}
        for i, row in enumerate(role_order[:sum(ROLE_COUNTS.values())])
    ]
    manifests["validation_shared.jsonl"] = [
        {"case_index": k * 200 + i, "source_row": i, "sample_id": r["sample_id"],
         "modality": m, "source_split": "val"}
        for k, m in enumerate(MODALITIES) for i, r in enumerate(val[:200])
    ]
    manifests["evaluation_shared.jsonl"] = [
        {"case_index": k * len(test) + i, "source_row": i, "sample_id": r["sample_id"],
         "modality": m, "source_split": "test"}
        for k, m in enumerate(MODALITIES) for i, r in enumerate(test)
    ]
    verify_manifests(manifests, train)
    return manifests


def verify_manifests(manifests, train):
    a, b = (manifests[f"phase1_{x}.jsonl"] for x in ("A", "B"))
    require(len(a) == len(b) == PHASE1_ROWS, "Phase 1 length mismatch")
    require([r["source_row"] for r in a] == [r["source_row"] for r in b], "Arm source order mismatch")
    require(Counter(r["modality"] for r in a) == {"step": PHASE1_ROWS}, "Arm A counts")
    require(Counter(r["modality"] for r in b) == {m: 18756 for m in MODALITIES}, "Arm B counts")
    source_counts = Counter(r["source_row"] for r in a)
    require(Counter(source_counts.values()) == {3: 24976, 4: 24}, "Unexpected source reuse")
    phase2 = manifests["phase2_shared.jsonl"]
    require(Counter(r["modality"] for r in phase2) == {m: 2000 for m in MODALITIES}, "Phase 2 counts")
    require({r["sample_id"] for r in phase2} == {r["sample_id"] for r in train[:2000]}, "Phase 2 IDs")
    roles = manifests["stage4b_roles.jsonl"]
    require(Counter(r["role"] for r in roles) == ROLE_COUNTS, "Stage 4b role counts")
    require(len({r["sample_id"] for r in roles}) == 3150, "Overlapping Stage 4b roles")
    for name, rows in manifests.items():
        require([r["case_index"] for r in rows] == list(range(len(rows))), f"Index mismatch: {name}")
        if rows[0]["source_split"] == "train":
            require(all(train[r["source_row"]]["sample_id"] == r["sample_id"] for r in rows), f"Source ID mismatch: {name}")


def save_manifests(out, manifests, splits):
    records = {}
    for name, rows in manifests.items():
        path = out / "manifests" / name
        write_once(path, b"".join(json_bytes(r) for r in rows))
        require(read_rows(path) == rows, f"Manifest read-back mismatch: {path}")
        records[name] = {**file_record(path), "rows": len(rows),
                         "unique_ids": len({r["sample_id"] for r in rows}),
                         "modality_counts": dict(Counter(r["modality"] for r in rows))}
        if "role" in rows[0]:
            records[name]["role_counts"] = dict(Counter(r["role"] for r in rows))
    for split, rows in splits.items():
        path = out / "manifests" / f"source_{split}_ids.txt"
        write_once(path, ("\n".join(r["sample_id"] for r in rows) + "\n").encode())
        records[path.name] = {**file_record(path), "rows": len(rows)}
    return records


def audit_resources(source, splits, out):
    """Read reference targets/STEP features; decode point and image inputs on CPU."""
    import numpy as np
    from PIL import Image
    from miragecad.data import load_step_brep_tensors

    def check_row(row, split):
        require(isinstance(row.get("text"), str) and row["text"].strip(), f"Empty text: {row['sample_id']}")
        item = {"sample_id": row["sample_id"], "split": split, "files": {}}
        for key in ("ir_path", "program_path", "step_feature_path", "point_path", "iso_image_path"):
            p = Path(row[key])
            if not p.is_absolute():
                p = source / p
            item["files"][key] = file_record(p)
            if key in ("ir_path", "program_path"):
                require(p.read_text(encoding="utf-8").strip(), f"Empty target: {p}")
            elif key == "step_feature_path":
                features = load_step_brep_tensors(p, strict=True)
                require(all(np.isfinite(v).all() for v in features.values()), f"Nonfinite STEP: {p}")
            elif key == "point_path":
                with np.load(p, allow_pickle=False) as points:
                    require(points.files, f"Empty point archive: {p}")
                    key_name = next((k for k in ("points", "xyz", "point_cloud") if k in points.files), points.files[0])
                    xyz = points[key_name]
                    require(xyz.ndim == 2 and xyz.shape[0] > 0 and xyz.shape[1] >= 3,
                            f"Invalid points: {p}: {xyz.shape}")
                    require(np.isfinite(xyz[:, :3]).all(), f"Nonfinite points: {p}")
            else:
                with Image.open(p) as img:
                    img.verify()
        return item

    inventory = out / "manifests" / "resource_inventory.jsonl"
    pending = inventory.with_suffix(".pending")
    records_count = 0
    h = hashlib.sha256()
    # Full binary hashes are recorded as well: source JSON paths alone do not freeze content.
    with pending.open("wb") as f, ThreadPoolExecutor(max_workers=16) as pool:
        for split, rows in splits.items():
            # Ordered map preserves deterministic inventory bytes while overlapping file I/O.
            for i, item in enumerate(pool.map(lambda row: check_row(row, split), rows)):
                line = json_bytes(item)
                h.update(line)
                f.write(line)
                records_count += 1
                if (i + 1) % 1000 == 0:
                    print(f"resources {split}: {i + 1}/{len(rows)} (content hashes + CPU decode)", flush=True)
    if inventory.exists():
        require(digest(inventory) == h.hexdigest(), "Resource content changed since previous preparation")
        pending.unlink()
    else:
        pending.rename(inventory)
    return {"status": "PASS", "source_rows": records_count, "files_per_row": 5,
            "all_five_resource_contents_hashed": True, "silent_skips": 0,
            "cpu_decoded": ["STEP", "point", "image"], "inventory": file_record(inventory),
        "latent_cache": "NOT_BUILT; future inference-only materializer must abort on any encoding failure"}


def audit_checkpoints(source, mapping):
    result = {}
    for name in ("align_25k", "prior_step_25k", "prior_point_25k", "prior_text_25k", "prior_image_25k",
                 "qwen25_coder_1_5b_program_25k"):
        files = {}
        for fname, previous in mapping["components"][name]["files"].items():
            record = file_record(source / "outputs" / name / fname)
            require(record["sha256"] == previous["sha256"], f"Shared checkpoint changed: {name}/{fname}")
            files[fname] = record
        if name == "qwen25_coder_1_5b_program_25k":
            for fname in ("tokenizer.json", "tokenizer_config.json", "special_tokens_map.json"):
                p = source / "outputs" / name / fname
                if p.is_file():
                    files[fname] = file_record(p)
        result[name] = files
    return {"status": "PASS", "both_arms_share_exact_files": True, "components": result}


def audit_spec(source, out, mapping):
    path = out / "05_execution_spec.json"
    spec = json.loads(path.read_text())
    require(spec["seed"] == spec["data_seed"] == SEED and spec["world_size"] == 1, "Spec seed/device mismatch")
    require(spec["training_authorized"] is False, "Preparation cannot authorize training")
    require(spec["model"]["revision"] == REVISION, "Base revision mismatch")
    for phase, rows, steps, lr in zip(spec["plan_phases"], (75024, 8000), (4689, 500), (2e-4, 1e-5)):
        require((phase["dataset_rows"], phase["expected_global_step"], phase["learning_rate"]) == (rows, steps, lr),
                "Plan spec budget mismatch")
        require(phase["fresh_optimizer_and_scheduler"] and phase["gradient_accumulation_steps"] == 16,
                "Plan boundary/reset mismatch")
    code = spec["stage4b"]
    require((code["dataset_rows"], code["predicted_rows"], code["gt_rows"], code["epochs"],
             code["gradient_accumulation_steps"], code["expected_global_step"]) == (3150, 945, 2205, 3, 8, 1182),
            "Stage4b spec budget mismatch")
    require(code["retain_invalid_or_empty_predicted_plans"] and not code["grammar_filter"], "Role filtering forbidden")
    require(spec["generation"]["P1a_plan_canonicalization"] and not spec["generation"]["program_code_repair"],
            "Repair policy mismatch")
    paths = [source / phase[f"{arm}_output"] for arm in ("A", "B") for phase in spec["plan_phases"]]
    paths.extend(source / code[f"{arm}_output"] for arm in ("A", "B"))
    require(len(set(paths)) == len(paths), "Training output directories collide")
    for p in paths:
        require(not p.exists(), f"Training path already exists; inspect explicitly before use: {p}")
    dependencies = {}
    for rel, previous in mapping["scripts"].items():
        if previous["exists"]:
            record = file_record(source / rel)
            require(record["sha256"] == previous["sha256"], f"Mapped source code changed: {rel}")
            dependencies[rel] = record
    for p in sorted((source / "miragecad").rglob("*.py")):
        dependencies[str(p.relative_to(source))] = file_record(p)
    write_once(out / "manifests" / "source_code_inventory.json", json_bytes(dependencies))
    return {"status": "PASS", "execution_spec": file_record(path), "isolated_training_paths": [str(p) for p in paths],
            "training_paths_absent": True, "mapped_source_hashes_unchanged": True,
            "source_code_inventory": file_record(out / "manifests" / "source_code_inventory.json")}


def runtime_budget(out):
    import torch
    import transformers
    import accelerate
    from torch import nn
    from transformers import Trainer, TrainingArguments, get_scheduler

    class CountDataset(torch.utils.data.Dataset):
        def __init__(self, n):
            self.n = n

        def __len__(self):
            return self.n

        def __getitem__(self, i):
            return {"row_index": torch.tensor(i)}

    class NoForwardModel(nn.Module):
        def __init__(self):
            super().__init__()
            self.weight = nn.Parameter(torch.zeros(1))

        def forward(self, **kwargs):
            raise RuntimeError("Preflight must never execute a model forward")

    result = {"status": "PASS", "torch": torch.__version__, "transformers": transformers.__version__,
              "accelerate": accelerate.__version__, "device": "cpu", "train_called": False,
              "forward_calls": 0, "backward_calls": 0, "optimizer_step_calls": 0,
              "method": "installed Trainer planning plus real DataLoader/get_batch_samples traversal",
              "trainer_source_sha256": digest(inspect.getsourcefile(Trainer)), "phases": {}}
    schedules = {}
    for label, n, accumulation, epochs, lr, expected in (
        ("plan_phase1", 75024, 16, 1, 2e-4, 4689),
        ("plan_phase2", 8000, 16, 1, 1e-5, 500),
        ("stage4b", 3150, 8, 3, 5e-5, 1182),
    ):
        args = TrainingArguments(output_dir=str(out / "artifacts" / "cpu_probe" / label),
            use_cpu=True, report_to=[], seed=SEED, data_seed=SEED, num_train_epochs=epochs,
            per_device_train_batch_size=1, gradient_accumulation_steps=accumulation,
            dataloader_drop_last=False, dataloader_pin_memory=False, dataloader_num_workers=0,
            remove_unused_columns=False, save_strategy="no", learning_rate=lr,
            optim="adamw_torch_fused", lr_scheduler_type="linear", warmup_ratio=0.03,
            weight_decay=0.0, train_sampling_strategy="random")
        trainer = Trainer(model=NoForwardModel(), args=args, train_dataset=CountDataset(n))
        require(args.world_size == 1, "Budget control requires exactly one process")
        loader = trainer.get_train_dataloader()
        plan = trainer.set_initial_training_values(args, loader)
        require(plan[-1] == expected, f"Trainer planned steps mismatch: {label}: {plan}")
        groups, rows_seen, order_hashes = [], 0, []
        for epoch in range(epochs):
            loader.set_epoch(epoch)
            iterator = iter(loader)
            epoch_groups = []
            seen = []
            while True:
                batches, _ = trainer.get_batch_samples(iterator, accumulation, torch.device("cpu"))
                if not batches:
                    break
                epoch_groups.append(len(batches))
                seen.extend(int(batch["row_index"].item()) for batch in batches)
            require(sorted(seen) == list(range(n)), f"DataLoader skipped/duplicated rows: {label}/{epoch}")
            rows_seen += len(seen)
            groups.extend(epoch_groups)
            order_hashes.append(object_hash(seen))
        require(len(groups) == expected and rows_seen == n * epochs, f"Traversed budget mismatch: {label}")
        # A second fresh loader tests actual paired-arm sampler reproducibility.
        second = trainer.get_train_dataloader()
        second.set_epoch(0)
        repeated = [int(batch["row_index"].item()) for batch in second]
        require(object_hash(repeated) == order_hashes[0], f"Paired sampler is not reproducible: {label}")
        trainer.create_optimizer()
        require(isinstance(trainer.optimizer, torch.optim.AdamW), "Unexpected optimizer")
        require(trainer.optimizer.defaults.get("fused") is True, "Fused AdamW not selected")
        warmup = args.get_warmup_steps(expected)
        scheduler = get_scheduler("linear", trainer.optimizer, num_warmup_steps=warmup, num_training_steps=expected)
        vector = [lr * scheduler.lr_lambdas[0](i) for i in range(expected + 1)]
        schedules[label] = vector
        result["phases"][label] = {
            "rows": n, "epochs": epochs, "accumulation": accumulation,
            "dataloader_microbatches_per_epoch": len(loader), "trainer_max_steps": plan[-1],
            "traversed_update_groups": len(groups), "row_presentations": rows_seen,
            "accumulation_group_sizes": dict(Counter(groups)), "warmup_steps": warmup,
            "optimizer": str(args.optim), "initial_lr": lr, "lr_vector_sha256": object_hash(vector),
            "sampler": str(args.train_sampling_strategy), "sampler_epoch_index_sha256": order_hashes,
            "paired_sampler_reproducibility": "PASS", "reset_optimizer_and_scheduler": True,
            "actual_trained_global_step": None,
        }
        print(f"CPU Trainer preflight: {label}: {len(groups)} groups / {rows_seen} presentations", flush=True)
    write_once(out / "manifests" / "lr_vectors.json", json_bytes(schedules))
    result["schedule_shared_by_both_arms"] = file_record(out / "manifests" / "lr_vectors.json")
    result["post_training_assertions_required"] = {
        "plan_phase1_global_step": 4689, "plan_phase2_global_step": 500,
        "stage4b_global_step": 1182, "expected_all_arms": True}
    return result


def common_initialization(out):
    import torch
    import peft
    from peft import LoraConfig, PeftModel, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed
    from huggingface_hub import snapshot_download
    from safetensors.torch import load_file
    from miragecad.soft_prefix import SoftPrefixAdapter, SoftPrefixConfig, save_soft_prefix_adapter

    snapshot = Path(snapshot_download(MODEL_ID, revision=REVISION, local_files_only=True))
    base_files = {p.name: file_record(p) for p in sorted(snapshot.iterdir()) if p.is_file()}
    root = out / "artifacts" / "initialization"
    completion = root / "initialization_actuals.json"
    if completion.exists():
        record = json.loads(completion.read_text())
        require(record["base_files"] == base_files, "Cached base model changed")
        for arm in ("A", "B"):
            for name, previous in record["arm_files"][arm].items():
                require(digest(root / f"arm_{arm}" / name) == previous["sha256"], f"Initialization changed: {arm}/{name}")
        return record
    require(not root.exists(), f"Incomplete initialization exists; inspect it explicitly: {root}")
    root.mkdir(parents=True)
    print("Creating untrained common LoRA/prefix initialization on CPU from local cached base", flush=True)
    base = AutoModelForCausalLM.from_pretrained(snapshot, local_files_only=True,
                                               dtype=torch.bfloat16, device_map={"": "cpu"})
    set_seed(SEED)
    config = LoraConfig(r=8, lora_alpha=16, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
                        target_modules=LORA_MODULES)
    model = get_peft_model(base, config)
    require(int(model.config.hidden_size) == 1536, "Unexpected base hidden size")
    prefix = SoftPrefixAdapter(SoftPrefixConfig(latent_dim=512, hidden_size=1536, prefix_len=4, dropout=0.0))
    directory = root / "arm_A"
    model.save_pretrained(directory, safe_serialization=True)
    save_soft_prefix_adapter(directory / "soft_prefix.pt", prefix)
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.save_pretrained(directory)
    shutil.copytree(directory, root / "arm_B")
    state = load_file(directory / "adapter_model.safetensors")
    require(all(torch.isfinite(t).all() for t in state.values()), "Nonfinite initialization")
    require(all(torch.count_nonzero(t) == 0 for k, t in state.items() if "lora_B" in k), "LoRA B not initially zero")
    require(any(torch.count_nonzero(t) > 0 for k, t in state.items() if "lora_A" in k), "LoRA A unexpectedly zero")
    # Reload the saved adapter and prefix to test the actual artifacts, without any forward pass.
    del state
    model.unload()
    reloaded = PeftModel.from_pretrained(base, root / "arm_B", is_trainable=True, local_files_only=True)
    require(any(p.requires_grad for p in reloaded.parameters()), "Reloaded LoRA is not trainable")
    a_prefix = torch.load(directory / "soft_prefix.pt", map_location="cpu", weights_only=True)
    b_prefix = torch.load(root / "arm_B" / "soft_prefix.pt", map_location="cpu", weights_only=True)
    require(all(torch.equal(a_prefix["state_dict"][k], b_prefix["state_dict"][k])
                for k in a_prefix["state_dict"]), "Prefix tensors mismatch")
    arm_files = {arm: {p.name: file_record(p) for p in sorted((root / f"arm_{arm}").iterdir()) if p.is_file()}
                 for arm in ("A", "B")}
    require({k: v["sha256"] for k, v in arm_files["A"].items()} ==
            {k: v["sha256"] for k, v in arm_files["B"].items()}, "Arm initialization hashes mismatch")
    record = {"status": "PASS", "training_started": False, "device": "cpu", "seed": SEED,
              "base_model": MODEL_ID, "base_revision": REVISION, "base_files": base_files,
              "peft": peft.__version__, "recipe": "CPU BF16 base; reset RNG; standard PEFT init; fresh FP32 prefix",
              "note": "A matched new initialization, not a claim of bitwise historical/4-bit initialization reproduction",
              "arm_files": arm_files, "identical_initialization_hashes": True,
              "adapter_reload": "PASS", "prefix_tensor_equality": "PASS"}
    write_once(completion, json_bytes(record))
    return record


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-root", type=Path, required=True)
    ap.add_argument("--package-root", type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument("--checks", nargs="+", choices=("manifests", "resources", "checkpoints", "budget", "initialization", "spec"),
                    default=["manifests", "resources", "checkpoints", "budget", "initialization", "spec"])
    args = ap.parse_args()
    source, out = args.source_root.resolve(), args.package_root.resolve()
    sys.path.insert(0, str(source))
    mapping = json.loads((out / "03_stage_mapping_actuals.json").read_text())
    current = out / "04_preflight_actuals.json"
    result = json.loads(current.read_text()) if current.exists() else {
        "purpose": "Review/04 exposure-policy preparation; no training", "training_started": False, "checks": {}}
    result.update(updated_utc=datetime.now(timezone.utc).isoformat(), source_root=str(source),
                  preparation_script=file_record(Path(__file__)))
    try:
        splits = {s: read_rows(source / f"data/25k/{s}.jsonl") for s in ("train", "val", "test")}
        for s in splits:
            actual = file_record(source / f"data/25k/{s}.jsonl")
            require(actual["sha256"] == mapping["datasets"][f"data/25k/{s}.jsonl"]["sha256"], f"Source changed: {s}")
        result["source_overlap_audit"] = {"status": "PASS", "overlaps": check_source_ids(splits)}
        result["source_datasets"] = {s: file_record(source / f"data/25k/{s}.jsonl") for s in splits}
        for check in args.checks:
            print(f"Starting preparation check: {check}", flush=True)
            result["checks"][check] = {"status": "RUNNING"}
            if check == "manifests":
                manifests = build_manifests(**splits)
                result["checks"][check] = {"status": "PASS", "files": save_manifests(out, manifests, splits),
                    "rng": "Python random.Random with separate named string seeds; manifest bytes are authoritative",
                    "phase1_common_id_sequence": "PASS", "train_only_role_selection": True,
                    "total_presentations": {"A": {"step": 77024, "point": 2000, "text": 2000, "image": 2000},
                                            "B": {m: 20756 for m in MODALITIES}}}
            elif check == "resources":
                result["checks"][check] = audit_resources(source, splits, out)
            elif check == "checkpoints":
                result["checks"][check] = audit_checkpoints(source, mapping)
            elif check == "budget":
                result["checks"][check] = runtime_budget(out)
            elif check == "initialization":
                result["checks"][check] = common_initialization(out)
            else:
                result["checks"][check] = audit_spec(source, out, mapping)
            result["checks"][check]["verified_by_script_sha256"] = result["preparation_script"]["sha256"]
            current.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    except Exception as exc:
        result["last_error"] = {"check": check if "check" in locals() else "source", "type": type(exc).__name__, "message": str(exc)}
        if "check" in locals():
            result["checks"][check] = {"status": "FAIL", "error": result["last_error"]}
        result["preflight_status"] = "FAIL_NOT_FROZEN"
        current.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        raise
    required = {"manifests", "resources", "checkpoints", "budget", "initialization", "spec"}
    result.pop("last_error", None)
    result["preflight_status"] = "PASS_PREPARATION_ONLY" if all(
        result["checks"].get(c, {}).get("status") == "PASS" and
        result["checks"][c].get("verified_by_script_sha256") == result["preparation_script"]["sha256"]
        for c in required) else "INCOMPLETE_NOT_FROZEN"
    result["training_entrypoint_status"] = "NOT_PREPARED; existing trainer cannot consume case manifests directly"
    result["latent_cache_status"] = "NOT_BUILT; source inputs verified separately"
    result["protocol_auto_frozen"] = False
    current.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"{result['preflight_status']}; no training started; actuals: {current}")


if __name__ == "__main__":
    main()
