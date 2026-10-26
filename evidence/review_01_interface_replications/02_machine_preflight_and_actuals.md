> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Machine Preflight And Actuals

## 需要修改的位置

主要脚本：

```text
__DEV_ROOT__\src\training_25k\44_seeds_a1e_b2p.sh
```

WSL 运行位置：

```text
~/workspace/MIRAGE/src/training_25k/44_seeds_a1e_b2p.sh
```

同步方式：

```bash
bash __DEV_ROOT__/src/sync_to_wsl.sh
bash __DEV_ROOT__/src/sync_to_wsl.sh --apply
```

## Preflight 必须检查

脚本启动 GPU 训练前必须检查：

- `MODALITY=step`
- `LIMIT=500`
- `ACCUM=8`
- `EPOCHS=1`
- `data/25k/train.jsonl` 行数为 25000
- `data/25k/train_b2pred_step.jsonl` 行数为 25000
- `outputs/e1_observation_bypass/pred_ir_step_present.jsonl` 行数为 500
- expected optimizer updates = `ceil(25000 / 8) * 1 = 3125`
- A1E 和 B2P 均使用 final checkpoint
- repair disabled
- seed 不能为 42
- Windows 源码和 WSL 源码一致，由 `_guard_fresh.sh` 检查

## Partial output 检查

如果输出目录存在但没有 root-level final artefacts，应视为 partial run。

对 A1E，正式完整目录至少应有：

- `adapter_model.safetensors`
- `soft_prefix.pt`

对 B2P，正式完整目录至少应有：

- `adapter_model.safetensors`

对 predictions，正式完整输出应有：

- `outputs/e1_observation_bypass/gen_code_step_A1E_s{seed}.jsonl`，500 行
- `outputs/e1_observation_bypass/gen_code_step_B2P_s{seed}.jsonl`，500 行

若发现 partial output，脚本应拒绝启动，并要求 archive/remove 后重跑。

## Actuals/provenance 应记录

每个 seed 完成后，应写：

```text
outputs/e1_observation_bypass/seed_{seed}_actuals.json
```

建议字段：

- seed
- start time
- end time
- source snapshot hash or script hashes
- train file path and SHA256
- B2P train file path and SHA256
- test slice path and SHA256
- predicted test IR path and SHA256
- CUDA version
- PyTorch version
- transformers version
- GPU name
- A1E output dir
- B2P output dir
- A1E actual train rows
- B2P actual train rows
- A1E actual optimizer updates
- B2P actual optimizer updates
- checkpoint selection rule
- decoding args
- repair flag
- prediction file paths
- prediction file SHA256

## 当前结论

冻结不能只写在 review 文档里。必须在 `44_seeds_a1e_b2p.sh` 里加入机器 preflight 和 actuals/provenance 输出，防止脚本实际执行与 frozen protocol 不一致。

