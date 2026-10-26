"""Focused tests for missing values, ranks, stable selection, and rare slots."""
import copy
import unittest
from common import ROOT, read
from select_cases import percentiles, rank_quantile, select


class SelectionTests(unittest.TestCase):
    def test_midrank(self):
        self.assertEqual(percentiles([("a",1),("b",1),("c",2),("d",3)]),{"a":.25,"b":.25,"c":.625,"d":.875})

    def test_zero_is_a_value(self):
        self.assertEqual(percentiles([("zero",0),("one",1)])["zero"],.25)

    def test_tie_is_id_stable(self):
        rank,_=rank_quantile(["c","a","b"],lambda _:1,.5)
        self.assertEqual(rank,["a","b","c"])

    def test_one_sample(self):
        self.assertEqual(percentiles([("a",23)]),{"a":.5})

    def test_actual_deterministic_and_unique(self):
        m=read(ROOT/"audit/master_records_v1.json")
        t=read(ROOT/"taxonomy/failure_taxonomy_v1.json")
        a,order=select(m,t)
        b,_=select(m,t)
        self.assertEqual(a,b)
        self.assertEqual(len(a),18)
        self.assertEqual(len({s["selected"]["sample_id"] for s in a}),18)
        self.assertTrue(all(s["ranking"] for s in a))
        self.assertEqual([s["cohort_size"] for slot in order for s in a if s["slot"]==slot], sorted(s["cohort_size"] for s in a))

    def test_order_does_not_change_selection(self):
        m=read(ROOT/"audit/master_records_v1.json")
        t=read(ROOT/"taxonomy/failure_taxonomy_v1.json")
        a,_=select(m,t)
        m["rows"].reverse()
        t["rows"].reverse()
        b,_=select(m,t)
        self.assertEqual(a,b)

    def test_null_iou_excluded_from_numeric_slots(self):
        m=read(ROOT/"audit/master_records_v1.json")
        t=read(ROOT/"taxonomy/failure_taxonomy_v1.json")
        a,_=select(m,t)
        views={r["sample_id"]:r["view"] for r in m["rows"]}
        for slot in a:
            if slot["slot"] in ("M01","M02","M03","M05","A01","A02","A03"):
                for r in slot["ranking"]:
                    self.assertIsNotNone(views[r["sample_id"]]["mirage_IoU"])
                    self.assertIsNotNone(views[r["sample_id"]]["cadr_IoU"])

    def test_missing_cohort_fails(self):
        m=read(ROOT/"audit/master_records_v1.json")
        t=read(ROOT/"taxonomy/failure_taxonomy_v1.json")
        m=copy.deepcopy(m)
        for row in m["rows"]:
            if row["view"]["mirage_IoU"] is not None and row["view"]["cadr_IoU"] is not None:
                row["view"]["mirage_IoU"]=row["view"]["cadr_IoU"]
        with self.assertRaisesRegex(ValueError,"Empty cohort"):
            select(m,t)


if __name__=="__main__":
    unittest.main()
