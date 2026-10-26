> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Review/01：真实 dataset CPU 核查与路径差异

日期：2026-10-25。源码/训练清单哈希与四 seed actuals 一致；没有模型加载、梯度、优化器或 GPU 推理。

## 执行与证据

- 在原生 WSL `src` 工作目录导入历史 `SoftPrefixIRDataset` 和哈希匹配的 `ProgramDataset`。
- 全量 25,000 行/arm，实际调用 50,000 次 `__getitem__`；逐项 assert `input_ids`、`labels`、attention mask 和有效监督数。
- A1E 仅为 dataset 返回值提供一个未参与 token 路径的 dummy latent；没有重新编码 latent，不把它说成 upstream 复现。
- 源码、prompt/data helper、tokenizer 配置和词表、两个训练 JSONL、逐程序哈希均另存。
- 25,000 个 STEP descriptor 的实际源文本和 SHA256 追加封存在 `review01_diagnosis_v2/step_feature_source_archive.jsonl`。

逐行输出：`review01_dataset_v1/per_sample_tokens_labels.jsonl`。
汇总与诊断：`review01_diagnosis_v2/summary.json`。

## 结果

| 分类 | A1E | B2P |
| --- | ---: | ---: |
| 完整 target（含 EOS）保留 | 25,000 | 18,241 |
| 仅丢 EOS | 0 | 19（0.076%） |
| 保留部分正文监督，正文尾部被截 | 0 | 6,096（24.384%） |
| 无有效 target 监督 | 0 | 644（2.576%） |
| 正文损失合计（含无监督子集） | 0 | 6,740（26.96%） |
| 完整 target 未保留合计 | 0 | 6,759（27.036%） |
| prompt token 中位数 | 137 | 654 |
| 丢失正文 token / 全部正文 token（不含 EOS） | 0 | 1,939,362 / 15,237,559（12.7275%） |

B2P 正文损失行中，丢失正文 token 的中位数 242，nearest-rank p90 609，最大 1,123。
644 是 6,740 的子集，不能再相加。

## 为什么与 Claude v2 不同

真实 JSONL 中 `step_feature_path` 是相对路径，例如 `data/25k/step_features/...json`。
prompt builder 会据此加载 descriptor。未以原训练 `src` 为工作目录时，路径可能无法解析；
data helper 对缺失输入有默认行为，仍能生成外观正常但 descriptor 数值不同的 evidence 文本。

诊断将该路径明确替换为一个不存在的路径（只在内存，不改源数据），用相同 tokenizer 和 prompt helper 再计算全部 25,000 行。
该 counterfactual **同时完整复现 Claude v2 两个 arm 的五项统计**：

- A1E prompt 中位 123、截断 0；
- B2P prompt 中位 639、EOS-only 30、正文截断 6,333、无监督 631、正文 token 丢失 1,853,778。

因此 Claude v2 数字适用于这里复现的“descriptor 路径不可解析”条件，不能直接作为原生训练路径的 token 核查结果。
单独保存该 counterfactual，不把它算成新训练或新的 experimental arm。

## 失败和修正记录

第一轮真实 dataset 已完成全部逐行检查，随后与 v2 汇总值比较的 guard 失败；保留原始文件，不覆盖。
第一版诊断缺少 `chdir(src)`，相对 feature 路径检查失败；修正后写入新的 `review01_diagnosis_v2`，保留未完成目录。
这两次停止不表示训练失败，也没有更改任何训练权重或旧 gate/geometry 数值。

## 使用边界

上述是以四份 actuals 匹配的 trainer、当前可核查并已封存的 helper/tokenizer/descriptor 做出的原生路径重建。
仍未补造历史训练当时的完整 prompt/tokenizer/descriptor 字节绑定，也未证明历史 prediction 使用了哪组 checkpoint 字节。
故来源/控制结论继续为 **HOLD_STRICT_MATCH_CLAIM**，不是恢复 matched comparison。

新审计不改变已保存的覆盖率与几何评分；初始化、checkpoint selection 和跨 step root 产物的问题仍单独存在。
