"""CPU contracts only: no Trainer.train, backward or optimizer step is allowed."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import torch

SOURCE = Path("__RUN_SOURCE_ROOT__")
PACKAGE = Path(__file__).resolve().parents[1]
IMPLEMENTATION = Path("__DEV_ROOT__/src/training_25k")
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(IMPLEMENTATION))

from cag_exposure_policy_core import (
    CodeDataset, PlanDataset, QueryCache, array_sha, collate, encoded, final_component,
    execution_hashes, plan_role_rows, record, reject_existing, sha, tokenize_supervised, write_json_new,
)
from cag_exposure_policy import adapter_trainer_class, count_loader, main, modality_batches


class Tokenizer:
    pad_token_id = 0
    eos_token = "~"

    def __call__(self, text, add_special_tokens=True):
        return {"input_ids": ([1] if add_special_tokens else []) + [2 + ord(c) % 20 for c in text]}

    def save_pretrained(self, directory):
        write_json_new(Path(directory) / "test_tokenizer.json", {"fixture": True})


class FixtureContext:
    fingerprint = "TEST_FIXTURE_ONLY_NEVER_A_TRAINING_CACHE"

    def __init__(self, directory, cases):
        self.cache_root = Path(directory)
        self.cases = cases

    def required_cases(self):
        return self.cases

    def key(self, case):
        import hashlib
        return hashlib.sha256(encoded(case)).hexdigest()


def make_fixture(directory):
    cases = [{"case_index": i, "source_row": i, "sample_id": f"fixture_{i}", "modality": m, "source_split": "train"}
             for i, m in enumerate(("step", "point"))]
    ctx = FixtureContext(directory, cases)
    entries = []
    for c in cases:
        key = ctx.key(c)
        stem = ctx.cache_root / key[:2] / key
        stem.parent.mkdir(parents=True, exist_ok=True)
        latent = np.arange(512, dtype=np.float32)
        points = np.ones((1024, 3), np.float32) if c["modality"] == "point" else np.empty((0, 3), np.float32)
        meta = {"key": key, "identity": ["train", c["sample_id"], c["modality"]], "train_prompt": "plan",
                "infer_prompt": "infer", "reference_ir": "GT_FIXTURE_PLAN", "reference_code": "part = 1",
                "evidence": "FIXTURE_EVIDENCE"}
        np.savez(stem.with_suffix(".npz"), latent=latent, points=points)
        write_json_new(stem.with_suffix(".json"), meta)
        entries.append({"identity": meta["identity"], "key": key, "metadata_sha256": sha(stem.with_suffix(".json")),
            "npz_sha256": sha(stem.with_suffix(".npz")), "latent_sha256": array_sha(latent), "points_sha256": array_sha(points)})
    (ctx.cache_root / "index.jsonl").write_bytes(b"".join(encoded(x) for x in entries))
    write_json_new(ctx.cache_root / "COMPLETE.json", {"fingerprint": ctx.fingerprint, "entries": len(entries),
                                                      "index_sha256": sha(ctx.cache_root / "index.jsonl")})
    return ctx, cases


class DataContracts(unittest.TestCase):
    def test_run_without_human_confirmation_is_rejected_before_loading(self):
        with patch.object(sys, "argv", ["cag_exposure_policy.py", "run"]):
            with self.assertRaisesRegex(ValueError, "NOT AUTHORIZED"):
                main()

    def test_real_cache_required(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "absent/incomplete"):
                QueryCache(FixtureContext(directory, []))

    def test_shared_cached_tensor_hashes_and_first_last_batches(self):
        with tempfile.TemporaryDirectory() as directory:
            ctx, cases = make_fixture(directory)
            cache = QueryCache(ctx)
            a = PlanDataset(cases, cache, Tokenizer())
            b = PlanDataset(cases, cache, Tokenizer())
            self.assertTrue(torch.equal(a[0]["z_ir_hat"], b[0]["z_ir_hat"]))
            self.assertEqual(array_sha(cache.load(cases[1])[2]), cache.entries[("train", "fixture_1", "point")]["points_sha256"])
            batch = collate([a[0], b[-1]], 0)
            self.assertEqual(tuple(batch["z_ir_hat"].shape), (2, 512))
            self.assertEqual(tuple(batch["input_ids"].shape), tuple(batch["labels"].shape))

    def test_cache_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            ctx, cases = make_fixture(directory)
            key = ctx.key(cases[0])
            (Path(directory) / key[:2] / f"{key}.npz").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "Cache bytes changed"):
                QueryCache(ctx)

    def test_wrong_cache_coverage_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            ctx, cases = make_fixture(directory)
            ctx.cases = cases[:1]
            with self.assertRaisesRegex(ValueError, "coverage mismatch"):
                QueryCache(ctx)

    def test_all_masked_target_rejected(self):
        with self.assertRaisesRegex(ValueError, "All target tokens truncated"):
            tokenize_supervised(Tokenizer(), "x" * 1600, "part = 1")

    def test_empty_reference_target_rejected(self):
        with self.assertRaisesRegex(ValueError, "Empty reference"):
            tokenize_supervised(Tokenizer(), "prompt", "")

    def test_empty_predicted_plan_does_not_fall_back_to_gt(self):
        c = {"sample_id": "x", "role": "predicted", "modality": "step", "source_split": "train"}
        predictions = [{"sample_id": "x", "source_split": "train", "modality": "step", "predicted_ir": ""}]
        by_id = plan_role_rows([c], predictions)
        dataset = CodeDataset([c], None, None, by_id)
        self.assertEqual(dataset.plan_for(c, {"reference_ir": "GT_MUST_NOT_LEAK"}), "")

    def test_invalid_predicted_plan_is_retained(self):
        c = {"sample_id": "x", "role": "predicted"}
        predictions = [{"sample_id": "x", "source_split": "train", "modality": "step", "predicted_ir": "not IR"}]
        by_id = plan_role_rows([c], predictions)
        self.assertEqual(CodeDataset([c], None, None, by_id).plan_for(c, {"reference_ir": "GT"}), "not IR")

    def test_wrong_arm_and_role_order_rejected(self):
        roles = [{"sample_id": "x", "role": "predicted"}]
        pred = [{"sample_id": "x", "source_split": "train", "modality": "step", "predicted_ir": "", "arm": "B"}]
        with self.assertRaisesRegex(ValueError, "Wrong-arm"):
            plan_role_rows(roles, pred, arm="A")
        with self.assertRaisesRegex(ValueError, "IDs/order"):
            plan_role_rows(roles, [])

    def test_no_partial_output_reuse(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "no overwrite"):
                reject_existing(directory)

    def test_generation_batch_never_crosses_modality_boundary(self):
        cases = [{"modality": m} for m in ("step", "point", "text", "image") for _ in range(2500)]
        batches = list(modality_batches(cases))
        self.assertEqual(sum(len(b) for _, b in batches), 10000)
        self.assertEqual(len(batches), 4 * 313)
        self.assertTrue(all(len({c["modality"] for c in batch}) == 1 for _, batch in batches))

    def test_phase_boundary_requires_same_arm_final_actual_step_and_prefix(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            (p / "adapter_model.safetensors").write_bytes(b"FIXTURE_ONLY")
            (p / "soft_prefix.pt").write_bytes(b"FIXTURE_ONLY")
            write_json_new(p / "trainer_state.json", {"global_step": 4689})
            write_json_new(p / "COMPLETE.json", {"arm": "A", "phase": "phase1", "fingerprint": "fixture",
                "actual_global_step": 4689, "checkpoint_selection": "final", "files": {
                    n: record(p / n) for n in ("adapter_model.safetensors", "soft_prefix.pt", "trainer_state.json")}})
            final_component(p, 4689, arm="A", phase="phase1", fingerprint="fixture")
            with self.assertRaisesRegex(ValueError, "Wrong arm"):
                final_component(p, 4689, arm="B", phase="phase1", fingerprint="fixture")
            with self.assertRaisesRegex(ValueError, "Actual final step"):
                final_component(p, 500, arm="A", phase="phase1", fingerprint="fixture")


class RuntimeContracts(unittest.TestCase):
    def test_installed_trainer_budgets_without_train_or_forward(self):
        ctx = argparse.Namespace(spec=json.loads((PACKAGE / "05_execution_spec.json").read_text()), package=PACKAGE,
                                 actuals=json.loads((PACKAGE / "04_preflight_actuals.json").read_text()))
        for stage, n, expected in (("phase1", 75024, 4689), ("phase2", 8000, 500), ("stage4b", 3150, 1182)):
            result = count_loader(ctx, stage, n)
            self.assertEqual(result["planned_updates"], expected)

    def test_adapter_only_save_with_tied_embeddings_and_prefix(self):
        from peft import LoraConfig, get_peft_model
        from transformers import Qwen2Config, Qwen2ForCausalLM, TrainingArguments
        from miragecad.soft_prefix import SoftPrefixAdapter, SoftPrefixConfig, load_soft_prefix_adapter
        from cag_exposure_policy_core import load_module

        original = load_module(SOURCE / "gen_scripts/train_soft_prefix_ir.py", "review04_tiny_save_test")
        config = Qwen2Config(vocab_size=32, hidden_size=32, intermediate_size=64, num_hidden_layers=1,
                            num_attention_heads=4, num_key_value_heads=2, tie_word_embeddings=True)
        base = Qwen2ForCausalLM(config)
        lm = get_peft_model(base, LoraConfig(r=2, lora_alpha=4, task_type="CAUSAL_LM", target_modules=["q_proj", "v_proj"]))
        prefix = SoftPrefixAdapter(SoftPrefixConfig(hidden_size=32))
        model = original.SoftPrefixCausalLM(lm, prefix)
        klass = adapter_trainer_class("phase1", Tokenizer(), {"current_indices": []})
        with tempfile.TemporaryDirectory() as directory:
            trainer = klass(model=model, args=TrainingArguments(output_dir=directory, use_cpu=True, report_to=[],
                                                                  remove_unused_columns=False))
            trainer.save_model(directory)
            self.assertTrue((Path(directory) / "adapter_model.safetensors").is_file())
            self.assertTrue((Path(directory) / "soft_prefix.pt").is_file())
            self.assertFalse((Path(directory) / "model.safetensors").exists())
            loaded = load_soft_prefix_adapter(Path(directory) / "soft_prefix.pt")
            self.assertTrue(all(torch.equal(v, loaded.state_dict()[k]) for k, v in prefix.state_dict().items()))


if __name__ == "__main__":
    torch.set_num_threads(2)
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    timestamp = datetime.now(timezone.utc)
    report = PACKAGE / "execution" / f"test_result_{timestamp.strftime('%Y%m%dT%H%M%S%fZ')}.json"
    write_json_new(report, {"status": "PASS" if result.wasSuccessful() else "FAIL", "tests_run": result.testsRun,
        "errors": len(result.errors), "failures": len(result.failures), "created_utc": timestamp.isoformat(),
        "execution_hashes": execution_hashes(), "training_started": False,
        "scope": "CPU contracts + adapter-only save; no train/backward/optimizer step"})
    raise SystemExit(0 if result.wasSuccessful() else 1)
