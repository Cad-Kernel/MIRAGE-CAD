> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Review/04 Final Results And Closure

Date: 2026-10-22. Reviewer target: R2 comment3. One paired seed42.

```yaml
Scientific protocol / original 62-file seal: FROZEN_UNCHANGED_PASS
Arm A plan training: COMPLETE_ACTUAL_4689_PLUS_500
Arm B plan training: COMPLETE_ACTUAL_4689_PLUS_500
Stage4b A/B: COMPLETE_ACTUAL_1182_EACH_FINAL_CHECKPOINT
Prediction A/B: COMPLETE_10000_EACH_READ_ONLY_UNCHANGED
Gate: COMPLETE_VERIFIED_8_GROUPS_2500_ROWS_EACH
Geometry: COMPLETE_VERIFIED_8_GROUPS_2500_ROWS_EACH
Readable reference clouds: 20000_OF_20000_GEOMETRY_ROWS
Geometry kernel crashes: 0
Standalone gate versus geometry-run gate flag differences: 0
Final audit CPU tests: 20_PASS
Independent NumPy / SciPy raw-result recomputation: PASS
Model / prediction / gate output immutability: PASS
Review/04 training exposure-policy diagnostic: CLOSED
Additional training / prediction / evaluation needed for Review/04: NONE
```

## 结论

这个实验已经完整跑完并登记，可以关闭。结果有价值，但不是 B 全面胜过 A。

A 是 STEP-first → balanced continuation；B 是 balanced-from-start。两臂实际 plan updates 都为4689+500，并在相同边界重置 optimizer/scheduler、切换 LR；Stage4b 都实际1182步。共享 upstream、初始化、固定 IDs、解码、evaluator 和 no-program-repair 策略保持不变。

最稳妥的研究结论是：**在这个单 paired-seed、预算匹配的 diagnostic 中，training exposure policy 改变了最终的四模态表现与取舍，不能把 modality profile 完全归因于共享架构。**

这不是 pure order-only ablation：B 同时改变了累计 modality exposure。它也不是 multi-seed curriculum robustness 结论，不能把四个 modality 当成四个独立训练 replicate。

## 四模态完整主表

每行 denominator=2500。CD/F@1 median 是各臂自己的 scoreable subset；unconditional mean F@1 对全部2500条计算，不可评分条目按0计。F@1 列为百分数。

| Modality | Arm | Syntax % | Build % | STEP export % | Scoreable count (%) | Conditional median CD | Conditional median F@1 % | Unconditional mean F@1 % |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| STEP | A | 97.28 | 60.96 | 60.08 | 1463 (58.52) | 3.142720 | 18.797687 | 10.795239 |
| STEP | B | 83.48 | 57.88 | 55.36 | 1325 (53.00) | 3.590553 | 14.500473 | 8.015022 |
| Point | A | 97.44 | 52.60 | 51.76 | 1267 (50.68) | 56.213655 | 3.512912 | 2.380663 |
| Point | B | 82.56 | 54.32 | 50.24 | 1188 (47.52) | 11.226172 | 5.268916 | 2.991428 |
| Text | A | 98.36 | 50.44 | 49.80 | 1233 (49.32) | 4.395175 | 16.013243 | 7.861099 |
| Text | B | 84.96 | 53.92 | 51.80 | 1192 (47.68) | 3.918623 | 15.592268 | 7.464002 |
| Image | A | 97.04 | 54.08 | 52.84 | 1283 (51.32) | 60.367040 | 4.064360 | 2.618009 |
| Image | B | 84.76 | 56.84 | 53.48 | 1264 (50.56) | 8.396628 | 5.077186 | 3.069695 |

Execute 和 solid-valid 在本次八组中均等于 Build；它们的所有原始计数、rate、runtime、错误和路径仍完整保存在 full result 与 machine summary，未因相同而删去。

## 如何解释

- **STEP：A 更好。** B 的 Build/export/scoreable 分别低3.08/4.72/5.52pp，unconditional F@1 低2.780218pp；paired CD 和 F@1 的 case-wise 胜负也偏向 A。
- **Point：B 几何改善明显，但覆盖端并不全面更好。** B 的 Build 高1.72pp，export 低1.52pp，scoreable 低3.16pp；conditional median CD 从56.213655降到11.226172，unconditional F@1 从2.380663%升到2.991428%。
- **Image：B 几何改善明显。** Build/export 高2.76/0.64pp，但 scoreable 低0.76pp；conditional median CD 从60.367040降到8.396628，unconditional F@1 从2.618009%升到3.069695%。绝对 F@1 仍低，不能称为高精度重建。
- **Text：mixed。** B 的 Build/export 更高，case-wise paired CD/F@1 胜负偏向 B，但全量 conditional median F@1 和 unconditional mean F@1 略低。尤其共同可评分集的 marginal median CD 是 A3.902040、B3.978552；虽然 B 在425对上 CD 更低、median paired(B-A)<0，也不能误写为“paired marginal median CD 更低”。
- **Syntax 和 scoreable：B 四模态全部更低。** 不能只突出非 STEP 的 Build 提升而省略这两项。

