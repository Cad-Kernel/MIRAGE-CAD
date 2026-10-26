"""Additive visual review of six locked main candidates; never author-signs them."""
from html import escape
from html.parser import HTMLParser
import os
from pathlib import Path
import sys
from urllib.parse import quote, unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"gallery_support"))
from common import ROOT, GALLERY, read, require, sha, utc, write_new, text_new

OUT = ROOT/"main_review_v1"
PARENT_SEAL = GALLERY/"gallery_archive_seal_v1.json"
METHODS = ("mirage", "cadr", "nn")
NAMES = {"mirage":"MIRAGE generated-plan", "cadr":"CAD-Recode", "nn":"NN retrieval"}

REVIEWS = {
    "M01": {
        "label":"GLOBAL_SHAPE_AND_THICKNESS_PROFILE_MISMATCH",
        "label_zh":"整体形状与厚度轮廓不匹配；仅有相对 IoU 优势",
        "observations_zh":[
            "Reference 在等轴图中是薄的开放框架，front 图呈窄条；MIRAGE 是带缺口和圆柱 boss 的厚块体，两视图均未复现原框架布局。",
            "CAD-Recode 保留了薄框架式外观，但形状细节明显不同；NN 是扁平十字板状构形，不是目标框架。",
            "原坐标共同画框中 reference/CAD-Recode 很小，MIRAGE/NN 较大。这是该坐标政策下的展示观察，不能独立解释成物理尺寸准确率。"
        ],
        "supported_terms":["global shape mismatch", "frame layout not reproduced", "thickness-profile mismatch", "relative IoU advantage only"],
        "unsupported_terms":["accurate success", "MIRAGE wins both metrics", "missing hole", "wrong extrusion", "proven topology failure"],
        "caption_en":"MIRAGE produces a notched bossed block instead of the thin open-frame reference. Its IoU is higher than CAD-Recode's in this selected case, but both IoUs are low and its CD is worse. This is a relative IoU advantage, not an accurate-reconstruction success.",
        "selection_caution":"Selected at the median positive MIRAGE-minus-CAD-Recode IoU difference among five eligible cases. It is not an absolute-success threshold or a joint CD/IoU win.",
        "semantic_scope":"Visible global shape and aspect profile; no operation-level causal diagnosis.",
        "additional_view_evidence":[]
    },
    "M02": {
        "label":"OPEN_FRAME_LAYOUT_NOT_REPRODUCED",
        "label_zh":"开放框架布局未复现，输出为块状构形",
        "observations_zh":[
            "Reference 有开放三角框架、大面积贯通空区及圆形端部；MIRAGE 的双视图显示块状构形，没有对应的框架轮廓和开口布局。",
            "CAD-Recode 保留部分板状/圆形端部母题，但可见轮廓和空区也不等同于 reference。圆片看起来分离不等于已证明 CAD 拓扑断开。",
            "NN 是桥形/阶梯板式构形，也没有复现该框架。"
        ],
        "supported_terms":["open-frame layout not reproduced", "global structural mismatch", "block-like replacement"],
        "unsupported_terms":["proven disconnected solids", "missing exactly N holes", "wrong extrusion", "minor-detail-only error"],
        "caption_en":"Near the paired median MIRAGE IoU, the reference's open triangular frame is not reproduced: MIRAGE returns block-like geometry. CAD-Recode retains more plate and circular-end structure but also differs in the visible openings and silhouette.",
        "selection_caution":"Near-median refers to MIRAGE IoU within the 200-case MIRAGE/CAD-Recode jointly IoU-scoreable cohort, not to all 400 cases or an unconditional median.",
        "semantic_scope":"Visible layout and silhouette; connectivity and internal topology unverified.",
        "additional_view_evidence":[]
    },
    "M03": {
        "label":"THIN_PLANAR_PART_REPLACED_BY_CAPSULE",
        "label_zh":"薄板被替换为胶囊状体；角部小开口仅作视图级说明",
        "observations_zh":[
            "Reference 是薄平面部件，在 front 图几乎为线；MIRAGE 与 NN 则是有圆头的厚柱/胶囊状体。主要错误是形状类别与厚度轮廓不匹配。",
            "MIRAGE 的既有 predicted plan 明确含 OP_CAPSULE，既有代码调用 part.capsule()，与渲染外观一致；这不证明错误来自哪一训练组件。",
            "CAD-Recode 保留薄板式外包络。放大查看原 640px 等轴视图，reference 右上角附近有可见小开口，CAD-Recode 对应位置未见同样开口。只能写 visible aperture not reproduced，不据此证明 STEP 中不存在任何内部孔。"
        ],
        "supported_terms":["thin planar part replaced by a capsule", "global shape/thickness mismatch", "reference corner aperture not visible in the CAD-Recode rendering"],
        "unsupported_terms":["wrong extrusion direction", "verified internal-hole count", "CAD-Recode recovered every feature", "MIRAGE only missed a hole"],
        "caption_en":"In this lower-tail case, MIRAGE generates a capsule rather than the thin planar reference, consistent with its predicted OP_CAPSULE plan and capsule API call. CAD-Recode retains the plate-like envelope; the small reference corner aperture is not visible in its fixed isometric view.",
        "selection_caution":"Selected near MIRAGE IoU q10 in the paired available-IoU cohort. The small-aperture remark is secondary to the global mismatch and is view-specific.",
        "semantic_scope":"Global shape supported by two views and static generated code. Aperture remark is visual only, not a topology proof.",
        "additional_view_evidence":["metric_space_reference_isometric.png","metric_space_cadr_isometric.png"]
    },
    "M04": {
        "label":"EXECUTION_FAILURE_UNEXPECTED_KEYWORD_ARGUMENT",
        "label_zh":"API 参数合约执行失败；不存在可供几何分类的预测模型",
        "observations_zh":[
            "Reference 和 CAD-Recode 在两个视角均呈矩形板块状实体；NN 为不同的楔形/渐变块体。",
            "MIRAGE syntax_ok=true，但 exec_ok/build/export=false；原生消息为 Part.wedge() got an unexpected keyword argument 'length'。",
            "既有 mirage_used.py 第 7 行向 part.wedge() 传入 length。只记录该调用与异常相符，不修改参数、重新执行或推断修复后的形状。"
        ],
        "supported_terms":["execution failure", "unexpected keyword argument", "API/schema-pattern failure", "no evaluated prediction geometry"],
        "unsupported_terms":["syntax failure", "wrong extrusion", "missing hole", "visually wrong MIRAGE solid", "model hallucination proved", "API-version mismatch proved"],
        "caption_en":"MIRAGE fails before producing evaluated geometry: the recorded runtime rejects the length keyword passed to Part.wedge(). The failure is shown explicitly, while the reference and CAD-Recode outputs retain the slab-like geometry. No replacement geometry is rendered.",
        "selection_caution":"A hash-ranked native API/schema-pattern execution failure with CAD-Recode CD available. This sample does not identify generation versus runtime API compatibility as the root cause.",
        "semantic_scope":"Native error and static source call verified. Geometry label for the absent MIRAGE output is not applicable.",
        "additional_view_evidence":[]
    },
    "M05": {
        "label":"CIRCULAR_OUTLINE_AND_APERTURE_LAYOUT_NOT_REPRODUCED",
        "label_zh":"圆盘轮廓及可见开口布局未复现，不能仅称缺孔",
        "observations_zh":[
            "Reference 是圆盘式部件；front 图有两个清晰的圆形通亮开口。MIRAGE 是带圆柱 boss 的块体，整体轮廓和开口布局都不同。",
            "CAD-Recode 保留圆形外包络，但 front 图出现环状间隙和矩形开口，不能写成其精确复现了原圆孔。NN 是另一种圆端块体。",
            "MIRAGE 原始 IoU=0 是可用的真实测量值，不是缺失指标或执行失败。"
        ],
        "supported_terms":["circular outline not reproduced", "different visible aperture layout", "global shape mismatch"],
        "unsupported_terms":["MIRAGE only missed two holes", "CAD-Recode exactly recovered the holes", "wrong extrusion proved", "IoU unavailable", "execution failure"],
        "caption_en":"CAD-Recode retains the circular envelope of the reference but differs in its visible openings. MIRAGE instead generates a bossed block with a different outline and aperture layout; its recorded IoU is zero. This is a global reconstruction mismatch, not an isolated missing-hole diagnosis.",
        "selection_caution":"Selected at the median positive CAD-Recode-minus-MIRAGE IoU gap, not the largest gap. Preserve the measured zero rather than marking it unavailable.",
        "semantic_scope":"View-level outline and aperture layout. Reference construction history and internal feature count are unavailable.",
        "additional_view_evidence":["metric_space_reference_front.png","metric_space_cadr_front.png"]
    },
    "M06": {
        "label":"STEPPED_SHAFT_PROFILE_REPLACED_BY_ELLIPSOID",
        "label_zh":"阶梯轴/法兰轮廓被椭球体替代",
        "observations_zh":[
            "Reference 和 CAD-Recode 都有明显的同轴宽部与窄轴阶梯轮廓；MIRAGE 与 NN 在两视图中均为椭圆/椭球状体，没有复现可见的台阶轴轮廓。",
            "MIRAGE 既有 plan 为 OP_ELLIPSOID，代码调用 part.ellipsoid()，支持将它描述为实际生成了椭球，而不是猜测 wrong extrusion。",
            "MIRAGE 在本例的 CD 和 IoU 都优于 NN，但仍未恢复阶梯轴，并明显弱于 CAD-Recode。相对优势不等于任务准确。"
        ],
        "supported_terms":["stepped shaft profile not reproduced", "ellipsoidal replacement", "loss of visible multi-radius structure"],
        "unsupported_terms":["accurate MIRAGE shaft reconstruction", "wrong extrusion proved", "only a small parameter error", "missing hole"],
        "caption_en":"The reference's stepped shaft-and-flange profile is closely retained by CAD-Recode. MIRAGE and NN instead produce ellipsoidal bodies without the visible stepped profile. MIRAGE improves both recorded geometry metrics over NN in this case, but this relative gain does not recover the target construction.",
        "selection_caution":"Selected near q75 of the absolute MIRAGE/NN IoU gap with no direction constraint. This is a retrospective stratified example, not an estimate of how often MIRAGE beats retrieval.",
        "semantic_scope":"Two-view stepped-profile loss; ellipsoid API independently present in the static prediction. No component-level causal claim.",
        "additional_view_evidence":[]
    }
}


