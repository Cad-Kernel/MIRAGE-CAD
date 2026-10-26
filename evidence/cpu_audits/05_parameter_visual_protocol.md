> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# 参数 before/after CPU 展示协议 v1

日期：2026-10-25。用途是展示既有 perturbation 结果，不新增训练、模型预测或语义编辑准确率研究。
本规则在本次 CPU 导出、网格化和看图之前固定；不是在原研究结果之前 preregistered。

## 来源和输入核查

- 使用原 `outputs/editability_25k/c_step.jsonl` 的 100 个程序。
- 对应 `scratch/editability_25k_step_c/editability_rows.jsonl`：100 baseline + 1608 results。
- 首先验证 ID、全部 baseline coverage 字段，以及每条 perturbation 的参数原值/目标值/边界裁剪规则。
- 整份子集、原始记录、参数修改函数、CLI 哈希另存；若任一对应失败，停止，不换程序补齐。

## 确定性六例选择

各桶内部按 `(sample_id, param, delta)` 升序，依次选择第一个满足条件、且未在更早桶中采用的 sample。
如桶没有候选，直接登记为空，不能按图像好看程度补选。

1. P01：`rebuilt_and_moved`，delta=+0.10。
2. P02：`rebuilt_and_moved`，delta=-0.10，与 P01 不同 sample。
3. P03：`rebuilt_no_change`，该 param 在原 baseline 的 `unreferenced_names` 中，delta=+0.25。
4. P04：`rebuilt_no_change`，该 param 不在 `unreferenced_names` 中，delta=+0.25。
5. P05：`broke_at_step_export_ok`，保留历史实际 delta。
6. P06：`broke_at_exec_ok`，保留历史实际 delta。

前后程序只调用原 `perturb(code, name, recorded_to)`，保留其 `:g` 格式化，不能手动修程序。
每例保存原声明、所有 params 引用、实际替换 diff，以及直接写成字面量的几何参数示例。
静态 literal 示例只说明该语法位置不是 params 引用，不能声称已完成全面依赖/可达性分析。

## CPU 执行、显示和失败处理

- 每个 before/after 单独 FllumaCLI 进程，保留开始事件、退出状态、错误与 native 日志。
- 使用原生 five-gate 过程，成功则保存 STEP；失败则保存阶段和占位卡，不产生替代形状。
- 原始 1608 行统计保持不变。本次新执行只作为当前 CPU illustration 的核查，单独显示历史/当前 outcome。
- WSL CadQuery 只做 STEP→render mesh，不运行 LM；固定 render-only linear deflection=0.03 mm、angular=0.3 rad。
- 视角固定为 azimuth 45/225 degrees、elevation 35.264389682754654 degrees，orthographic。
- 每例使用 before 和 after 的共同 union frame、相同 pixels/mm，不对 after 单独放大或重新对齐。
- 每侧两个视图；固定背景、光照与颜色；保留网格、相机、STEP、PNG、代码和 JSON。
- 如果当前执行与历史记录不同，保留差异，不重试修到符合历史。

## 解释与作者判断

“moved”只表示几何变化；“no change”不自动等于参数未使用，P03/P04 特意区分静态引用状态。
不声称 intended feature 正确、依赖正确或无关几何保持。
最终主文采用、几何语义标签和图注由作者在技术准备全部完成后确认。
