> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Result Table Template

## Gate And Geometry Table

最终至少应形成如下表格。

| Seed | Arm | Build | STEP Export | Joint Scoreable | Median CD | F@1 | Uncond. F@1 | Notes |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 42 | A1E | TBD | TBD | TBD | TBD | TBD | TBD | existing reference |
| 42 | B2P | TBD | TBD | TBD | TBD | TBD | TBD | existing reference |
| 1 | A1E | TBD | TBD | TBD | TBD | TBD | TBD | frozen run |
| 1 | B2P | TBD | TBD | TBD | TBD | TBD | TBD | frozen run |
| 2 | A1E | TBD | TBD | TBD | TBD | TBD | TBD | frozen run |
| 2 | B2P | TBD | TBD | TBD | TBD | TBD | TBD | frozen run |

## 要回答的三个问题

### 1. Build / STEP Export 是否稳定

如果 B2P 每个 seed 都比 A1E 高，才可以讨论 method-level coverage difference。

如果只有 seed 42 或某一个 seed 高，则必须写成：

> Coverage advantage was observed in one run but was not stable across seeds.

### 2. Geometry fidelity 是否稳定接近

重点看 jointly scoreable subset 上：

- median CD；
- F@1；
- unconditional F@1。

如果三个 seed 都接近，才可以更强地支持：

> textualization did not materially degrade per-part fidelity under the matched protocol.

如果各 seed 方向不稳定，应改成：

> The matched runs do not support a stable fidelity advantage for either interface.

### 3. Seed variance 有多大

必须区分：

- sample-level uncertainty；
- training-run uncertainty。

Reviewer 1/2 的核心不满就是原来的统计只覆盖前者，不覆盖后者。

## 论文结论写法模板

强结果时：

> Across the frozen exact-match runs, the textual-plan interface and direct-latent interface showed similar per-part geometric fidelity, while coverage differences were [stable / not stable] across seeds.

弱结果时：

> The additional exact-match seeds show that the previously observed coverage difference is not stable enough to support a method-level advantage. We therefore narrow the claim: construction conditioning is useful, while the present evidence does not establish a stable coverage or fidelity advantage for textualization itself.

## 当前结论

这组实验的成功标准不是 B2P 赢，而是把 textual-vs-continuous comparison 从“一个偶然 checkpoint 对比”升级为“冻结 protocol 下的受控比较”。

