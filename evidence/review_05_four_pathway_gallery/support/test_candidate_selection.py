import copy
import json
from pathlib import Path
import tempfile
import unittest

import select_gallery_candidates as s


def cohort():
    rows=[]
    for i in range(48):
        rows.append({"sample_id":f"case_{i:03d}","modality":"text","eligible":True,"scoreable":True,
            "cd":float(50-i),"f1":i/100,"complexity_tier":f"L{i%4+1}","operation_count":i%7+1,
            "operation_set":["OP_A"]+(["OP_RARE"] if i==47 else []),"gate_status":"pass","gate_error":""})
    s.percentiles(rows,"cd")
    s.percentiles(rows,"f1")
    for i in range(48,60):
        rows.append({"sample_id":f"case_{i:03d}","modality":"text","eligible":True,"scoreable":False,
            "cd":None,"f1":None,"complexity_tier":f"L{i%4+1}","operation_count":i%7+1,
            "operation_set":["OP_A"],"gate_status":"execution_failure" if i<58 else "syntax_failure",
            "gate_error":"exec error: API" if i<56 else "exec error: other" if i<58 else "SyntaxError"})
    return rows


class CandidateContracts(unittest.TestCase):
    def test_midrank_ties_and_singleton(self):
        rows=[{"v":0.},{"v":0.},{"v":1.}]
        s.percentiles(rows,"v")
        self.assertEqual([r["v_percentile"] for r in rows],[.25,.25,1.])
        one=[{"v":7.}]
        s.percentiles(one,"v")
        self.assertEqual(one[0]["v_percentile"],.5)

    def test_determinism_independent_of_input_order(self):
        a=cohort()
        b=list(reversed(copy.deepcopy(a)))
        self.assertEqual(s.select_cases(a),s.select_cases(b))

    def test_main_pair_and_all_tiers(self):
        rows=cohort()
        choices,shortages=s.select_cases(rows)
        self.assertFalse(shortages)
        main=[x for x in choices if x["placement"]=="main"]
        self.assertEqual([x["case_type"] for x in main],["representative_success","hard_failure"])
        self.assertEqual(len({x["sample_id"] for x in choices}),len(choices))
        index={x["sample_id"]:x for x in rows}
        self.assertEqual({index[x["sample_id"]]["complexity_tier"] for x in choices},{"L1","L2","L3","L4"})

    def test_main_success_not_maximum_f1(self):
        rows=cohort()
        choice=s.select_cases(rows)[0][0]
        selected=next(x for x in rows if x["sample_id"]==choice["sample_id"])
        self.assertLess(abs(selected["f1_percentile"]-.5),.02)
        self.assertNotEqual(selected["f1"],.47)

    def test_common_failure_uses_majority_stage_and_error(self):
        rows=[x for x in cohort() if not x["scoreable"]]
        _,detail=s.common_failure(rows)
        self.assertEqual(detail["stage"],"execution_failure")
        self.assertEqual(detail["exact_error"],"exec error: API")
        self.assertEqual(detail["stage_count"],10)
        self.assertEqual(detail["exact_error_count"],8)

    def test_low_tail_is_tenth_percentile_not_worst(self):
        rows=cohort()
        choice=next(x for x in s.select_cases(rows)[0] if x["case_type"]=="low_tail")
        row=next(x for x in rows if x["sample_id"]==choice["sample_id"])
        self.assertLess(abs(row["f1_percentile"]-.1),.02)
        self.assertGreater(row["f1"],0)

    def test_rarity_uses_object_frequency(self):
        choices,_=s.select_cases(cohort())
        rare=next(x for x in choices if x["case_type"]=="rare_operation")
        self.assertEqual(rare["sample_id"],"case_047")
        self.assertEqual(rare["detail"]["objects_with_each_rarest_operation"],1)
        self.assertEqual(rare["detail"]["rarity_denominator"],60)

    def test_ineligible_never_selected(self):
        rows=cohort()
        rows[24]["eligible"]=False
        choices,_=s.select_cases(rows)
        self.assertNotIn(rows[24]["sample_id"],{x["sample_id"] for x in choices})

    def test_shortages_not_fabricated(self):
        choices,shortages=s.select_cases([])
        self.assertFalse(choices)
        self.assertGreater(len(shortages),0)

    def test_feature_parser_and_wrong_sample(self):
        ir="PART case CAT bracket UNITS mm SEED 42\nF sketch OP_SKETCH\nF pad OP_EXTRUDE"
        features=s.reference_features(ir,"case")
        self.assertEqual(features["operation_count"],2)
        self.assertEqual(features["operation_set"],["OP_EXTRUDE","OP_SKETCH"])
        with self.assertRaisesRegex(ValueError,"identity"):
            s.reference_features(ir,"another")
        with self.assertRaisesRegex(ValueError,"units"):
            s.reference_features(ir.replace("UNITS mm","UNITS inch"),"case")

    def test_scoreable_not_just_export_or_zero_f1(self):
        c={**{k:True for k in s.FLAGS},"cd":1.,"f_score_1pct":0.}
        self.assertTrue(s.scoreable({"has_target":True},c))
        self.assertFalse(s.scoreable({"has_target":False},c))
        for value in (None,float("nan"),True):
            self.assertFalse(s.scoreable({"has_target":True},{**c,"cd":value}))

    def test_physical_locator_and_duplicate_guards(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"rows.jsonl"
            path.write_text('\n{"sample_id":"a"}\n\n{"sample_id":"b"}\n',encoding="utf-8")
            rows=s.read_index(path,["a","b"])
            self.assertEqual(rows["b"]["line_1based"],4)
            with self.assertRaisesRegex(ValueError,"order"):
                s.read_index(path,["b","a"])
            path.write_text('{"sample_id":"a"}\n{"sample_id":"a"}\n',encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"Duplicate"):
                s.read_index(path)

    def test_nonrepository_does_not_receive_an_invented_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            observed=s.observe_checkout(directory)
            self.assertIsNone(observed["commit"])
            self.assertEqual(observed["git_status"],"UNAVAILABLE_OR_NOT_A_REPOSITORY")


if __name__=="__main__":
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CandidateContracts))
    s.write_json(s.PACKAGE/"selection/candidate_contract_tests_v2.json",{"created_utc":s.now(),"status":"PASS" if result.wasSuccessful() else "FAIL",
        "tests_run":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),"source":s.file_record(s.__file__),
        "test_source":s.file_record(__file__),"scope":"Synthetic selection/percentile/rarity/tier/locator guards only; no model/CAD"})
    raise SystemExit(0 if result.wasSuccessful() else 1)