def verify_parent():
    seal=read(PARENT_SEAL)
    for name,item in seal["files"].items():
        require(sha(ROOT/name)==item["sha256"],"Parent evidence changed: "+name)
    return len(seal["files"])


def link(path,base=OUT):
    return quote(os.path.relpath(path,base).replace("\\","/"),safe="/.")


def metric(value,percent=False):
    return "unavailable" if value is None else (f"{value*100:.4f}%" if percent else f"{value:.6g}")


def case_markdown(row):
    lines=[f"# {row['slot']} {row['sample_id']}","",f"## {row['label_zh']}","",
        "Reviewer: AI assistant visual inspection. Author confirmation: PENDING.","",
        "已查看：归一化与 reference-world 两张四方法 panel，各含 isometric/front 两视图。", ""]
    for series,path in row["panels"].items():
        lines.append(f"[{series}]({path})")
    lines += ["","## Original Metrics","","CD: historical external dimensionless squared CD x1000. IoU: fraction in JSON, percent below.","",
              "| Method | CD x1000 | IoU | Primary outcome |","| --- | ---: | ---: | --- |"]
    for method in METHODS:
        t=row["native_metrics"][method]
        lines.append(f"| {NAMES[method]} | {metric(t['CD'])} | {metric(t['IoU'],True)} | {t['primary_outcome']} |")
    lines += ["","## View-Supported Observations",""]+[f"- {v}" for v in row["observations_zh"]]
    lines += ["","## Wording Boundary","","Allowed: "+"; ".join(row["supported_terms"]),"",
              "Not established: "+"; ".join(row["unsupported_terms"]),"",row["semantic_scope"],"",
              "## Caption Draft","",row["caption_en"],"","Selection caveat: "+row["selection_caution"],"",
              "## Exact Static Evidence","","Full evaluated code: "+row["code_path"],"",
              "Predicted-plan excerpt (not a ground-truth construction history):","","```text"]
    lines += row["predicted_plan_excerpt"]+["```","","Generated-code excerpt; original line numbers:","","```python"]
    lines += [f"{v['line_1based']:>3}: {v['text']}" for v in row["code_excerpt"]]+["```","",
              "Native MIRAGE gate:","","```json"]
    import json
    lines += [json.dumps(row["mirage_gate"],indent=2,ensure_ascii=False),"```","",
              "No reference construction program/tree is available for these external STEP targets. Do not infer a ground-truth extrusion sequence.","",
              "## Author Sign-Off","","- Label confirmation: pending","- Caption confirmation: pending","- Main-text inclusion: recommended, not author-final","",
              "Keep all original evidence. Any confirmation/revision must be a separate version.",""]
    return "\n".join(lines)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets=[]
    def handle_starttag(self,tag,attrs):
        self.targets.extend(v for k,v in attrs if k in ("src","href"))