这些结果说明存在 exposure-policy trade-off，而不是一个策略在所有指标上占优。Stage4b validation loss B 略低也没有转化为全面更好的最终 CAD，不能用 validation loss 替代 downstream evaluation。

## 共同可评分集

下表为 case-wise 胜负，不是 seed-level significance。所有原始 paired distribution、delta distribution、ties、IDs 和未校正 exact p 值均在 full results / JSON 中。

| Modality | Joint N | CD: B wins / A wins / ties | F@1: B wins / A wins / ties |
| --- | ---: | ---: | ---: |
| STEP | 918 | 412 / 505 / 1 | 422 / 495 / 1 |
| Point | 717 | 632 / 85 / 0 | 494 / 206 / 17 |
| Text | 731 | 425 / 306 / 0 | 398 / 331 / 2 |
| Image | 750 | 639 / 111 / 0 | 490 / 245 / 15 |

不要把 joint N 加起来当成独立训练 replicate，也不要用极小的 case-level p-value 宣称 curriculum 的跨 seed 稳定性。每个 modality 的 paired subset 是两臂成功结果的交集，存在成功选择条件。

## Export 后的采样失败

所有20000个 geometry rows 都读取到了 reference cloud，且 geometry-run gate 与独立 gate 的五级标记逐条一致。下面的差额不是丢失结果，也不是缺失 reference，而是原生 evaluator 已记录的生成模型 point-cloud sampling failure。

| Modality | A exported but unscoreable | B exported but unscoreable |
| --- | ---: | ---: |
| STEP | 39 | 59 |
| Point | 27 | 68 |
| Text | 12 | 103 |
| Image | 38 | 73 |

这些条目保留原 ID、原生错误和全部 gate flags。它们不进入 conditional CD/F@1，但 unconditional F@1 按0计。不能用 Build/export 数字代替 scoreable。

## Raw Mean CD 与离群值

所有 raw mean、median、sample SD、min/max、quartiles、q95/q99、bbox error/diagonal/ratio 都保留，未 clipping、winsorization 或剔除离群值。部分组 raw mean CD 被极端几何输出支配，例如 B/STEP mean≈1.1582e8、max≈1.5346e11；A/Text、B/Text、A/Image 也有严重离群值。

因此不要概括成“B 改善 mean CD”或“所有几何指标都改善”。主文应优先清楚区分 paired case-wise geometry、conditional medians 和 unconditional F@1；raw means 仍在完整 evidence package 中公开。`CD>1000` 仅作为事后检索标记，不是 scoring/exclusion/selection threshold。

## 文件与查询入口

- 完整可读汇总：[result/01_complete_evaluation_results.md](__EVIDENCE_SOURCE_ROOT__/04/result/01_complete_evaluation_results.md)。含全部8组五级 gate、scoreable、全分布、paired tests、完整错误频数与绝对路径/SHA256。
- 完整 machine summary：[cag_exposure_policy_eval_summary.json](__EVIDENCE_SOURCE_ROOT__/04/result/cag_exposure_policy_eval_summary.json)。含所有 failure/scored/export-but-unscoreable IDs、极端值、source/model/protocol lineage、原始 native summaries 与每组 hashes。
- 逐样本证据：`__EVIDENCE_SOURCE_ROOT__\04\result\paired_cases_{step,point,text,image}.jsonl`，各2500条；每条保存 A/B 原生 gate 与 geometry row、scoreable、unconditional F@1、prediction/input/raw-result/reference-point path 和1-based行号。未只挑成功案例。
- 最终 registrar：`__EVIDENCE_SOURCE_ROOT__\04\execution\register_exposure_final_results.py`。
- 单测：`execution/test_exposure_final_audit.py`；当前20 PASS source-bound report 为 `exposure_final_audit_tests_20261022.json`。前一天生成的同名日期21测试报告保留为历史快照，当前 authority 是日期22版本。
- 独立验证：`execution/verify_exposure_final_summary.py` 与 `exposure_final_independent_verification_20261022.json`。从原生 rows 再算每个统计量；NumPy quantiles/sampleSD、SciPy binomtest 与已登记结果一致，并核对了全部逐样本 archive。
- 完成后证据 inventory：`execution/final_evidence_inventory_20261022.json`，由 `seal_final_evidence.py` 核对最终报告、逐样本 archive、当前 index 和32个 exact-test tails 后生成；极小 p-value 使用 relative tolerance1e-10、absolute tolerance0，不能把“接近0”当作尾概率一致。该 inventory 不替代原始 frozen protocol/seal。
- 两臂完整训练记录与 native loss histories：`16_stage4b_B_and_paired_training_results.md`、`execution/stage4b_B_and_paired_training_completed_20261018.json`；计划分支见 record13、packing runtime amendment 见 record10。历史记录不重写。

