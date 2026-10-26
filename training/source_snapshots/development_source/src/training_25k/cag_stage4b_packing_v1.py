"""Stage4b-only supervised packing overlay; never used for plan training/inference."""
from __future__ import annotations

import hashlib
import json

import torch
from torch.utils.data import Dataset

POLICY = "stage4b_preserve_full_code_truncate_construction_plan_v1"
MAX_LENGTH = 1536
SENTINEL = "__R04_STAGE4B_CONSTRUCTION_PLAN_FIELD_7da5e9__"


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=True, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def check(ok, message):
    if not ok:
        raise ValueError(message)


def tokenize_stage4b_preserve_target(tokenizer, plan, target, *, modality, evidence, case_id):
    from miragecad.gen_prompts import build_program_prompt

    check(isinstance(plan, str), f"{case_id}: missing construction plan (empty string is allowed)")
    check(isinstance(target, str) and target.strip(), f"{case_id}: empty reference-code target")
    check(isinstance(evidence, str), f"{case_id}: missing frozen query evidence")
    check(tokenizer.is_fast and tokenizer.eos_token is not None, f"{case_id}: fast tokenizer/EOS required")
    check(SENTINEL not in plan and SENTINEL not in evidence, f"{case_id}: reserved sentinel collision")
    template = build_program_prompt({}, modality, SENTINEL, evidence_text=evidence)
    check(template.count(SENTINEL) == 1, f"{case_id}: ambiguous plan field")
    prefix, suffix = template.split(SENTINEL)
    prompt = build_program_prompt({}, modality, plan, evidence_text=evidence)
    check(prompt == prefix + plan + suffix, f"{case_id}: unexpected prompt serialization")
    target_ids = tokenizer(target + tokenizer.eos_token, add_special_tokens=False)["input_ids"]
    check(target_ids and target_ids[-1] == tokenizer.eos_token_id, f"{case_id}: appended EOS missing")
    prompt_ids = tokenizer(prompt, add_special_tokens=True)["input_ids"]
    original_prompt_count = len(prompt_ids)
    empty_ids = tokenizer(prefix + suffix, add_special_tokens=True)["input_ids"]
    check(len(empty_ids) + len(target_ids) <= MAX_LENGTH,
          f"{case_id}: instruction+target overflow: scaffold={len(empty_ids)}, "
          f"target={len(target_ids)}, cap={MAX_LENGTH}; no row dropping or target clipping")
    plan_encoding = tokenizer(plan, add_special_tokens=False, return_offsets_mapping=True)
    offsets = plan_encoding["offset_mapping"]
    check(len(offsets) == len(plan_encoding["input_ids"]), f"{case_id}: invalid tokenizer offsets")
    check(all(0 <= start <= end <= len(plan) for start, end in offsets), f"{case_id}: invalid text offsets")
    visible = plan
    needs_truncation = original_prompt_count + len(target_ids) > MAX_LENGTH
    if needs_truncation:
        # Offset endpoints preserve literal Unicode text. Recount the whole prompt:
        # BPE insertion-boundary lengths are not additive or necessarily monotone.
        budget = MAX_LENGTH - len(empty_ids) - len(target_ids)
        k = min(len(offsets), budget)
        while True:
            end = offsets[k - 1][1] if k else 0
            visible = plan[:end]
            prompt_ids = tokenizer(prefix + visible + suffix, add_special_tokens=True)["input_ids"]
            if len(prompt_ids) + len(target_ids) <= MAX_LENGTH:
                break
            k -= 1
            check(k >= 0, f"{case_id}: empty-plan endpoint unexpectedly failed")
        check(len(visible) < len(plan), f"{case_id}: overflowing plan was not shortened")
    ids = prompt_ids + target_ids
    labels = [-100] * len(prompt_ids) + target_ids
    check(len(ids) <= MAX_LENGTH, f"{case_id}: packed sequence overflow")
    check([x for x in labels if x != -100] == target_ids, f"{case_id}: full target supervision changed")
    legacy_retained = min(len(target_ids), max(0, MAX_LENGTH - original_prompt_count))
    audit = {
        "policy": POLICY, "max_length": MAX_LENGTH, "plan_truncated": needs_truncation,
        "source_plan_sha256": digest(plan), "reference_code_sha256": digest(target),
        "source_plan_characters": len(plan), "retained_plan_characters": len(visible),
        "original_plan_tokens": len(plan_encoding["input_ids"]),
        "retained_plan_tokens": len(tokenizer(visible, add_special_tokens=False)["input_ids"]),
        "retained_plan_sha256": digest(visible), "visible_plan": visible,
        "original_prompt_tokens": original_prompt_count, "final_prompt_tokens": len(prompt_ids),
        "full_target_tokens_including_eos": len(target_ids), "full_target_ids_sha256": digest(target_ids),
        "final_sequence_tokens": len(ids), "supervised_tokens": len(target_ids),
        "legacy_supervised_tokens": legacy_retained, "legacy_zero_supervision": legacy_retained == 0,
        "model_plan_empty": not plan, "plan_emptied_by_budget": bool(plan) and not visible,
        "protected_scaffold_sha256": digest([prefix, suffix]), "evidence_sha256": digest(evidence),
        "input_ids_sha256": digest(ids), "labels_sha256": digest(labels),
        "zero_supervision": False, "instruction_target_overflow": False,
    }
    feature = {"input_ids": torch.tensor(ids, dtype=torch.long),
               "labels": torch.tensor(labels, dtype=torch.long),
               "attention_mask": torch.ones(len(ids), dtype=torch.long)}
    return feature, audit


class Stage4bPackedDataset(Dataset):
    """Fixed role manifest; no filtering or empty-prediction fallback to GT."""

    def __init__(self, cases, cache, tokenizer, predictions):
        self.cases, self.cache, self.tokenizer, self.predictions = cases, cache, tokenizer, predictions

    def __len__(self):
        return len(self.cases)

    def audited_item(self, i):
        case = self.cases[i]
        meta, _, _ = self.cache.load(case)
        role = case.get("role", "gt")
        check(role in ("gt", "predicted"), f"{case['sample_id']}: unknown role")
        if role == "predicted":
            check(case["sample_id"] in self.predictions, f"{case['sample_id']}: missing predicted-role plan")
            plan = self.predictions[case["sample_id"]]["predicted_ir"]
        else:
            plan = meta["reference_ir"]
        feature, audit = tokenize_stage4b_preserve_target(
            self.tokenizer, plan, meta["reference_code"], modality=case["modality"],
            evidence=meta["evidence"], case_id=f"{case['sample_id']}/{role}")
        audit.update({"case_index": case["case_index"], "sample_id": case["sample_id"],
                      "role": role, "modality": case["modality"], "source_split": case["source_split"]})
        return feature, audit

    def __getitem__(self, i):
        return self.audited_item(i)[0]
