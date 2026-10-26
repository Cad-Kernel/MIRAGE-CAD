"""B-only continuation contracts: CPU/stubs only, never real training/generation."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

IMPLEMENTATION = Path("__DEV_ROOT__/src/training_25k")
PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IMPLEMENTATION))
import cag_exposure_policy_b_only as b
from cag_exposure_policy_core import read_json, record, write_json_new


def fixture(root):
    ctx = SimpleNamespace(source=Path(root), package=Path(root) / "package",
                          spec=read_json(PACKAGE / "05_execution_spec.json"),
                          manifests={"phase1_B": [], "phase2_shared": []})
    a, _ = b.arm_roots(ctx)
    a.mkdir(parents=True)
    (a / "KEEP.txt").write_text("untouched", encoding="utf-8")
    return ctx


class BOnlyContracts(unittest.TestCase):
    def test_default_action_is_cpu_preflight(self):
        self.assertEqual(b.parser().parse_args([]).action, "preflight")

    def test_run_requires_confirmation_before_context_loading(self):
        with patch.object(sys, "argv", ["b_only", "run"]), patch.object(b, "FrozenInputs") as loader:
            with self.assertRaisesRegex(ValueError, "NOT AUTHORIZED"):
                b.main()
            loader.assert_not_called()

    def test_preflight_rejects_training_confirmation(self):
        with patch.object(sys, "argv", ["b_only", "preflight", "--confirm-training"]), patch.object(b, "FrozenInputs") as loader:
            with self.assertRaisesRegex(ValueError, "cannot be passed to preflight"):
                b.main()
            loader.assert_not_called()

    def test_no_arm_or_stage_cli_override(self):
        for argv in (["--arm", "A"], ["--stage", "stage4b"], ["stage4b"], ["generate"]):
            with self.subTest(argv=argv), self.assertRaises(SystemExit):
                b.parser().parse_args(argv)

    def test_absent_B_is_accepted_without_creating_it(self):
        with tempfile.TemporaryDirectory() as root:
            ctx = fixture(root)
            b.output_guards(ctx)
            self.assertFalse(b.arm_roots(ctx)[1].exists())

    def test_empty_B_is_accepted_without_writes(self):
        with tempfile.TemporaryDirectory() as root:
            ctx = fixture(root)
            target = b.arm_roots(ctx)[1]
            target.mkdir()
            b.output_guards(ctx)
            self.assertEqual(list(target.iterdir()), [])

    def test_partial_B_refuses_resume(self):
        with tempfile.TemporaryDirectory() as root:
            ctx = fixture(root)
            target = b.arm_roots(ctx)[1]
            target.mkdir()
            (target / "B_ONLY_STARTED.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "no overwrite or silent resume"):
                b.output_guards(ctx)

    def test_completed_B_also_refuses_rerun(self):
        with tempfile.TemporaryDirectory() as root:
            ctx = fixture(root)
            target = b.arm_roots(ctx)[1]
            target.mkdir()
            (target / "B_ONLY_COMPLETE.json").write_text("{}")
            with self.assertRaises(ValueError):
                b.output_guards(ctx)

    def test_any_A_stage4b_directory_blocks(self):
        with tempfile.TemporaryDirectory() as root:
            ctx = fixture(root)
            (b.arm_roots(ctx)[0] / "stage4b").mkdir()
            with self.assertRaisesRegex(ValueError, "Output already exists"):
                b.output_guards(ctx)

    def test_any_B_stage4b_directory_blocks(self):
        with tempfile.TemporaryDirectory() as root:
            ctx = fixture(root)
            (b.arm_roots(ctx)[1] / "stage4b").mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, "Output already exists"):
                b.output_guards(ctx)

    def test_missing_A_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            ctx = fixture(root)
            a, _ = b.arm_roots(ctx)
            (a / "KEEP.txt").unlink()
            a.rmdir()
            with self.assertRaisesRegex(ValueError, "Completed A output must exist"):
                b.output_guards(ctx)

    def test_A_snapshot_is_read_only_and_detects_mutation(self):
        with tempfile.TemporaryDirectory() as root:
            ctx = fixture(root)
            a, _ = b.arm_roots(ctx)
            snapshot = b.tree_snapshot(a)
            b.assert_tree_unchanged(a, snapshot)
            (a / "KEEP.txt").write_text("modified")
            with self.assertRaisesRegex(ValueError, "Protected A output tree changed"):
                b.assert_tree_unchanged(a, snapshot)

    def test_A_snapshot_detects_added_file(self):
        with tempfile.TemporaryDirectory() as root:
            ctx = fixture(root)
            a, _ = b.arm_roots(ctx)
            snapshot = b.tree_snapshot(a)
            (a / "UNEXPECTED.txt").write_text("new")
            with self.assertRaises(ValueError):
                b.assert_tree_unchanged(a, snapshot)

    def test_plan_stage_rejects_stage4b_before_original_call(self):
        with patch.object(b.original, "train_stage") as trainer:
            for phase in ("stage4b", "phase3", "A"):
                with self.assertRaisesRegex(ValueError, "forbids Stage4b"):
                    b.train_b_phase(None, phase, None, None)
            trainer.assert_not_called()

    def test_exact_B_only_call_graph(self):
        events = []
        ctx, cache, report = object(), object(), Path("fixture.json")

        def train(c, arm, stage, query_cache, path):
            self.assertIs(c, ctx)
            self.assertIs(query_cache, cache)
            self.assertEqual(path, report)
            events.append(("train", arm, stage))

        def generate(c, arm, query_cache, *, training_roles):
            self.assertTrue(training_roles)
            events.append(("generate", arm, training_roles))

        with patch.object(b.original, "train_stage", side_effect=train), patch.object(b.original, "generate", side_effect=generate), patch.object(b.original, "run") as full_run:
            b.execute_b_sequence(ctx, cache, report, lambda phase: events.append(("boundary", phase)))
            full_run.assert_not_called()
        self.assertEqual(events, [("train", "B", "phase1"), ("boundary", "phase1"),
                                  ("train", "B", "phase2"), ("boundary", "phase2"),
                                  ("generate", "B", True), ("boundary", "train_roles_945")])

    def test_phase1_failure_stops_without_generation(self):
        with patch.object(b.original, "train_stage", side_effect=ValueError("fixture failure")) as train, patch.object(b.original, "generate") as generate:
            with self.assertRaisesRegex(ValueError, "fixture failure"):
                b.execute_b_sequence(None, None, None, lambda phase: None)
            self.assertEqual(train.call_count, 1)
            generate.assert_not_called()

    def test_phase2_failure_stops_without_generation(self):
        with patch.object(b.original, "train_stage", side_effect=[None, ValueError("phase2 failure")]), patch.object(b.original, "generate") as generate:
            with self.assertRaisesRegex(ValueError, "phase2 failure"):
                b.execute_b_sequence(None, None, None, lambda phase: None)
            generate.assert_not_called()

    def test_run_directly_requires_human_confirmation(self):
        with patch.object(b, "output_guards") as guard:
            with self.assertRaisesRegex(ValueError, "NOT AUTHORIZED"):
                b.run(None, None, confirmed=False)
            guard.assert_not_called()

    def test_policy_lock_is_immutable_and_not_a_training_release(self):
        with tempfile.TemporaryDirectory() as root:
            ctx = SimpleNamespace(package=Path(root))
            policy = {"scope": "all plan fields", "stage4b_training_authorized": False}
            first = b.policy_lock(ctx, policy, create=True)
            self.assertEqual(first, b.policy_lock(ctx, policy, create=False))
            with self.assertRaisesRegex(ValueError, "Locked packing policy changed"):
                b.policy_lock(ctx, {**policy, "scope": "changed"}, create=True)

    def test_missing_policy_lock_cannot_be_created_by_run(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(ValueError, "run CPU preflight first"):
                b.policy_lock(SimpleNamespace(package=Path(root)), {}, create=False)

    def test_audit_path_cannot_write_into_A_or_B(self):
        with tempfile.TemporaryDirectory() as root:
            ctx = fixture(root)
            for arm_root in b.arm_roots(ctx):
                with self.assertRaisesRegex(ValueError, "never write into A/B"):
                    b.audit_report_path(ctx, arm_root / "forbidden.json")

    def test_audit_path_is_confined_to_execution(self):
        with tempfile.TemporaryDirectory() as root:
            ctx = fixture(root)
            path = ctx.package / "execution/report.json"
            self.assertEqual(b.audit_report_path(ctx, path), path.resolve())
            with self.assertRaises(ValueError):
                b.audit_report_path(ctx, ctx.package / "execution/report.txt")

    def test_noncanonical_package_fails_before_loading_release(self):
        with tempfile.TemporaryDirectory() as root:
            ctx = fixture(root)
            ctx.fingerprint = b.PARENT
            with self.assertRaisesRegex(ValueError, "canonical frozen package"):
                b.checked_inputs(ctx)

    def test_actual_startup_hash_and_optimizer_reset_are_checked(self):
        with tempfile.TemporaryDirectory() as root:
            ctx = fixture(root)
            _, target = b.arm_roots(ctx)
            initial = ctx.package / ctx.spec["plan_adapter"]["initialization_B"]
            initial.mkdir(parents=True)
            stage = target / "plan_phase1"
            stage.mkdir(parents=True)
            for name in ("adapter_model.safetensors", "adapter_config.json", "soft_prefix.pt"):
                (initial / name).write_text("fixture weights")
            report = {"fingerprint": b.PARENT, "arm": "B", "stage": "phase1", "fresh_optimizer_and_scheduler": True,
                      "startup": {name: record(initial / name) for name in ("adapter_model.safetensors", "adapter_config.json", "soft_prefix.pt")}}
            write_json_new(stage / "training_report.json", report)
            b.verify_model_startup(ctx, "B", "phase1")
            (initial / "soft_prefix.pt").write_text("changed")
            with self.assertRaisesRegex(ValueError, "Actual loaded startup"):
                b.verify_model_startup(ctx, "B", "phase1")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()
    b.reject_existing(args.report)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(BOnlyContracts)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    write_json_new(args.report, {"created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if result.wasSuccessful() else "FAIL", "tests_run": result.testsRun,
        "failures": len(result.failures), "errors": len(result.errors), "sources": b.own_sources(),
        "test_source": record(Path(__file__)), "training_started": False,
        "scope": "CPU/stub call-graph and guard contracts, no real model forward/backward/training/generation"})
    sys.exit(0 if result.wasSuccessful() else 1)
