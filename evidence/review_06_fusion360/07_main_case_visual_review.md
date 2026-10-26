> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Six Main Fusion 360 Cases: Visual Recheck

Date: 2026-10-22, Europe/Paris.

**六例逐图复核完成；这是 AI-assisted visual review，不冒充作者/人工签署。**
作者对标签、图注和主文采用范围的最终确认仍为 PENDING。
没有开启 Review/07，也没有训练、重新预测、执行 CAD 程序、重新评分或重新渲染。

## 1. Read This Version

新审核入口：[main_review_v1/index.html](main_review_v1/index.html)。
每例同时展示归一化与 reference-world 两套原图，并链接原始指标、plan/code 摘录和归档路径。

- [六例完整审核记录 JSON](main_review_v1/main_review_records_v1.json)
- [六例英文图注草案与共用 legend](main_review_v1/caption_drafts_en.md)
- [作者签署模板，另存填写](main_review_v1/author_signoff_template_v1.json)
- [原值、路径和父版本核验](main_review_v1/validation_v1.json)
- [本轮新增文件 seal](main_review_v1/review_seal_v1.json)

原 `START_HERE.md`、旧 CSV、gallery、raw archive 与 taxonomy 都是已封存记录，没有改写。
本文件是新增的 main-review 状态入口。旧的 `author_confirmation=PENDING` 不被静默覆盖。

## 2. Six-Case Decisions

| Case | 本轮可支持的具体标签 | 不能写成 | 主文建议 |
| --- | --- | --- | --- |
| [M01](main_review_v1/cases/M01.md) | 目标薄开放框架未复现，生成厚的带 boss 缺口块体；仅有相对 IoU 优势 | accurate success、CD/IoU 全胜、仅仅缺孔 | 保留，明确 metric-specific relative advantage |
| [M02](main_review_v1/cases/M02.md) | 开放三角框架与空区布局未复现，输出为块状构形 | 已证明 disconnected solids、minor detail error | 保留，代表 paired near-median |
| [M03](main_review_v1/cases/M03.md) | 薄平面部件被胶囊状体替代；CAD-Recode 未显示 reference 可见角部小开口 | 已证明 wrong extrusion、MIRAGE 只是漏了一个孔 | 保留，代表 low-tail global mismatch |
| [M04](main_review_v1/cases/M04.md) | API 参数合约执行失败，拒绝 `Part.wedge()` 的 `length` keyword | syntax failure、缺孔、wrong extrusion 或不存在输出的几何缺陷 | 保留，代表 hard execution failure |
| [M05](main_review_v1/cases/M05.md) | 圆盘轮廓与可见开口布局被不同的 bossed block 替代 | 仅缺两个孔、CAD-Recode 精确恢复原孔、IoU unavailable | 保留，代表 CAD-Recode 优势及不同 aperture layout |
| [M06](main_review_v1/cases/M06.md) | 阶梯轴/法兰轮廓被椭球体替代，未恢复多半径阶梯结构 | MIRAGE 准确恢复轴、仅参数微调误差、已证明 wrong extrusion | 保留，代表 MIRAGE/NN contrast |

推荐主文仍采用冻结的 **M01–M06 全六例**，不在看图后换成更好看的 ID。
它们覆盖 relative IoU advantage、near-median、low-tail、执行失败、CAD-Recode 优势与 NN contrast。
这只是主文采用建议，最终排版尚未由作者确认。

若最终版面只容纳四例，可使用 **M01、M02、M04、M06** 的明确 display-only subset：
保留相对优势的反例边界、中位样本、硬失败和 NN 对照。M03/M05 移附录而不是删原数据，
全部 18 例及排名不变。这不是新的实验筛样或重新计算总体结果。

## 3. Labels That Need Care

### M01 Is Not an Accurate Success

MIRAGE / CAD-Recode / NN 的原 IoU 分别约为 **1.7739% / 0.0427% / 18.7839%**。
CD x1000 分别为 **51.5254 / 3.7825 / 3.1148**。
所以 M01 只有 MIRAGE 相对 CAD-Recode 的 IoU 优势；CD 更差，NN 两项还优于 MIRAGE。
图中 MIRAGE 也未恢复 reference 框架。不能把它作为全面优越或准确的外部重建证据。
旧 panel 的 `relative_mirage_success` 是冻结的 selection bucket，不等于最终语义 success 标签。
新图注应使用 **relative IoU advantage only**；不改掉旧 bucket 以掩盖原选择过程。