def main():
    require(not OUT.exists(),"No implicit overwrite of a review version")
    before=verify_parent()
    source=read(GALLERY/"selection_v1.json")
    original=read(ROOT/"audit/master_records_v1.json")
    master={r["sample_id"]:r for r in original["rows"]}
    rows=[]
    for case in source["cases"]:
        if case["placement"]!="main":
            continue
        slot=case["slot"]
        base=GALLERY/"cases"/case["case_id"]
        evidence=REVIEWS[slot]
        code_path=base/"code/mirage_used.py"
        code=code_path.read_text(encoding="utf-8")
        require(code==case["master"]["source_records"]["mirage_used"]["prediction"],"Static code differs from original")
        require(master[case["sample_id"]]==case["master"],"Case correspondence changed")
        plan=case["master"]["source_records"]["mirage_used"]["predicted_ir"]
        panels={series:str(base/(series+"_panel.png")) for series in ("metric_space","reference_world")}
        views=[str(base/p) for p in evidence["additional_view_evidence"]]
        sources=[code_path,base/"case_record.json",base/"archived_asset_paths.json",base/"render_manifest.json"]
        sources += [Path(p) for p in panels.values()]+[Path(p) for p in views]
        row={"slot":slot,"sample_id":case["sample_id"],"case_id":case["case_id"],**evidence,
            "reviewer_type":"AI_ASSISTANT","review_status":"VISUAL_RECHECK_COMPLETE_AUTHOR_CONFIRMATION_PENDING",
            "author_confirmed":False,"author_confirmed_semantic_label":None,
            "panels":panels,"additional_inspected_views":views,
            "native_metrics":{m:case["taxonomy"][m] for m in METHODS},
            "mirage_gate":case["master"]["source_records"]["mirage_gate"],
            "code_path":str(code_path),"archived_assets_record":str(base/"archived_asset_paths.json"),
            "predicted_plan_excerpt":[l for l in plan.splitlines() if l.startswith("F ")][:5],
            "code_excerpt":[{"line_1based":i,"text":line} for i,line in enumerate(code.splitlines(),1) if "part." in line][:6],
            "selection_bucket":case["selection_bucket"],"original_selection_rank":case["selected_priority"],
            "recommendation":"KEEP_IN_SIX_CASE_MAIN_DRAFT_AUTHOR_DECISION_PENDING",
            "new_training_prediction_program_execution_scoring_rendering":False,
            "source_hashes":{str(p):sha(p) for p in sources}}
        require(row["code_excerpt"],"No exact code excerpt")
        rows.append(row)
    require([r["slot"] for r in rows]==[f"M{i:02}" for i in range(1,7)],"Lost or reordered main IDs")
    require(len({r["sample_id"] for r in rows})==6,"Duplicate main sample ID")
    require("part.capsule(" in rows[2]["code_excerpt"][0]["text"],"M03 static operation not corroborated")
    require("unexpected keyword argument 'length'" in rows[3]["mirage_gate"]["error"],"M04 source error differs")
    require(rows[3]["code_excerpt"][0]["line_1based"]==7,"M04 line-number evidence differs")
    require("part.ellipsoid(" in rows[5]["code_excerpt"][0]["text"],"M06 static operation not corroborated")
    write_new(OUT/"main_review_records_v1.json",{"status":"SIX_MAIN_VISUAL_RECHECKS_COMPLETE_AUTHOR_SIGNOFF_PENDING",
        "created_utc":utc(),"client_date":"2026-10-22","reviewer_type":"AI_ASSISTANT",
        "parent_seal_sha256":sha(PARENT_SEAL),"selection_sha256":sha(GALLERY/"selection_v1.json"),
        "all_original_main_ids_retained":True,"recommend_main_case_count":6,
        "compact_four_case_option":["M01","M02","M04","M06"],
        "compact_option_scope":"Page-limit-only display subset, not reselection or quality filtering; M03/M05 and all appendix data remain archived. Not author-final.",
        "rows":rows,"author_signoff":None})
    for row in rows:
        text_new(OUT/"cases"/(row["slot"]+".md"),case_markdown(row))
    text_new(OUT/"caption_drafts_en.md","# Fusion 360 Main-Case Caption Drafts\n\nAuthor confirmation pending. No new metrics.\n\n"
        +"\n\n".join("## "+r["slot"]+" "+r["sample_id"]+"\n\n"+r["caption_en"] for r in rows)
        +"\n\n## Shared Legend\n\nColumns: reference, CAD-Recode, MIRAGE generated-plan, NN retrieval. "
        "Each panel contains fixed isometric and front orthographic views. The shape-normalized series "
        "independently centers and scales each shape as in the existing external metrics, removing global "
        "scale and translation. A separate reference-world diagnostic uses the declared CAD-Recode DSL "
        "conversion and shared union framing. CD is the historical dimensionless squared CD x1000. "
        "Unavailable metrics are not zero. Placeholders denote recorded failures, not generated replacement solids.\n")
    write_new(OUT/"author_signoff_template_v1.json",{"status":"UNFILLED_TEMPLATE_COPY_TO_NEW_VERSION",
        "instructions":"Confirm or revise each label/caption after checking the cited two-view panels. Save a separate response version; do not edit sealed evidence.",
        "rows":[{"slot":r["slot"],"sample_id":r["sample_id"],"label_confirmed":None,
            "caption_confirmed":None,"main_inclusion":None,"revised_wording":None,"reviewer_name":None,"date":None} for r in rows]})
    body='<h1>Fusion 360: six main-candidate visual rechecks</h1><p>AI-assisted review completed; author sign-off is still pending. Original figures, IDs, metrics and failure records are unchanged.</p>'
    body+='<p><a href="'+link(OUT/"main_review_records_v1.json")+'">Full review records</a> <a href="'+link(OUT/"caption_drafts_en.md")+'">English caption drafts</a> <a href="'+link(OUT/"author_signoff_template_v1.json")+'">Author sign-off template</a></p>'
    for row in rows:
        body+='<section><h2>'+escape(row["slot"]+" "+row["sample_id"])+'</h2><h3>'+escape(row["label_zh"])+'</h3><ul>'
        body+=''.join('<li>'+escape(o)+'</li>' for o in row["observations_zh"])
        body+='</ul><p><strong>Caption draft:</strong> '+escape(row["caption_en"])+'</p>'
        body+='<p><strong>Not established:</strong> '+escape('; '.join(row["unsupported_terms"]))+'</p>'
        body+='<p><a href="'+link(OUT/"cases"/(row["slot"]+".md"))+'">Per-case record, code and metrics</a> <a href="'+link(row["archived_assets_record"])+'">Original/archived asset paths</a></p>'
        for series,path in row["panels"].items():
            body+='<h3>'+escape(series)+'</h3><a href="'+link(path)+'"><img loading="lazy" src="'+link(path)+'" alt="Four-method, two-view evidence"></a>'
        body+='</section>'
    page='<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fusion 360 main review v1</title><style>body{font:16px Arial,sans-serif;line-height:1.6;max-width:1380px;margin:24px auto;padding:12px;color:#20303a}section{border-top:1px solid #ddd;margin-top:30px;padding-top:12px}img{max-width:100%;height:auto}a{color:#086b6a;margin-right:16px}h1{font-size:28px}h2{font-size:23px}h3{font-size:19px}li{margin:8px 0}</style><body>'+body+'</body></html>\n'
    text_new(OUT/"index.html",page)
    parser=Links()
    parser.feed(page)
    for target in parser.targets:
        url=urlsplit(target)
        require(not url.scheme and (OUT/unquote(url.path)).is_file(),"Broken local review link")
    for row in rows:
        for path,digest in row["source_hashes"].items():
            require(sha(path)==digest,"Review source changed")
        for method in METHODS:
            require(row["native_metrics"][method]==next(c for c in source["cases"] if c["slot"]==row["slot"])["taxonomy"][method],"Metric or error changed")
    require(rows[4]["native_metrics"]["mirage"]["IoU"]==0,"M05 measured zero lost")
    require(rows[3]["native_metrics"]["mirage"]["IoU"] is None,"M04 missing metric became zero")
    after=verify_parent()
    write_new(OUT/"validation_v1.json",{"status":"PASS_SIX_ID_IMAGE_CODE_LOG_METRIC_AND_LINK_CHECKS",
        "six_original_main_ids_unchanged":True,"parent_sealed_files_checked_before_and_after":before,
        "parent_counts_equal":before==after,"native_records_exact":True,"null_and_measured_zero_preserved":True,
        "local_links_checked":len(parser.targets),"static_operation_checks":["M03 capsule","M04 wedge length exception and line7","M06 ellipsoid"],
        "author_confirmation":"PENDING","new_training_predictions_execution_scoring_or_rendering":False})
    print("Six individual rechecks saved. Parent files unchanged:",after,"Author sign-off PENDING.")


if __name__=="__main__":
    main()
