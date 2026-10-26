"""Small synthetic log fixtures, never model/CAD execution."""
import copy
import unittest
from classify_native_logs import classify,subtype


def good():
    native={"pipeline_status":"SUCCESS","cd_status":"ok","iou_status":"ok",
            "evaluation":{"cd_x1000":1.25,"iou":.5,"remesh_status":"ok"}}
    gate={k:True for k in ("syntax_ok","exec_ok","build_ok","solid_valid","step_export_ok")}
    return native,gate


class NativeTaxonomyTests(unittest.TestCase):
    def failed(self,field,error):
        n,g=good()
        n.update(pipeline_status="NO_GEOMETRY",cd_status=None,iou_status=None,evaluation={})
        fields=list(g)
        for k in fields[fields.index(field):]:
            g[k]=False
        g["error"]=error
        return n,g

    def test_cd_scoreable_is_not_semantic_success(self):
        n,g=good()
        r=classify("mirage",n,g)
        self.assertEqual(r["primary_outcome"],"CD_SCOREABLE")
        self.assertIsNone(r["verified_semantic_failure"])
        self.assertEqual(r["geometry_review_status"],"NOT_VISUALLY_REVIEWED")

    def test_scoreable_has_no_spurious_ok_error(self):
        n,g=good()
        self.assertIsNone(classify("mirage",n,g)["reported_error"])

    def test_measured_zero_iou_preserved(self):
        n,g=good()
        n["evaluation"]["iou"]=0.0
        r=classify("mirage",n,g)
        self.assertEqual(r["IoU"],0.0)
        self.assertEqual(r["iou_outcome"],"IOU_AVAILABLE")
        self.assertIsNone(r["verified_failure_class"])

    def test_boolean_failure_separate_from_primary(self):
        n,g=good()
        n["iou_status"]="boolean_failed"
        n["evaluation"]["iou"]=None
        r=classify("mirage",n,g)
        self.assertEqual(r["primary_outcome"],"CD_SCOREABLE")
        self.assertIsNone(r["verified_failure_class"])
        self.assertIsNone(r["IoU"])
        self.assertEqual(r["iou_failure_class"],"IOU_BOOLEAN_FAILURE")

    def test_syntax_precedes_execution_flag(self):
        n,g=self.failed("syntax_ok","SyntaxError: invalid syntax")
        self.assertEqual(classify("mirage",n,g)["primary_outcome"],"SYNTAX_FAILURE")

    def test_crash_not_mislabelled_syntax(self):
        n,g=self.failed("syntax_ok","kernel access violation (0xC0000005)")
        self.assertEqual(classify("mirage",n,g)["primary_outcome"],"KERNEL_CRASH_STAGE_UNRESOLVED")

    def test_build_gate_distinct(self):
        n,g=self.failed("build_ok","build error")
        self.assertEqual(classify("mirage",n,g)["primary_outcome"],"BUILD_FAILURE")

    def test_solid_validity_gate_distinct(self):
        n,g=self.failed("solid_valid","invalid solid")
        self.assertEqual(classify("mirage",n,g)["primary_outcome"],"SOLID_VALIDITY_FAILURE")

    def test_export_error_not_moved_to_build(self):
        n,g=self.failed("step_export_ok","STEP export error: OCCT build failed")
        r=classify("mirage",n,g)
        self.assertEqual(r["primary_outcome"],"STEP_EXPORT_FAILURE")
        self.assertEqual(r["reason_subtype"],"OCCT_BUILD_ERROR_DURING_STEP_EXPORT")

    def test_post_export_empty_mesh(self):
        n,g=good()
        n.update(pipeline_status="EMPTY_PREDICTION_MESH",cd_status=None,iou_status=None,evaluation={},pred_mesh_triangles_on_failure=0)
        r=classify("nn",n,g)
        self.assertEqual(r["primary_outcome"],"EMPTY_PREDICTION_MESH")
        self.assertEqual(r["reason_subtype"],"ZERO_TRIANGLE_TESSELLATION_REPORTED")

    def test_empty_mesh_does_not_invent_zero_triangles(self):
        self.assertEqual(subtype("EMPTY_PREDICTION_MESH","",native={})[0],"EMPTY_TESSELLATION_REPORTED")

    def test_zero_face_remesh_failure(self):
        n,g=good()
        n.update(pipeline_status="REMESH_FAILED",cd_status=None,iou_status="ineligible",evaluation={"remesh_status":"REMESH_FAILED"},prediction_step_diagnostics={"n_faces":0})
        r=classify("mirage",n,g)
        self.assertEqual(r["reason_subtype"],"ZERO_FACE_PREDICTION_REPORTED")
        self.assertEqual(r["iou_outcome"],"UNAVAILABLE_AFTER_PRIMARY_FAILURE")

    def test_missing_method_names_retained(self):
        result=subtype("EXECUTION_FAILURE","exec error: 'Part' object has no attribute 'clip_stock'")
        self.assertEqual(result,("MISSING_API_ATTRIBUTE","Part / clip_stock"))

    def test_unexpected_keyword_names_retained(self):
        result=subtype("EXECUTION_FAILURE","exec error: Part.wedge() got an unexpected keyword argument 'width'")
        self.assertEqual(result,("UNEXPECTED_KEYWORD_ARGUMENT","Part.wedge / width"))

    def test_topology_reference_is_log_fact(self):
        self.assertEqual(subtype("EXECUTION_FAILURE","exec error: topology reference 'abc' did not resolve any face")[0],"UNRESOLVED_TOPOLOGY_REFERENCE")

    def test_quoted_word_not_assumed_keyerror(self):
        self.assertEqual(subtype("EXECUTION_FAILURE","exec error: 'width'")[0],"EXECUTION_FAILURE_REASON_UNSPECIFIED")

    def test_cadr_traceback_required_for_line_label(self):
        error="StdFail_NotDone: BRep_API: command not done"
        self.assertEqual(subtype("EXECUTION_FAILURE",error)[0],"KERNEL_OPERATION_ERROR_REPORTED")
        self.assertEqual(subtype("EXECUTION_FAILURE",error,"Edge.makeLine(...)")[0],"CADQUERY_LINE_EDGE_CONSTRUCTION_REPORTED")

    def test_cadr_arc_traceback_label(self):
        self.assertEqual(subtype("EXECUTION_FAILURE","StdFail_NotDone: GC_MakeArcOfCircle::Value() - no result","makeThreePointArc(...)")[0],"CADQUERY_THREE_POINT_ARC_CONSTRUCTION_REPORTED")

    def test_nonfinite_cd_rejected(self):
        n,g=good()
        n["evaluation"]["cd_x1000"]=float("nan")
        with self.assertRaises(ValueError):
            classify("mirage",n,g)

    def test_conflicting_failure_and_valid_cd_rejected(self):
        n,g=good()
        g["exec_ok"]=False
        with self.assertRaises(ValueError):
            classify("mirage",n,g)


if __name__=="__main__":
    unittest.main()