### Missing Hole Requires a Visible Reference Feature

M03 的原 640px 等轴图中，reference 靠近右上角有小开口，CAD-Recode 的对应显示中未见。
允许写 **the reference corner aperture is not visible in the CAD-Recode rendering**。
这只是 view-level observation；未核验其 STEP 内部拓扑，不能写已证明三维通孔被删除。

M05 front 图中 reference 有两个明确圆形通亮开口；CAD-Recode 显示的是不同矩形开口及
环状间隙。可以写 **different visible aperture layout**。
MIRAGE 连整体形状都不同，主要标签应为 global mismatch，而不是隔离地归为 missing holes。

### Wrong Extrusion Is Not Established in These Six Cases

这批 external targets 提供 reference STEP，不提供可信的 GT construction program/history。
看到厚度、轮廓或方向不同，不足以唯一反推一次 extrusion 的错误。六例都不采用确定性的
wrong-extrusion 标签。M03 既有生成代码明确调用 `part.capsule()`，M06 调用 `part.ellipsoid()`，
因此实际生成的 primitive 可以由静态证据和图像相互印证，但不能据此证明哪个训练阶段造成错误。

M02/M06 可以描述可见结构没有恢复，M06 也可以审慎写 loss of the visible stepped profile。
不要把所有错误概括成 oversimplification：M01/M05 还生成了 reference 没有对应轮廓的复杂块体，
这更像 global structural mismatch，而非仅仅少了细节。

### M04 Has No Geometry to Diagnose

原 gate 的 syntax_ok=true，exec_ok=false；原异常与 `mirage_used.py` 第 7 行的 length 调用相符。
只记录 API/schema-pattern execution failure。没有修脚本、重跑、生成预测实体或把 API 版本
问题/模型幻觉选为已经证明的根因。其 CD/IoU 保留 null，不填零。

### M06's Relative NN Gain Does Not Recover the Target

MIRAGE 相对 NN 的原 IoU 为 **36.5526% vs 20.1080%**，CD x1000 为 **35.9630 vs 61.5049**；
两项相对 NN 更好，但阶梯轴仍被椭球体替代，CAD-Recode IoU 约 **99.3329%**。
因此该例可展示 retrieval contrast，也同时展示外部能力边界。

## 4. Paper-Ready Draft After Author Confirmation

> The two-view comparisons distinguish executable but structurally mismatched
> predictions from pipeline failures. In the selected cases, MIRAGE replaces
> open-frame, thin-plate, circular, and stepped-shaft references with different
> block, capsule, or ellipsoid-like constructions. CAD-Recode often retains more
> of the global envelope, although visible aperture layouts may still differ.
> A separate case fails at an API keyword contract before geometry is available.
> Relative IoU or retrieval gains should not be read as accurate reconstruction:
> the selected relative-IoU example remains poor in absolute terms and has worse
> CD than CAD-Recode. These examples illustrate failure modes rather than their
> population frequencies or component-level causes.

主文形状比较优先使用明确声明过的 shape-normalized series。
reference-world series 单独作为尺度/位置约定诊断，不混入为同一种几何准确率图。
所有数字都是既有外部指标，没有重算。不要把有意分层选出的六例当作总体统计样本。

## 5. Preservation and Next Boundary

- 12 张原 main panel 全部重新查看，各 panel 含两固定视角。
- 另外查看 M03 reference/CAD-Recode 等轴原图及 M05 reference/CAD-Recode front 原图。
- 六例 static predicted plan / code 与原 gate 逐一对应，没有执行代码。
- 六例原始指标、M04 null 和 M05 measured zero 保持不变。
- 父版本 5,750 个封存文件在本轮前后重新核验，全部相同。
- 本轮只新增审核、图注、导航和核验证据；原始数据及此前 CSV 不覆盖。
- 作者确认标签/图注/采用范围尚未完成，因此不把 human review 标成 CLOSED。
- **本轮到此为止，不开 Review/07。**确认后再进入 controlled edit evidence 的准备。
