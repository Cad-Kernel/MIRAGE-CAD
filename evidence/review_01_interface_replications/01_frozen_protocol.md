> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Frozen Protocol — A1E/B2P Exact-Match Multi-Seed

## 核心问题

本实验比较两种 construction interface：

- **A1E / B1a**：continuous construction latent directly conditions the code decoder。
- **B2P / B2-Pred**：textual predicted construction plan conditions the code decoder。

目标不是证明某一方一定赢，而是把原来的单 checkpoint 对比升级成受控方法比较。

## Primary Protocol

冻结如下 primary protocol。除非在产生任何新结果前发现技术上不可执行，否则不得更改。

```yaml
primary_comparison:
  modality: step
  seeds:
    reference_existing: 42
    new_runs: [1, 2]

  data:
    train_jsonl: data/25k/train.jsonl
    train_rows_required: 25000
    b2p_train_jsonl: data/25k/train_b2pred_step.jsonl
    b2p_train_rows_required: 25000
    test_jsonl: data/25k/test.jsonl
    test_slice: first 500 STEP rows
    predicted_test_ir: outputs/e1_observation_bypass/pred_ir_step_present.jsonl
    predicted_test_ir_rows_required: 500

  A1E:
    output_dir_template: outputs/b1_1epoch_step_s{seed}
    arm_label_template: A1E_s{seed}
    updates: 3125
    epochs: 1
    gradient_accumulation_steps: 8
    checkpoint_selection: final

  B2P:
    output_dir_template: outputs/b2_pred_matched_step_s{seed}
    arm_label_template: B2P_s{seed}
    updates: 3125
    epochs: 1
    gradient_accumulation_steps: 8
    checkpoint_selection: final

  decoding:
    limit: 500
    batch_size: 16
    repair: false
    decoding_policy: same for both arms
```

## 不允许的行为

- 不允许先跑 seed 1，再根据 seed 1 结果改 seed 2 设置。
- 不允许在 3125 vs 3125 和 3000 vs 3000 之间根据结果切换。
- 不允许使用已有 partial output 作为正式 seed 结果。
- 不允许 A1E 和 B2P 使用不同 test slice、不同 decoding、不同 repair setting。
- 不允许用 sample-level bootstrap 替代 training-seed variance。

## 如果必须改 protocol

只有在新结果产生前发现技术原因导致 3125 vs 3125 不可执行，才允许改。改动必须记录：

- 改动原因；
- 改动时间；
- 改动前是否已有任何新结果；
- 新 primary protocol；
- 对 reviewer response 的影响。

## 当前结论

当前冻结建议为：**A1E @ 3125 vs B2P @ 3125，final checkpoint，same 500 STEP slice，same decoding，no repair，new seeds 1 and 2**。

