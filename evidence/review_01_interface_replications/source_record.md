> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# 01 — A1E/B2P Frozen Comparison

本文件夹记录本轮 major revision 的第一个核心动作：

> 冻结并执行 A1E/B2P exact-match multi-seed comparison，用来回应 Reviewer 1 和 Reviewer 2 对 continuous-vs-textual construction interface 对照不够受控的质疑。

## 为什么这是第一个动作

这不是普通补实验，而是本轮 revision 最核心的因果比较实验。它回答的问题是：

> 在其他训练条件尽量完全相同的情况下，continuous latent interface 和 textual plan interface 的差别，到底来自 interface 本身，还是来自训练步数、checkpoint、seed 等混杂因素？

原稿中的 B1a / B2-Pred 比较有几个明显口子：

- update count 不同；
- checkpoint-selection rule 不同；
- single seed；
- continuous adapter 和 textual interface 本身不对称；
- bootstrap 只反映 test-part uncertainty，不能反映 training-run uncertainty。

因此这组实验必须先冻结 protocol，再运行。不能看 seed 1 的结果后再修改 seed 2 的设置。

## 文件说明

- `01_frozen_protocol.md`  
  人类可读的冻结实验协议。规则必须在新结果产生前确定。

- `02_machine_preflight_and_actuals.md`  
  脚本层面应该检查什么、actuals/provenance 应该记录什么。

- `03_partial_run_policy.md`  
  处理已有 partial seed 输出的规则，避免旧输出污染正式实验。

- `04_result_table_template.md`  
  最终写入论文和 rebuttal 前应汇总的结果表模板。

## 当前结论

截至 2026-09-29，registered four-seed frozen A1E/B2P comparison 已全部闭环：

```yaml
Seed 1: CLOSED
Seed 2: CLOSED
Seed 3: CLOSED
Seed 4: CLOSED
```

四个 seed 均使用相同的 STEP evaluation slice、3125 updates、final checkpoint、相同 decoding 设置、无 repair。核心结果是：B2P 在所有四个 frozen replicates 中均保持更高 Build/STEP coverage；paired scoreable subset 上，B2P 的 median CD 和 median F@1 也在四个 seed 中均优于 A1E。

四 seed 均值：

| Arm | Mean Build | Mean STEP export | Mean scored | Mean paired CD | Mean paired F@1 | Mean unconditional F@1 |
|---|---:|---:|---:|---:|---:|---:|
| A1E | 73.80% | 73.05% | 361.75 / 500 | 2.491 | 20.43% | 14.76% |
| B2P | 90.65% | 89.90% | 447.50 / 500 | 2.288 | 21.31% | 18.77% |

Per-seed closed records:

- `seed 1/01_seed1_closed_record.md`
- `seed 2/01_seed2_closed_record.md`
- `seed 3/01_seed3_closed_record.md`
- `seed 4/01_seed4_closed_record.md`

Result and interpretation records:

- `result/01_four_seed_frozen_a1e_b2p_full_results.md`
- `result/02_interpretation_and_rebuttal_position.md`

Decision:

> A1E/B2P frozen multi-seed replication is CLOSED. Do not continue to seed 5/6 by default. Use this four-seed exact-match result to answer the central comparison critique, and move revision effort to qualitative examples, Fusion 360 failure analysis, construction-disjoint diagnostics, STEP/global-descriptor wording, editability-claim narrowing, and Stage 3b curriculum discussion.

