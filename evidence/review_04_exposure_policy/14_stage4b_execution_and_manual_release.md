> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Stage4b-Only Execution And Manual Release

Date:2026-10-18. Seed42; one paired exposure-policy diagnostic.

Later result update: both human-operated A/B runs are independently verified COMPLETE at native1182 steps each; see `16_stage4b_B_and_paired_training_results.md`. The release/preflight commands below are historical, not instructions to rerun training. Do not rerun A/B or the absent-output preflight. Four-modality inference/evaluation remains pending.

Current acceptance:26 CPU contracts PASS; actual A/B packed-data Trainer traversal PASS; no Stage4b training started by the assistant. Execution fingerprint: `5d0b3ea3718f8f035c3cd8808ca66481e8e8574866266f9caa9d98582ad47291`.

This is a separate training-execution overlay. It does not retrain plan phases, regenerate plans, change the frozen packing policy, or launch training by the assistant. Run A first; B is guarded by verified A completion. Each command stops after its one Stage4b arm.

## Source And Evidence

Canonical code checkout: `__DEV_ROOT__\src\training_25k`.
Frozen data/import/output checkout: `__RUN_SOURCE_ROOT__`.

Entrypoint SHA256: `12871f780608950b9524c99aaa2effe9dfb430f37b394ae7e6a1d1b9ba7b205b`. Bash wrapper SHA256: `71f9a883aecd815b084b4c99959cf8759e3c24f51b3b20be93c7dcdd33ecee23`. New uncommitted files are identified by these hashes, not by assuming they are already included in a Git commit.

- `cag_stage4b_execution.py`: isolated Stage4b training, packed-data materialization, real-data CPU Trainer traversal, runtime token/sampler/LR audits and overlay final validator.
- `cag_run_stage4b_only.sh`: default CPU paired preflight; explicit `run --arm A/B --confirm-training` is mandatory for training.
- `execution/test_stage4b_execution.py` and `stage4b_execution_contract_tests_v2.json`:26 passing CPU contracts, including the actual frozen LR endpoint convention and tied-weight PEFT code-adapter-only save. No training, model forward, backward or optimizer step.
- `execution/stage4b_execution_preflight_v1.json`: final source-bound CPU execution preflight. Release requires PASS; it is not a trained result.
- Corresponding `.protected_inventory.json`: both complete plan branches/predictions/B-only records, excluding only their direct `stage4b` output subtree.
- `execution/stage4b_manual_release_v1.json`: registered manual commands, source/policy/test/preflight hashes and per-arm release gates. Registration itself never trains.

Initial test harness attempt1 recorded one missing `miragecad` import because its standalone test had not added the frozen source checkout to `sys.path`. Only the test import path was corrected;25 tests passed at that revision. The initial attempt remains in `stage4b_execution_contract_tests_attempt1.json`; no experiment/training/packing policy was changed to pass it.

The first real CPU preflight then correctly stopped on an overly strict new guard that assumed LR-vector length equals update count. The immutable vector has1183 entries for1182 updates, including the terminal post-update endpoint. The guard was corrected and an actual-frozen-data regression test added. The vector/hash, update count, scheduler and scientific protocol were not changed; no model training had started. The prior25-test report is historical; release uses the current26-test v2 report.

Frozen LR vector SHA256 remains `1d18a934fe80a4e1d8102b1aea669497cd4ec781aaf5e8f4a1816627055e904c`. Update-start checks use indices0..1181; the terminal index1182 is not another optimizer update.

## Scope And Invariants

Both arms start from the same frozen historical Stage4 GT-plan code adapter, not from their plan model or from the other arm's Stage4b result. Actual loaded LoRA tensors are checked by the original audited loader. No plan prefix is loaded into the code decoder.

The immutable945 predicted/2205 GT roles remain in fixed source order. The actual arm-specific full P1a plans are retained, including all grammar-invalid plans. Training and validation use the existing hash-locked `Stage4bPackedDataset`:1536 cap, full reference code/EOS, complete scaffold/evidence, deterministic plan-field right truncation, no filtering or GT fallback.

All actual packed feature IDs/label hashes must match the paired PASS audit. Materialized tensors are reused for training; preprocessing cannot introduce new RNG or arm-specific target loss. Three epochs, batch1, accumulation8, LR5e-5, the exact1182-step LR vector, original sampler policy and final-checkpoint selection stay fixed. Reset seed/data_seed42 after preprocessing/model loading, as in the original implementation.

Only a fresh, absent target Stage4b directory is accepted. Even an empty or partially created directory blocks rerun. The directory is claimed atomically; `STARTED.json` is not a resume instruction. Reports can only be direct non-symlink JSON files under `Review/04/execution`, never a path inside A/B outputs.

