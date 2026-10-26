> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Fusion 360 Gallery Results v1

Date: 2026-10-22.

选图协议已在选 ID 和渲染之前冻结。已完成 **6 个主文候选 + 12 个附录候选**，
18 个不同 sample ID，每例均保留 Reference / CAD-Recode / MIRAGE generated-plan / NN retrieval。
本轮没有训练、重新预测、执行生成程序、代码修复或重新评分。

## 1. Current Status

| Item | Status |
| --- | --- |
| Step 1 correspondence audit | CLOSED / original seal unchanged |
| Step 2 native/log taxonomy | CLOSED / original seal unchanged |
| Step 3 selection and dual-coordinate rendering | COMPLETE / validation PASS |
| Assistant visual observations | 18 provisional records saved |
| Author confirmation of semantic shape labels | PENDING |
| Full registered raw-source archive | COMPLETE / byte-exact |
| Final manuscript layout/submission subset | NOT FIXED; may be changed separately |

**暂不把 Step 3 的作者语义审核标成 CLOSED，也不宣布所有 Fusion 360 reviewer 要求已全部解决。**
`CURRENT_STATUS.md` 与原 README 属于旧封存快照，故没有覆盖。新入口是 `START_HERE.md`。

## 2. Where to Find Everything

- `gallery_v1/index.html`：全部 18 例、两套图、逐例数据/归档路径/相机记录入口。
- `gallery_v1/main_metric_space_contact.png`：主文 6 例，归一化形状对比总览。
- `gallery_v1/main_reference_world_contact.png`：主文 6 例，原坐标诊断总览。
- `gallery_v1/appendix_*_contact.png`：附录 12 例，两套总览。
- `gallery_v1/cases/<slot>_<sample_id>/`：逐例原始记录、plan、raw/used code、NPZ、
  16 个独立视图/占位图、两张四方法双视角 panel、相机和正逆变换矩阵。
- `fusion360_gallery_cases_v1.csv`：18 行、20 列，候选 ID、选择理由、指标和主要路径。
- `fusion360_gallery_assets_v1.csv`：72 行、27 列，每个 case/method 的原 STEP、
  归档 STEP、网格、四个视图、原生证据及日志路径。
- `gallery_v1/selection_v1.json`：冻结规则、所有候选范围、完整排名、分位数、
  unique-ID 分配顺序和最终选择。没有看图后换样本。
- `gallery_v1/render_protocol_v1.json`：实际渲染设置、源码 hash、72 个 method slots。
- `gallery_v1/visual_review_v1.json`：看图之后才写的 18 条观察，均为作者待确认。
- `gallery_v1/author_review_template_v1.json`：后续另存填写，不覆盖已封存记录。
- `raw_archive_v1/archive_manifest_v1.json`：完整原始路径到归档副本的映射。
- `gallery_v1/independent_validation_v1.json`：选择复现、字节/相机/变换/像素/CSV 验证。
- `gallery_v1/gallery_archive_seal_v1.json`：本轮新增证据单独封存。

这些是研究证据，不是锁死的论文排版。改字体、列数、裁掉 panel 标题或减少展示例数时，
优先使用独立 640x640 PNG 和原始 STEP/NPZ，另存新的排版版本，不改原始证据。

## 3. Main Candidate Table

CD 为历史外部无量纲 symmetric squared CD x1000，不能和内部毫米 CD 混用。
IoU 下列写成百分比。缺失保持缺失，M05 的 0.00% 是真实测得零值。

| Slot | sample_id | Bucket | MIRAGE CD | MIRAGE IoU | CAD-Recode CD | CAD-Recode IoU |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| M01 | f360_82203_8b9714ce_0000 | relative IoU success | 51.5254 | 1.7739% | 3.7825 | 0.0427% |
| M02 | f360_43562_004c6cea_0003 | near paired median | 16.9004 | 6.0460% | 1.1193 | 31.2305% |
| M03 | f360_34917_61633e20_0004 | low-tail scoreable | 50.5718 | 0.6213% | 0.0568 | 37.4583% |
| M04 | f360_54501_96041527_0000 | API execution failure | unavailable | unavailable | 0.1985 | 99.1564% |
| M05 | f360_121262_f4a03dbc_0000 | CAD-Recode advantage | 34.8837 | 0.0000% | 1.0356 | 79.0779% |
| M06 | f360_55031_57f7bdba_0000 | NN contrast | 35.9630 | 36.5526% | 0.2595 | 99.3329% |

