"""Stage4b-only CPU contracts. No train(), forward(), backward() or optimizer step."""
import argparse
from contextlib import redirect_stderr
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import torch

PACKAGE = Path(__file__).resolve().parents[1]
IMPLEMENTATION = Path("__DEV_ROOT__/src/training_25k")
sys.path.insert(0, "__RUN_SOURCE_ROOT__")
sys.path.insert(0, str(IMPLEMENTATION))
import cag_stage4b_execution as s
from cag_exposure_policy_core import read_json, record, value_sha, write_json_new


def fixture(root):
    ctx = SimpleNamespace(source=Path(root), package=Path(root) / "package", spec=read_json(PACKAGE / "05_execution_spec.json"))
    for arm_root in s.lineage.arm_roots(ctx):
        (arm_root / "plan_phase1").mkdir(parents=True)
        (arm_root / "plan_phase1/model.bin").write_text("protected plan weights")
        (arm_root / "predictions").mkdir()
        (arm_root / "predictions/train_roles_plans.jsonl").write_text("fixed plans")
    return ctx


def audit_fixture():
    trace = s.new_trace()
    order = [2, 0, 1]
    frozen = {"trainer_max_steps": 1182, "sampler_epoch_index_sha256": [value_sha(order)] * 3}
    data = {"rows": 3, "full_target_tokens_one_pass": 6, "input_tokens_one_pass": 10}
    calls = []
    audit = s.RuntimeAudit(frozen, [0.0, 0.1], trace, data, lambda: calls.append("read_only_check"))
    return audit, trace, frozen, data, calls, order


