"""CPU packing/role/collation contracts; no model initialization or training."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import random
import sys
import unittest

import torch

IMPLEMENTATION = Path("__DEV_ROOT__/src/training_25k")
SOURCE = Path("__RUN_SOURCE_ROOT__")
PACKAGE = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(IMPLEMENTATION), str(SOURCE)]
from cag_stage4b_packing_v1 import Stage4bPackedDataset, tokenize_stage4b_preserve_target, MAX_LENGTH
from cag_exposure_policy_core import collate, tokenize_supervised, write_json_new
from miragecad.gen_prompts import build_program_prompt


class CharacterTokenizer:
    is_fast = True
    eos_token = "~"
    eos_token_id = ord("~") + 2
    pad_token_id = 0

    def __call__(self, text, add_special_tokens=True, return_offsets_mapping=False):
        out = {"input_ids": ([1] if add_special_tokens else []) + [ord(c) + 2 for c in text]}
        if return_offsets_mapping:
            out["offset_mapping"] = [(i, i + 1) for i in range(len(text))]
        return out


class PackingContracts(unittest.TestCase):
    def setUp(self):
        self.tok = CharacterTokenizer()

    def pack(self, plan="PLAN", target="part = 1", evidence="FROZEN EVIDENCE", tok=None):
        return tokenize_stage4b_preserve_target(tok or self.tok, plan, target,
                    modality="step", evidence=evidence, case_id="fixture/predicted")

    def test_fitting_sequence_matches_legacy_exactly(self):
        new, _ = self.pack()
        old = tokenize_supervised(self.tok, build_program_prompt({}, "step", "PLAN", evidence_text="FROZEN EVIDENCE"), "part = 1")
        self.assertTrue(all(torch.equal(old[k], new[k]) for k in old))

    def test_exact_boundary_preserves_eos(self):
        base = len(self.pack(plan="")[0]["input_ids"])
        f, a = self.pack(plan="x" * (1536 - base))
        self.assertEqual(len(f["input_ids"]), 1536)
        self.assertFalse(a["plan_truncated"])
        self.assertEqual(f["labels"][-1].item(), self.tok.eos_token_id)

    def test_overflow_protects_target_and_suffix(self):
        f, a = self.pack(plan="PLAN" * 1000)
        self.assertTrue(a["plan_truncated"])
        expected = self.tok("part = 1~", add_special_tokens=False)["input_ids"]
        self.assertEqual(f["labels"][f["labels"] != -100].tolist(), expected)
        text = "".join(chr(i - 2) for i in f["input_ids"].tolist()[1:-len(expected)])
        self.assertEqual(text, build_program_prompt({}, "step", a["visible_plan"], evidence_text="FROZEN EVIDENCE"))

    def test_unicode_is_literal_prefix(self):
        plan = "孔径\U0001f527é\n" * 500
        _, a = self.pack(plan=plan)
        self.assertTrue(plan.startswith(a["visible_plan"]))
        self.assertNotIn("\ufffd", a["visible_plan"])

    def test_empty_plan_not_replaced(self):
        _, a = self.pack(plan="")
        self.assertEqual(a["visible_plan"], "")
        self.assertTrue(a["model_plan_empty"])
        self.assertFalse(a["plan_emptied_by_budget"])

    def test_invalid_plan_retained_without_grammar_filter(self):
        _, a = self.pack(plan="NOT_VALID_IR")
        self.assertEqual(a["visible_plan"], "NOT_VALID_IR")

    def test_hard_overflow_fails_with_identity(self):
        with self.assertRaisesRegex(ValueError, "fixture/predicted: instruction\\+target overflow"):
            self.pack(plan="", target="x" * 2000)

    def test_budget_can_empty_plan(self):
        base = len(self.pack(plan="", target="x")[0]["input_ids"])
        _, a = self.pack(plan="MUST BE EMPTY", target="x" * (1537 - base))
        self.assertEqual(a["final_sequence_tokens"], MAX_LENGTH)
        self.assertTrue(a["plan_emptied_by_budget"])

    def test_missing_target_fails(self):
        for value in (None, "", " "):
            with self.assertRaisesRegex(ValueError, "empty reference-code target"):
                self.pack(target=value)

    def test_missing_plan_not_treated_as_empty(self):
        with self.assertRaisesRegex(ValueError, "missing construction plan"):
            self.pack(plan=None)

    def test_deterministic_across_rng_and_call_order(self):
        f, a = self.pack(plan="p" * 4000)
        random.seed(923)
        self.pack(plan="ANOTHER")
        g, b = self.pack(plan="p" * 4000)
        self.assertEqual(a, b)
        self.assertTrue(torch.equal(f["input_ids"], g["input_ids"]))

    def test_collator_preserves_full_labels(self):
        features = [self.pack(plan=p)[0] for p in ("x", "p" * 4000)]
        batch = collate(features, self.tok.pad_token_id)
        self.assertTrue(torch.all(batch["labels"][batch["attention_mask"] == 0] == -100))
        self.assertEqual((batch["labels"] != -100).sum(1).tolist(), [9, 9])

    def test_roles_share_policy_and_empty_prediction_stays_empty(self):
        class Cache:
            def load(self, case):
                return {"reference_ir": "GT_PLAN", "reference_code": "part = 1", "evidence": "e"}, None, None
        cases = [{"sample_id": "x", "case_index": 0, "source_split": "train", "modality": "step", "role": "predicted"},
                 {"sample_id": "y", "case_index": 1, "source_split": "train", "modality": "step", "role": "gt"}]
        d = Stage4bPackedDataset(cases, Cache(), self.tok, {"x": {"predicted_ir": ""}})
        self.assertEqual(d.audited_item(0)[1]["visible_plan"], "")
        self.assertEqual(d.audited_item(1)[1]["visible_plan"], "GT_PLAN")
        d.predictions = {}
        with self.assertRaisesRegex(ValueError, "missing predicted-role plan"):
            d[0]

    def test_real_frozen_bpe_tokenizer(self):
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(PACKAGE / "artifacts/initialization/arm_A", local_files_only=True)
        for plan in ("ADD box\nEND", "NOT_IR" * 2000, "孔é\U0001f527" * 1600, ""):
            f, a = self.pack(plan=plan, tok=tok)
            self.assertLessEqual(len(f["input_ids"]), 1536)
            target = tok("part = 1" + tok.eos_token, add_special_tokens=False)["input_ids"]
            self.assertEqual(f["labels"][f["labels"] != -100].tolist(), target)
            self.assertTrue(plan.startswith(a["visible_plan"]))
            if not a["plan_truncated"]:
                old = tokenize_supervised(tok, build_program_prompt({}, "step", plan, evidence_text="FROZEN EVIDENCE"), "part = 1")
                self.assertTrue(torch.equal(f["input_ids"], old["input_ids"]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PackingContracts)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    write_json_new(args.report, {"created_utc": datetime.now(timezone.utc).isoformat(), "tests_run": result.testsRun,
        "failures": len(result.failures), "errors": len(result.errors), "status": "PASS" if result.wasSuccessful() else "FAIL",
        "training_started": False, "real_frozen_bpe_tokenizer_tested": True})
    sys.exit(0 if result.wasSuccessful() else 1)
