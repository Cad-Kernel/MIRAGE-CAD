"""Read-only contract tests; never load or execute model/CAD source."""
import ast
from pathlib import Path
import unittest
from audit_fusion360 import unique_index,metric,resolve


class AuditContractTests(unittest.TestCase):
    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):
            unique_index([{"sample_id":"a"},{"sample_id":"a"}],"fixture")

    def test_join_is_keyed_not_positional(self):
        original=[{"sample_id":"a"},{"sample_id":"b"}]
        reversed_rows=[{"sample_id":"b","value":20},{"sample_id":"a","value":10}]
        indexed=unique_index(reversed_rows,"fixture")
        self.assertEqual([indexed[r["sample_id"]]["value"] for r in original],[10,20])

    def test_failed_iou_not_coerced_to_zero(self):
        row={"iou_status":"boolean_failed","evaluation":{"iou":None}}
        self.assertIsNone(metric(row,"iou","iou_status"))

    def test_measured_zero_is_preserved(self):
        row={"iou_status":"ok","evaluation":{"iou":0.0}}
        self.assertEqual(metric(row,"iou","iou_status"),0.0)

    def test_status_ok_without_value_rejected(self):
        with self.assertRaises(ValueError):
            metric({"cd_status":"ok","evaluation":{}},"cd_x1000","cd_status")

    def test_nonfinite_metric_rejected(self):
        with self.assertRaises(ValueError):
            metric({"cd_status":"ok","evaluation":{"cd_x1000":float("nan")}},"cd_x1000","cd_status")

    def test_windows_wsl_paths_are_same_file_identity(self):
        self.assertEqual(resolve("__LOCAL_WORKSPACE__/Project/a.step"),resolve("__LOCAL_WORKSPACE__\\Project\\a.step"))
        self.assertEqual(resolve("__USER_HOME__/a.json"),resolve("//wsl.localhost/Ubuntu__USER_HOME__/a.json"))

    def test_no_model_or_cad_imports(self):
        tree=ast.parse((Path(__file__).parent/"audit_fusion360.py").read_text())
        imported=[]
        for n in ast.walk(tree):
            if isinstance(n,ast.Import):
                imported.extend(a.name.split(".")[0] for a in n.names)
            elif isinstance(n,ast.ImportFrom) and n.module:
                imported.append(n.module.split(".")[0])
        self.assertFalse(set(imported)&{"torch","transformers","flluma","cadquery","OCP","trimesh"})


if __name__=="__main__":
    unittest.main()
