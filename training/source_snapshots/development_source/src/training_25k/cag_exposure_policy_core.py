"""Frozen Review/04 data contracts. No training, model loading, or cache synthesis."""
from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from functools import cached_property, lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import torch
from torch.utils.data import Dataset


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")) + "\n").encode()


def value_sha(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def array_sha(array):
    a = np.ascontiguousarray(array)
    h = hashlib.sha256(encoded({"shape": a.shape, "dtype": a.dtype.str}))
    h.update(a.tobytes())
    return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_rows(path):
    with Path(path).open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_json_new(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as f:
        f.write(encoded(obj))


def record(path):
    p = Path(path).resolve()
    return {"path": str(p), "sha256": sha(p), "bytes": p.stat().st_size}


def verify_record(item):
    p = Path(item["path"])
    require(p.is_file(), f"Missing frozen file: {p}")
    require(p.stat().st_size == item["bytes"] and sha(p) == item["sha256"], f"Frozen hash mismatch: {p}")


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def reject_existing(path):
    require(not Path(path).exists(), f"Output already exists; no overwrite or implicit resume: {path}")


class FrozenInputs:
    def __init__(self, package_root, source_root):
        self.package = Path(package_root).resolve()
        self.source = Path(source_root).resolve()
        self.spec = read_json(self.package / "05_execution_spec.json")
        self.actuals = read_json(self.package / "04_preflight_actuals.json")
        self.seal = read_json(self.package / "07_frozen_package_seal.json")
        require(self.spec["status"] == "FROZEN" and self.seal["protocol"] == "FROZEN", "Protocol is not FROZEN")
        require(self.actuals["preflight_status"] == "PASS_PREPARATION_ONLY", "Preparation has not passed")
        require(str(self.source) == self.actuals["source_root"], "Use the frozen source checkout")
        sys.path.insert(0, str(self.source))
        self.manifests = {}
        self.splits = {}
        self.inventory = None

    def guard(self, resources=False):
        # The original preparation seal is never edited by execution tools.
        for item in self.seal["files"]:
            verify_record(item)
        for item in read_json(self.package / "manifests/source_code_inventory.json").values():
            verify_record(item)
        for split in ("train", "val", "test"):
            self.splits[split] = read_rows(self.source / f"data/25k/{split}.jsonl")
            ids = [r["sample_id"] for r in self.splits[split]]
            require(len(ids) == len(set(ids)), f"Duplicate source ID: {split}")
        id_sets = {s: {r["sample_id"] for r in rows} for s, rows in self.splits.items()}
        require(not (id_sets["train"] & id_sets["val"] or id_sets["train"] & id_sets["test"]
                     or id_sets["val"] & id_sets["test"]), "Source split leakage")
        for name, expected in (("phase1_A", 75024), ("phase1_B", 75024), ("phase2_shared", 8000),
                               ("stage4b_roles", 3150), ("validation_shared", 800), ("evaluation_shared", 10000)):
            data = read_rows(self.package / f"manifests/{name}.jsonl")
            require(len(data) == expected, f"Manifest rows changed: {name}")
            for i, case in enumerate(data):
                require(case["case_index"] == i, f"Case order/index mismatch: {name}/{i}")
                self.resolve(case)
            self.manifests[name] = data
        a, b = self.manifests["phase1_A"], self.manifests["phase1_B"]
        require([c["sample_id"] for c in a] == [c["sample_id"] for c in b], "Paired source order changed")
        require(Counter(c["modality"] for c in a) == {"step": 75024}, "Phase 1 A exposure changed")
        require(Counter(c["modality"] for c in b) == {m: 18756 for m in ("step", "point", "text", "image")},
                "Phase 1 B exposure changed")
        require(Counter(c["role"] for c in self.manifests["stage4b_roles"]) == {"predicted": 945, "gt": 2205},
                "Role counts changed")
        self.inventory = {(r["split"], r["sample_id"]): r for r in read_rows(
            self.package / "manifests/resource_inventory.jsonl")}
        if resources:
            files = [item for row in self.inventory.values() for item in row["files"].values()]
            with ThreadPoolExecutor(max_workers=16) as pool:
                for _ in pool.map(verify_record, files):
                    pass
        import accelerate
        import peft
        import transformers
        frozen = self.actuals["checks"]["budget"]
        require(torch.__version__ == frozen["torch"] and transformers.__version__ == frozen["transformers"]
                and accelerate.__version__ == frozen["accelerate"]
                and peft.__version__ == self.actuals["checks"]["initialization"]["peft"], "Runtime version drift")
        from transformers import Trainer
        import inspect
        require(sha(inspect.getsourcefile(Trainer)) == frozen["trainer_source_sha256"], "Trainer implementation drift")
        return self

    def resolve(self, case):
        require(case["source_split"] in self.splits, "Unknown source split")
        rows = self.splits[case["source_split"]]
        i = case["source_row"]
        require(isinstance(i, int) and 0 <= i < len(rows), "Source row out of range")
        row = rows[i]
        require(row["sample_id"] == case["sample_id"], "Manifest source ID mismatch")
        require(case["modality"] in ("step", "point", "text", "image"), "Unknown modality")
        return row

    @property
    def cache_root(self):
        return self.source / self.spec["shared_cache_root"]

    @cached_property
    def fingerprint(self):
        return value_sha({"schema": "review04_query_cache_v1", "spec": sha(self.package / "05_execution_spec.json"),
                          "resources": sha(self.package / "manifests/resource_inventory.jsonl"),
                          "source_code": sha(self.package / "manifests/source_code_inventory.json"),
                          "upstreams": self.actuals["checks"]["checkpoints"]["components"],
                          "execution": execution_hashes()})

    def required_cases(self):
        cases = {}
        for manifest in self.manifests.values():
            for c in manifest:
                cases[case_identity(c)] = c
        # Fixed original Stage4b validation is all 2500 val STEP cases.
        for i, row in enumerate(self.splits["val"]):
            c = {"case_index": i, "source_row": i, "sample_id": row["sample_id"],
                 "source_split": "val", "modality": "step"}
            cases[case_identity(c)] = c
        return [cases[k] for k in sorted(cases)]

    def key(self, case):
        m, split, sid = case["modality"], case["source_split"], case["sample_id"]
        upstreams = self.actuals["checks"]["checkpoints"]["components"]
        return value_sha({"identity": [split, sid, m], "fingerprint": self.fingerprint,
                          "encoder_sha256": upstreams["align_25k"]["best.pt"]["sha256"],
                          "prior_sha256": upstreams[f"prior_{m}_25k"]["best.pt"]["sha256"],
                          "point_sampling_seed": self.spec["point_sampling"]["seed"],
                          "point_count": 1024, "effective_point_sampling": "fps"})


def execution_hashes():
    root = Path(__file__).resolve().parent
    return {name: sha(root / name) for name in ("cag_exposure_policy_core.py", "cag_exposure_policy.py",
                                               "cag_run_exposure_policy.sh")}


def case_identity(case):
    return case["source_split"], case["sample_id"], case["modality"]


class QueryCache:
    def __init__(self, ctx, *, verify=True):
        self.ctx = ctx
        self.root = ctx.cache_root
        require((self.root / "COMPLETE.json").is_file(), "BLOCKED: real shared latent cache is absent/incomplete")
        self.complete = read_json(self.root / "COMPLETE.json")
        require(self.complete["fingerprint"] == ctx.fingerprint, "Cache fingerprint drift; do not rebuild silently")
        require(sha(self.root / "index.jsonl") == self.complete["index_sha256"], "Cache index changed")
        rows = read_rows(self.root / "index.jsonl")
        self.entries = {tuple(r["identity"]): r for r in rows}
        expected = {case_identity(c) for c in ctx.required_cases()}
        require(len(rows) == len(self.entries) and set(self.entries) == expected, "Cache ID/modality coverage mismatch")
        require(len(rows) == self.complete["entries"], "Cache complete count mismatch")
        for c in ctx.required_cases():
            require(self.entries[case_identity(c)]["key"] == ctx.key(c), "Cache key mismatch")
        if verify:
            for i, c in enumerate(ctx.required_cases()):
                self.load(c)
                if (i + 1) % 10000 == 0:
                    print(f"verified cached entries {i + 1}/{len(rows)}", flush=True)

    @lru_cache(maxsize=2048)
    def _load(self, identity):
        item = self.entries[identity]
        stem = self.root / item["key"][:2] / item["key"]
        meta_path, tensor_path = stem.with_suffix(".json"), stem.with_suffix(".npz")
        require(sha(meta_path) == item["metadata_sha256"] and sha(tensor_path) == item["npz_sha256"], "Cache bytes changed")
        meta = read_json(meta_path)
        require(meta["key"] == item["key"] and tuple(meta["identity"]) == identity, "Cache identity changed")
        with np.load(tensor_path, allow_pickle=False) as data:
            latent, points = data["latent"].copy(), data["points"].copy()
        require(latent.shape == (512,) and latent.dtype == np.float32 and np.isfinite(latent).all(), "Invalid cached latent")
        expected_points = (1024, 3) if identity[2] == "point" else (0, 3)
        require(points.shape == expected_points and points.dtype == np.float32 and np.isfinite(points).all(), "Invalid cached points")
        require(array_sha(latent) == item["latent_sha256"] and array_sha(points) == item["points_sha256"], "Tensor hash mismatch")
        require(meta["reference_ir"].strip() and meta["reference_code"].strip(), "Empty reference target")
        latent.setflags(write=False)
        points.setflags(write=False)
        return meta, latent, points

    def load(self, case):
        return self._load(case_identity(case))


def tokenize_supervised(tokenizer, prompt, target, max_length=1536):
    require(isinstance(target, str) and target.strip(), "Empty reference training target")
    prompt_ids = tokenizer(prompt, add_special_tokens=True)["input_ids"]
    target_ids = tokenizer(target + tokenizer.eos_token, add_special_tokens=False)["input_ids"]
    ids = (prompt_ids + target_ids)[:max_length]
    masked = min(len(prompt_ids), len(ids))
    labels = [-100] * masked + target_ids[:len(ids) - masked]
    require(any(x != -100 for x in labels), "All target tokens truncated; do not drop this case")
    return {"input_ids": torch.tensor(ids, dtype=torch.long), "labels": torch.tensor(labels, dtype=torch.long),
            "attention_mask": torch.ones(len(ids), dtype=torch.long)}


class PlanDataset(Dataset):
    def __init__(self, cases, cache, tokenizer):
        self.cases, self.cache, self.tokenizer = cases, cache, tokenizer

    def __len__(self):
        return len(self.cases)

    def __getitem__(self, i):
        meta, latent, _ = self.cache.load(self.cases[i])
        item = tokenize_supervised(self.tokenizer, meta["train_prompt"], meta["reference_ir"])
        item["z_ir_hat"] = torch.tensor(latent.copy())
        return item


def plan_role_rows(roles, predictions, *, arm=None, phase2_hash=None):
    expected = [c["sample_id"] for c in roles if c["role"] == "predicted"]
    require([r["sample_id"] for r in predictions] == expected, "Predicted role IDs/order mismatch")
    require(len(set(expected)) == len(expected), "Duplicate predicted role ID")
    by_id = {}
    for r in predictions:
        require(isinstance(r.get("predicted_ir"), str), "Missing predicted plan, distinct from empty string")
        require(r.get("source_split") == "train" and r.get("modality") == "step", "Train-only STEP prediction required")
        if arm is not None:
            require(r.get("arm") == arm, "Wrong-arm predicted plan")
        if phase2_hash is not None:
            require(r.get("plan_model_sha256") == phase2_hash, "Predictions are not from this final phase2 model")
        by_id[r["sample_id"]] = r
    return by_id


class CodeDataset(Dataset):
    def __init__(self, cases, cache, tokenizer, predictions=None):
        self.cases, self.cache, self.tokenizer = cases, cache, tokenizer
        self.predictions = predictions or {}

    def __len__(self):
        return len(self.cases)

    def plan_for(self, case, meta):
        if case.get("role", "gt") == "predicted":
            # Do not use `predicted or GT`: an empty prediction is an experimental input.
            require(case["sample_id"] in self.predictions, "Missing predicted-role plan")
            return self.predictions[case["sample_id"]]["predicted_ir"]
        require(case.get("role", "gt") == "gt", "Unknown fixed role")
        return meta["reference_ir"]

    def __getitem__(self, i):
        from miragecad.gen_prompts import build_program_prompt
        case = self.cases[i]
        meta, _, _ = self.cache.load(case)
        prompt = build_program_prompt({}, case["modality"], self.plan_for(case, meta), evidence_text=meta["evidence"])
        return tokenize_supervised(self.tokenizer, prompt, meta["reference_code"])


def collate(features, pad_id):
    max_len = max(len(item["input_ids"]) for item in features)
    out = {}
    for key, padding in (("input_ids", pad_id), ("attention_mask", 0), ("labels", -100)):
        out[key] = torch.stack([torch.cat([x[key], torch.full((max_len - len(x[key]),), padding, dtype=torch.long)])
                                for x in features])
    if "z_ir_hat" in features[0]:
        out["z_ir_hat"] = torch.stack([x["z_ir_hat"] for x in features])
    return out


def final_component(path, expected_step, *, arm, phase, fingerprint):
    path = Path(path)
    completion = read_json(path / "COMPLETE.json")
    require(completion["arm"] == arm and completion["phase"] == phase and completion["fingerprint"] == fingerprint,
            "Wrong arm/phase/fingerprint at phase boundary")
    state = read_json(path / "trainer_state.json")
    require(completion["actual_global_step"] == state["global_step"] == expected_step, "Actual final step mismatch")
    require(completion["checkpoint_selection"] == "final", "Non-final checkpoint rejected")
    for item in completion["files"].values():
        verify_record(item)
    require("soft_prefix.pt" in completion["files"] or phase == "stage4b", "Final prefix missing")
    return completion
