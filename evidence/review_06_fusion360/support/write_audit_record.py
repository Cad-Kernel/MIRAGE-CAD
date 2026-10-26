"""Write the Step-1 inventory record from actual counts; no geometric ranking."""
from collections import Counter
from pathlib import Path
from audit_fusion360 import ROOT,read,write_new


def main():
    a=read(ROOT/"audit/correspondence_v1.json")
    master=read(ROOT/"audit/master_records_v1.json")
    validation=read(ROOT/"audit/independent_validation_v1.json")
    inventory=read(ROOT/"audit/source_files_v1.json")["files"]
    assert validation["status"]=="PASS_INDEPENDENT_STEP1_VALIDATION"
    coverage=a["coverage_inventory"]
    lines=["# Fusion 360 Inventory and Correspondence Audit", "", "Date: 2026-10-22.", "",
        "Status: **STEP 1 COMPLETE / PASS WITH EXPLICIT PROVENANCE LIMITATIONS**.", "",
        "本轮只审计既有文件、样本对应关系、原始指标的可用性和来源哈希。没有训练、模型推理、",
        "重新生成计划/代码、执行 CAD 程序、导出 STEP、网格化、重新评分、渲染或挑选案例。",
        "Step 2 failure taxonomy、Step 3 case selection/rendering、Step 4 raw archive/submission subset 均未开始。", "",
        "## 1. Master Universe", "",
        "权威顺序是既有 `rows.jsonl` 的 400 个唯一 sample_id，不按任一方法成功子集或指标排序。",
        "master 已保存为 `audit/master_ids_v1.txt`；CSV 与 typed master 均保持此顺序。", "",
        "```text",a["master_authority"],"```", "",
        "既有 queries、step_index、旧 external manifest、generated plan、两条 MIRAGE 路径的原始/最终预测、",
        "gate、原生 geometry、geometry input 和 persistent-export 清单共 17 个行式来源，全部各 400 行，",
        "ID 集合及行顺序均一致。三组逐样本目录各 400 份 terminal manifest，集合也完全一致；",
        "目录词典序与原输入顺序不同（各有 398 个位置不同），因此通过 sample_id 合并，而不是逐行拼接。", "",
        f"400 个 external_id 均属于官方 test split（{a['official_split']['test']} 个），与官方 train split（{a['official_split']['train']} 个）的交集为 0。",
        "这不等于已证明 CAD-Recode 的预训练数据与这批测试模型没有重叠；上游训练重叠仍未核实。", "",
        "## 2. Existing-Result Availability", "",
        "以下仅为已存在记录的数量核验，不是新一次性能评估，也不涉及几何排名或选图。", "",
        "| Condition | Master IDs | Historical STEP export | STEP file present now | CD available | IoU available |",
        "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for name,label in (("mirage","MIRAGE point generated-plan"),("nn","MIRAGE point NN-IR assisted"),("cadr","CAD-Recode")):
        c=coverage[name]
        lines.append(f"| {label} | 400 | {c['historical_export_ok']} | {c['STEP_exists_current']} | {c['CD_scoreable']} | {c['IoU_scoreable']} |")
    lines += ["", "Registry 中 `*_scoreable` 明确定义为 **CD 可用**，`*_iou_scoreable` 单独定义为 IoU 可用。",
        "不能把 exported / measurable / CD scoreable / IoU scoreable 当成同一个分母。IoU 失败保持 null，",
        "真实测得 IoU=0 则保留 0，不混为一谈。NN-IR 是训练索引辅助路径，不是自主 generated-plan 方法。", "",
        "| Pair | Full universe | Joint CD availability | Joint IoU availability |", "| --- | ---: | ---: | ---: |"]
    for pair,label in (("mirage_vs_cadr","Generated-plan / CAD-Recode"),("nn_vs_cadr","NN-IR / CAD-Recode"),("mirage_vs_nn","Generated-plan / NN-IR")):
        p=a["paired_metric_availability"][pair]
        lines.append(f"| {label} | 400 | {p['CD']} | {p['IoU']} |")
    lines += ["", "## 3. File and Hash Checks", "",
        f"- {validation['existing_source_file_rehashes']} 个实际存在文件已计算 SHA256，并在独立复核中重新校验；源文件总字节数为 {sum(x['bytes'] or 0 for x in inventory.values())}。",
        f"- {validation['historical_file_hash_checks']} 项历史文件哈希对照全部一致，冲突 0：包括 400 个 reference STEP、CAD-Recode raw generation/code、已导出的预测 STEP。",
        "- 400 份 CAD-Recode 保留的 model-input NPY 数组，其连续数组字节哈希与历史 manifest 全部相符；文件容器 SHA 与数组 SHA 分开记录。",
        "- 400 个原始 MIRAGE 输入点云存在；Windows 原几何评分使用的点云副本逐字节相同。两处 STEP descriptor 副本也逐字节相同。",
        "- 两条 MIRAGE 最终预测的代码经原 builder 声明的 strip 规则后，与各自 geometry input 的唯一 candidate 完全一致。",
        "- 每条 JSONL 预测、plan、gate、export/geometry record 均保存物理行号、行字节 SHA 和整文件 SHA；不是仅按文件名猜测样本。",
        "- NN 的 400 条 nearest-training-sample 引用全部存在于登记的 25k train IDs 中。",
        "- CAD-Recode 独立 execution_result.json 与 manifest 内嵌 runner_result 全部一致。",
        "- MIRAGE standalone gate、persistent export、旧 native geometry gate 和 terminal scoring manifest 的已记录 gates 均无冲突。",
        "- 181 个方法失败时未产生的 prediction STEP（generated-plan 168、NN 5、CAD-Recode 8）明确记为不存在，CSV 路径留空；没有替代模型或造文件。",
        "- 所有 required reference/input/log/metric 文件均存在，完整性错误 0。空 stdout/stderr 文件不作为缺失或失败原因。", "",
        "## 4. Legacy Placeholder Paths", "",
        "旧 `scratch/external_manifest/manifest.jsonl` 是早期准备快照：400 个 GT mesh、400 个 MIRAGE mesh、400 个 CAD-Recode mesh 路径都是不存在的占位路径，",
        "且旧 CAD-Recode-exists 标记不能代表后来的实际运行。原文件未修改，原始行保存在 typed master。",
        "这 1,200 条占位路径与上面的 181 个实际失败输出分开统计；不能把它们当成持久化网格或原始文件丢失。",
        "当前可用的持久几何资产是 reference STEP 与各方法实际保留的 prediction STEP。后续如需 mesh/render，必须另行进入 Step 3。", "",
        "## 5. Registry and Query Paths", "",
        "- `fusion360_case_registry.csv`: 400 行、67 列，一行对应同一个外部 test sample 的三个方法。",
        "- `audit/master_records_v1.json`: CSV typed values、完整 native records、完整源行、所有物理行定位与资产映射。",
        "- `audit/source_files_v1.json`: 实际文件/缺失输出、大小、SHA256、用途和历史 SHA 校验。",
        "- `audit/correspondence_v1.json`: 每个来源的 ID/order、终态计数、数组哈希、paired availability 和历史限制。",
        "- `audit/independent_validation_v1.json`: CSV/native/locator 二次核对、源文件重新 hash 和 8 项 CPU 单测。",
        "- `audit/csv_validation_v1.json`: artifact-tool typed worksheet 与 CSV roundtrip 校验。",
        "- `support/case_registry_preview.png`: 仅 CSV ID 列预览，不是 CAD 渲染或 qualitative case selection。", "",
        "`mirage_prediction_path` / `nn_prediction_path` 指向完整已评价的 repaired_p0 JSONL，而不是单个代码文件；",
        "必须同时使用 `*_prediction_line_1based` 和 `*_prediction_line_sha256` 定位。CAD-Recode 指向其逐样本 extracted_code.py。",
        "`mirage_log_path` / `nn_log_path` 是带行号的 standalone gate JSONL；`*_metric_manifest_path` 才是共同外部 evaluator 的指标记录。",
        "CAD-Recode stdout/stderr、raw generation 和 retained model-input 文件也在 typed master 的 assets 及 source inventory 中。", "",
        "## 6. Metric and Provenance Boundaries", "",
        "CSV 的 CD 是已有 `evaluation.cd_x1000`，即归一化坐标下双向 squared nearest-neighbour mean 之和乘 1000；",
        "不是内部 native-mm CD，不能跨协议直接比较。当前共同 evaluator 的函数体对 GT/prediction 使用 per-shape normalization；",
        "某些旧模块的导言讨论 fixed DSL mapping，不可替代实际被调用的函数体。这里只保留来源，不重算或更改指标。",
        "IoU 从已有合格/ok 记录逐值复制，不把 failed/ineligible 记录填成 0。", "",
        "历史 canonical mesh 的双数组 fingerprint 和 MIRAGE gt_verified 标记原样保留，但本轮没有重建网格，",
        "因此不声称当前重新验证了 canonical-mesh fingerprint。当前 source STEP 文件字节与 CAD-Recode 历史 source SHA 匹配则已实际验证。",
        "CAD-Recode 和 MIRAGE 的模型输入预处理/训练条件不相同；存在共同 reference 不代表这是一项只改变 planning 的受控比较。",
        "当前脚本字节通过哈希登记，不补造历史 checkout、训练 seed 或模型权重执行绑定。", "",
        "## 7. Remaining Work", "",
        "`verified_failure_class`, `failure_evidence`, `selection_bucket` 的 400 行均为 null/空白。原始 native status/error 保存在独立列和源行中，",
        "这不是遗漏失败数据，而是明确没有提前进入 taxonomy。没有按 CD/IoU 排序、求新分位数、挑相对成功或低分样本。", "",
        "接下来只可按另行确认的 Step 2 做日志驱动 failure taxonomy；看图确认之前，不写 missing-hole、wrong-topology 等语义标签。",
        "主文最终图、失败图和 relative-success 示例都还没有选。Step 4 的完整 raw-asset archive 也没有在此轮执行。", "",
        "Review/04 的 17 个 final evidence 文件，以及 Review/05 candidate seal 385 个、render seal 370 个、raw archive seal 237 个文件均复核未改变。",
        "没有重启任何内部训练实验。", ""]
    path=ROOT/"01_inventory_and_correspondence_audit.md"
    with path.open("x",encoding="utf-8") as f:
        f.write("\n".join(lines))
    contracts={}
    for c in master["csv_columns"]:
        examples=[r[c] for r in master["csv_rows"] if r[c] is not None]
        types=sorted({type(v).__name__ for v in examples})
        contracts[c]={"non_null_types":types,"nullable":any(r[c] is None for r in master["csv_rows"])}
    write_new(ROOT/"audit/registry_field_contract_v1.json",{"columns":contracts,"row_key":"sample_id","order":"master_index from original rows.jsonl", "scoreable_definition":"CD available; IoU separately flagged", "CD_units":"normalized dimensionless squared symmetric CD times1000", "reserved_step2_step3_fields":["verified_failure_class","failure_evidence","selection_bucket"]})
    print("Wrote factual Step-1 audit record and 67-field contract; no taxonomy or case selection")


if __name__=="__main__":
    main()
