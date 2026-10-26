> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# 外部 baseline：权重、许可、版本与可执行条件核查

核查日期：2026-10-25。C06 本轮桌面核查完成。这里的完成只指公开来源、版本、许可标注和指标实现检查；没有新增模型实验，也不能把 R1.3 标成全部解决。

机器记录：[baseline_registry.json](__EVIDENCE_SOURCE_ROOT__/09_cpu_preparation/external_baselines_v1/baseline_registry.json)、[validation.json](__EVIDENCE_SOURCE_ROOT__/09_cpu_preparation/external_baselines_v1/validation.json)。初步文件 04 保留；本文件及 09 补充其待核验项目。

## 实际核查范围

- 固定 6 个官方 GitHub 仓库的完整 commit；其 API tree 均未截断。
- 保存 8 个 HF 仓库的 metadata/revision，以及官方小型文本文件。
- 129 份 HTTP 响应正文与 receipt 中的大小、SHA256 相符；包含 7 份论文 HTML、3 份项目/许可网页。
- 对 GenCAD-3D 三个归档及 Text2CAD 一个权重对象执行 HEAD，均读取 0 字节权重正文。
- 6 组论文表格的相关原始数值在本地 HTML 中复核，9 个指标源码文件通过 Python AST 解析。仅解析，不导入、不执行外部代码。

这些检查没有验证压缩包内容、模型可加载性、GPU 内存、原生 CAD 导出或完整推理环境。Git LFS SHA 是远端 metadata 公布的对象摘要，并非本机下载后复算的摘要。

## 方法和访问条件