class ExecutionContracts(unittest.TestCase):
    def test_default_is_cpu_paired_preflight(self):
        args = s.parser().parse_args([])
        self.assertEqual(args.action, "preflight")
        self.assertIsNone(args.arm)

    def test_unconfirmed_run_rejected_before_context_loading(self):
        for args in (["run"], ["run", "--arm", "A"], ["run", "--confirm-training"]):
            with patch.object(sys, "argv", ["stage4b", *args]), patch.object(s, "FrozenInputs") as loader:
                with self.assertRaisesRegex(ValueError, "NOT AUTHORIZED"):
                    s.main()
                loader.assert_not_called()

    def test_preflight_refuses_arm_or_confirmation(self):
        for args in (["preflight", "--arm", "A"], ["preflight", "--confirm-training"]):
            with patch.object(sys, "argv", ["stage4b", *args]), patch.object(s, "FrozenInputs") as loader:
                with self.assertRaisesRegex(ValueError, "Preflight checks both arms"):
                    s.main()
                loader.assert_not_called()

    def test_no_phase_training_or_generation_actions(self):
        for args in (["phase1"], ["generate"], ["run", "--stage", "phase2"], ["run", "--arm", "C"]):
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                s.parser().parse_args(args)

    def test_direct_run_without_confirmation_never_loads_model(self):
        with patch.object(s.original, "load_train_model") as loader:
            with self.assertRaisesRegex(ValueError, "NOT AUTHORIZED"):
                s.run(None, "A", None, confirmed=False)
            loader.assert_not_called()

    def test_only_stage4b_paths_are_exposed(self):
        with tempfile.TemporaryDirectory() as root:
            ctx = fixture(root)
            self.assertEqual(s.output_path(ctx, "A").name, "stage4b")
            with self.assertRaisesRegex(ValueError, "Only Stage4b arm"):
                s.output_path(ctx, "phase1")

    def test_A_requires_both_stage4b_outputs_absent(self):
        with tempfile.TemporaryDirectory() as root:
            ctx = fixture(root)
            self.assertEqual(s.run_guards(ctx, "A", "fp"), s.output_path(ctx, "A"))
            s.output_path(ctx, "B").mkdir()
            with self.assertRaisesRegex(ValueError, "Output already exists"):
                s.run_guards(ctx, "A", "fp")

    def test_any_partial_target_even_empty_blocks_resume(self):
        with tempfile.TemporaryDirectory() as root:
            ctx = fixture(root)
            s.output_path(ctx, "A").mkdir()
            with self.assertRaisesRegex(ValueError, "no overwrite or implicit resume"):
                s.run_guards(ctx, "A", "fp")

    def test_B_cannot_start_without_A_final(self):
        with tempfile.TemporaryDirectory() as root:
            ctx = fixture(root)
            with patch.object(s, "final_stage4b", side_effect=ValueError("A is not complete")) as verify:
                with self.assertRaisesRegex(ValueError, "A is not complete"):
                    s.run_guards(ctx, "B", "fp")
                verify.assert_called_once_with(ctx, "A", "fp")

    def test_B_requires_same_overlay_fingerprint_for_A(self):
        with tempfile.TemporaryDirectory() as root:
            ctx = fixture(root)
            with patch.object(s, "final_stage4b", return_value={}) as verify:
                s.run_guards(ctx, "B", "locked-fingerprint")
                verify.assert_called_once_with(ctx, "A", "locked-fingerprint")

    def test_protected_plan_snapshot_excludes_only_stage4b(self):
        with tempfile.TemporaryDirectory() as root:
            ctx = fixture(root)
            snapshot = s.protected_snapshot(ctx)
            s.output_path(ctx, "A").mkdir()
            (s.output_path(ctx, "A") / "new_adapter.bin").write_text("allowed new artifact")
            s.verify_protected(ctx, snapshot)
            (s.lineage.arm_roots(ctx)[0] / "plan_phase1/model.bin").write_text("changed")
            with self.assertRaisesRegex(ValueError, "Completed plan branch"):
                s.verify_protected(ctx, snapshot)

    def test_added_root_file_is_not_hidden_by_stage4b_exclusion(self):
        with tempfile.TemporaryDirectory() as root:
            ctx = fixture(root)
            snapshot = s.protected_snapshot(ctx)
            (s.lineage.arm_roots(ctx)[1] / "unexpected.txt").write_text("new")
            with self.assertRaises(ValueError):
                s.verify_protected(ctx, snapshot)

    def test_legacy_final_marker_is_not_accepted_as_overlay(self):
        with tempfile.TemporaryDirectory() as root:
            ctx = fixture(root)
            output = s.output_path(ctx, "A")
            output.mkdir()
            write_json_new(output / "COMPLETE.json", {"fingerprint": s.PARENT, "actual_global_step": 1182})
            with self.assertRaisesRegex(ValueError, "Not the audited Stage4b overlay"):
                s.final_stage4b(ctx, "A", "new-execution-fingerprint")

    def test_indexed_collation_preserves_EOS_and_masks_padding(self):
        features = [{"input_ids": torch.tensor([1, 2, 99]), "labels": torch.tensor([-100, 2, 99]),
                     "attention_mask": torch.ones(3, dtype=torch.long)},
                    {"input_ids": torch.tensor([3, 99]), "labels": torch.tensor([-100, 99]),
                     "attention_mask": torch.ones(2, dtype=torch.long)}]
        dataset = s.IndexedPackedDataset(features)
        batch = s.indexed_collator([dataset[0], dataset[1]], 0)
        self.assertEqual(batch["_case_index"], [0, 1])
        self.assertTrue(torch.all(batch["labels"][batch["attention_mask"] == 0] == -100))
        self.assertEqual(batch["labels"][0, -1].item(), 99)
        self.assertEqual(batch["labels"][1, -2].item(), 99)

    def test_runtime_requires_fresh_native_global_step(self):
        audit, _, _, _, _, _ = audit_fixture()
        opt = SimpleNamespace(state={})
        for step, maximum in ((1, 1182), (0, 1181)):
            with self.assertRaisesRegex(ValueError, "Not fresh"):
                audit.on_train_begin(None, SimpleNamespace(global_step=step, max_steps=maximum), None, optimizer=opt)

    def test_runtime_requires_empty_optimizer_state(self):
        audit, _, _, _, _, _ = audit_fixture()
        with self.assertRaisesRegex(ValueError, "Optimizer state was not reset"):
            audit.on_train_begin(None, SimpleNamespace(global_step=0, max_steps=1182), None,
                                 optimizer=SimpleNamespace(state={"stale": 1}))

    def test_runtime_checks_LR_each_update(self):
        audit, trace, _, _, _, _ = audit_fixture()
        audit.on_step_begin(None, SimpleNamespace(global_step=0), None,
                            optimizer=SimpleNamespace(param_groups=[{"lr": 0.0}]))
        self.assertEqual(trace["lr_steps_checked"], 1)
        with self.assertRaisesRegex(ValueError, "LR schedule drift"):
            audit.on_step_begin(None, SimpleNamespace(global_step=1), None,
                                optimizer=SimpleNamespace(param_groups=[{"lr": 0.2}]))

    def test_runtime_epoch_records_full_exposure_and_checks_readonly(self):
        audit, trace, _, _, calls, order = audit_fixture()
        trace.update(current_indices=order, current_target_tokens=6, current_input_tokens=10, current_padding_tokens=2)
        audit.on_epoch_end(None, None, None)
        self.assertEqual(calls, ["read_only_check"])
        self.assertEqual(trace["epochs"][0]["supervised_target_tokens"], 6)
        self.assertEqual(trace["epochs"][0]["presentations"], 3)
        self.assertEqual(trace["current_indices"], [])
        self.assertEqual(trace["current_target_tokens"], 0)

    def test_runtime_rejects_dropped_or_duplicate_rows(self):
        audit, trace, _, _, _, _ = audit_fixture()
        trace.update(current_indices=[0, 0, 2], current_target_tokens=6, current_input_tokens=10)
        with self.assertRaisesRegex(ValueError, "Dropped/duplicated"):
            audit.on_epoch_end(None, None, None)

    def test_runtime_rejects_sampler_order_change(self):
        audit, trace, _, _, _, _ = audit_fixture()
        trace.update(current_indices=[0, 1, 2], current_target_tokens=6, current_input_tokens=10)
        with self.assertRaisesRegex(ValueError, "Sampler order changed"):
            audit.on_epoch_end(None, None, None)

    def test_runtime_rejects_target_or_input_token_loss(self):
        for target, inputs in ((5, 10), (6, 9)):
            audit, trace, _, _, _, order = audit_fixture()
            trace.update(current_indices=order, current_target_tokens=target, current_input_tokens=inputs)
            with self.assertRaisesRegex(ValueError, "token exposure mismatch"):
                audit.on_epoch_end(None, None, None)

    def test_final_trace_requires_1182_native_updates_and_three_epochs(self):
        _, trace, frozen, data, _, order = audit_fixture()
        trace["lr_steps_checked"] = 1182
        trace["epochs"] = [{"index_sha256": value_sha(order), "presentations": 3, "supervised_target_tokens": 6}] * 3
        s.verify_final_trace(trace, data, frozen)
        trace["lr_steps_checked"] = 1181
        with self.assertRaisesRegex(ValueError, "Incomplete actual LR"):
            s.verify_final_trace(trace, data, frozen)

    def test_training_step_accounting_uses_real_labels_not_role_flags(self):
        trace = s.new_trace()

        class Parent:
            def training_step(self, model, inputs, num_items_in_batch=None):
                trace["current_indices"].extend(inputs.pop("_case_index"))
                return torch.tensor(1.0)

        with patch.object(s.original, "adapter_trainer_class", return_value=Parent):
            trainer = s.trainer_class(None, trace)()
            trainer.training_step(None, {"labels": torch.tensor([[-100, 7, 99, -100]]),
                "attention_mask": torch.tensor([[1, 1, 1, 0]]), "_case_index": [4]})
        self.assertEqual(trace["current_target_tokens"], 2)
        self.assertEqual(trace["current_input_tokens"], 3)
        self.assertEqual(trace["current_padding_tokens"], 1)
        self.assertEqual(trace["current_indices"], [4])

    def test_execution_fingerprint_binds_source_and_packing_dependencies(self):
        first = s.execution_fingerprint({"source": "one", "packing": "locked"})
        self.assertNotEqual(first, s.execution_fingerprint({"source": "two", "packing": "locked"}))
        self.assertNotEqual(first, s.execution_fingerprint({"source": "one", "packing": "different"}))
        self.assertNotEqual(first, s.PARENT)

    def test_real_frozen_LR_has_1182_updates_plus_terminal_endpoint(self):
        ctx = SimpleNamespace(package=PACKAGE, spec=read_json(PACKAGE / "05_execution_spec.json"),
                              actuals=read_json(PACKAGE / "04_preflight_actuals.json"))
        frozen, lr = s.verify_budget(ctx)
        self.assertEqual(frozen["trainer_max_steps"], 1182)
        self.assertEqual(len(lr), 1183)
        self.assertEqual(lr[-1], 0.0)

    def test_real_tied_weight_adapter_only_save_without_prefix_or_forward(self):
        from peft import LoraConfig, get_peft_model
        from transformers import Qwen2Config, Qwen2ForCausalLM, TrainingArguments

        class Tok:
            def save_pretrained(self, directory):
                write_json_new(Path(directory) / "test_tokenizer.json", {"fixture": True})

        model = Qwen2ForCausalLM(Qwen2Config(vocab_size=32, hidden_size=32, intermediate_size=64,
            num_hidden_layers=1, num_attention_heads=4, num_key_value_heads=2, tie_word_embeddings=True))
        model = get_peft_model(model, LoraConfig(r=2, lora_alpha=4, task_type="CAUSAL_LM", target_modules=["q_proj", "v_proj"]))
        with tempfile.TemporaryDirectory() as directory:
            klass = s.trainer_class(Tok(), s.new_trace())
            trainer = klass(model=model, args=TrainingArguments(output_dir=directory, use_cpu=True, report_to=[]))
            with patch.object(model, "forward", side_effect=AssertionError("No CPU model forward")):
                trainer.save_model(directory)
            self.assertTrue((Path(directory) / "adapter_model.safetensors").is_file())
            self.assertFalse((Path(directory) / "model.safetensors").exists())
            self.assertFalse((Path(directory) / "soft_prefix.pt").exists())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()
    s.reject_existing(args.report)
    torch.set_num_threads(2)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ExecutionContracts))
    write_json_new(args.report, {"created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if result.wasSuccessful() else "FAIL", "tests_run": result.testsRun,
        "failures": len(result.failures), "errors": len(result.errors), "sources": s.own_sources(),
        "test_source": record(Path(__file__)), "training_started": False,
        "scope": "CPU guard/callback/collator and tiny tied-weight adapter save; no train/forward/backward/optimizer step"})
    sys.exit(0 if result.wasSuccessful() else 1)
