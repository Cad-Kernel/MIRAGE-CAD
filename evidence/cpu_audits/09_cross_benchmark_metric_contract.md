> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# CD / F / IR：跨方法指标口径与写作草稿

日期：2026-10-25。对应机器记录：[metric_contracts.json](__EVIDENCE_SOURCE_ROOT__/09_cpu_preparation/external_baselines_v1/metric_contracts.json)。以下依据明确版本的源码和论文，不把当前代码推成原论文历史执行的字节证明。

记 `dPQ`、`dQP` 为两向最近邻的欧氏距离。即使名称都叫 Chamfer distance，也不能默认同一量。

| 方法/设置 | CD 公式与倍率 | 采样与归一化/对齐 | 成功/失败分母 |
| --- | --- | --- | --- |
| MIRAGE native，内部 01–04 | `0.5 mean(dPQ²) + 0.5 mean(dQP²)`；此处 raw，不附 ×1000 | candidate 默认 1,024 点；target 为输入的 point cloud；CD helper 不新做居中、缩放或刚性对齐 | scoreable conditional CD；另报全 query 的 coverage 和 failures=0 的 unconditional F@1 |
| MIRAGE Fusion 外部协议 | `1000 [mean(dPQ²)+mean(dQP²)]` | 8,192 点；独立 bbox 居中/最大边归一化；CAD-Recode fixed-DSL affine 是另外明确声明的路径 | 保留 Review/06 原 measurable/scoreable 分母，不以 CADBench VSR 代替 |
| GenCAD-3D | `1000 [mean(dPQ²)+mean(dQP²)]` | CD evaluator 默认 2,000 点；GT 为预生成 cloud，生成 cloud 仅在 max-abs >2 时按 max-abs 缩放；不能等同于 MIRAGE 独立 bbox normalization | conditional median；GT 缺失/构建/采样失败返回 None；SL 指标先按序列长度分组、再平均各组 median CD / IR |
| Text2CAD | `1000 [mean(dPQ²)+mean(dQP²)]` | 实际 test.py 为 8,192 点；两 cloud 各除以全坐标 `max-min`，normalize_pc 本身不居中 | invalid=-1；GT 构建失败会跳过；eval_seq 的 UID 异常可不进 report；CD 只用 `cd>0`，IR 的分母是保留的 report rows |
| Pointer-CAD | `1000 [mean(dPQ²)+mean(dQP²)]` | 实际 test.py 传 **8,192**，不是 helper 默认 1,024；各 cloud 去采样点均值，再除以全坐标 max-min | CD 使用 status=true 且 metric 非 None 的行；failure rate 用全 results entries |
| CADBench | `mean(dPQ)+mean(dQP)`，**未平方** | 默认 10,000 点；alpha-wrap、bbox 最大边→2；质量中心/惯性主轴对齐，四种方向按 IoU 选；有 fallback | CD success-only；adjusted IoU/SIoU 对失败计 0；source 同时暴露 success-only 版本，必须写清使用哪个键；论文另有分层 aggregate |
| CADCrafter | 未核实精确公式/倍率 | 论文说明 median CD，但本轮未识别官方 metric implementation；不能据 DeepCAD 引用补出细节 | implementation-level 分母未核实 |
| Img2CAD（SVG） | 未核实精确公式/倍率 | 同上；保留原表数值和 task，不自动换算 | implementation-level 分母未核实 |

固定代码定位：