The original62-file seal, original3 execution files and fingerprints, all saved plan-phase weights/metadata and all plans remain intact. Before manual training, common/base/shared checkpoints and cache are revalidated, and all raw source-resource records are byte-checked. CPU preflight checks sealed inventory and consumed cache entries; it does not claim a fresh full raw-resource byte scan.

## CPU And Runtime Gates

Preflight materializes actual A3150, B3150 and shared validation2500 inputs. It uses the same new indexed collator and Trainer subclass as training, with a CPU dummy model whose forward raises. It traverses all three epochs for each arm and requires:

```text
3150 rows x3 epochs =9450 presentations
1182 planned updates =1179 groups of8 +3 groups of6
Full supervised target tokens per pass =1898764 per arm
Full supervised target tokens over3 train epochs =5696292 per arm
Same frozen sampler hashes, no duplicate/missing IDs
Full code/EOS preserved, padding never supervised
No model forward/backward/optimizer step in preflight
```

Actual materialized CPU counts:

| Set | Rows | Full Target Tokens / Pass | Full Input Tokens / Pass | Target Loss / Zero Supervision |
| --- | ---: | ---: | ---: | --- |
| A train | 3150 | 1898764 | 3765107 | 0 /0 |
| B train | 3150 | 1898764 | 3813613 | 0 /0 |
| Shared validation | 2500 | 1528910 | 3002738 | 0 /0 |

Both three-epoch CPU traversals produce the frozen sampler hashes and1182 planned update groups. Full target/EOS identity is equal across arms; input-token totals differ because arm-specific plan text differs. Equal input-token compute is not claimed.

At actual training startup, native global_step must be0, max_steps1182 and optimizer state empty. Every update's LR is checked. At each epoch end, actual row order, full target-token total and input-token total must match preflight. The saved plan branches and source/policy/cache identities are checked read-only. During B, the already completed A Stage4b tree is additionally snapshotted and must remain unchanged.

Before saving completion, require native actual `trainer_state.global_step ==1182`, three complete exposure epochs,1182 checked LR updates, exact full-target presentations and finite trainable weights. Intermediate checkpoint saving remains adapter-only and never serializes tied base-model weights or a plan prefix.

GPU model loading, loss/gradient execution and native final1182 steps are not claimed tested by CPU preflight. The human-operated real run remains responsible for those runtime gates; any failure stops without silent resume.

## Manual Command: A First

Run in WSL Ubuntu, `ai_dev` active, only after current execution preflight and manual release records exist:

```bash
cd ~/workspace/MIRAGE/src
bash __DEV_ROOT__/src/training_25k/cag_run_stage4b_only.sh run --arm A --confirm-training
```

The command does input/resource/cache verification before loading the GPU model, so it can spend time checking hashes before the progress bar appears. It performs **only A Stage4b**, then stops. No prediction, evaluator or plan-training function is called.

B's separately conditional command is:

```bash
cd ~/workspace/MIRAGE/src
bash __DEV_ROOT__/src/training_25k/cag_run_stage4b_only.sh run --arm B --confirm-training
```

Do not run B before A has completed and been inspected. B startup independently validates A's overlay completion, actual1182 steps, common Stage4 initialization, exposure trace, all final artifact hashes and the same execution fingerprint. A partial or legacy completion cannot satisfy this guard.

Do not rerun B-only or the old full wrapper. On error/restart, preserve every output and request inspection. No directory deletion, implicit optimizer resume, role replacement or new initialization is authorized.

## Outputs And Future Inference

For each arm, the frozen output path is:
`__RUN_SOURCE_ROOT__/outputs/exposure_policy_s42/arm_A/stage4b`
or the corresponding `arm_B/stage4b`.

Files include `STARTED.json`, `PACKING_ACTUALS.json`, final `adapter_model.safetensors`, `adapter_config.json`, tokenizer files, native `trainer_state.json`, `training_report.json`, and `COMPLETE.json`. The report records the loaded common Stage4 files, actual per-epoch target/input/padding counts, actual row/sampler/LR traces, source hashes and preflight identity.

New completion schema is `review04_stage4b_overlay_final_v1`. Its fingerprint binds the new execution sources/tests, parent protocol, locked packing, exact paired inputs and shared Stage4 initialization. The old parent fingerprint is retained explicitly as `parent_fingerprint`; old metadata is never rewritten to impersonate the amended implementation.

The old generic `final_path`/full `generate` path intentionally does not accept this new overlay fingerprint. Future four-modality inference must use the audited `final_stage4b` validator in an explicit inference entrypoint, leaving test-time prompts/decoding unchanged and never using target-aware training packing. This release does not provide or run inference.

After both actual1182-step Stage4b arms close, generate the original2500 IDs per modality, then unchanged gate/geometry and the4x2 result table. This remains one exposure-policy diagnostic, not a multi-seed or architecture-only claim.
