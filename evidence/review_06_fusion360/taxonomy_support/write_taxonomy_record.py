"""Report complete native-log counts, retaining uncertainty and visual-review boundary."""
from classify_native_logs import ROOT,read,write_new


def main():
    data=read(ROOT/"taxonomy/failure_taxonomy_v1.json")
    validation=read(ROOT/"taxonomy/independent_validation_v1.json")
    if validation["status"]!="PASS_INDEPENDENT_NATIVE_LOG_TAXONOMY_VALIDATION":
        raise ValueError("Independent validation must pass first")
    counts=data["counts"]
    methods=(("mirage","MIRAGE generated-plan"),("nn","NN-IR assisted"),("cadr","CAD-Recode"))
    order=["CD_SCOREABLE","SYNTAX_FAILURE","EXECUTION_FAILURE","BUILD_FAILURE","SOLID_VALIDITY_FAILURE",
        "STEP_EXPORT_FAILURE","KERNEL_CRASH_STAGE_UNRESOLVED","EMPTY_PREDICTION_MESH","REMESH_FAILURE"]
    lines=["# Fusion 360 Native-Log Failure Taxonomy", "", "Date: 2026-10-22.", "",
        "Status: **Step 2 native/log taxonomy COMPLETE / independently verified PASS**.", "",
        "本记录不等于完成了外部几何的视觉/语义错误分析。没有训练、新预测、代码修复、CAD 执行、重新评分、渲染或选图。",
        "全部 400 个原始 test ID 的三个方法均保留，共 1,200 条 method/sample 记录；既有指标逐值保留。", "",
        "## 1. Definitions and Denominators", "",
        "`primary_outcome` 是从记录的程序 gate 到 CD 评分之间首个被证实的结果，单方法各类别之和严格为 400。",
        "原生内核崩溃单列，不能因崩溃时 incomplete flags 为 false 就错误归为 syntax failure。",
        "CAD-Recode 使用自己的原生 execution/runner 记录，未假装执行了 Flluma 的五个 gate。", "",
        "`CD_SCOREABLE` 只表示已存在可用 CD，不代表语义成功，也不表示 IoU 一定可用。",
        "IoU 的 boolean failure 单独统计；它与 primary outcome 不是可相加的互斥失败类别。",
        "失败 IoU 保留 null，真实测得的 0 保留 0。", "",
        "## 2. Complete Primary Outcomes", "",
        "| Recorded outcome | MIRAGE generated-plan | NN-IR assisted | CAD-Recode |", "| --- | ---: | ---: | ---: |"]
    for label in order:
        values=[counts[m]["primary_outcomes"].get(label,0) for m,_ in methods]
        lines.append("| "+label+" | "+" | ".join(map(str,values))+" |")
    lines += ["| Total | 400 | 400 | 400 |", "",
        "MIRAGE generated-plan：174 条没有可用 CD，其中 168 条未导出 STEP（160 execution、2 syntax、5 export、1 kernel crash），",
        "232 条已有 STEP 中又有 5 条被原生 tessellator 报告为 zero-triangle mesh、1 条 remesh failure（原生诊断 n_faces=0），",
        "最终 226 条 CD 可用。这里的 empty 指固定评分管线产生的空网格，不是本轮对数学实体重新作出的判断。", "",
        "NN-IR：5 条在导出前失败（3 syntax、2 execution），395 条已有 STEP 中 3 条报告空网格，392 条 CD 可用。",
        "CAD-Recode：8 条 execution failure，392 条 CD 可用。", "",
        "## 3. All Primary-Failure Reason Subtypes", "",
        "下表每条 primary failure 只计入一个 subtype，不按指标值推断原因。", "",
        "| Native reason subtype | MIRAGE generated-plan | NN-IR assisted | CAD-Recode |", "| --- | ---: | ---: | ---: |"]
    subtypes=sorted(set().union(*(counts[m]["primary_failure_reason_subtypes"] for m,_ in methods)))
    for subtype in subtypes:
        values=[counts[m]["primary_failure_reason_subtypes"].get(subtype,0) for m,_ in methods]
        lines.append("| "+subtype+" | "+" | ".join(map(str,values))+" |")
    lines += ["| Total primary failures | 174 | 8 | 8 |", "",
        "MIRAGE 的 160 个 execution failure 中，45 条缺失 API attribute、75 条 unexpected keyword，合计 **120/160=75.0%**。",
        "这是两个明确日志类别的描述性计数，不是对所有错误根因的归因。缺失 API 只能证明记录的运行时没有该属性，",
        "不能仅据此判定是模型幻觉、训练数据错误、plan 问题还是训练/运行 API 版本差异。", "",
        "还有 6 条只有 `exec error: 'width'`、`'length'`、`'stock'`、`'boss_profile'` 等简短消息；",
        "保留为 EXECUTION_FAILURE_REASON_UNSPECIFIED，不把引号中的词擅自解释为 KeyError 或特定 CAD 特征错误。", "",
        "CAD-Recode 的 8 条执行失败中，4 条 traceback 指向 line-edge construction，4 条指向 three-point-arc construction，",
        "均有对应 exception 和调用栈支持。没有进一步推断点共线、缺特征或拓扑缺陷。", "",
        "## 4. IoU Availability Is a Separate Axis", "",
        "| IoU outcome | MIRAGE generated-plan | NN-IR assisted | CAD-Recode |", "| --- | ---: | ---: | ---: |"]
    for label in ("IOU_AVAILABLE","IOU_BOOLEAN_FAILURE","UNAVAILABLE_AFTER_PRIMARY_FAILURE"):
        values=[counts[m]["iou_outcomes"].get(label,0) for m,_ in methods]
        lines.append("| "+label+" | "+" | ".join(map(str,values))+" |")
    lines += ["| Total | 400 | 400 | 400 |", "",
        "因此 CD 可评分集合内另外有 14 / 3 / 13 条 IoU boolean failure；未把它们写成 IoU=0，也未混进程序失败计数。",
        "三方法真实测得 IoU=0 的记录分别为 4 / 7 / 11 条，均原样保留，共 22 条。", "",
        "## 5. Evidence and Files", "",
        "- `fusion360_failure_taxonomy_v1.csv`：1,200 行、28 列，主键 `(sample_id, method)`；明确 primary outcome、reason subtype、IoU outcome、原始指标和证据路径。",
        "- `fusion360_case_registry_step2_v1.csv`：400 行、94 列，原 Step-1 的 67 列逐值不变，追加三个方法各自的 9 个分类/证据字段。",
        "- 原 Step-1 `fusion360_case_registry.csv` 没有覆盖；其保留字段与 notes 仍然是原审计快照。新的 method-prefixed 字段才是 Step-2 标签。",
        "- `taxonomy/evidence_v1/<method>/<sample_id>.json`：每条记录的原生结果、逐字日志、规则、源文件 hash、JSONL 物理行号和 sealed-master pointer，共 1,200 份。",
        "- `taxonomy/failure_taxonomy_v1.json`：全部 typed records、完整 reason/outcome 计数、来源及规则哈希。",
        "- `02_failure_taxonomy_protocol.md`：回顾性日志分类规则，非预注册实验。",
        "- `taxonomy/independent_validation_v1.json`：独立首阶段 oracle、CSV/source/evidence、原值保留、源文件 hash 和单测结果。",
        "- `taxonomy/csv_validation_v1.json`：两份 CSV 的 typed values 与包含多行 traceback 的 RFC4180 roundtrip 均 PASS。",
        "- `taxonomy/step2_package_seal_v1.json`：本阶段新增证据和脚本的单独封存。", "",
        "CSV 中部分 traceback 含换行，因此应用 CSV parser 的逻辑行数，不要用物理换行数判断是否恰好 1,200 行。",
        "failure_evidence 对每条记录均提供可追溯的 native evidence；CD-scoreable 且 primary failure class 为 null 并不代表没有 IoU 问题。", "",
        "## 6. Interpretation and Limits", "",
        "本轮可支持：外部 generated-plan 路径的失效不仅有执行/API 合规问题；原 native gate 报告 STEP 导出成功，也不保证固定外部评分器能取得可用表面。",
        "但这没有证明 MIRAGE 在可评分样本上几何准确，也不能把 CAD-Recode 差距归因于 planning；训练数据、架构和预处理条件均不同。",
        "此前的外部几何差距仍按原始 CD/IoU 结果解释，未重算、删样本、替换失败或新增阈值。", "",
        "**形状/特征层面的 poor reconstruction 尚未分类。**所有记录的 geometry_review_status 为 NOT_VISUALLY_REVIEWED，",
        "semantic failure 与 selection bucket 均为空。没有从低 IoU 猜缺孔、wrong topology、disconnected features，也没有新设 acceptance threshold。",
        "接下来 Step 3 需要先确定 retrospective selection 与坐标/相机/比例政策，再实际渲染和检查。Reviewer 对 side-by-side 及具体重建缺陷的要求仍不能仅凭本记录宣布全部解决。", "",
        "## 7. Validation and Preservation", "",
        "- 20 个 synthetic log contract tests PASS。",
        "- 独立 stage oracle 与 1,200 条 primary outcome 全部一致。",
        "- 2,404 个被使用的原生 manifest/gate/export/runner/log 源文件重新校验 SHA256，一致。",
        "- 两份 CSV 和逐条 evidence 保持原始 CD/IoU、null、true/false 及多行 traceback。",
        "- Step-1 的 20 个封存文件（含原 README/CSV/master）未改动。Review/04-05 的此前封存文件也核验未改变。",
        "- Step 3 未开始；Step 4 未开始；没有任何 GPU/model/CAD 运行。", "",
        "## 8. Reviewer-Facing Draft", "",
        "> We audited all 400 external test cases using the existing execution and evaluation logs. For MIRAGE's generated-plan pathway, 160 cases failed during execution; 120 of these reported either a missing API attribute (45) or an unexpected keyword argument (75). Five further cases failed STEP export, two had syntax failures, and one triggered a native kernel access violation. Of the 232 exported STEP files, five yielded zero-triangle meshes under the fixed external tessellator and one failed remeshing, leaving 226 cases with available CD. IoU remained unavailable due to boolean failures in 14 of those cases; these were not assigned IoU zero. These diagnostics identify pipeline-level failure modes, not semantic reconstruction quality, which requires the separate qualitative comparisons.", ""]
    with (ROOT/"03_failure_taxonomy_results.md").open("x",encoding="utf-8") as f:
        f.write("\n".join(lines))
    with (ROOT/"CURRENT_STATUS.md").open("x",encoding="utf-8") as f:
        f.write("# Fusion 360 Current Status\n\nDate: 2026-10-22.\n\nStep 1 correspondence audit: COMPLETE / PASS (immutable snapshot).\n\nStep 2 native/log taxonomy: COMPLETE / PASS. See `03_failure_taxonomy_results.md`, the 1,200-row long CSV and the 400-row Step-2 wide CSV.\n\nStep 3 selection, matched-camera rendering and semantic geometry analysis: NOT STARTED.\n\nStep 4 full raw-asset archive/submission subset: NOT STARTED.\n\nNo training, new predictions, CAD execution or metric evaluation occurred. The original README is a sealed historical Step-1 record and is intentionally not rewritten.\n")
    print("Wrote complete Step-2 outcome/subtype tables, preservation record and current status")


if __name__=="__main__":
    main()