| 对象 | 版本与权重证据 | 许可标注，分开处理 | 本轮结论 |
| --- | --- | --- | --- |
| GenCAD-3D | 代码 `50bf5133c5f895b183fed8dac1df43aa7c1aab1f`；HF `yu-nomi/GenCAD_3D` revision `5b7be2ff8c879b08744e8e55a0ca6457d5c77e4a`；3 个归档 HEAD 均 200 | 代码 MIT；HF dataset card 为 MIT；**weight repo 的 card/README 未声明许可** | 有公开权重对象的 inference-only 候选；尚不能说全部推理条件和再分发权限已满足。[代码](https://github.com/yunomi-git/GenCAD-3D/tree/50bf5133c5f895b183fed8dac1df43aa7c1aab1f)、[权重](https://huggingface.co/yu-nomi/GenCAD_3D/tree/5b7be2ff8c879b08744e8e55a0ca6457d5c77e4a) |
| Text2CAD | 代码 `669a81472ede2269837c22a4d00070eaac360c82`；权重实际放在 HF **dataset** `SadilKhan/Text2CAD`，revision `422d4c93198c3cd98d5c2092c0ab214b3a76a68d`；metadata 公开，`gated=auto`；未认证 HEAD 401 | 代码 LICENSE 与 HF 仓库声明 CC BY-NC-SA 4.0；网页要求登录并接受条件 | 找到权重不等于无条件可下载。本轮未登录、未接受条款；作者访问决定后置。[许可](https://github.com/SadilKhan/Text2CAD/blob/669a81472ede2269837c22a4d00070eaac360c82/LICENSE)、[访问条件](https://huggingface.co/datasets/SadilKhan/Text2CAD) |
| Pointer-CAD | 代码 `a5c32d702f9569565d89a94de44b3af0020bcab0`；检查了 README、项目页、GitHub releases、作者 HF 公开 model 列表及相关 issue；releases=0，作者 model 列表为空 | 固定完整 tree 未发现根目录许可；Recap-OmniCAD dataset card 的 CC BY 4.0 不能代替代码/权重许可 | **在已查官方渠道未识别到 checkpoint**。不能改写为“全网无权重”或“确定无法运行”。[代码](https://github.com/Snitro/Pointer-CAD/tree/a5c32d702f9569565d89a94de44b3af0020bcab0)、[项目](https://snitro.github.io/Pointer-CAD-Page/)、[checkpoint issue](https://github.com/Snitro/Pointer-CAD/issues/19) |
| CAD-Recode | 代码 `03e3262119b38939feaa44b8368ad8db99243d47`；HF v1/v1.5 均有公开 model metadata | 固定代码 LICENSE.md 为 CC BY-NC 4.0；两个 model card 也声明 CC BY-NC 4.0，不能按 MIT 归档 | 既有 Fusion 比较保留；本轮未下载或重跑。当前 HF revision 不补成旧预测的历史版本证明。[固定许可原文](https://github.com/filapro/cad-recode/blob/03e3262119b38939feaa44b8368ad8db99243d47/LICENSE.md)、[v1.5](https://huggingface.co/filapro/cad-recode-v1.5) |
| CADCrafter | 正确身份为 Cheng Chen 等的 CVPR 2025 / arXiv:2504.04753；补查 v2，并保存全文 HTML | 未确认官方代码、权重、数据的许可；论文公开许可不等于模型许可 | 所查论文页面尚未定位官方可运行代码/checkpoint，保持 NOT_VERIFIED；不声称已经证明无法执行。[论文 v2](https://arxiv.org/html/2504.04753v2) |
| Img2CAD（SVG） | Tianrun Chen 等，arXiv:2410.03417；检查论文与共同作者页面 | 官方运行材料/许可未核实 | 保持 NOT_VERIFIED。另一同名项目不能替代该论文。[论文](https://arxiv.org/html/2410.03417v1)、[共同作者页面](https://chunan-yu.github.io/) |
| Img2CAD（factorization，同名警示） | `qq456cvb/Img2CAD`，代码 `afe48afa3f66e793ac9b64d3df4aab8c3ef7f7e3`；HF 有分类别模型文件 | 代码与 HF card 标注 MIT | CITATION 的作者/完整标题与 SVG 论文不同，不用它证明 SVG 已开源。[CITATION](https://github.com/qq456cvb/Img2CAD/blob/afe48afa3f66e793ac9b64d3df4aab8c3ef7f7e3/CITATION.cff) |

## 可下载对象的精确标识

完整大小与 advertised LFS SHA256 存在 registry，不省略成只有短哈希。主要对象如下：

| 对象 | 字节数 | 当前核查级别 |
| --- | ---: | --- |
| GenCAD Autoencoder.zip | 149,267,169 | metadata + HEAD 200 |
| GenCAD Contrastive.zip | 513,922,220 | metadata + HEAD 200 |
| GenCAD Diffusion.zip | 4,681,412,235 | metadata + HEAD 200 |
| GenCAD 三个归档合计 | 5,344,601,624 | 未下载、未解压；不同架构 variant 是否匹配未测 |
| Text2CAD `text2cad_v1.0/Text2CAD_1.0.pth` | 91,601,866 | metadata；未认证 HEAD 401 |
| CAD-Recode v1 `model.safetensors` | 3,087,805,256 | metadata only；HF revision `1e070ab9a4ccd56a768444ffb01732230548be45` |
| CAD-Recode v1.5 `model.safetensors` | 3,087,786,824 | metadata only；HF revision `765e8cc315a1a77bd8c69ccd0b403bad20ce35e8` |

## CADBench：可以研究适配，但不是现成四模态实验

本次锁定 [anniedoris/CADBench](https://github.com/anniedoris/CADBench/tree/99e41a2eeb351f04611e83980f9f23cb0ca216c7) / [arXiv:2605.10873v1](https://arxiv.org/html/2605.10873v1)，不与其他同名 benchmark 混用。Reviewer 未给具体论文 ID，不能声称他已经确认这一身份。

HF `DeCoDELab/CADBench` revision `7cf5b3ec195228e4342cfa534d25662d36e96cbc` 的 metadata 列出 18,000 例、6 个 3,000 例 split；下载总量约 80.23 GB（80,229,154,806 bytes）。本轮没有下载资产。schema 有 STEP/STL/OBJ/GLB、单/多视图和 PBR 图像、noisy mesh、file_id/label，**没有自然语言 instruction 字段**。不能把分类 label 当作 MIRAGE 的自然语言输入。B/F/E/A 是 STEP-based families；M/O 为 mesh-based，不能假设每行 STEP 都非空。

官方执行入口接受 CadQuery code；MIRAGE Flluma code 需要单独验证 export/backend adapter。采样、归一化、对齐与失败分母也需锁定后才能比较，见 09。

代码 MIT 不涵盖所有来源数据。[DATASET_LICENSE.md](https://github.com/anniedoris/CADBench/blob/99e41a2eeb351f04611e83980f9f23cb0ca216c7/DATASET_LICENSE.md) 保留 constituent licenses，Fusion 360 和 Objaverse 等不能一概标为 MIT。

## Fusion comparator 的训练数据问题

[CAD-Recode 论文 v2 §3.2](https://arxiv.org/html/2412.14042v2) 说明其程序生成训练集未使用人工设计 CAD 的序列。这可用于说明训练来源，**不等于**“Fusion 400 与训练数据 exact/near-duplicate overlap=0”，也不核验基础 Qwen 模型的数据接触。本地旧 Fusion 记录指向 v1.5，缺失历史 HF revision/实际 weight-byte 绑定；本轮新 metadata 不能补写该历史事实。

## 对 reviewer 回答的用途与边界

R1.2 的范围收窄与 R1.3 的 baseline 要求分开回答。当前有了带版本、可访问性和指标差异证据的资料；还没有共同协议实验，也没有对每个方法作出有证据的 genuinely impossible 判定。不能只因完成本表便把 R1.3 改成 ADDRESSED。

实际 inference-only 候选、访问条款和是否采用异构 cross-benchmark 表，放到作者最后一批决定。本轮不自动下载、安装、训练或运行这些模型。
