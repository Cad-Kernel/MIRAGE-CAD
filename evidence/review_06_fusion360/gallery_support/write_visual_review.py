"""Record assistant observations after viewing both contact-series and A10 detail."""
from common import *

OBSERVATIONS = {
    "M01": ("GLOBAL_SHAPE_MISMATCH", "Reference is a thin open frame with diagonal members. CAD-Recode also renders a thin frame-like structure, while MIRAGE is a thick notched block with a raised circular boss. NN is a cross-like plate. Relative MIRAGE success here means only higher IoU than CAD-Recode: both IoUs are very low, and MIRAGE CD is worse. Do not caption this as an accurate reconstruction."),
    "M02": ("OPEN_FRAME_REPLACED_BY_BLOCKS", "The reference has open triangular-frame regions and circular end features. MIRAGE shows separate block-like elements rather than the visible frame. CAD-Recode preserves more of the broad plate/circular motif but visibly differs in the openings and detached-looking circular elements. Connectivity is not inferred from the image alone."),
    "M03": ("PLANAR_TO_ROUNDED_BODY", "Reference and CAD-Recode appear as thin upright planar parts, almost edge-on in the front view. MIRAGE and NN are rounded capsule-like bodies. This is a visible global shape/thickness mismatch, not merely an API failure."),
    "M04": ("NATIVE_EXECUTION_FAILURE", "Reference and CAD-Recode are rectangular slab-like solids in both views. MIRAGE has no historical executed geometry and is an explicit API/schema-pattern execution-failure placeholder. NN is a different tapered/wedge-like solid. Do not infer what the failed MIRAGE code would have looked like."),
    "M05": ("CIRCULAR_PART_REPLACED_BY_BOSSED_BLOCK", "Reference is a circular disk-like part with visible openings; CAD-Recode retains a circular envelope but differs in the openings. MIRAGE is a bossed block with a different global outline, and NN is an obround block. MIRAGE's measured zero IoU is retained, not treated as missing."),
    "M06": ("STEPPED_SHAFT_TO_OVAL_BODY", "Reference and CAD-Recode have a stepped coaxial shaft-and-flange outline. MIRAGE and NN are flattened oval/ellipsoid-like bodies without the visible stepped shaft profile. MIRAGE's IoU advantage over NN is relative, not faithful recovery of the shaft."),
    "A01": ("SLENDER_LINK_TO_BLOCK", "Reference and CAD-Recode are slender rounded-end link-like parts; small openings are visible at the reference ends. MIRAGE is a notched block with circular detail and NN is a stepped bridge-like plate. This supports a global family mismatch, not a specific causal explanation."),
    "A02": ("COAXIAL_SHAFT_TO_BOSSED_BLOCK", "Reference is a stepped cylindrical/coaxial part. CAD-Recode retains the broad cylindrical envelope but fewer visible step details. MIRAGE is a bossed block and NN is a cross-like plate; neither matches the visible cylindrical reference outline."),
    "A03": ("STEPPED_PIN_TO_CAPSULE", "Reference and CAD-Recode show a pin with a narrower terminal shaft. MIRAGE is a rounded capsule-like body, so the visible step and narrow terminal section are not reproduced. NN is also rounded and narrower. Being at MIRAGE's paired q90 does not make this an absolute success."),
    "A04": ("NATIVE_EXECUTION_FAILURE", "Reference and CAD-Recode show shaft/flange-like parts. MIRAGE remains a missing-API execution-failure placeholder. NN shows repeated fins, a different global construction. No semantic geometry label is assigned to the absent MIRAGE output."),
    "A05": ("PERFORATED_PLATE_TO_SOLID_BLOCK", "The reference is a waisted plate with four visibly open corner holes. CAD-Recode retains a waisted plate-like silhouette, but the four corresponding openings are not visible in these views. MIRAGE has separate block-like pieces and NN is capsule-like. Hole absence is a view-level observation, not a proven count of all internal features."),
    "A06": ("NATIVE_CADR_FAILURE_AND_ROUNDED_MIRAGE", "Reference shows a shaft behind a circular flange. CAD-Recode has no executed geometry. MIRAGE and NN are rounded oval/sphere-like shapes rather than the visible shaft/flange profile. Preserve CAD-Recode's execution error as a separate log category."),
    "A07": ("NATIVE_EMPTY_MESH", "Reference and CAD-Recode have annular/ring-like envelopes, with visible local detail differences. MIRAGE remains the historical empty-tessellation placeholder. NN is a solid box-like body. A successful import at another tolerance is not attempted to replace the MIRAGE failure."),
    "A08": ("NATIVE_REMESH_FAILURE", "Reference and CAD-Recode are slender straight rod-like solids. MIRAGE is the native remesh-failure placeholder, while NN is a stepped bridge-like plate. No model output is fabricated for the failed branch."),
    "A09": ("NATIVE_STEP_EXPORT_FAILURE", "Reference and CAD-Recode are short cylindrical bodies with a wider top flange. MIRAGE is an export-failure placeholder. NN is a taller faceted prism-like body with a different height/profile. The failed export is not interpreted as a visual geometry defect."),
    "A10": ("EXTREME_ASPECT_RATIO_RENDERED_GEOMETRY", "Reference is an open rectangular channel with a cylindrical extension; CAD-Recode retains side walls and the cylindrical extension but differs in the channel silhouette. MIRAGE is line-like in both fixed views, not a missing render. CD is available but IoU boolean evaluation failed. The reference-world union frame makes several methods subpixel. Cause and physical topology are unconfirmed; inspect the archived 3D shape before any stronger semantic label."),
    "A11": ("RECTANGULAR_FRAME_TO_TORUS", "Reference and CAD-Recode have rectangular open-frame outlines. MIRAGE instead renders as a rounded torus-like ring. NN remains the native empty-mesh placeholder. This supports a visible outline mismatch; it does not assign a training cause."),
    "A12": ("NATIVE_KERNEL_CRASH_UNRESOLVED", "Reference and CAD-Recode render as multi-block/bracket-like structures with different front silhouettes. MIRAGE is the native kernel-crash placeholder with unresolved crash stage. NN is a bossed/obround block. CAD-Recode's native IoU is a measured zero, not an unavailable metric; no metric troubleshooting or causal inference is performed here.")
}


