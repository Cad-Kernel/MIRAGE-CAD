> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Partial Run Policy

## 已观察到的状态

当前 WSL 输出中存在：

```text
~/workspace/MIRAGE/src/outputs/b1_1epoch_step_s1
```

该目录内观察到：

- `checkpoint-500/`
- `checkpoint-1000/`

但没有确认 root-level final artefacts：

- `adapter_model.safetensors`
- `soft_prefix.pt`

同时未发现：

- `outputs/b2_pred_matched_step_s1`
- `outputs/b1_1epoch_step_s2`
- `outputs/b2_pred_matched_step_s2`
- `outputs/e1_observation_bypass/gen_code_step_A1E_s1.jsonl`
- `outputs/e1_observation_bypass/gen_code_step_B2P_s1.jsonl`
- `outputs/e1_observation_bypass/gen_code_step_A1E_s2.jsonl`
- `outputs/e1_observation_bypass/gen_code_step_B2P_s2.jsonl`
- `outputs/e1_observation_bypass/seed_1_actuals.json`
- `outputs/e1_observation_bypass/seed_2_actuals.json`

## 规则

已有 partial output 不得作为正式 seed 结果使用。

推荐处理方式：

1. 在正式跑 seed 1 前，将 partial 目录 archive：

```bash
mkdir -p outputs/archive
mv outputs/b1_1epoch_step_s1 outputs/archive/b1_1epoch_step_s1_partial_before_frozen_protocol
```

2. 或者删除 partial 目录后重跑。

3. 不建议自动 resume，除非 frozen protocol 明确规定 resume 方式，且 A1E/B2P 两臂对称。

4. 脚本应检测 partial output 并报错，不应静默跳过或静默 resume。

## 为什么不能 resume

这组实验用于回应 reviewer 对 checkpoint、update count、seed variance 的质疑。若 seed 1 使用 partial resume，而 seed 2 从头运行，或 A1E resume 但 B2P 从头运行，会引入新的不对称。

最稳的做法是：archive partial，按 frozen protocol 从干净输出目录开始。

## 当前结论

正式 seed 1 开始前，必须处理 `outputs/b1_1epoch_step_s1` partial 目录。否则 `44_seeds_a1e_b2p.sh` 可能跳过或混入旧状态，破坏实验可解释性。