数值完整精度和 NN 指标在 CSV/JSON 中保留；本表只为阅读而四舍五入。
分位数来自 protocol 声明的具体可用/配对集合，不是全部 400 例的无条件分位数。

## 4. Important Interpretation

### Relative Success Is Not Accurate Reconstruction

MIRAGE/CAD-Recode jointly IoU-scoreable 的 200 例中，MIRAGE IoU 严格更高的只有 5 例，
CAD-Recode 严格更高的 193 例，其余 2 例相等。M01 按这 5 例的正 IoU 差值中位数选择，
并非选绝对最高 IoU。M01 的 MIRAGE IoU 仍只有约 1.77%，且 CD 比 CAD-Recode 更差。
所以其 bucket 只能写 **relative IoU advantage**，不能写 representative accurate success、
all-metric success 或 broad external generalization。这些计数只用于解释选图 cohort，
不是新推断统计，更不能用 18 个刻意分层样本估计总体错误发生率。

### View-Supported Provisional Findings

双视角中可见的例子包括：开放框架被 block-like 构形替代（M02）、薄平面部件变成
capsule-like body（M03）、圆盘轮廓变成带 boss 的块体（M05）、阶梯轴变成椭圆体（M06）、
矩形开框变成 torus-like ring（A11）。A05 的 reference 四角有可见开孔，而 CAD-Recode
对应视图中未见相同开孔。这些是 view-level observation，尚未由作者确认，不能自动升级成
拓扑证明、全部内部特征的计数或模型训练失败原因。

A10 的 MIRAGE 有可用 CD，但 IoU boolean failed；实际网格在两张固定图中呈近直线，
不是 renderer 没有工作。其极端尺度/长宽比也令 reference-world 共同画框下部分方法小于
1 像素。保存原网格及所有矩阵供后续检查，没有放大单一方法、替换样本或把 IoU 填零。

M04/A04 等执行失败只保留错误占位；没有猜测不存在的输出是否缺孔或 wrong extrusion。
API/schema 的 120/160=75% 保持为日志类别计数，仍未证明 generation 与 API-version
compatibility 哪个是根因。

### The Two Coordinate Series Answer Different Questions

归一化图按既有外部指标的 per-shape bbox 居中/尺度政策比较形状；它主动去掉全局位置/尺度误差。
原坐标图保留 MIRAGE/NN/reference 的 native coordinates，仅按已声明的输入/DSL 约定转换
CAD-Recode，所有方法共享 union frame。后者只是诊断，不是新的 physical-accuracy score，
也不能证明三个方法原本具有相同训练单位约定。图注必须写清是哪一套。

## 5. Render and Validation Actuals

- 72 个 case/method slots：64 个既有 STEP 成功 CPU 网格化，8 个历史失败占位，无新转换失败。
- 288 个独立图像：256 个真实几何视图 + 32 个明确失败占位。
- 每 case 两坐标系 x 四方法 x 两固定视角，另有 36 张 panel 和 4 张 contact sheet。
- 6 个 reference-world 视图有显式 subpixel warning，未单独 auto-fit。
- 原始网格顶点/三角面及仅 exact-coordinate welding 后的数组均保留。
- 14 个 contract tests PASS；18 ID 唯一且重算选择一致。
- 同 case/view/series 四方法相机完全相同，所有正逆变换可逆，图像无裁切。
- 5,039 个归档对象重验 SHA256；两份 CSV 的 typed values / roundtrip / 原指标一致。
- Step 1 的 20 个文件、Step 2 的 1,218 个文件 hash 未变。
- 作者确认状态仍为 PENDING，没有把 assistant 观察冒充人工确认。

## 6. Reviewer-Facing Draft After Author Confirmation

> We added a stratified qualitative gallery comparing the reference, CAD-Recode,
> MIRAGE generated-plan, and NN-retrieval outputs on the same locked test IDs.
> Cases were selected deterministically from predefined metric quantiles and
> recorded failure categories before rendering. Each comparison includes two
> fixed orthographic views with a common camera and framing across methods.
> We retain both explicitly shape-normalized comparisons and a separate
> reference-coordinate diagnostic with recorded transformations. The examples
> distinguish executable but geometrically mismatched outputs from execution,
> export, and tessellation failures; missing geometry is shown as a labelled
> failure rather than a reconstructed substitute. These qualitative examples
> illustrate capability limits and do not establish broad external generalization.

具体形状标签应在作者检查后再加入最终稿。不要把这段写成已经完成了新的 external training、
new scoring 或独立于历史预处理政策的公平性证明。