代码 checkout：Windows `__DEV_ROOT__`；实际训练/数据 root 为 WSL `__RUN_SOURCE_ROOT__`。新增受审计的执行 overlays 位于 Windows `__DEV_ROOT__\src\training_25k`，WSL 调用路径 `__DEV_ROOT__/src/training_25k`。不要假设整个 checkout 是 clean commit；公开代码时应按各 release/actuals 中的 source hashes 与 dirty-tree provenance 整理。

权重：`__RUN_SOURCE_ROOT__/outputs/exposure_policy_s42/arm_{A,B}/{plan_phase1,plan_phase2,stage4b}`。两臂最终权重与先前只读 inventory 保持一致，本次没有重训或改权重。

预测：`__RUN_SOURCE_ROOT__/outputs/exposure_policy_s42/evaluation_v1/arm_{A,B}`。每组 `test_code_<modality>.jsonl` 与 `geom_input_<modality>.jsonl` 的 SHA256 均已保存；native staging input 与对应 frozen input byte-identical。

Gate：`__DEV_ROOT__\scratch\exec_r04_<modality>_<A|B>`。

Geometry：`__DEV_ROOT__\scratch\geom_r04_<modality>_<A|B>`。

Evaluator wrappers：`__DEV_ROOT__\src\scripts\evaluate_execution.ps1`、`evaluate_geometry_nbest.ps1`；实际 Python evaluator 来自 WSL source root，并逐组复制到 native staging。所有 source hashes 与 evaluation release 相符。原生 Python 为3.11.11；先前辅助语法审计发现的 WSL3.12 parser 差异没有改变 native 结果。

**图像资产边界：** 原生 scorer 使用 temporary directory，生成的 `candidate.step` 与 sampled PLY 不持久保存。当前登记的是实际存在的预测、reference point、指标、日志及 source/line locator，不能把临时 STEP 路径当成可复用图资产。后续 qualitative gallery 需要在单独的受控渲染流程中从已锁定 case/code 重建并保存持久 STEP、两个视角图和失败日志；本次没有选择 gallery cases 或生成渲染图，也没有重跑 CAD。

## Reviewer-Facing Draft

> We added a predeclared, single-paired-seed exposure-policy diagnostic comparing STEP-first training followed by balanced four-modality continuation with balanced training from the start. Both arms used identical shared upstream components, matched plan-training budgets and optimizer-reset schedules, matched downstream adaptation, final checkpoints, and the same no-program-repair evaluation on 2,500 fixed cases per modality. Balanced-from-start increased Build success for Point, Text and Image, but decreased STEP Build from 60.96% to 57.88%. Point and Image showed better paired geometric fidelity, whereas STEP favored STEP-first training. Text exhibited mixed conditional, paired and unconditional outcomes. Syntax and scoreable coverage were lower for balanced-from-start in all four modalities. These results show that the observed modality profile depends on the training exposure policy and should not be attributed solely to the shared architecture. Because this control also changes cumulative modality exposure and uses one paired seed, it is not a pure order-only ablation or an estimate of seed-level curriculum robustness.

在 Methods/Supplement 中同时披露 training-only target-preserving packing amendment、发生时间、GT/predicted/validation 统一应用、没有删除 rows/改变 roles，以及 inference 没有使用 reference target 长度。不要省略这些执行修复来暗示 byte-for-byte historical reproduction。

## 下一步

Review/01、02、03、04 的已冻结内部训练型实验均已关闭。**不要继续跑 Review/04 训练、prediction、gate、geometry，也不要加 seed 或重新选权重。**

接下来进入 qualitative success/failure gallery 与 Fusion360 failure analysis；external/public benchmark 仍需独立 feasibility triage，不能因为内部实验完成就声称外部泛化已解决。现有 `05_qualitative` registry/schema 可承接这些 per-case IDs/paths，但登记 schema 不等于图和 gallery 已完成。
