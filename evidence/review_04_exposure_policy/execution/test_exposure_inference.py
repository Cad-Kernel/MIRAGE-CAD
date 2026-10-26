"""CPU contracts for evaluation-only inference; no real model forward or training."""
import argparse
import ast
from contextlib import redirect_stderr
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import torch

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, "__RUN_SOURCE_ROOT__")
sys.path.insert(0, "__DEV_ROOT__/src/training_25k")
import cag_exposure_inference as s
from cag_exposure_policy_core import read_json, record, value_sha, write_json_new
from miragecad.gen_prompts import build_ir_prompt, build_program_prompt, get_query_evidence


def context(root):
    return SimpleNamespace(source=Path(root), package=PACKAGE,
                           spec=read_json(PACKAGE / "05_execution_spec.json"))


def evaluation_fixture():
    rows = [{"sample_id": f"id_{i}"} for i in range(2500)]
    cases = [{"case_index": j * 2500 + i, "source_row": i, "source_split": "test",
              "sample_id": row["sample_id"], "modality": m}
             for j, m in enumerate(s.MODALITIES) for i, row in enumerate(rows)]
    ctx = context("/tmp/inference_contract_unused")
    ctx.manifests = {"evaluation_shared": cases}
    ctx.splits = {"test": rows}
    ctx.resolve = lambda c: rows[c["source_row"]]
    return ctx, cases


def query_fixture(modality="text", reference="TARGET_MUST_NOT_ENTER_PROMPT"):
    evidence = "query-only dimensions" if modality == "text" else ""
    planner_evidence = "Point cloud query." if modality == "point" else evidence
    meta = {"infer_prompt": build_ir_prompt({}, modality, evidence_text=planner_evidence),
            "evidence": evidence, "reference_code": reference, "reference_ir": reference}
    latent = np.zeros(512, dtype=np.float32)
    points = np.zeros((0, 3), dtype=np.float32)
    ctx = SimpleNamespace(resolve=lambda c: {"text": evidence, "program_path": reference, "ir_path": reference})
    cache = SimpleNamespace(load=lambda c: (meta, latent, points))
    case = {"case_index": 0, "sample_id": "id", "modality": modality, "source_split": "test"}
    return ctx, cache, case, meta


class FakeBatch(dict):
    def to(self, device):
        return self


class FakeTokenizer:
    padding_side, truncation_side, eos_token_id = "left", "right", 2

    def __call__(self, texts, *, truncation=False, max_length=None, padding=False, return_tensors=None, **kwargs):
        texts = [texts] if isinstance(texts, str) else texts
        ids = [[ord(char) + 3 for char in text] for text in texts]
        if truncation:
            ids = [row[:max_length] for row in ids]
        if return_tensors:
            width = max(map(len, ids))
            return FakeBatch(input_ids=torch.tensor([[0] * (width - len(row)) + row for row in ids]),
                             attention_mask=torch.tensor([[0] * (width - len(row)) + [1] * len(row) for row in ids]))
        return {"input_ids": ids}

    def decode(self, sequence, **kwargs):
        return "".join(chr(int(i) - 3) for i in sequence if int(i) > 2)


