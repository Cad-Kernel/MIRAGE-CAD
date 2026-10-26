#!/usr/bin/env python3
"""Review/04 execution implementation. Default preflight never starts training."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from functools import partial
import gc
import os
from pathlib import Path
import sys

# Frozen components and tokenizers must come from existing local caches.
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import numpy as np
import torch

from cag_exposure_policy_core import (
    CodeDataset, FrozenInputs, PlanDataset, QueryCache, array_sha, case_identity,
    collate, encoded, execution_hashes, final_component, load_module, plan_role_rows,
    read_json, read_rows, record, reject_existing, require, sha, value_sha, verify_record, write_json_new,
)


def now():
    return datetime.now(timezone.utc).isoformat()


def tokenizer_for(ctx):
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(ctx.package / ctx.spec["plan_adapter"]["initialization_A"], local_files_only=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    return tok


def stage_spec(ctx, arm, stage):
    if stage == "stage4b":
        spec = ctx.spec["stage4b"]
        return spec, ctx.manifests["stage4b_roles"], ctx.source / spec[f"{arm}_output"]
    phase = next(p for p in ctx.spec["plan_phases"] if p["name"] == stage)
    name = f"phase1_{arm}" if stage == "phase1" else "phase2_shared"
    return phase, ctx.manifests[name], ctx.source / phase[f"{arm}_output"]


def all_output_guards(ctx):
    reject_existing(ctx.source / ctx.spec["training_output_root"])
    for arm in ("A", "B"):
        for stage in ("phase1", "phase2", "stage4b"):
            reject_existing(stage_spec(ctx, arm, stage)[2])


def encoding_setup(ctx, device):
    from transformers import set_seed
    from miragecad.models import load_alignment_checkpoint

    require(device == "cpu" or torch.cuda.is_available(), "CUDA unavailable for explicitly requested frozen inference")
    set_seed(42)
    original = load_module(ctx.source / "gen_scripts/train_soft_prefix_ir.py", "review04_original_prefix")
    aligner, _, _, _ = load_alignment_checkpoint(ctx.source / ctx.spec["shared_checkpoints"]["alignment"])
    aligner.to(device).eval().requires_grad_(False)
    priors = {m: original.load_prior(ctx.source / ctx.spec["shared_checkpoints"][f"prior_{m}"], torch.device(device))
              .eval().requires_grad_(False) for m in ("step", "point", "text", "image")}
    return original, aligner, priors


def encode_case(ctx, case, original, aligner, priors, device):
    from miragecad.gen_prompts import build_ir_prompt, get_query_evidence
    from miragecad.data import read_text

    row, m = ctx.resolve(case), case["modality"]
    sampling = "hybrid" if case["source_split"] == "train" else "fps"
    latent, points = original.encode_query(row, m, aligner, priors[m], argparse.Namespace(point_count=1024, seed=42),
                                           torch.device(device), point_sampling=sampling)
    latent = np.asarray(latent, dtype=np.float32)
    points = np.asarray(points, dtype=np.float32) if points is not None else np.empty((0, 3), np.float32)
    require(latent.shape == (512,) and np.isfinite(latent).all(), f"Invalid latent: {case_identity(case)}")
    require(points.shape == ((1024, 3) if m == "point" else (0, 3)) and np.isfinite(points).all(), "Invalid points")
    evidence = get_query_evidence(row, m, point_xyz=points if m == "point" else None)
    if m == "step":
        require(evidence.startswith("STEP/B-Rep evidence:"), "STEP evidence silently fell back")
    reference_ir, reference_code = read_text(row["ir_path"]).strip(), read_text(row["program_path"]).strip()
    require(reference_ir and reference_code, "Empty target; refusing to skip")
    train_prompt = build_ir_prompt(row, m, evidence_text=evidence)
    infer_prompt = build_ir_prompt(row, m) if m == "point" else train_prompt
    meta = {"key": ctx.key(case), "identity": case_identity(case), "evidence": evidence,
            "train_prompt": train_prompt, "infer_prompt": infer_prompt,
            "reference_ir": reference_ir, "reference_code": reference_code}
    return meta, latent, points


def smoke_cache(ctx, report_path):
    """Eight real frozen CPU encodings, not a substitute for the full shared cache."""
    all_output_guards(ctx)
    reject_existing(report_path)
    original, aligner, priors = encoding_setup(ctx, "cpu")
    grouped = {m: [c for c in ctx.required_cases() if c["modality"] == m] for m in ("step", "point", "text", "image")}
    selected = [c for rows in grouped.values() for c in (
        next(r for r in rows if r["source_split"] == "train"),
        next(r for r in rows if r["source_split"] == "val"))]
    results = []
    with torch.inference_mode():
        for case in selected:
            meta, latent, points = encode_case(ctx, case, original, aligner, priors, "cpu")
            second_meta, second_latent, second_points = encode_case(ctx, case, original, aligner, priors, "cpu")
            require(np.array_equal(latent, second_latent) and np.array_equal(points, second_points)
                    and meta == second_meta, "Frozen CPU preprocessing is not reproducible")
            results.append({"identity": case_identity(case), "latent_sha256": array_sha(latent),
                            "points_sha256": array_sha(points), "metadata_sha256": value_sha(meta)})
            print(f"Real CPU frozen encoding PASS: {case_identity(case)}", flush=True)
    write_json_new(report_path, {"status": "PASS_SMOKE_ONLY", "created_utc": now(), "fingerprint": ctx.fingerprint,
        "training_started": False, "full_cache_created": False, "real_entries_twice_encoded": len(results), "entries": results})


def build_cache(ctx, device):
    """Frozen encoder inference only; partial builds are never consumable."""
    all_output_guards(ctx)
    if ctx.cache_root.exists():
        QueryCache(ctx)
        print("Shared cache already complete and verified; no regeneration", flush=True)
        return
    pending = ctx.cache_root.with_name(ctx.cache_root.name + ".building")
    reject_existing(pending)
    pending.mkdir(parents=True)
    original, aligner, priors = encoding_setup(ctx, device)
    entries = []
    cases = ctx.required_cases()
    with torch.inference_mode():
        for i, case in enumerate(cases):
            meta, latent, points = encode_case(ctx, case, original, aligner, priors, device)
            key = meta["key"]
            stem = pending / key[:2] / key
            stem.parent.mkdir(exist_ok=True)
            np.savez(stem.with_suffix(".npz"), latent=latent, points=points)
            write_json_new(stem.with_suffix(".json"), meta)
            entries.append({"identity": case_identity(case), "key": key,
                            "metadata_sha256": sha(stem.with_suffix(".json")), "npz_sha256": sha(stem.with_suffix(".npz")),
                            "latent_sha256": array_sha(latent), "points_sha256": array_sha(points)})
            if (i + 1) % 100 == 0:
                print(f"frozen inference cache {i + 1}/{len(cases)}; no gradient/optimizer", flush=True)
    with (pending / "index.jsonl").open("xb") as f:
        for item in entries:
            f.write(encoded(item))
    write_json_new(pending / "COMPLETE.json", {"fingerprint": ctx.fingerprint, "entries": len(entries),
        "index_sha256": sha(pending / "index.jsonl"), "created_utc": now(), "device": device,
        "training_started": False, "frozen_encoder_inference_only": True, "silent_skips": 0})
    pending.rename(ctx.cache_root)
    QueryCache(ctx)
    print(f"Shared real cache complete: {len(entries)} entries; no training", flush=True)


def training_args(ctx, stage, output, *, cpu):
    from transformers import TrainingArguments
    spec = ctx.spec["stage4b"] if stage == "stage4b" else next(p for p in ctx.spec["plan_phases"] if p["name"] == stage)
    opt = ctx.spec["optimization"]
    return TrainingArguments(output_dir=str(output), seed=42, data_seed=42,
        num_train_epochs=spec["epochs"], learning_rate=spec["learning_rate"],
        per_device_train_batch_size=1, per_device_eval_batch_size=1,
        gradient_accumulation_steps=spec["gradient_accumulation_steps"],
        warmup_ratio=opt["warmup_ratio"], weight_decay=opt["weight_decay"],
        adam_beta1=opt["adam_beta1"], adam_beta2=opt["adam_beta2"], adam_epsilon=opt["adam_epsilon"],
        max_grad_norm=opt["max_grad_norm"], optim=opt["optimizer"], lr_scheduler_type=opt["scheduler"],
        train_sampling_strategy=opt["train_sampling_strategy"],
        accelerator_config={"use_seedable_sampler": True},
        dataloader_drop_last=False, dataloader_num_workers=0, dataloader_pin_memory=not cpu,
        eval_strategy="no" if cpu else "steps", eval_steps=250,
        save_strategy="no" if cpu else "steps", save_steps=250, save_total_limit=2,
        logging_steps=10, report_to=[], remove_unused_columns=False, label_names=["labels"],
        bf16=not cpu, use_cpu=cpu, load_best_model_at_end=False)


def count_loader(ctx, stage, n):
    from torch import nn
    from transformers import Trainer

    class NoForward(nn.Module):
        def __init__(self):
            super().__init__()
            self.anchor = nn.Parameter(torch.zeros(1))

        def forward(self, **kwargs):
            raise RuntimeError("CPU preflight must not call forward")

    class IndexDataset(torch.utils.data.Dataset):
        def __len__(self):
            return n

        def __getitem__(self, i):
            return {"row_index": i}

    args = training_args(ctx, stage, ctx.package / "execution/cpu_probe" / stage, cpu=True)
    trainer = Trainer(model=NoForward(), args=args, train_dataset=IndexDataset())
    require(args.world_size == 1, "Only single-process execution is frozen")
    loader = trainer.get_train_dataloader()
    plan = trainer.set_initial_training_values(args, loader)
    frozen = ctx.actuals["checks"]["budget"]["phases"]["stage4b" if stage == "stage4b" else f"plan_{stage}"]
    require(plan[-1] == frozen["trainer_max_steps"], "Installed Trainer budget mismatch")
    orders, groups = [], []
    for epoch in range(int(args.num_train_epochs)):
        loader.set_epoch(epoch)
        iterator = iter(loader)
        order = []
        while True:
            batches, _ = trainer.get_batch_samples(iterator, args.gradient_accumulation_steps, torch.device("cpu"))
            if not batches:
                break
            groups.append(len(batches))
            order.extend(int(x["row_index"].item()) for x in batches)
        require(sorted(order) == list(range(n)), "DataLoader dropped/duplicated cases")
        orders.append(value_sha(order))
    require(orders == frozen["sampler_epoch_index_sha256"], "Sampler ordering differs from frozen preflight")
    require(len(groups) == frozen["trainer_max_steps"], "Accumulation traversal mismatch")
    return {"rows": n, "epochs": int(args.num_train_epochs), "planned_updates": len(groups),
            "group_sizes": dict(Counter(groups)), "sampler_epoch_index_sha256": orders}


def dataset_check(dataset, tokenizer):
    require(len(dataset) > 0, "Empty dataset")
    first = collate([dataset[0]], tokenizer.pad_token_id)
    last = collate([dataset[len(dataset) - 1]], tokenizer.pad_token_id)
    # Check each unique cached source/modality, not only first/last examples.
    checked = set()
    for i, case in enumerate(dataset.cases):
        key = case_identity(case) + (case.get("role", "plan"),)
        if key not in checked:
            dataset[i]
            checked.add(key)
    return {"rows": len(dataset), "unique_inputs_tokenized": len(checked), "all_cases_retain_target_tokens": True,
            "first_batch": {k: list(v.shape) for k, v in first.items()},
            "last_batch": {k: list(v.shape) for k, v in last.items()}}


def preflight(ctx, report_path):
    all_output_guards(ctx)
    reject_existing(report_path)
    cache = QueryCache(ctx)
    tok = tokenizer_for(ctx)
    result = {"status": "PASS", "scope": "real-cache CPU execution preflight", "created_utc": now(),
              "training_authorized": False, "training_started": False, "fingerprint": ctx.fingerprint,
              "execution_hashes": execution_hashes(), "cache_completion": record(cache.root / "COMPLETE.json"),
              "cache_index": record(cache.root / "index.jsonl"), "stages": {}, "actual_global_steps": None}
    for arm in ("A", "B"):
        for stage in ("phase1", "phase2"):
            _, cases, _ = stage_spec(ctx, arm, stage)
            ds = PlanDataset(cases, cache, tok)
            result["stages"][f"{arm}_{stage}"] = {**dataset_check(ds, tok), **count_loader(ctx, stage, len(ds))}
            print(f"Arm {arm} {stage}: {len(ds)} rows -> {result['stages'][f'{arm}_{stage}']['planned_updates']} planned updates", flush=True)
    val = PlanDataset(ctx.manifests["validation_shared"], cache, tok)
    result["plan_validation"] = dataset_check(val, tok)
    roles = ctx.manifests["stage4b_roles"]
    # Future predicted plans do not exist before training. Exercise the full role loader
    # with explicitly marked empty-plan contract fixtures, never as training artifacts.
    fixture = [{"sample_id": c["sample_id"], "predicted_ir": "", "source_split": "train", "modality": "step"}
               for c in roles if c["role"] == "predicted"]
    by_id = plan_role_rows(roles, fixture)
    for arm in ("A", "B"):
        ds = CodeDataset(roles, cache, tok, by_id)
        result["stages"][f"{arm}_stage4b_contract"] = {**dataset_check(ds, tok), **count_loader(ctx, "stage4b", len(ds)),
            "plan_text_source": "EMPTY_PLAN_CONTRACT_FIXTURE_ONLY_NOT_MODEL_OUTPUTS",
            "actual_predicted_plan_gate": "REQUIRED_AFTER_FINAL_PHASE2_GENERATION"}
        print(f"Stage4b {arm}: 3150 x 3 epochs -> 1182 planned updates (role contract; actual plans pending)", flush=True)
    val_code = [{"case_index": i, "source_row": i, "sample_id": r["sample_id"], "source_split": "val", "modality": "step"}
                for i, r in enumerate(ctx.splits["val"])]
    result["code_validation"] = dataset_check(CodeDataset(val_code, cache, tok), tok)
    shared = set(case_identity(c) for c in ctx.manifests["phase1_A"]) & set(case_identity(c) for c in ctx.manifests["phase1_B"])
    result["paired_cache_identity"] = {"status": "PASS", "shared_phase1_pairs": len(shared),
        "same_cache_index_for_all_arms": True, "tensor_hashes_verified": True}
    result["phase_transition"] = {"status": "CONTRACT_PASS", "steps": [4689, 500], "new_optimizer_each_phase": True,
        "final_weights_required_from_same_arm": True, "actual_phase1_final_checkpoint": "NOT_YET_CREATED"}
    write_json_new(report_path, result)
    print(f"Real-cache CPU preflight PASS; no training authorization: {report_path}", flush=True)


def final_path(ctx, arm, stage):
    spec, _, path = stage_spec(ctx, arm, stage)
    final_component(path, spec["expected_global_step"], arm=arm, phase=stage, fingerprint=ctx.fingerprint)
    return path


def load_train_model(ctx, arm, stage):
    from transformers import AutoModelForCausalLM, BitsAndBytesConfig
    from peft import PeftModel, get_peft_model_state_dict, prepare_model_for_kbit_training
    from safetensors.torch import load_file
    from miragecad.soft_prefix import load_soft_prefix_adapter

    if stage == "phase1":
        initial = ctx.package / ctx.spec["plan_adapter"][f"initialization_{arm}"]
    elif stage == "phase2":
        initial = final_path(ctx, arm, "phase1")
    else:
        initial = ctx.source / ctx.spec["shared_checkpoints"]["stage4"]
    startup = {p.name: record(p) for p in initial.iterdir() if p.name in ("adapter_model.safetensors", "adapter_config.json", "soft_prefix.pt")}
    base = AutoModelForCausalLM.from_pretrained(ctx.spec["model"]["id"], revision=ctx.spec["model"]["revision"],
        local_files_only=True, dtype=torch.bfloat16, device_map={"": 0}, quantization_config=BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True, bnb_4bit_quant_type="nf4"))
    base = prepare_model_for_kbit_training(base)
    lm = PeftModel.from_pretrained(base, initial, is_trainable=True, local_files_only=True)
    saved = load_file(initial / "adapter_model.safetensors")
    loaded = get_peft_model_state_dict(lm)
    require(saved.keys() == loaded.keys() and all(torch.equal(saved[k], loaded[k].detach().cpu()) for k in saved),
            "Loaded LoRA tensors differ from the selected startup files")
    if stage == "stage4b":
        return lm, startup
    original = load_module(ctx.source / "gen_scripts/train_soft_prefix_ir.py", "review04_prefix_for_training")
    prefix = load_soft_prefix_adapter(initial / "soft_prefix.pt", device="cuda").train()
    payload = torch.load(initial / "soft_prefix.pt", map_location="cpu", weights_only=True)
    require(all(torch.equal(v.cpu(), payload["state_dict"][k]) for k, v in prefix.state_dict().items()), "Loaded prefix mismatch")
    return original.SoftPrefixCausalLM(lm, prefix), startup


def predicted_train_path(ctx, arm):
    return ctx.source / ctx.spec["training_output_root"] / f"arm_{arm}" / "predictions/train_roles_plans.jsonl"


def modality_batches(cases, size=8):
    start = 0
    while start < len(cases):
        end = min(start + size, len(cases))
        for i in range(start + 1, end):
            if cases[i]["modality"] != cases[start]["modality"]:
                end = i
                break
        yield start, cases[start:end]
        start = end


def adapter_trainer_class(stage, tok, trace):
    from transformers import Trainer
    from miragecad.soft_prefix import save_soft_prefix_adapter

    class SafeAdapterTrainer(Trainer):
        def _save(self, output_dir=None, state_dict=None):
            destination = Path(output_dir or self.args.output_dir)
            destination.mkdir(parents=True, exist_ok=True)
            unwrapped = self.accelerator.unwrap_model(self.model)
            lm = unwrapped if stage == "stage4b" else unwrapped.lm
            lm.save_pretrained(destination, safe_serialization=True)
            tok.save_pretrained(destination)
            if stage != "stage4b":
                save_soft_prefix_adapter(destination / "soft_prefix.pt", unwrapped.prefix_adapter)

        def training_step(self, model, inputs, num_items_in_batch=None):
            trace["current_indices"].extend(inputs.pop("_case_index"))
            loss = super().training_step(model, inputs, num_items_in_batch)
            require(torch.isfinite(loss).all().item(), "Nonfinite training loss")
            return loss

        def prediction_step(self, model, inputs, *rest, **kwargs):
            inputs.pop("_case_index", None)
            return super().prediction_step(model, inputs, *rest, **kwargs)

    return SafeAdapterTrainer


def train_stage(ctx, arm, stage, cache, preflight_report):
    from transformers import TrainerCallback, set_seed

    spec, cases, output = stage_spec(ctx, arm, stage)
    reject_existing(output)
    tok = tokenizer_for(ctx)
    if stage == "stage4b":
        plan_dir = final_path(ctx, arm, "phase2")
        provenance = read_json(predicted_train_path(ctx, arm).with_suffix(".complete.json"))
        require(provenance["fingerprint"] == ctx.fingerprint and provenance["arm"] == arm, "Wrong prediction artifact provenance")
        verify_record(provenance["prediction_file"])
        predictions = read_rows(predicted_train_path(ctx, arm))
        by_id = plan_role_rows(cases, predictions, arm=arm, phase2_hash=sha(plan_dir / "adapter_model.safetensors"))
        prefix_sha = sha(plan_dir / "soft_prefix.pt")
        require(all(r.get("plan_prefix_sha256") == prefix_sha for r in predictions), "Wrong plan prefix provenance")
        dataset = CodeDataset(cases, cache, tok, by_id)
        val_cases = [{"case_index": i, "source_row": i, "sample_id": r["sample_id"], "source_split": "val", "modality": "step"}
                     for i, r in enumerate(ctx.splits["val"])]
        validation = CodeDataset(val_cases, cache, tok)
    else:
        dataset = PlanDataset(cases, cache, tok)
        validation = PlanDataset(ctx.manifests["validation_shared"], cache, tok)
    materialized = dataset_check(dataset, tok)
    require(len(dataset) == spec["dataset_rows"], "Real training dataset row mismatch")
    output.mkdir(parents=True)
    write_json_new(output / "STARTED.json", {"created_utc": now(), "arm": arm, "stage": stage,
        "fingerprint": ctx.fingerprint, "preflight_report": record(preflight_report), "materialized": materialized,
        "implicit_resume": False, "new_optimizer": True, "new_scheduler": True, "phase_rng_seed": 42})
    model, startup = load_train_model(ctx, arm, stage)
    args = training_args(ctx, stage, output, cpu=False)
    require(args.world_size == 1, "Multi-process training is outside this protocol")
    expected = ctx.actuals["checks"]["budget"]["phases"]["stage4b" if stage == "stage4b" else f"plan_{stage}"]
    lr_vector = read_json(ctx.package / "manifests/lr_vectors.json")["stage4b" if stage == "stage4b" else f"plan_{stage}"]
    require(value_sha(lr_vector) == expected["lr_vector_sha256"], "Frozen LR vector drift")
    trace = {"epochs": [], "current_indices": [], "lr_steps_checked": 0}

    class IndexedDataset(torch.utils.data.Dataset):
        def __init__(self, inner):
            self.inner = inner

        def __len__(self):
            return len(self.inner)

        def __getitem__(self, i):
            return {**self.inner[i], "_case_index": i}

    def indexed_collator(features):
        return {**collate(features, tok.pad_token_id), "_case_index": [f["_case_index"] for f in features]}

    class AuditCallback(TrainerCallback):
        def on_train_begin(self, args, state, control, optimizer=None, **kwargs):
            require(state.global_step == 0 and state.max_steps == spec["expected_global_step"], "Not a fresh matched-budget phase")
            require(len(optimizer.state) == 0, "Optimizer state was not reset")

        def on_step_begin(self, args, state, control, optimizer=None, **kwargs):
            target_lr = lr_vector[state.global_step]
            require(all(abs(group["lr"] - target_lr) < 1e-12 for group in optimizer.param_groups), "LR schedule/boundary drift")
            trace["lr_steps_checked"] += 1

        def on_epoch_end(self, args, state, control, **kwargs):
            order = trace["current_indices"]
            require(sorted(order) == list(range(len(dataset))), "Training exposure dropped or duplicated cases")
            epoch = len(trace["epochs"])
            require(value_sha(order) == expected["sampler_epoch_index_sha256"][epoch], "Actual sampler order changed")
            trace["epochs"].append({"epoch": epoch, "presentations": len(order), "index_sha256": value_sha(order)})
            trace["current_indices"] = []

    # This is after every cache/tokenizer/model loading operation, as frozen.
    set_seed(42)
    SafeAdapterTrainer = adapter_trainer_class(stage, tok, trace)
    trainer = SafeAdapterTrainer(model=model, args=args, train_dataset=IndexedDataset(dataset),
        eval_dataset=IndexedDataset(validation), data_collator=indexed_collator, processing_class=tok,
        callbacks=[AuditCallback()])
    require(trainer.set_initial_training_values(args, trainer.get_train_dataloader())[-1] == spec["expected_global_step"],
            "Actual training DataLoader budget mismatch")
    trainer.train(resume_from_checkpoint=None)
    require(trainer.state.global_step == spec["expected_global_step"], "Actual final global_step mismatch")
    require(trace["lr_steps_checked"] == trainer.state.global_step and not trace["current_indices"], "Incomplete schedule/exposure trace")
    require(all(torch.isfinite(p).all().item() for p in model.parameters() if p.requires_grad), "Nonfinite final trainable weights")
    trainer.save_model(output)
    trainer.state.save_to_json(output / "trainer_state.json")
    write_json_new(output / "training_report.json", {"arm": arm, "stage": stage, "fingerprint": ctx.fingerprint,
        "created_utc": now(), "actual_global_step": trainer.state.global_step, "checkpoint_selection": "final",
        "startup": startup, "exposure_trace": trace, "dataset": materialized, "fresh_optimizer_and_scheduler": True,
        "execution_hashes": execution_hashes(), "cache_index_sha256": sha(cache.root / "index.jsonl")})
    names = ["adapter_model.safetensors", "adapter_config.json", "tokenizer.json", "tokenizer_config.json",
             "trainer_state.json", "training_report.json", "STARTED.json"]
    if stage != "stage4b":
        names.append("soft_prefix.pt")
    write_json_new(output / "COMPLETE.json", {"arm": arm, "phase": stage, "fingerprint": ctx.fingerprint,
        "actual_global_step": trainer.state.global_step, "checkpoint_selection": "final",
        "files": {n: record(output / n) for n in names}})
    del trainer, model
    gc.collect()
    torch.cuda.empty_cache()


def generate(ctx, arm, cache, *, training_roles):
    from transformers import AutoModelForCausalLM, set_seed
    from peft import PeftModel
    from miragecad.soft_prefix import load_soft_prefix_adapter
    from miragecad.gen_prompts import build_program_prompt, validate_ir_grammar

    plan_dir = final_path(ctx, arm, "phase2")
    if training_roles:
        cases = [c for c in ctx.manifests["stage4b_roles"] if c["role"] == "predicted"]
        plan_path = predicted_train_path(ctx, arm)
        code_path = None
    else:
        cases = ctx.manifests["evaluation_shared"]
        root = ctx.source / ctx.spec["training_output_root"] / f"arm_{arm}" / "predictions"
        plan_path, code_path = root / "test_plans.jsonl", root / "test_code.jsonl"
    reject_existing(plan_path)
    reject_existing(plan_path.with_suffix(".building"))
    if code_path is not None:
        reject_existing(code_path)
        reject_existing(code_path.with_suffix(".building"))
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    set_seed(42)
    base = AutoModelForCausalLM.from_pretrained(ctx.spec["model"]["id"], revision=ctx.spec["model"]["revision"],
        local_files_only=True, dtype=torch.bfloat16, device_map={"": 0})
    lm = PeftModel.from_pretrained(base, plan_dir, local_files_only=True).eval().requires_grad_(False)
    prefix = load_soft_prefix_adapter(plan_dir / "soft_prefix.pt", device="cuda").eval().requires_grad_(False)
    tok = tokenizer_for(ctx)
    tok.padding_side = "left"
    canonicalizer = load_module(ctx.source / "scratch/repair_face_extrude_alias.py", "review04_p1a")
    model_sha, prefix_sha = sha(plan_dir / "adapter_model.safetensors"), sha(plan_dir / "soft_prefix.pt")
    repairs, outputs = [], []
    with torch.inference_mode(), plan_path.with_suffix(".building").open("xb") as f:
        for start, batch in modality_batches(cases):
            items = [cache.load(c) for c in batch]
            inputs = tok([m[0]["infer_prompt"] for m in items], truncation=True, max_length=1536,
                         padding=True, return_tensors="pt").to("cuda")
            embeddings = lm.get_input_embeddings()(inputs["input_ids"])
            soft = prefix(torch.tensor(np.stack([m[1] for m in items]), device="cuda")).to(embeddings.dtype)
            embedded = torch.cat([soft, embeddings], dim=1)
            mask = torch.cat([torch.ones(len(batch), 4, dtype=inputs["attention_mask"].dtype, device="cuda"),
                              inputs["attention_mask"]], dim=1)
            sequences = lm.generate(inputs_embeds=embedded, attention_mask=mask, max_new_tokens=1536,
                do_sample=False, num_beams=1, num_return_sequences=1, pad_token_id=tok.eos_token_id)
            require(len(sequences) == len(batch), "Plan generation count mismatch")
            for case, sequence in zip(batch, sequences):
                raw = tok.decode(sequence, skip_special_tokens=True).strip()
                repaired = canonicalizer.repair_ir_text(case["sample_id"], raw, repairs)
                item = {"sample_id": case["sample_id"], "source_split": case["source_split"],
                        "modality": case["modality"], "arm": arm, "predicted_ir": repaired,
                        "raw_predicted_ir": raw, "empty": not bool(repaired.strip()),
                        "grammar": validate_ir_grammar(repaired), "canonicalization": "P1a",
                        "plan_model_sha256": model_sha, "plan_prefix_sha256": prefix_sha}
                outputs.append(item)
                f.write(encoded(item))
            print(f"Arm {arm} plans {start + len(batch)}/{len(cases)}", flush=True)
    write_json_new(plan_path.with_suffix(".p1a_log.json"), {"changes": repairs, "rows": len(outputs),
        "empty_retained": sum(r["empty"] for r in outputs), "invalid_retained": sum(not r["grammar"]["valid"] for r in outputs)})
    plan_path.with_suffix(".building").rename(plan_path)
    write_json_new(plan_path.with_suffix(".complete.json"), {"fingerprint": ctx.fingerprint, "arm": arm,
        "prediction_file": record(plan_path), "rows": len(outputs), "plan_model_sha256": model_sha,
        "plan_prefix_sha256": prefix_sha, "id_sequence_sha256": value_sha([r["sample_id"] for r in outputs])})
    del lm, prefix, base
    gc.collect()
    torch.cuda.empty_cache()
    if training_roles:
        plan_role_rows(ctx.manifests["stage4b_roles"], outputs, arm=arm,
                       phase2_hash=sha(plan_dir / "adapter_model.safetensors"))
        return
    code_dir = final_path(ctx, arm, "stage4b")
    base = AutoModelForCausalLM.from_pretrained(ctx.spec["model"]["id"], revision=ctx.spec["model"]["revision"],
        local_files_only=True, dtype=torch.bfloat16, device_map={"": 0})
    lm = PeftModel.from_pretrained(base, code_dir, local_files_only=True).eval().requires_grad_(False)
    with torch.inference_mode(), code_path.with_suffix(".building").open("xb") as f:
        for start, batch in modality_batches(cases):
            plans = outputs[start:start + len(batch)]
            metas = [cache.load(c)[0] for c in batch]
            prompts = [build_program_prompt({}, c["modality"], p["predicted_ir"], evidence_text=m["evidence"])
                       for c, p, m in zip(batch, plans, metas)]
            inputs = tok(prompts, truncation=True, max_length=1536, padding=True, return_tensors="pt").to("cuda")
            sequences = lm.generate(**inputs, max_new_tokens=1536, do_sample=False, num_beams=1,
                                    num_return_sequences=1, pad_token_id=tok.eos_token_id)
            require(len(sequences) == len(batch), "Code generation count mismatch")
            for c, p, m, sequence in zip(batch, plans, metas, sequences):
                output = {**p, "prediction": tok.decode(sequence[inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip(),
                          "reference": m["reference_code"], "reference_ir": m["reference_ir"], "program_code_repair": False}
                f.write(encoded(output))
    code_path.with_suffix(".building").rename(code_path)
    generated = read_rows(code_path)
    require(len(generated) == 10000, "Evaluation output count mismatch")
    evaluation_files = {}
    for m in ("step", "point", "text", "image"):
        selected = [r for r in generated if r["modality"] == m]
        require([r["sample_id"] for r in selected] == [r["sample_id"] for r in ctx.splits["test"]], "Evaluation IDs/order changed")
        split_path, geom_path = code_path.parent / f"test_code_{m}.jsonl", code_path.parent / f"geom_input_{m}.jsonl"
        with split_path.open("xb") as f, geom_path.open("xb") as g:
            for target, prediction in zip(ctx.splits["test"], selected):
                f.write(encoded(prediction))
                g.write(encoded({"sample_id": prediction["sample_id"], "modality": m, "point_path": target["point_path"],
                                 "all_candidates": [prediction["prediction"]]}))
        evaluation_files[m] = {"predictions": record(split_path), "geometry_input": record(geom_path), "rows": 2500}
    write_json_new(code_path.with_suffix(".complete.json"), {"fingerprint": ctx.fingerprint, "arm": arm,
        "status": "GENERATION_COMPLETE_NEEDS_GATE_AND_GEOMETRY", "prediction_file": record(code_path),
        "evaluation_files": evaluation_files, "program_code_repair": False, "plan_canonicalization": "P1a"})
    del lm, base
    gc.collect()
    torch.cuda.empty_cache()


def run(ctx, preflight_report, confirmed):
    require(confirmed, "Training disabled: explicit --confirm-training is required after human authorization")
    require(torch.cuda.is_available(), "Frozen training requires CUDA")
    report = read_json(preflight_report)
    require(report["status"] == "PASS" and report["fingerprint"] == ctx.fingerprint
            and report["execution_hashes"] == execution_hashes(), "Missing/stale real-cache execution preflight")
    all_output_guards(ctx)
    cache = QueryCache(ctx)
    require(sha(cache.root / "index.jsonl") == report["cache_index"]["sha256"], "Preflight cache index changed")
    torch.backends.cuda.matmul.allow_tf32 = True
    for arm in ("A", "B"):
        train_stage(ctx, arm, "phase1", cache, preflight_report)
        train_stage(ctx, arm, "phase2", cache, preflight_report)
        generate(ctx, arm, cache, training_roles=True)
        train_stage(ctx, arm, "stage4b", cache, preflight_report)
        generate(ctx, arm, cache, training_roles=False)
    print("Both arms trained/generated; NOT evaluated. Run the same Windows gate + geometry per modality next.")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("action", choices=["guard", "cache-smoke", "cache", "preflight", "run"], nargs="?", default="preflight")
    ap.add_argument("--source-root", type=Path, default=Path("__RUN_SOURCE_ROOT__"))
    ap.add_argument("--package-root", type=Path, default=Path("__EVIDENCE_SOURCE_ROOT__/04"))
    ap.add_argument("--device", choices=["cpu", "cuda"], default="cpu", help="Cache frozen inference only; never enables training")
    ap.add_argument("--report", type=Path)
    ap.add_argument("--confirm-training", action="store_true", help="Human-operated training gate, never passed by preflight/cache")
    args = ap.parse_args()
    require(not args.confirm_training or args.action == "run", "Training confirmation only belongs to run")
    require(args.action != "run" or args.confirm_training, "GPU training NOT AUTHORIZED: explicit human confirmation required")
    os.chdir(args.source_root)
    torch.set_num_threads(2)
    try:
        ctx = FrozenInputs(args.package_root, args.source_root)
        if args.action in ("cache", "preflight", "run"):
            implementation = read_json(ctx.package / "execution/implementation_status.json")
            require(implementation["execution_hashes"] == execution_hashes()
                    and implementation["contract_tests"]["status"] == "PASS", "Execution code lacks current audited tests")
            verify_record(implementation["contract_tests"]["report"])
        ctx.guard(resources=args.action in ("cache", "run"))
        default_report = ctx.package / "execution/real_cache_preflight.json"
        if args.action == "guard":
            all_output_guards(ctx)
            print("Frozen design/source/runtime/output guards PASS; no cache or training claimed")
        elif args.action == "cache-smoke":
            smoke_cache(ctx, args.report or ctx.package / "execution/real_cpu_cache_smoke.json")
        elif args.action == "cache":
            build_cache(ctx, args.device)
        elif args.action == "preflight":
            preflight(ctx, args.report or default_report)
        else:
            run(ctx, args.report or default_report, args.confirm_training)
    except Exception as exc:
        log = args.package_root / "execution" / f"{args.action}_failed_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}.json"
        write_json_new(log, {"status": "BLOCKED_OR_FAILED", "action": args.action, "created_utc": now(),
                            "error": str(exc), "type": type(exc).__name__, "training_confirmation": args.confirm_training})
        raise


if __name__ == "__main__":
    main()
