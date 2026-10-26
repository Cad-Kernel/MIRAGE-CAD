"""CPU-only gate-registration contracts; no program/CAD execution."""
from pathlib import Path
import sys
import tempfile
import unittest

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, "__RUN_SOURCE_ROOT__")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import register_exposure_gate_results as audit
from cag_exposure_policy_core import record, reject_existing, write_json_new


def fixture():
    ids = [f"id{i}" for i in range(2500)]
    rows = [{"sample_id": sid, **{flag: True for flag in audit.FLAGS}, "error": ""} for sid in ids]
    predictions = [{"prediction": "part = 1"} for _ in ids]
    native = [{"sample_id": sid, "syntax_ok": True, "code_sha256": audit.code_sha("part = 1")} for sid in ids]
    return rows, predictions, ids, native


class GateAuditContracts(unittest.TestCase):
    def test_all_success_counts(self):
        result = audit.audit_rows(*fixture())
        self.assertEqual(result["counts"], {flag: 2500 for flag in audit.FLAGS})
        self.assertEqual(result["first_failure_stage_counts"], {"all_gates_pass": 2500})

    def test_order_and_duplicate_rejected(self):
        for duplicate in (True, False):
            rows, predictions, ids, native = fixture()
            if duplicate:
                rows[0]["sample_id"] = rows[1]["sample_id"]
            else:
                rows[0], rows[1] = rows[1], rows[0]
            with self.assertRaisesRegex(ValueError, "ID order mismatch"):
                audit.audit_rows(rows, predictions, ids, native)

    def test_non_boolean_rejected(self):
        rows, predictions, ids, native = fixture()
        rows[0]["exec_ok"] = 1
        with self.assertRaisesRegex(ValueError, "schema"):
            audit.audit_rows(rows, predictions, ids, native)

    def test_non_monotonic_rejected(self):
        rows, predictions, ids, native = fixture()
        rows[0]["exec_ok"] = False
        with self.assertRaisesRegex(ValueError, "Non-monotonic"):
            audit.audit_rows(rows, predictions, ids, native)

    def test_actual_syntax_disagreement_rejected(self):
        rows, predictions, ids, native = fixture()
        predictions[0]["prediction"] = "part = ("
        native[0].update(syntax_ok=False, code_sha256=audit.code_sha("part = ("))
        with self.assertRaisesRegex(ValueError, "AST syntax mismatch"):
            audit.audit_rows(rows, predictions, ids, native)

    def test_native311_f_string_failure_not_silently_replaced_by312_parse(self):
        rows, predictions, ids, native = fixture()
        rows[0].update({flag: False for flag in audit.FLAGS})
        rows[0]["error"] = "SyntaxError: f-string: unmatched '['"
        predictions[0]["prediction"] = "text=f'{params['thickness']}'"
        native[0].update(syntax_ok=False, code_sha256=audit.code_sha(predictions[0]["prediction"]))
        result = audit.audit_rows(rows, predictions, ids, native)
        self.assertEqual(result["default_parser_disagreement_sample_ids"], [ids[0]])
        self.assertEqual(result["counts"]["syntax_ok"], 2499)

    def test_execution_failure_category(self):
        rows, predictions, ids, native = fixture()
        rows[0].update({flag: False for flag in audit.FLAGS[1:]})
        rows[0]["error"] = "exec error: unknown API"
        result = audit.audit_rows(rows, predictions, ids, native)
        self.assertEqual(result["first_failure_stage_counts"]["exec_ok_failure"], 1)
        self.assertEqual(result["failure_sample_ids_by_stage"]["exec_ok_failure"], [ids[0]])

    def test_export_failure_category(self):
        rows, predictions, ids, native = fixture()
        rows[0].update(step_export_ok=False, error="STEP export error: no solid")
        result = audit.audit_rows(rows, predictions, ids, native)
        self.assertEqual(result["first_failure_stage_counts"]["step_export_ok_failure"], 1)

    def test_kernel_crash_not_misclassified_as_syntax(self):
        rows, predictions, ids, native = fixture()
        rows[0].update({flag: False for flag in audit.FLAGS})
        rows[0]["error"] = "kernel access violation recorded on resume"
        result = audit.audit_rows(rows, predictions, ids, native)
        self.assertEqual(result["kernel_crashes"], 1)
        self.assertEqual(result["independent_AST_checks"], 2499)
        self.assertEqual(result["first_failure_stage_counts"]["kernel_crash"], 1)

    def test_success_cannot_have_error(self):
        rows, predictions, ids, native = fixture()
        rows[0]["error"] = "unexpected"
        with self.assertRaisesRegex(ValueError, "Successful row"):
            audit.audit_rows(rows, predictions, ids, native)

    def test_failure_cannot_omit_error(self):
        rows, predictions, ids, native = fixture()
        rows[0]["step_export_ok"] = False
        with self.assertRaisesRegex(ValueError, "lacks an error"):
            audit.audit_rows(rows, predictions, ids, native)

    def test_utf16_and_utf8_logs_decode_exactly(self):
        text = "Python runtime: 3.11.11\nresuming: 10 already scored\n"
        with tempfile.TemporaryDirectory() as directory:
            for encoding in ("utf-16", "utf-8-sig"):
                path = Path(directory) / encoding
                path.write_bytes(text.encode(encoding))
                self.assertEqual(audit.read_cli_log(path), text)


if __name__ == "__main__":
    destination = PACKAGE / "execution/exposure_gate_audit_tests_20261021_v2.json"
    reject_existing(destination)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(GateAuditContracts))
    write_json_new(destination, {"created_utc": audit.s.original.now(), "status": "PASS" if result.wasSuccessful() else "FAIL",
        "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "audit_source": record(Path(audit.__file__)), "test_source": record(Path(__file__)),
        "CAD_or_model_execution": False, "scope": "Synthetic rows, Python AST compatibility and UTF16/UTF8 decoding only"})
    sys.exit(0 if result.wasSuccessful() else 1)