- [GenCAD CD 与 sampling](https://github.com/yunomi-git/GenCAD-3D/blob/50bf5133c5f895b183fed8dac1df43aa7c1aab1f/autoencoder/evaluation/evaluate_ae_cd.py)、[diffusion 调用链](https://github.com/yunomi-git/GenCAD-3D/blob/50bf5133c5f895b183fed8dac1df43aa7c1aab1f/diffusion/evaluation/run_reconstruction_evaluations.py)。
- [Text2CAD 8,192 点及 ×1000](https://github.com/SadilKhan/Text2CAD/blob/669a81472ede2269837c22a4d00070eaac360c82/Cad_VLM/test.py#L213-L272)、[normalize_pc](https://github.com/SadilKhan/Text2CAD/blob/669a81472ede2269837c22a4d00070eaac360c82/CadSeqProc/utility/utils.py#L328-L331)、[分母和正值筛选](https://github.com/SadilKhan/Text2CAD/blob/669a81472ede2269837c22a4d00070eaac360c82/Evaluation/eval_seq.py)。
- [Pointer 实际调用](https://github.com/Snitro/Pointer-CAD/blob/a5c32d702f9569565d89a94de44b3af0020bcab0/test.py#L494-L501)、[CD helper](https://github.com/Snitro/Pointer-CAD/blob/a5c32d702f9569565d89a94de44b3af0020bcab0/measurements/chamfer_distance.py)、[聚合](https://github.com/Snitro/Pointer-CAD/blob/a5c32d702f9569565d89a94de44b3af0020bcab0/eval.py)。
- [CADBench 未平方 CD / SIoU](https://github.com/anniedoris/CADBench/blob/99e41a2eeb351f04611e83980f9f23cb0ca216c7/CADBenchEval/CADBench/Eval/geometry/_utils.py#L158-L205)、[主 evaluator](https://github.com/anniedoris/CADBench/blob/99e41a2eeb351f04611e83980f9f23cb0ca216c7/CADBenchEval/CADBench/Eval/_main.py)。
- MIRAGE 本轮读取的两个 helper 已复制并存 SHA；见 [local_helpers](__EVIDENCE_SOURCE_ROOT__/09_cpu_preparation/external_baselines_v1/local_helpers)。该副本用于当前定义检查，旧实验 lineage 仍引用各 evidence package。

## 三个容易造成论文错误的点

**平方不能靠统一倍率修正。** 仅在 cloud、归一化和采样完全相同的前提下，half-sum squared 与 sum squared 才差 2 倍。未平方与平方距离之间不存在通用常数换算。[自写的一点 cloud 算例](__EVIDENCE_SOURCE_ROOT__/09_cpu_preparation/external_baselines_v1/synthetic_formula_demo.json) 用距离 1 和 3 验证该事实；这不是模型新结果。

**F1 不都是 surface F@1。** MIRAGE native F@1 是阈值为 target bbox diagonal 1% 的 harmonic precision/recall。Text2CAD / Pointer 的 line、arc、circle、extrusion F1 是原语/序列指标。CADBench SIoU 是双向 near-surface coverage 的平均，也不是 harmonic F1。

**CADBench 论文与当前源码的 SIoU 阈值要分别记录。** [论文 §3.2](https://arxiv.org/html/2605.10873v1) 使用 target bbox diagonal 的 1%；固定源码 helper 默认绝对阈值 `0.02`，主 evaluator 无 override。在最大边→2 的空间中，这一般不等于 bbox diagonal 的 1%。这里记录版本/默认值差别，不断言原论文运行采用了错误实现。

## 可用于跨 benchmark 资料表的数值

这是分设置的 published-results 索引，**不是共同 test set 排行榜**。保留原始尺度，未知定义显式留空。实际导入主文前还需作者决定其用途。每行值已与本次保存的论文 HTML 对照；提取的原文 table text 在 [published_table_text.json](__EVIDENCE_SOURCE_ROOT__/09_cpu_preparation/external_baselines_v1/published_table_text.json)。

| 方法与原论文设置 | 报告值 | 必须同时出现的限制 | 来源 |
| --- | --- | --- | --- |
| GenCAD-3D PC+N，SynthBal-1MFT autoencoder，Original contrastive data | IoU^SL 44.8；IR^SL 22.09 | 按长度组等权，非逐 query 平均；输入有 normals，训练语料不同 | [Table 4 / §7](https://arxiv.org/html/2509.15246v1) |
| CADCrafter single-view，DeepCAD synthetic | median CD 0.049；IR 0.042 | 原表值；具体 CD 定义待补；IR 保留源表表示，不能混同 MIRAGE Build | [v2 Table 1](https://arxiv.org/html/2504.04753v2) |
| CADCrafter single-view，RealCAD | median CD 0.082；IR 0.087 | 非 MIRAGE 程序数据；同上 | [v2 Table 1](https://arxiv.org/html/2504.04753v2) |
| Img2CAD（SVG），ABC-mono | CD 0.16144；invalid ratio 0.28815 | 用原论文自身 ABC-mono 表；不能把 CADCrafter 中复述的另一 row 当作同协议重跑 | [Table III](https://arxiv.org/html/2410.03417v1) |
| Text2CAD，expert L3 prompts | median CD 0.37；mean CD 26.41；IR 0.93% | CD ×1000；不是所有 prompt levels 的平均；原语 F1 不当 surface F@1 | [Table 1](https://arxiv.org/html/2409.17106v1) |
| Pointer-CAD 1.5B，Recap-DeepCAD | mean CD 2.58；median CD 0.30 | text + intermediate B-Rep；不是完整 STEP 输入 baseline | [Table 3(a)](https://arxiv.org/html/2603.04337v1) |
| CADBench 中 CAD-Recode，clean-mesh aggregate | IoU 0.506；CD 0.064；VSR 0.919 | CADBench 的分层 aggregate；不替换本项目 Fusion 400 的结果 | [Table 2](https://arxiv.org/html/2605.10873v1) |

## 可以预写的英文解释，尚未粘入论文

> Published CAD-generation results use different input settings, datasets and geometric evaluation conventions. The source audit identified differences in distance powers, directional averaging, normalization, surface sampling and failure denominators. We therefore retain each published result under its original protocol and do not interpret the cross-benchmark table as a common-test-set ranking. Primitive-level F1 and surface F@1 are reported separately.

这段只说明资料表用途；不能代替代表性 baseline 的共同协议比较，也不能代替有证据的不可执行说明。R1.3 仍为 PARTIALLY ADDRESSED。
