"""Small regression tests for the frozen manifest builder (no torch/model imports)."""
from pathlib import Path
import tempfile
import unittest

import prepare_exposure_policy as prep


class ManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.splits = {s: [{"sample_id": f"{s}_{i}"} for i in range(n)]
                      for s, n in (("train", 25000), ("val", 2500), ("test", 2500))}
        cls.manifests = prep.build_manifests(**cls.splits)

    def test_counts_and_roles(self):
        prep.verify_manifests(self.manifests, self.splits["train"])
        self.assertEqual(len(self.manifests["evaluation_shared.jsonl"]), 10000)
        self.assertEqual(len(self.manifests["validation_shared.jsonl"]), 800)

    def test_deterministic_bytes(self):
        again = prep.build_manifests(**self.splits)
        self.assertEqual(prep.object_hash(again), prep.object_hash(self.manifests))

    def test_duplicate_id_rejected(self):
        bad = {**self.splits, "train": self.splits["train"] + [self.splits["train"][0]]}
        with self.assertRaisesRegex(ValueError, "Duplicate ID"):
            prep.check_source_ids(bad)

    def test_split_leakage_rejected(self):
        bad = {**self.splits, "val": [self.splits["train"][0]]}
        with self.assertRaisesRegex(ValueError, "leakage"):
            prep.check_source_ids(bad)

    def test_arm_order_change_rejected(self):
        bad = {**self.manifests, "phase1_B.jsonl": list(reversed(self.manifests["phase1_B.jsonl"]))}
        with self.assertRaisesRegex(ValueError, "source order"):
            prep.verify_manifests(bad, self.splits["train"])

    def test_role_change_rejected(self):
        roles = [dict(r) for r in self.manifests["stage4b_roles.jsonl"]]
        roles[0]["role"] = "gt"
        bad = {**self.manifests, "stage4b_roles.jsonl": roles}
        with self.assertRaisesRegex(ValueError, "role counts"):
            prep.verify_manifests(bad, self.splits["train"])

    def test_existing_content_cannot_be_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "manifest.json"
            prep.write_once(p, b"original\n")
            prep.write_once(p, b"original\n")
            with self.assertRaisesRegex(ValueError, "Refusing to replace"):
                prep.write_once(p, b"changed\n")
            self.assertEqual(p.read_bytes(), b"original\n")


if __name__ == "__main__":
    unittest.main()