def main():
    selection=read(GALLERY/"selection_v1.json")
    rows=[]
    for case in selection["cases"]:
        code,observation=OBSERVATIONS[case["slot"]]
        base=GALLERY/"cases"/case["case_id"]
        rows.append({"slot":case["slot"],"sample_id":case["sample_id"],
            "reviewer":"assistant visual inspection", "review_status":"PROVISIONAL_AWAITING_AUTHOR_CONFIRMATION",
            "review_evidence":[str(base/"metric_space_panel.png"),str(base/"reference_world_panel.png")],
            "view_scope":"Both fixed views in contact panels; A10 also inspected in its full individual panel",
            "provisional_observation_code":code,"observation":observation,
            "verified_semantic_failure":None,"author_confirmed":False,"causal_claim":None})
    write_new(GALLERY/"visual_review_v1.json",{"status":"ASSISTANT_OBSERVATIONS_RECORDED_AUTHOR_REVIEW_PENDING",
        "created_utc":utc(),"rows":rows,"scope":"View-specific provisional observations, not author-confirmed taxonomy updates",
        "earlier_step2_labels_modified":False,"selection_modified_after_viewing":False})
    write_new(GALLERY/"author_review_template_v1.json",{"instructions":"Copy this template to a new version. Confirm/revise view-level observations after inspecting the original 640px views or archived 3D STEP. Do not overwrite sealed raw evidence.",
        "cases":[{"slot":r["slot"],"sample_id":r["sample_id"],"author_confirmed":None,
                  "accepted_label":None,"revised_observation":None,"view_evidence":[],"reviewer":None,"date":None} for r in rows]})
    print("18 provisional visual observations saved; author confirmation still pending.")


if __name__=="__main__":
    main()
