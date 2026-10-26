"""CPU-only contracts for final row audit and descriptive paired statistics."""
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import register_exposure_final_results as audit


def fixture():
    ids = ["case1", "case2"]
    candidates = [{**{k:True for k in audit.FLAGS}, "error":"", "cd":x, "f_score_1pct":0.25,
        "bbox_err":0.1, "target_bbox_diag":10., "gen_bbox_diag":9., "bbox_ratio_to_gt":0.9} for x in (1.,3.)]
    rows = [{"sample_id":sid,"modality":"step","has_target":True,"candidate_results":[c]} for sid,c in zip(ids,candidates)]
    gates = [{"sample_id":sid, **{k:True for k in audit.FLAGS}, "error":""} for sid in ids]
    inputs = [{"sample_id":sid,"modality":"step","all_candidates":["code"]} for sid in ids]
    preds = [{"sample_id":sid,"modality":"step","prediction":"code"} for sid in ids]
    return rows,gates,inputs,preds,ids,"step"


class FinalAuditContracts(unittest.TestCase):
    def test_success_and_metric_distributions(self):
        out, _ = audit.audit_geometry(*fixture())
        self.assertEqual(out["rows"],2)
        self.assertEqual(out["scoreable"],2)
        self.assertEqual(out["conditional"]["cd"]["mean"],2)
        self.assertEqual(out["conditional"]["cd"]["q25"],1.5)
        self.assertEqual(out["unconditional_f_score_1pct"]["mean"],0.25)

    def test_post_export_failure_zero_only_for_unconditional_f1(self):
        args=fixture()
        c=args[0][1]["candidate_results"][0]
        c.update({k:None for k in audit.METRICS})
        c["error"]="point cloud sampling failed on generated part"
        out,_=audit.audit_geometry(*args)
        self.assertEqual(out["scoreable"],1)
        self.assertEqual(out["conditional"]["cd"]["mean"],1)
        self.assertEqual(out["unconditional_f_score_1pct"]["mean"],0.125)
        self.assertEqual(out["export_but_unscoreable_ids"],["case2"])
        self.assertEqual(out["first_failure_stage_counts"]["post_export_geometry_failure"],1)

    def test_fail_missing_or_duplicate_id(self):
        for data_index in range(4):
            args=fixture()
            args[data_index][1]["sample_id"]="case1"
            with self.assertRaisesRegex(ValueError,"ID/order/count/uniqueness"):
                audit.audit_geometry(*args)

    def test_fail_reordered_rows(self):
        args=fixture()
        args[0].reverse()
        with self.assertRaises(ValueError): audit.audit_geometry(*args)

    def test_fail_wrong_modality(self):
        args=fixture()
        args[2][1]["modality"]="point"
        with self.assertRaisesRegex(ValueError,"modality"): audit.audit_geometry(*args)

    def test_fail_wrong_prediction(self):
        args=fixture()
        args[2][1]["all_candidates"]=["different"]
        with self.assertRaisesRegex(ValueError,"prediction/input"): audit.audit_geometry(*args)

    def test_fail_multiple_candidates(self):
        args=fixture()
        args[0][0]["candidate_results"]*=2
        with self.assertRaisesRegex(ValueError,"one candidate"): audit.audit_geometry(*args)

    def test_fail_bad_flags(self):
        for invalid in (1,None):
            args=fixture()
            args[0][0]["candidate_results"][0]["build_ok"]=invalid
            with self.assertRaisesRegex(ValueError,"gate flag"): audit.audit_geometry(*args)

    def test_fail_nonmonotonic_flags(self):
        args=fixture()
        args[0][0]["candidate_results"][0]["exec_ok"]=False
        with self.assertRaisesRegex(ValueError,"monotonic"): audit.audit_geometry(*args)

    def test_fail_invalid_numeric_metrics(self):
        for key,value in (("cd",float("nan")),("cd",float("inf")),("cd",True),("cd",-1.),("f_score_1pct",1.01),("f_score_1pct",-0.1)):
            args=fixture()
            args[0][0]["candidate_results"][0][key]=value
            with self.assertRaises(ValueError): audit.audit_geometry(*args)

    def test_fail_metrics_without_target(self):
        args=fixture()
        args[0][0]["has_target"]=False
        with self.assertRaisesRegex(ValueError,"without valid target"): audit.audit_geometry(*args)

    def test_missing_target_retained(self):
        args=fixture()
        args[0][0]["has_target"]=False
        args[0][0]["candidate_results"][0].update({k:None for k in audit.METRICS})
        out,_=audit.audit_geometry(*args)
        self.assertEqual(out["rows"],2)
        self.assertEqual(out["missing_target_ids"],["case1"])
        self.assertEqual(out["scoreable"],1)

    def test_native_crash_not_syntax_failure(self):
        args=fixture()
        args[0][0].update(has_target=None,candidate_results=[],error="kernel access violation recorded on resume")
        out,_=audit.audit_geometry(*args)
        self.assertEqual(out["kernel_crash_ids"],["case1"])
        self.assertEqual(out["first_failure_stage_counts"]["kernel_crash"],1)
        self.assertNotIn("syntax_ok_failure",out["first_failure_stage_counts"])

    def test_geometry_gate_disagreement_preserved(self):
        args=fixture()
        args[1][0]["step_export_ok"]=False
        args[1][0]["error"]="native gate export failure"
        out,_=audit.audit_geometry(*args)
        self.assertEqual(out["standalone_vs_geometry_gate_mismatches"][0]["flags"],["step_export_ok"])

    def test_no_outlier_filtering(self):
        args=fixture()
        args[0][1]["candidate_results"][0]["cd"]=1e15
        out,_=audit.audit_geometry(*args)
        self.assertEqual(out["conditional"]["cd"]["n"],2)
        self.assertGreater(out["conditional"]["cd"]["mean"],1e14)
        self.assertEqual(out["extreme_cd_cases_gt_1000"][0]["sample_id"],"case2")

    def test_error_does_not_coexist_with_scored_success(self):
        args=fixture()
        args[0][0]["candidate_results"][0]["error"]="unexpected"
        with self.assertRaisesRegex(ValueError,"failure message"): audit.audit_geometry(*args)

    def test_paired_directions_and_ties(self):
        cd=audit.paired([2.,1.,3.],[1.,2.,3.+1e-13],True)
        f1=audit.paired([0.,.5,.25],[.1,.4,.25],False)
        self.assertEqual((cd["B_wins"],cd["A_wins"],cd["ties"]),(1,1,1))
        self.assertEqual((f1["B_wins"],f1["A_wins"],f1["ties"]),(1,1,1))

    def test_paired_rejects_unequal_or_nonfinite(self):
        for a,b in (([1.],[]),([1.],[float("inf")]),([True],[1.])):
            with self.assertRaises(ValueError): audit.paired(a,b,True)

    def test_exact_sign_p_and_empty(self):
        self.assertEqual(audit.sign_p(0,0),1.)
        self.assertEqual(audit.sign_p(10,0),2/1024)
        self.assertEqual(audit.sign_p(1,1),1.)
        self.assertEqual(audit.paired([],[],True)["n"],0)

    def test_describe_sample_sd_and_interpolated_quantiles(self):
        out=audit.describe([0.,2.])
        self.assertAlmostEqual(out["sd_sample"],math.sqrt(2.))
        self.assertEqual(out["q99"],1.98)
        self.assertEqual(audit.describe([]),{"n":0})


if __name__ == "__main__":
    destination=audit.PACKAGE/"execution/exposure_final_audit_tests_20261022.json"
    audit.reject_existing(destination)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(FinalAuditContracts))
    audit.write_json_new(destination,{"created_utc":audit.inference.original.now(),"status":"PASS" if result.wasSuccessful() else "FAIL",
        "tests_run":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),
        "audit_source":audit.record(Path(audit.__file__)),"test_source":audit.record(Path(__file__)),
        "metric_helper_source":audit.record(Path(audit.prior_metrics.__file__)),"CAD_or_model_execution":False,
        "scope":"Synthetic geometry rows, ID/association/schema guards, scoreable/denominator/outlier/paired-statistic contracts"})
    sys.exit(0 if result.wasSuccessful() else 1)
