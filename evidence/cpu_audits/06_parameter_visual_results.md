> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# 参数 before/after：CPU 展示素材与原始记录

日期：2026-10-25。状态：**素材生成和范围内 QA 完成；作者语义审核/采用仍 PENDING**。

入口：[六例审核页](__EVIDENCE_SOURCE_ROOT__/09_cpu_preparation/parameter_visuals_v1/index.html)。
完整原始包：`parameter_visuals_v1_complete.zip`；SHA256 `ec7f240b4ee7f71f6bb8fdf1ae83d718ad9943cd0a9431e06449ddf7422338ee`。

## 实际完成

- 找到原参数研究的 `outputs/editability_25k/c_step.jsonl`，100 个 ID/顺序全部对应原 baseline。
- 全部 100 行 coverage 字段逐项一致；全部 1,608 次 perturbation 的原值、delta、边界裁剪后的目标值核对通过。
- 在本次 CPU 看图/导出前固定六桶选择规则，保留 `05_parameter_visual_protocol.md` 及其哈希；结果不是原研究前 preregistered。
- 使用原 `perturb()` 替换规则，执行 12 个独立 native CPU 进程，没有附加修复或换例。
- 导出 10 个 STEP，2 个 after 按历史类别失败；20 张真实几何视图、4 张失败卡、6 张全尺寸 panel 和 1 张总览，共 31 PNG。
- 两个固定视角，每例 before/after 同一 union frame、相机和 pixels/mm；没有单独放大 after。
- 31 张 PNG 可解码；49 个本地 HTML 链接有效；代码哈希和当前结果核对通过。

## 六例

| Case | Query sample ID | 参数 / 修改 | 原始记录 | 本次 CPU 结果 |
| --- | --- | --- | --- | --- |
| P01 | flluma_0090123 | flange_height：36.94→40.634（+10%） | rebuilt_and_moved | 前后可导出，网格顶点集变化；当前体积差 -320.383148 mm³ |
| P02 | flluma_0090189 | boss_height：5.34→4.806（-10%） | rebuilt_and_moved | 前后可导出，网格顶点集变化；当前体积差 -107.887667 mm³ |
| P03 | flluma_0090198 | clamp_length：25.1→31.375（+25%） | rebuilt_no_change；参数未被 params 下标引用 | 前后 render mesh 顶点集完全相同，当前体积差 0 |
| P04 | flluma_0091127 | hole_radius：2.01→2.5125（+25%） | rebuilt_no_change；代码有 params 下标引用 | 前后 render mesh 顶点集完全相同，当前体积差 0 |
| P05 | flluma_0098828 | boss_radius：10.14→12.675（+25%） | broke_at_step_export_ok | before 可导出；after 为 `ExportError: OCCT build failed` |
| P06 | flluma_0093632 | path_height：9.1→11.375（+25%） | broke_at_exec_ok | before 可导出；after 为 topology reference 未解析到 face |

当前体积/表面积来自本次导出的 STEP，通过 CadQuery 读取，单独记在 mesh/render records，**不替代原论文指标**。
网格顶点集一致是固定 tessellation 下的展示诊断，不是一般 B-Rep 等价性证明。

## 可用于讨论的、来源可查的观察

- P03 与 P04 明确区分了“静态未引用”和“代码引用但几何未变”。不能把所有 no-change 都叫作 dead parameter。
- P01 的同一个 `flange_height` 在原代码中同时用于 cylinder 和 pocket box 的 height。源码能直接验证这个共享引用；正向参数修改的净体积反而下降，因此不能用“参数增大→体积增大”当作 intended-feature correctness。
- 每例 case.json 都列出直接 numeric literal 参数位置和行号，例如 translate offset。它们不是 params 下标表达式；这只是语法位置证据，不是全面的依赖可达性证明。
- P05/P06 的失败保持可见，没有 after 假几何、修复后替代或样本替换。

## 原始材料和路径

```text
parameter_visuals_v1/
  prepared_cases.json              # 六桶、来源哈希、全部 jobs
  selection_protocol.md
  sources/
    original_c_step.jsonl          # 原 100 行输入，完整保留
    original_perturbation_rows.jsonl
    recorded_perturbation_implementation.py
  cases/P01 ... P06/
    case.json
    before.py / after.py / change.diff
    before/                       # after/ 同样布局
      native_cli.log
      native_events.jsonl
      native_export.json
      model.step                  # 仅成功时
      display_mesh.npz            # 仅成功时
      mesh_record.json
      view_1.png / view_2.png
    render_record.json
    panel.png / index.html
  case_registry.json              # 路径与原始/current 状态，typed JSON
  native_exports_summary.json
  display_mesh_summary.json
  render_summary.json
  qa_summary.json
  asset_manifest.json
  contact_sheet.png / index.html
```

Native executable 与原 05 相同 Release FllumaCLI，具体 SHA、embedded Python 版本、每个进程日志均已记录。
网格使用既有 `probe_cadrecode_mesh.py::tessellate_step`，helper SHA 与 05 的冻结记录一致，deflection=0.03 mm / angular=0.3 rad。
原始输入与本次 before/after code 对应经过结构与数值核查；仍不凭当前源码恢复已删除历史 STEP 的字节身份或训练 checkpoint 绑定。

## 写作边界与草拟 caption

原 100 / 74 / 1608 / 1321 等 aggregate 没有修改。六例为按 outcome 分层的解释性候选，不代表 prevalence，也不是新的 plan-vs-code 编辑对照。
没有完成 intended-feature / dependency correctness / unrelated-geometry preservation 研究，作者签署和最终主文选取仍后置。

下面是供以后人工检查、放入正文后使用的 caption 草稿，**不是已放入论文的声明**：

> Parameter-perturbation illustrations from the recorded STEP program study. Two examples rebuild with changed geometry (P01–P02), two rebuild without a visible mesh change despite different static parameter-reference status (P03–P04), and two fail after perturbation at export or topology-reference execution (P05–P06). Each pair uses two fixed views with a common camera and scale. These are current CPU re-exports of the recorded programs and value changes; the original aggregate results are unchanged. The examples illustrate parameter responsiveness and failure modes, not semantic editing accuracy.