class InferenceContracts(unittest.TestCase):
    def test_default_cpu_preflight(self):
        args = s.parser().parse_args([])
        self.assertEqual(args.action, "preflight")
        self.assertIsNone(args.arm)
        self.assertFalse(args.confirm_generation)

    def test_run_needs_arm_and_human_confirmation_before_context(self):
        for argv in (["run"], ["run", "--arm", "A"], ["run", "--confirm-generation"]):
            with patch.object(sys, "argv", ["inference", *argv]), patch.object(s, "FrozenInputs") as frozen:
                with self.assertRaisesRegex(ValueError, "NOT AUTHORIZED"):
                    s.main()
                frozen.assert_not_called()

    def test_preflight_disallows_arm_and_generation_flag(self):
        for argv in (["preflight", "--arm", "A"], ["preflight", "--confirm-generation"]):
            with patch.object(sys, "argv", ["inference", *argv]), patch.object(s, "FrozenInputs") as frozen:
                with self.assertRaisesRegex(ValueError, "Preflight checks both"):
                    s.main()
                frozen.assert_not_called()

    def test_no_training_resume_sampling_or_limit_cli(self):
        for argv in (["train"], ["run", "--confirm-training"], ["run", "--resume"],
                     ["run", "--limit", "10"], ["run", "--arm", "C"], ["run", "--repair"]):
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                s.parser().parse_args(argv)

    def test_direct_run_refuses_unconfirmed_model_loading(self):
        with patch.object(s, "load_inference_model") as model:
            with self.assertRaisesRegex(ValueError, "NOT AUTHORIZED"):
                s.run(None, "A", None, confirmed=False)
            model.assert_not_called()

    def test_no_training_saving_or_target_packing_calls_in_source(self):
        module = ast.parse(Path(s.__file__).read_text())
        forbidden = {"train", "backward", "step", "save_model", "save_pretrained", "train_stage",
                     "tokenize_supervised", "Stage4bPackedDataset", "tokenize_stage4b_preserve_target"}
        names = {node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
                 for node in ast.walk(module) if isinstance(node, ast.Call)
                 and isinstance(node.func, (ast.Name, ast.Attribute))}
        self.assertFalse(names & forbidden)

    def test_fixed_manifest_all_10000_ids_in_frozen_order(self):
        ctx, cases = evaluation_fixture()
        self.assertIs(s.validate_cases(ctx), cases)

    def test_manifest_order_modality_split_and_id_mutations_fail(self):
        for field, bad in (("sample_id", "wrong"), ("source_split", "train"),
                           ("modality", "text"), ("source_row", 1), ("case_index", 1)):
            ctx, cases = evaluation_fixture()
            cases[0][field] = bad
            with self.assertRaisesRegex(ValueError, "IDs/order/modality"):
                s.validate_cases(ctx)

    def test_duplicate_test_ids_fail(self):
        ctx, _ = evaluation_fixture()
        ctx.splits["test"][1]["sample_id"] = ctx.splits["test"][0]["sample_id"]
        with self.assertRaisesRegex(ValueError, "uniqueness"):
            s.validate_cases(ctx)

    def test_decoding_repair_or_evidence_policy_mutations_fail(self):
        for key, value in (("do_sample", True), ("program_code_repair", True), ("num_beams", 2),
                           ("P1a_plan_canonicalization", False), ("point_plan_evidence", "on")):
            ctx, _ = evaluation_fixture()
            ctx.spec["generation"][key] = value
            with self.assertRaisesRegex(ValueError, "policy drift"):
                s.validate_cases(ctx)

    def test_point_seed_mutation_fails(self):
        ctx, _ = evaluation_fixture()
        ctx.spec["point_sampling"]["seed"] = 43
        with self.assertRaisesRegex(ValueError, "Point policy"):
            s.validate_cases(ctx)

    def test_batches_do_not_cross_modality_boundary_and_include_last_four(self):
        _, cases = evaluation_fixture()
        batches = list(s.original.modality_batches(cases, size=8))
        self.assertEqual(len(batches), 1252)
        self.assertEqual([c for _, batch in batches for c in batch], cases)
        self.assertTrue(all(len({c["modality"] for c in batch}) == 1 for _, batch in batches))
        self.assertEqual(sum(len(batch) == 4 for _, batch in batches), 4)

    def test_outputs_are_separate_from_read_only_training_arms(self):
        with tempfile.TemporaryDirectory() as directory:
            ctx = context(directory)
            self.assertEqual(s.output_path(ctx, "A"), ctx.source / ctx.spec["training_output_root"] / "evaluation_v1/arm_A")
            self.assertNotEqual(s.output_path(ctx, "A").parent, s.training.output_path(ctx, "A").parent)
            with self.assertRaisesRegex(ValueError, "Only inference arm"):
                s.output_path(ctx, "C")

    def test_any_partial_directory_blocks_implicit_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            ctx = context(directory)
            s.output_path(ctx, "A").mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, "no overwrite or implicit resume"):
                s.run_guards(ctx, "A", "fp")

    def test_A_refuses_existing_B_output(self):
        with tempfile.TemporaryDirectory() as directory:
            ctx = context(directory)
            s.output_path(ctx, "B").mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, "Output already exists"):
                s.run_guards(ctx, "A", "fp")

    def test_B_requires_valid_A_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            ctx = context(directory)
            with patch.object(s, "verify_generation", side_effect=ValueError("A not complete")) as verify:
                with self.assertRaisesRegex(ValueError, "A not complete"):
                    s.run_guards(ctx, "B", "fp")
                verify.assert_called_once_with(ctx, "A", "fp")

    def test_weight_file_or_mtime_change_fails_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            ctx = context(directory)
            for root in s.lineage.arm_roots(ctx):
                root.mkdir(parents=True)
                (root / "model.bin").write_bytes(b"original")
            expected = s.protected_snapshot(ctx)
            (s.lineage.arm_roots(ctx)[0] / "model.bin").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "Read-only"):
                s.verify_protected(ctx, expected)

    def test_poisoned_reference_text_and_lengths_cannot_change_prompts(self):
        first = query_fixture(reference="reference_one")
        second = query_fixture(reference="reference_two" * 10000)
        q1, q2 = s.query_input(*first[:3]), s.query_input(*second[:3])
        self.assertEqual(q1.plan_prompt, q2.plan_prompt)
        self.assertEqual(s.code_prompt(q1, "PREDICTED"), s.code_prompt(q2, "PREDICTED"))
        self.assertFalse(hasattr(q1, "reference_code"))
        self.assertNotIn("reference_two", s.code_prompt(q2, "PREDICTED"))

    def test_cached_prompt_containing_target_injection_is_rejected(self):
        ctx, cache, case, meta = query_fixture()
        meta["infer_prompt"] += meta["reference_code"]
        with self.assertRaisesRegex(ValueError, "hidden target"):
            s.query_input(ctx, cache, case)

    def test_cached_evidence_drift_is_rejected(self):
        ctx, cache, case, meta = query_fixture()
        meta["evidence"] = "changed"
        with self.assertRaisesRegex(ValueError, "query evidence"):
            s.query_input(ctx, cache, case)

    def test_point_uses_cached_points_but_plan_evidence_stays_off(self):
        points = np.arange(3072, dtype=np.float32).reshape(1024, 3)
        meta = {"infer_prompt": build_ir_prompt({}, "point"),
                "evidence": get_query_evidence({}, "point", point_xyz=points)}
        cache = SimpleNamespace(load=lambda c: (meta, np.zeros(512, np.float32), points))
        ctx = SimpleNamespace(resolve=lambda c: {"text": "HIDDEN_TEXT_NOT_FOR_POINT"})
        q = s.query_input(ctx, cache, {"modality": "point"})
        self.assertNotIn("bbox_size", q.plan_prompt)
        self.assertIn("Point cloud query.", q.plan_prompt)
        self.assertIn("bbox_size", s.code_prompt(q, "PREDICTED"))
        self.assertNotIn("HIDDEN_TEXT", s.code_prompt(q, "PREDICTED"))

    def test_empty_and_invalid_predicted_plans_are_not_replaced_with_GT(self):
        ctx, cache, case, _ = query_fixture()
        q = s.query_input(ctx, cache, case)
        for plan in ("", "INVALID PLAN"):
            self.assertEqual(s.code_prompt(q, plan), build_program_prompt({}, "text", plan, evidence_text=q.evidence))
        with self.assertRaisesRegex(ValueError, "Missing plan"):
            s.code_prompt(q, None)

    def test_empty_plan_P1a_is_called_and_row_retained(self):
        ctx, _, case, _ = query_fixture()
        calls = []
        canonicalizer = SimpleNamespace(repair_ir_text=lambda sid, raw, logs: calls.append((sid, raw)) or raw)
        row = s.plan_row(case, "B", "", canonicalizer, [], "model", "prefix")
        self.assertEqual(calls, [(case["sample_id"], "")])
        self.assertTrue(row["empty"])
        self.assertEqual(row["canonicalization"], "P1a")

    def test_generation_kwargs_match_historical_greedy_policy(self):
        ctx, _ = evaluation_fixture()
        self.assertEqual(s.generation_kwargs(ctx, FakeTokenizer()), {"max_new_tokens": 1536, "do_sample": False,
            "num_beams": 1, "num_return_sequences": 1, "pad_token_id": 2})

    def test_whole_prompt_right_truncation_and_left_padding(self):
        tok = FakeTokenizer()
        inputs = s.tokenize_batch(tok, ["a", "b" * 1600])
        self.assertEqual(inputs["input_ids"].shape, (2, 1536))
        self.assertEqual(int(inputs["attention_mask"][0].sum()), 1)
        ctx, cache, case, _ = query_fixture()
        q = s.query_input(ctx, cache, case)
        rows = s.input_audit(tok, ["a", "b" * 1600], inputs, [case, case], [q, q])
        self.assertFalse(rows[0]["prompt_truncated"])
        self.assertTrue(rows[1]["prompt_truncated"])

    def test_wrong_padding_or_truncation_direction_fails(self):
        for attr, value in (("padding_side", "right"), ("truncation_side", "left")):
            tok = FakeTokenizer()
            setattr(tok, attr, value)
            with self.assertRaisesRegex(ValueError, "padding/truncation"):
                s.tokenize_batch(tok, ["prompt"])

    def test_dropped_wrong_arm_and_reordered_outputs_fail(self):
        _, cases = evaluation_fixture()
        row = {**cases[0], "arm": "A"}
        with self.assertRaisesRegex(ValueError, "count"):
            s.validate_rows([], cases[:1], "A")
        for key, value in (("arm", "B"), ("sample_id", "wrong"), ("modality", "image")):
            with self.assertRaisesRegex(ValueError, "IDs/order/arm"):
                s.validate_rows([{**row, key: value}], cases[:1], "A")

    def test_geometry_preserves_empty_candidate_and_original_point_target(self):
        ctx = SimpleNamespace(resolve=lambda c: {"point_path": "/fixed/target.npy"})
        case = {"sample_id": "id", "modality": "image"}
        self.assertEqual(s.geometry_row(ctx, case, {"prediction": ""}),
                         {**case, "point_path": "/fixed/target.npy", "all_candidates": [""]})

    def test_wrong_generation_fingerprint_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            ctx = context(directory)
            root = s.output_path(ctx, "A")
            root.mkdir(parents=True)
            write_json_new(root / "COMPLETE.json", {"version": s.VERSION, "inference_fingerprint": "wrong"})
            with self.assertRaisesRegex(ValueError, "Wrong inference completion"):
                s.verify_generation(ctx, "A", "expected")

    def test_fingerprint_binds_sources_and_final_models(self):
        self.assertNotEqual(s.inference_fingerprint({"model": "A", "source": "v1"}),
                            s.inference_fingerprint({"model": "B", "source": "v1"}))
        self.assertNotEqual(s.inference_fingerprint({"model": "A", "source": "v1"}),
                            s.inference_fingerprint({"model": "A", "source": "v2"}))

    def test_actual_frozen_tokenizer_matches_legacy_inference_batch(self):
        from transformers import AutoTokenizer
        directory = PACKAGE / "artifacts/initialization/arm_A"
        tok = AutoTokenizer.from_pretrained(directory, local_files_only=True)
        if tok.pad_token is None:
            tok.pad_token = tok.eos_token
        tok.padding_side = "left"
        prompts = [build_ir_prompt({}, "point"), build_program_prompt({}, "step", "INVALID\n" * 2000, evidence_text="query")]
        actual = s.tokenize_batch(tok, prompts)
        legacy = tok(prompts, truncation=True, max_length=1536, padding=True, return_tensors="pt")
        for key in ("input_ids", "attention_mask"):
            self.assertTrue(torch.equal(actual[key], legacy[key]))

    def test_soft_prefix_inputs_match_legacy_embedding_and_mask_layout(self):
        tok = FakeTokenizer()
        inputs = s.tokenize_batch(tok, ["short", "longer input"])
        ctx, cache, case, _ = query_fixture()
        query = s.query_input(ctx, cache, case)
        embed = lambda ids: ids.float().unsqueeze(-1).repeat(1, 1, 3)
        model = SimpleNamespace(get_input_embeddings=lambda: embed)
        prefix = lambda latent: torch.ones(len(latent), 4, 3)
        result = s.plan_model_inputs(model, prefix, inputs, [query, query])
        self.assertTrue(torch.equal(result["inputs_embeds"], torch.cat([torch.ones(2, 4, 3), embed(inputs["input_ids"])], dim=1)))
        self.assertTrue(torch.equal(result["attention_mask"], torch.cat([torch.ones(2, 4, dtype=torch.long), inputs["attention_mask"]], dim=1)))
        with self.assertRaisesRegex(ValueError, "four-token soft-prefix"):
            s.plan_model_inputs(model, lambda latent: torch.zeros(len(latent), 3, 3), inputs, [query, query])

    def test_all_eight_modality_exports_keep_fixed_ids_empty_codes_and_targets(self):
        ctx, cases = evaluation_fixture()
        ctx.resolve = lambda c: {"point_path": f"/fixed/{c['sample_id']}.npy"}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (root / "test_code.jsonl").open("xb") as stream:
                for case in cases:
                    stream.write(s.encoded({**case, "arm": "A", "prediction": ""}))
            files = s.export_modality_files(ctx, "A", root, cases)
            self.assertEqual(len(files), 8)
            for m in s.MODALITIES:
                rows = s.read_rows(root / f"test_code_{m}.jsonl")
                geometry = s.read_rows(root / f"geom_input_{m}.jsonl")
                self.assertEqual([r["sample_id"] for r in rows], [r["sample_id"] for r in ctx.splits["test"]])
                self.assertEqual(len(geometry), 2500)
                self.assertTrue(all(r["all_candidates"] == [""] for r in geometry))
            with self.assertRaises(FileExistsError):
                s.export_modality_files(ctx, "A", root, cases)

    def test_mock_plan_generation_keeps_invalid_and_empty_without_real_forward(self):
        tok = FakeTokenizer()
        qctx, cache, case, _ = query_fixture()
        cases = [case, {**case, "case_index": 1, "sample_id": "id2"}]
        query = s.query_input(qctx, cache, case)
        inputs = s.tokenize_batch(tok, [query.plan_prompt] * 2)
        audits = s.input_audit(tok, [query.plan_prompt] * 2, inputs, cases, [query] * 2)

        class StubPrefix:
            def eval(self):
                return self

            def requires_grad_(self, flag):
                return self

            def parameters(self):
                return []

            def __call__(self, latent):
                return torch.zeros(len(latent), 4, 3)

        class StubModel:
            def get_input_embeddings(self):
                return lambda ids: torch.zeros(*ids.shape, 3)

            def generate(self, inputs_embeds, attention_mask, **kwargs):
                if not torch.is_inference_mode_enabled():
                    raise AssertionError("Plan generation must use inference_mode")
                return [torch.tensor([ord(c) + 3 for c in "INVALID"]), torch.tensor([], dtype=torch.long)]

        with tempfile.TemporaryDirectory() as directory:
            ctx = context(directory)
            plan_dir = Path(directory) / "phase2"
            plan_dir.mkdir()
            (plan_dir / "adapter_model.safetensors").write_bytes(b"stub-model")
            (plan_dir / "soft_prefix.pt").write_bytes(b"stub-prefix")
            root = s.output_path(ctx, "A")
            root.mkdir(parents=True)
            canonicalizer = SimpleNamespace(repair_ir_text=lambda sid, raw, repairs: raw)
            calls = []
            with patch.object(s.original, "final_path", return_value=plan_dir), \
                    patch.object(s, "load_inference_model", return_value=StubModel()), \
                    patch("miragecad.soft_prefix.load_soft_prefix_adapter", return_value=StubPrefix()), \
                    patch.object(s, "query_input", return_value=query), \
                    patch.object(s, "load_module", return_value=canonicalizer), patch.object(torch.cuda, "empty_cache"):
                rows = s.generate_plans(ctx, "A", root, cache, tok, cases, audits, lambda: calls.append("readonly"))
            self.assertEqual([r["predicted_ir"] for r in rows], ["INVALID", ""])
            self.assertTrue(rows[1]["empty"])
            self.assertEqual(s.read_json(root / "test_plans.p1a_log.json")["rows"], 2)
            self.assertEqual(calls, ["readonly"])

    def test_mock_code_generation_is_inference_only_and_keeps_raw_output(self):
        tok = FakeTokenizer()
        raw_code = "part = BROKEN_API()"

        class StubModel:
            def generate(self, input_ids, attention_mask, **kwargs):
                if not torch.is_inference_mode_enabled():
                    raise AssertionError("Must run in inference_mode")
                suffix = torch.tensor([[ord(c) + 3 for c in raw_code] for _ in input_ids])
                return torch.cat([input_ids, suffix], dim=1)

        with tempfile.TemporaryDirectory() as directory:
            ctx = context(directory)
            model_dir = s.training.output_path(ctx, "A")
            model_dir.mkdir(parents=True)
            (model_dir / "adapter_model.safetensors").write_bytes(b"stub-file-only-no-model")
            root = s.output_path(ctx, "A")
            root.mkdir(parents=True)
            qctx, cache, case, _ = query_fixture()
            q = s.query_input(qctx, cache, case)
            plan = {**case, "arm": "A", "predicted_ir": "INVALID"}
            calls = []
            with patch.object(s, "load_inference_model", return_value=StubModel()), \
                    patch.object(s, "query_input", return_value=q), patch.object(torch.cuda, "empty_cache"):
                s.generate_codes(ctx, "A", root, cache, tok, [case], [plan], lambda: calls.append("readonly"))
            row = s.read_rows(root / "test_code.jsonl")[0]
            self.assertEqual(row["prediction"], raw_code)
            self.assertFalse(row["program_code_repair"])
            self.assertEqual(row["reference"], "TARGET_MUST_NOT_ENTER_PROMPT")
            self.assertEqual(calls, ["readonly"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()
    s.reject_existing(args.report)
    torch.set_num_threads(2)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(InferenceContracts))
    write_json_new(args.report, {"created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if result.wasSuccessful() else "FAIL", "tests_run": result.testsRun,
        "failures": len(result.failures), "errors": len(result.errors), "sources": s.own_sources(),
        "test_source": record(Path(__file__)), "training_started": False, "real_model_forward": False,
        "scope": "CPU guards, source-bound finals/paths, query-only prompts, real tokenizer, stub-only code generation"})
    sys.exit(0 if result.wasSuccessful() else 1)
