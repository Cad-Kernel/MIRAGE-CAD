#!/usr/bin/env python3
"""Stage4b-only packing overlay. CPU preflight by default; human starts each arm."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from functools import partial
import gc
import os
from pathlib import Path

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import torch
from torch.utils.data import Dataset
from transformers import TrainerCallback
import cag_exposure_policy as original
import cag_exposure_policy_b_only as lineage
from cag_exposure_policy_core import (
    FrozenInputs, QueryCache, collate, read_json, read_rows, record, reject_existing,
    require, sha, value_sha, verify_record, write_json_new,
)
from cag_stage4b_packing_v1 import Stage4bPackedDataset, digest

VERSION = "review04_stage4b_execution_v1"
SCHEMA = "review04_stage4b_overlay_final_v1"
PARENT, AMENDMENT = lineage.PARENT, lineage.AMENDMENT


def now():
    return datetime.now(timezone.utc).isoformat()


def own_sources():
    root = Path(__file__).resolve().parent
    return {n: record(root / n) for n in ("cag_stage4b_execution.py", "cag_run_stage4b_only.sh")}


def output_path(ctx, arm):
    require(arm in ("A", "B"), "Only Stage4b arm A or B is supported")
    root = lineage.arm_roots(ctx)[0 if arm == "A" else 1]
    output = ctx.source / ctx.spec["stage4b"][f"{arm}_output"]
    require(output == root / "stage4b" and not output.is_symlink() and not root.is_symlink(), "Unsafe Stage4b output path")
    require(output.resolve() != (ctx.source / ctx.spec["shared_checkpoints"]["stage4"]).resolve(), "Output aliases shared Stage4")
    return output


def protected_snapshot(ctx):
    # Only the fixed direct Stage4b subtree is writable. Protect all completed
    # plan checkpoints, predictions, B-only markers and any other arm assets.
    result = {}
    for arm, root in zip(("A", "B"), lineage.arm_roots(ctx)):
        require(root.is_dir() and not root.is_symlink(), "Completed plan arm root missing/linked")
        files, directories = {}, []
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(root)
            if relative.parts[0] == "stage4b":
                continue
            require(not path.is_symlink(), f"Linked protected plan asset: {path}")
            if path.is_file():
                files[relative.as_posix()] = {"sha256": sha(path), "bytes": path.stat().st_size,
                                             "mtime_ns": path.stat().st_mtime_ns}
            elif path.is_dir():
                directories.append(relative.as_posix())
            else:
                raise ValueError(f"Unsupported protected asset: {path}")
        result[arm] = {"root": str(root), "files": files, "directories": directories}
    return result


def verify_protected(ctx, expected):
    require(protected_snapshot(ctx) == expected, "Completed plan branch/predictions changed; stop without retraining or regeneration")


def verify_budget(ctx):
    expected = ctx.actuals["checks"]["budget"]["phases"]["stage4b"]
    lr = read_json(ctx.package / "manifests/lr_vectors.json")["stage4b"]
    require(ctx.spec["stage4b"]["expected_global_step"] == expected["trainer_max_steps"] == 1182,
            "Stage4b update budget drift")
    # The frozen vector includes the scheduler's terminal post-update endpoint.
    # on_step_begin consumes indices0..1181; index1182 is not an extra update.
    require(len(lr) == 1183 and value_sha(lr) == expected["lr_vector_sha256"], "Frozen Stage4b LR endpoint/hash drift")
    return expected, lr


def checked_inputs(ctx):
    common = lineage.checked_inputs(ctx)
    lock = lineage.policy_lock(ctx, lineage.policy_identity(ctx), create=False)
    path = ctx.package / "execution/stage4b_packing_v1_preflight_after_B/preflight_actuals.json"
    paired = read_json(path)
    require(paired["status"] == "PASS_PAIRED" and paired["paired_actual_plan_preflight"] == "PASS", "Actual paired packing PASS required")
    require(paired["amendment_fingerprint"] == AMENDMENT
            and paired["policy_identity"] == read_json(lock["path"])["policy"]["identity"], "Packing lock drift")
    lineage.verify_records({k: paired[k] for k in ("policy_identity", "audit_script", "cache_complete", "cache_index", "provenance")})
    for label in ("A", "B", "validation"):
        require(paired["datasets"][label]["status"] == "PASS" and paired["datasets"][label]["failure_rows"] == 0,
                "Packing failures are not acceptable")
        verify_record(paired["datasets"][label]["row_audit"])
    registration = ctx.package / "execution/plan_branches_and_paired_preflight_20261018/actuals.json"
    registered = read_json(registration)
    require(registered["status"] == "B_PLAN_BRANCH_COMPLETE_PAIRED_CPU_PREFLIGHT_PASS", "Plan-branch registration missing")
    verify_record(registered["B_only_completion"])
    branches = {arm: lineage.verify_plan_branch(ctx, arm) for arm in ("A", "B")}
    require(branches == registered["branches"], "Registered plan branch changed")
    complete = read_json(registered["B_only_completion"]["path"])
    require(complete["A"] == branches["A"] and complete["B"] == branches["B"]
            and complete["sources"] == lineage.own_sources() and complete["policy_lock"] == lock, "B-only lineage mismatch")
    stage4 = ctx.actuals["checks"]["checkpoints"]["components"]["qwen25_coder_1_5b_program_25k"]
    lineage.verify_records(stage4)
    require(not (ctx.source / ctx.spec["shared_checkpoints"]["stage4"] / "soft_prefix.pt").exists(),
            "Shared code-decoder Stage4 must not acquire a plan prefix")
    verify_budget(ctx)
    test_path = ctx.package / "execution/stage4b_execution_contract_tests_v2.json"
    tests = read_json(test_path)
    require(tests["status"] == "PASS" and tests["sources"] == own_sources(), "Current Stage4b CPU tests required")
    verify_record(tests["test_source"])
    dependencies = {"common": common, "policy_lock": lock, "paired_packing": record(path),
                    "registered_plan_branches": record(registration), "branches": branches,
                    "shared_stage4": stage4, "tests": record(test_path), "sources": own_sources(),
                    "execution_spec": record(ctx.package / "05_execution_spec.json"),
                    "lr_vectors": record(ctx.package / "manifests/lr_vectors.json")}
    return dependencies, paired


def execution_fingerprint(dependencies):
    return value_sha({"version": VERSION, "parent": PARENT, "amendment": AMENDMENT, "dependencies": dependencies})


class IndexedPackedDataset(Dataset):
    def __init__(self, features):
        self.features = features

    def __len__(self):
        return len(self.features)

    def __getitem__(self, index):
        return {**self.features[index], "_case_index": index}


def indexed_collator(features, pad_id):
    return {**collate(features, pad_id), "_case_index": [f["_case_index"] for f in features]}


def materialize(ctx, label, cache, tok, paired):
    expected = read_rows(paired["datasets"][label]["row_audit"]["path"])
    if label == "validation":
        cases = [{"case_index": i, "source_row": i, "sample_id": r["sample_id"], "source_split": "val",
                  "modality": "step", "role": "gt"} for i, r in enumerate(ctx.splits["val"])]
        predictions = {}
    else:
        cases = ctx.manifests["stage4b_roles"]
        predictions = {r["sample_id"]: r for r in read_rows(original.predicted_train_path(ctx, label))}
    source = Stage4bPackedDataset(cases, cache, tok, predictions)
    require(len(expected) == len(source) == (2500 if label == "validation" else 3150), "Real dataset rows changed")
    features, identities, target_total, input_total, crops = [], [], 0, 0, Counter()
    for i, baseline in enumerate(expected):
        feature, audit = source.audited_item(i)
        for key in ("case_index", "sample_id", "role", "input_ids_sha256", "labels_sha256", "full_target_ids_sha256"):
            require(audit[key] == baseline[key], f"{label}/{i}: packed input differs from paired PASS: {key}")
        target = feature["labels"][feature["labels"] != -100].tolist()
        require(target and target[-1] == tok.eos_token_id and digest(target) == baseline["full_target_ids_sha256"], "Full target/EOS loss")
        require(len(feature["input_ids"]) <= 1536 and int(feature["attention_mask"].sum()) == len(feature["input_ids"]), "Invalid packed mask/length")
        target_total += len(target)
        input_total += len(feature["input_ids"])
        if audit["plan_truncated"]:
            crops[audit["role"]] += 1
        identities.append([i, audit["input_ids_sha256"], audit["labels_sha256"]])
        features.append(feature)
    require(target_total == paired["datasets"][label]["full_supervised_tokens_one_pass"], "Target-token exposure drift")
    return IndexedPackedDataset(features), {
        "rows": len(features), "full_target_tokens_one_pass": target_total, "input_tokens_one_pass": input_total,
        "plan_crops": dict(crops), "EOS_preserved": "all", "zero_supervision_rows": 0, "target_truncated_rows": 0,
        "ordered_feature_ids_sha256": value_sha(identities), "paired_row_audit": paired["datasets"][label]["row_audit"]}


def new_trace():
    return {"epochs": [], "current_indices": [], "lr_steps_checked": 0,
            "current_target_tokens": 0, "current_input_tokens": 0, "current_padding_tokens": 0}


class RuntimeAudit(TrainerCallback):
    def __init__(self, frozen, lr, trace, materialized, verify_readonly):
        self.frozen, self.lr, self.trace, self.data, self.verify_readonly = frozen, lr, trace, materialized, verify_readonly

    def on_train_begin(self, args, state, control, optimizer=None, **kwargs):
        require(state.global_step == 0 and state.max_steps == self.frozen["trainer_max_steps"], "Not fresh matched-budget Stage4b training")
        require(optimizer is not None and len(optimizer.state) == 0, "Optimizer state was not reset")

    def on_step_begin(self, args, state, control, optimizer=None, **kwargs):
        require(0 <= state.global_step < len(self.lr), "Step outside frozen LR vector")
        require(all(abs(group["lr"] - self.lr[state.global_step]) < 1e-12 for group in optimizer.param_groups), "LR schedule drift")
        self.trace["lr_steps_checked"] += 1

    def on_epoch_end(self, args, state, control, **kwargs):
        order, epoch = self.trace["current_indices"], len(self.trace["epochs"])
        require(sorted(order) == list(range(self.data["rows"])), "Dropped/duplicated training rows")
        require(epoch < len(self.frozen["sampler_epoch_index_sha256"])
                and value_sha(order) == self.frozen["sampler_epoch_index_sha256"][epoch], "Sampler order changed")
        require(self.trace["current_target_tokens"] == self.data["full_target_tokens_one_pass"], "Actual target-token exposure mismatch")
        require(self.trace["current_input_tokens"] == self.data["input_tokens_one_pass"], "Actual input-token exposure mismatch")
        self.verify_readonly()
        self.trace["epochs"].append({"epoch": epoch, "presentations": len(order), "index_sha256": value_sha(order),
            "supervised_target_tokens": self.trace["current_target_tokens"], "input_tokens": self.trace["current_input_tokens"],
            "padding_tokens": self.trace["current_padding_tokens"]})
        for key in ("current_target_tokens", "current_input_tokens", "current_padding_tokens"):
            self.trace[key] = 0
        self.trace["current_indices"] = []


def trainer_class(tok, trace):
    parent = original.adapter_trainer_class("stage4b", tok, trace)

    class TokenAuditedTrainer(parent):
        def training_step(self, model, inputs, num_items_in_batch=None):
            trace["current_target_tokens"] += int((inputs["labels"] != -100).sum().item())
            trace["current_input_tokens"] += int(inputs["attention_mask"].sum().item())
            trace["current_padding_tokens"] += int((inputs["attention_mask"] == 0).sum().item())
            return super().training_step(model, inputs, num_items_in_batch)

    return TokenAuditedTrainer


def build_trainer(ctx, model, tok, dataset, validation, trace, materialized, verify_readonly, output, *, cpu):
    args = original.training_args(ctx, "stage4b", output, cpu=cpu)
    require(args.world_size == 1, "Only the frozen single-process run is allowed")
    frozen, lr = verify_budget(ctx)
    audit = RuntimeAudit(frozen, lr, trace, materialized, verify_readonly)
    klass = trainer_class(tok, trace)
    return klass(model=model, args=args, train_dataset=dataset, eval_dataset=validation,
                 data_collator=partial(indexed_collator, pad_id=tok.pad_token_id), processing_class=tok,
                 callbacks=[audit])


def cpu_traverse(ctx, tok, dataset, validation, materialized, output):
    class NoForward(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.anchor = torch.nn.Parameter(torch.zeros(1))

        def forward(self, **kwargs):
            raise RuntimeError("CPU audit must never call model.forward")

    trainer = build_trainer(ctx, NoForward(), tok, dataset, validation, new_trace(), materialized, lambda: None, output, cpu=True)
    loader = trainer.get_train_dataloader()
    require(trainer.set_initial_training_values(trainer.args, loader)[-1] == 1182, "Real Stage4b Trainer budget mismatch")
    hashes, groups, targets = [], [], 0
    for epoch in range(3):
        loader.set_epoch(epoch)
        iterator, order = iter(loader), []
        while True:
            batches, _ = trainer.get_batch_samples(iterator, 8, torch.device("cpu"))
            if not batches:
                break
            groups.append(len(batches))
            for batch in batches:
                order.extend(batch["_case_index"])
                targets += int((batch["labels"] != -100).sum())
                require(torch.all(batch["labels"][batch["attention_mask"] == 0] == -100).item(), "Padding is supervised")
        require(sorted(order) == list(range(3150)), "CPU traversal dropped/duplicated rows")
        hashes.append(value_sha(order))
    expected = ctx.actuals["checks"]["budget"]["phases"]["stage4b"]
    require(hashes == expected["sampler_epoch_index_sha256"] and len(groups) == 1182, "Actual packed-data sampler/budget drift")
    require(targets == 3 * materialized["full_target_tokens_one_pass"], "CPU packed target exposure drift")
    return {"rows": 3150, "epochs": 3, "planned_updates": len(groups), "group_sizes": dict(Counter(groups)),
            "sampler_epoch_index_sha256": hashes, "target_tokens_three_epochs": targets, "model_forward_called": False}


def verify_final_trace(trace, materialized, frozen):
    require(trace["lr_steps_checked"] == frozen["trainer_max_steps"] == 1182, "Incomplete actual LR trace")
    require(len(trace["epochs"]) == 3 and not trace["current_indices"], "Incomplete actual epoch trace")
    require([e["index_sha256"] for e in trace["epochs"]] == frozen["sampler_epoch_index_sha256"], "Final sampler trace drift")
    require(all(e["presentations"] == materialized["rows"] for e in trace["epochs"]), "Final row presentation count drift")
    require(sum(e["supervised_target_tokens"] for e in trace["epochs"]) == 3 * materialized["full_target_tokens_one_pass"],
            "Incomplete actual full-target exposure")


def final_stage4b(ctx, arm, fingerprint):
    output = output_path(ctx, arm)
    complete = read_json(output / "COMPLETE.json")
    require(complete.get("schema") == SCHEMA and complete.get("fingerprint") == fingerprint,
            "Not the audited Stage4b overlay final")
    require(complete["parent_fingerprint"] == PARENT and complete["amendment_fingerprint"] == AMENDMENT
            and complete["arm"] == arm and complete["phase"] == "stage4b", "Stage4b lineage/arm mismatch")
    names = {"adapter_model.safetensors", "adapter_config.json", "tokenizer.json", "tokenizer_config.json",
             "trainer_state.json", "training_report.json", "STARTED.json", "PACKING_ACTUALS.json"}
    require(set(complete["files"]) == names and all(Path(r["path"]).resolve() == (output / n).resolve()
            for n, r in complete["files"].items()), "Stage4b final files point outside the selected output")
    lineage.verify_records(complete["files"])
    state, report = read_json(output / "trainer_state.json"), read_json(output / "training_report.json")
    require(complete["checkpoint_selection"] == report["checkpoint_selection"] == "final"
            and complete["actual_global_step"] == state["global_step"] == report["actual_global_step"] == 1182,
            "Native actual Stage4b step/checkpoint mismatch")
    initial = ctx.source / ctx.spec["shared_checkpoints"]["stage4"]
    expected = {n: record(initial / n) for n in ("adapter_model.safetensors", "adapter_config.json")}
    require(report["startup"] == expected and report["fingerprint"] == fingerprint
            and report["arm"] == arm and report["stage"] == "stage4b"
            and report["parent_fingerprint"] == PARENT and report["amendment_fingerprint"] == AMENDMENT
            and report["fresh_optimizer_and_scheduler"], "Stage4b startup/execution mismatch")
    verify_record(report["preflight"])
    pre = read_json(report["preflight"]["path"])
    require(pre["status"] == "PASS_STAGE4B_EXECUTION_CPU_PREFLIGHT" and pre["execution_fingerprint"] == fingerprint
            and report["dataset"] == pre["arms"][arm]["dataset"] and report["validation"] == pre["validation"],
            "Stage4b final dataset/preflight mismatch")
    verify_final_trace(report["exposure_trace"], report["dataset"], ctx.actuals["checks"]["budget"]["phases"]["stage4b"])
    return record(output / "COMPLETE.json")


def run_guards(ctx, arm, fingerprint):
    target = output_path(ctx, arm)
    reject_existing(target)
    if arm == "A":
        reject_existing(output_path(ctx, "B"))
    else:
        final_stage4b(ctx, "A", fingerprint)
    return target


def preflight(ctx, report_path):
    report_path = lineage.audit_report_path(ctx, report_path)
    reject_existing(report_path)
    for arm in ("A", "B"):
        reject_existing(output_path(ctx, arm))
    dependencies, paired = checked_inputs(ctx)
    fingerprint = execution_fingerprint(dependencies)
    protected = protected_snapshot(ctx)
    cache, tok = QueryCache(ctx, verify=False), original.tokenizer_for(ctx)
    validation, val_summary = materialize(ctx, "validation", cache, tok, paired)
    summaries = {}
    for arm in ("A", "B"):
        dataset, summary = materialize(ctx, arm, cache, tok, paired)
        summaries[arm] = {"dataset": summary, "cpu_dataloader": cpu_traverse(ctx, tok, dataset, validation, summary,
                                  ctx.package / f"execution/cpu_probe/stage4b_overlay_{arm}")}
        print(f"Stage4b {arm}: actual packed3150 x3 ->1182 planned updates; full target/EOS PASS; no training", flush=True)
        del dataset
    require(summaries["A"]["dataset"]["full_target_tokens_one_pass"] == summaries["B"]["dataset"]["full_target_tokens_one_pass"],
            "Paired target exposure differs")
    verify_protected(ctx, protected)
    inventory = report_path.with_suffix(".protected_inventory.json")
    reject_existing(inventory)
    write_json_new(inventory, protected)
    write_json_new(report_path, {"version": VERSION, "status": "PASS_STAGE4B_EXECUTION_CPU_PREFLIGHT", "created_utc": now(),
        "parent_fingerprint": PARENT, "amendment_fingerprint": AMENDMENT, "execution_fingerprint": fingerprint,
        "dependencies": dependencies, "arms": summaries, "validation": val_summary, "protected_inventory": record(inventory),
        "training_started": False, "actual_global_steps": None, "both_Stage4b_outputs_absent": True,
        "scope": "Actual full packed datasets and real indexed collator/Trainer CPU traversal; no forward/backward/optimizer step",
        "raw_resource_check": "sealed inventory checked here; full source-resource byte verification also runs at manual training startup",
        "cache_check": "full index/identity coverage plus byte/tensor verification of all consumed inputs; no cache regeneration"})
    print(f"Stage4b-only execution CPU preflight PASS: {report_path}; no training", flush=True)


def run(ctx, arm, report_path, *, confirmed):
    require(confirmed, "Stage4b training NOT AUTHORIZED: human --confirm-training required")
    require(arm in ("A", "B"), "Choose exactly one Stage4b arm")
    report_path = lineage.audit_report_path(ctx, report_path)
    pre = read_json(report_path)
    require(pre["status"] == "PASS_STAGE4B_EXECUTION_CPU_PREFLIGHT" and pre["version"] == VERSION, "Current Stage4b CPU preflight required")
    dependencies, paired = checked_inputs(ctx)
    fingerprint = execution_fingerprint(dependencies)
    require(pre["dependencies"] == dependencies and pre["execution_fingerprint"] == fingerprint, "Stage4b preflight/source/input drift")
    verify_record(pre["protected_inventory"])
    protected = read_json(pre["protected_inventory"]["path"])
    verify_protected(ctx, protected)
    output = run_guards(ctx, arm, fingerprint)
    require(torch.cuda.is_available(), "Explicit Stage4b run requires CUDA")
    ctx.guard(resources=True)
    peer_snapshot = lineage.tree_snapshot(output_path(ctx, "A")) if arm == "B" else None

    def verify_readonly():
        verify_protected(ctx, protected)
        require(own_sources() == dependencies["sources"] and lineage.execution_hashes() == dependencies["common"]["original_execution"],
                "Execution source changed during training")
        verify_record(dependencies["policy_lock"])
        verify_record(dependencies["common"]["cache_index"])
        verify_record(dependencies["common"]["cache_complete"])
        if arm == "A":
            reject_existing(output_path(ctx, "B"))
        else:
            lineage.assert_tree_unchanged(output_path(ctx, "A"), peer_snapshot)

    cache, tok = QueryCache(ctx), original.tokenizer_for(ctx)
    dataset, summary = materialize(ctx, arm, cache, tok, paired)
    validation, val_summary = materialize(ctx, "validation", cache, tok, paired)
    require(summary == pre["arms"][arm]["dataset"] and val_summary == pre["validation"], "Materialized dataset differs from CPU PASS")
    require(original.count_loader(ctx, "stage4b", len(dataset))["planned_updates"] == 1182, "Manual run budget drift")
    output = run_guards(ctx, arm, fingerprint)
    output.mkdir(parents=True, exist_ok=False)
    write_json_new(output / "STARTED.json", {"version": VERSION, "arm": arm, "phase": "stage4b", "created_utc": now(),
        "fingerprint": fingerprint, "parent_fingerprint": PARENT, "amendment_fingerprint": AMENDMENT,
        "preflight": record(report_path), "policy_lock": dependencies["policy_lock"], "sources": own_sources(),
        "implicit_resume": False, "new_optimizer_and_scheduler": True, "seed": 42})
    write_json_new(output / "PACKING_ACTUALS.json", {"dataset": summary, "validation": val_summary,
        "policy_lock": dependencies["policy_lock"], "paired_preflight": dependencies["paired_packing"]})
    torch.backends.cuda.matmul.allow_tf32 = True
    model, startup = original.load_train_model(ctx, arm, "stage4b")
    initial = ctx.source / ctx.spec["shared_checkpoints"]["stage4"]
    require(startup == {n: record(initial / n) for n in ("adapter_model.safetensors", "adapter_config.json")}, "Actual shared Stage4 startup drift")
    trace = new_trace()
    from transformers import set_seed
    set_seed(42)
    trainer = build_trainer(ctx, model, tok, dataset, validation, trace, summary, verify_readonly, output, cpu=False)
    require(trainer.set_initial_training_values(trainer.args, trainer.get_train_dataloader())[-1] == 1182, "Native training budget mismatch")
    try:
        trainer.train(resume_from_checkpoint=None)
        require(trainer.state.global_step == 1182, "Actual final Stage4b global_step mismatch")
        verify_final_trace(trace, summary, ctx.actuals["checks"]["budget"]["phases"]["stage4b"])
        require(all(torch.isfinite(p).all().item() for p in model.parameters() if p.requires_grad), "Nonfinite trained weights")
        trainer.save_model(output)
        trainer.state.save_to_json(output / "trainer_state.json")
        verify_readonly()
        write_json_new(output / "training_report.json", {"version": VERSION, "arm": arm, "stage": "stage4b", "created_utc": now(),
            "fingerprint": fingerprint, "parent_fingerprint": PARENT, "amendment_fingerprint": AMENDMENT,
            "checkpoint_selection": "final", "actual_global_step": trainer.state.global_step, "startup": startup,
            "dataset": summary, "validation": val_summary, "exposure_trace": trace, "policy_lock": dependencies["policy_lock"],
            "fresh_optimizer_and_scheduler": True, "sources": own_sources(), "preflight": record(report_path)})
        names = ("adapter_model.safetensors", "adapter_config.json", "tokenizer.json", "tokenizer_config.json",
                 "trainer_state.json", "training_report.json", "STARTED.json", "PACKING_ACTUALS.json")
        write_json_new(output / "COMPLETE.json", {"schema": SCHEMA, "version": VERSION, "arm": arm, "phase": "stage4b",
            "fingerprint": fingerprint, "parent_fingerprint": PARENT, "amendment_fingerprint": AMENDMENT,
            "checkpoint_selection": "final", "actual_global_step": 1182, "files": {n: record(output / n) for n in names}})
        final_stage4b(ctx, arm, fingerprint)
    finally:
        verify_readonly()
    del trainer, model
    gc.collect()
    torch.cuda.empty_cache()
    print(f"Stage4b {arm} COMPLETE: native actual_global_step=1182, final adapter saved. STOP; no plan training or prediction/evaluation ran.", flush=True)


def parser():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("action", choices=("preflight", "run"), nargs="?", default="preflight")
    ap.add_argument("--arm", choices=("A", "B"))
    ap.add_argument("--confirm-training", action="store_true")
    ap.add_argument("--source-root", type=Path, default=Path("__RUN_SOURCE_ROOT__"))
    ap.add_argument("--package-root", type=Path, default=Path("__EVIDENCE_SOURCE_ROOT__/04"))
    ap.add_argument("--report", type=Path)
    return ap


def main():
    args = parser().parse_args()
    require(args.action != "run" or (args.confirm_training and args.arm), "Stage4b training NOT AUTHORIZED: --arm and --confirm-training required")
    require(args.action != "preflight" or (not args.arm and not args.confirm_training), "Preflight checks both arms; no arm/training flag allowed")
    os.chdir(args.source_root)
    torch.set_num_threads(2)
    ctx = FrozenInputs(args.package_root, args.source_root).guard()
    report = args.report or ctx.package / "execution/stage4b_execution_preflight_v1.json"
    try:
        if args.action == "preflight":
            preflight(ctx, report)
        else:
            run(ctx, args.arm, report, confirmed=args.confirm_training)
    except Exception as exc:
        write_json_new(ctx.package / f"execution/stage4b_execution_failed_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}.json",
                       {"version": VERSION, "created_utc": now(), "action": args.action, "arm": args.arm,
                        "status": "FAILED_NO_AUTOMATIC_RESUME", "error": str(exc), "type": type(exc).__name__})
        raise


if __name__ == "__main__":
    main()
