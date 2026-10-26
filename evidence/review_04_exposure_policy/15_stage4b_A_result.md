> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Stage4b A -- Verified Training Result

Date: 2026-10-18. Seed42. Human-operated training; independent CPU-only result registration.

Later update: B has also completed and both finals are verified in `16_stage4b_B_and_paired_training_results.md`. This A-only result preserves its original pre-B snapshot. The B command below has already been run; do not rerun it.

```yaml
Arm A plan phases: COMPLETE_4689_AND_500
Arm A train-role plans: COMPLETE_945_UNCHANGED
Arm A Stage4b: COMPLETE_VERIFIED_NATIVE_1182
Arm B plan phases and train-role plans: COMPLETE_UNCHANGED
Arm B Stage4b: NOT_STARTED_MANUAL_START_GUARD_PASS
Four-modality test prediction: NOT_STARTED
Gate and geometry evaluation: NOT_STARTED
Review/04: OPEN
```

## Native Results

| Item | Actual |
| --- | ---: |
| Native final global_step | 1182 |
| Epochs | 3 |
| Training rows / predicted roles / GT roles | 3150 / 945 / 2205 |
| Actual sample presentations | 9450 |
| Mean training loss | 0.06388404345149316 |
| Final validation loss | 0.008523370139300823 |
| Native train_runtime, seconds | 8833.8024 |
| Native train_samples_per_second | 1.07 |
| Native train_steps_per_second | 0.134 |
| Final eval_runtime, seconds | 532.3527 |
| Final eval_samples_per_second / eval_steps_per_second | 4.696 / 4.696 |
| Full supervised target tokens / epoch | 1898764 |
| Full supervised target tokens / all training | 5696292 |
| Input tokens / epoch / all training | 3765107 / 11295321 |
| Padding tokens / all training | 0 |
| Train plan crops / predicted / GT | 624 / 211 / 413 |
| Target-truncated / zero-supervision rows | 0 / 0 |

All native validation observations are retained, without selecting the best checkpoint:

| Step | Validation Loss |
| ---: | ---: |
| 250 | 0.011244372464716434 |
| 500 | 0.00990257691591978 |
| 750 | 0.009005818516016006 |
| 1000 | 0.008635826408863068 |
| 1182 | 0.008523370139300823 |

Checkpoint selection remains **final**. Full native Trainer state/log history, training report, startup/final file hashes and dependency records are copied into `execution/stage4b_A_completed_20261018.json`; the original model outputs are not rewritten.

## Verification And Provenance

Independent registration passed the original frozen-package seal, current source/dependency identity, overlay completion schema/fingerprint, all eight final-file hashes, native1182 steps, shared historical Stage4 initialization, paired packing identity, actual three-epoch sampler hashes, all1182 LR checks and complete-target exposure. Both plan branches/predictions match the protected pre-training inventory. B's output directory is absent and its read-only startup gate passes. This registration does not rescan every raw resource or all83997 cached tensors, load a model, or start any training/inference.

Execution fingerprint: `5d0b3ea3718f8f035c3cd8808ca66481e8e8574866266f9caa9d98582ad47291`.

Loaded common Stage4 adapter SHA256: `ea70a898cb6e0fa50ec001553e1358d7c88d31e9674aaf9ae8e18319709875f7`.
Final A adapter SHA256: `d6be94e295ff8373994a0c21e52d420d51feb2a907860e5fe92d4d2e8026003a` (73911112 bytes).

Code checkout: `__DEV_ROOT__`.
Canonical training entrypoint: `__DEV_ROOT__\src\training_25k\cag_stage4b_execution.py`.
Wrapper: `__DEV_ROOT__\src\training_25k\cag_run_stage4b_only.sh`.
Source data/import/output checkout: `__RUN_SOURCE_ROOT__`.
Final A output: `__RUN_SOURCE_ROOT__/outputs/exposure_policy_s42/arm_A/stage4b`.
Windows access: `__RUN_SOURCE_ROOT__\outputs\exposure_policy_s42\arm_A\stage4b`.
Machine result: `__EVIDENCE_SOURCE_ROOT__\04\execution\stage4b_A_completed_20261018.json`.
CPU-only registrar: `__EVIDENCE_SOURCE_ROOT__\04\execution\register_stage4b_A_result.py`.

## Interpretation

A's amended Stage4b training completed successfully within the frozen row/update budget, with complete code/EOS supervision and decreasing observed validation loss. The PEFT vocabulary/config warning did not prevent a valid final adapter and completion record from being saved.

These are teacher-forced training/GT-plan validation losses, not generated-code syntax, CAD Build, STEP-export or geometry results. They neither establish A/B superiority nor close the exposure-policy experiment. Historical pre-amendment losses are not directly comparable because target-label exposure changed. Keep the one-seed diagnostic limitation and unchanged scientific scope.

## Historical Next Manual Run

Run **B Stage4b only**, from the same shared Stage4 initialization, not from A's final adapter:

```bash
cd ~/workspace/MIRAGE/src
conda activate ai_dev
bash __DEV_ROOT__/src/training_25k/cag_run_stage4b_only.sh run --arm B --confirm-training
```

The command rechecks A's verified final and all frozen input/source guards, trains only B, and stops. Do not rerun A, B-only plan continuation, the original full wrapper, or the paired execution preflight that requires both Stage4b outputs absent. Preserve all outputs on any error. After B, verify native1182 and register its results before four-modality inference/evaluation through an overlay-aware entrypoint. No GPU training or inference was launched by this registration.
