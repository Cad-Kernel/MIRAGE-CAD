> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Stage4b B And Paired Training Results

Date: 2026-10-18. Seed42. All training was manually run by the operator. Result verification/registration was CPU-only.

```yaml
Scientific protocol and input manifests: FROZEN_UNCHANGED
Arm A plan branch: COMPLETE_4689_AND_500_945_PLANS
Arm B plan branch: COMPLETE_4689_AND_500_945_PLANS
Stage4b A: COMPLETE_VERIFIED_NATIVE_1182
Stage4b B: COMPLETE_VERIFIED_NATIVE_1182
Training: COMPLETE_BOTH_ARMS
Four-modality test prediction: NOT_STARTED
Gate and geometry evaluation: NOT_STARTED
Review/04: OPEN_EVALUATION_PENDING
```

## Actual Training Results

| Metric | A: STEP-First | B: Balanced-From-Start |
| --- | ---: | ---: |
| Native final global_step | 1182 | 1182 |
| Epochs | 3 | 3 |
| Training rows | 3150 | 3150 |
| Predicted / GT roles | 945 / 2205 | 945 / 2205 |
| Actual sample presentations | 9450 | 9450 |
| Mean train loss | 0.06388404345149316 | 0.06474417716567286 |
| Final GT-plan validation loss | 0.008523370139300823 | 0.008466003462672234 |
| Native train_runtime, seconds | 8833.8024 | 8987.1077 |
| Native train_samples_per_second | 1.07 | 1.052 |
| Native train_steps_per_second | 0.134 | 0.132 |
| Final eval_runtime, seconds | 532.3527 | 521.701 |
| Final eval_samples_per_second | 4.696 | 4.792 |
| Final eval_steps_per_second | 4.696 | 4.792 |
| Full supervised target tokens / epoch | 1898764 | 1898764 |
| Full supervised target tokens / all train epochs | 5696292 | 5696292 |
| Input tokens / epoch | 3765107 | 3813613 |
| Input tokens / all train epochs | 11295321 | 11440839 |
| Padding tokens / all train epochs | 0 | 0 |
| Construction-plan crops / predicted / GT | 624 / 211 / 413 | 733 / 320 / 413 |
| Target-truncated / zero-supervision rows | 0 / 0 | 0 / 0 |

Shared validation remains2500 GT-plan STEP cases with459 plan-field crops, complete code/EOS targets,1528910 supervised tokens and3002738 input tokens per pass. Arm-specific plan lengths/input-token compute need not match; target exposure, row roles, sampler and optimizer-step budgets do match. Final-checkpoint selection remains unchanged.

All native validation observations, without best-checkpoint selection:

| Step | A Validation Loss | B Validation Loss |
| ---: | ---: | ---: |
| 250 | 0.011244372464716434 | 0.011341751553118229 |
| 500 | 0.00990257691591978 | 0.009575403295457363 |
| 750 | 0.009005818516016006 | 0.008969283662736416 |
| 1000 | 0.008635826408863068 | 0.008586423471570015 |
| 1182 | 0.008523370139300823 | 0.008466003462672234 |

## Verification

Both overlay completion records and all final artifact hashes pass. Native state/report/completion agree on1182 actual optimizer steps. Both reports use the same frozen historical Stage4 initialization and shared validation. All three actual sampler hashes,1182 LR checks,9450 presentations and5696292 supervised target tokens per arm match the frozen/preflight contracts. Full code/EOS remains intact under the1536 cap.

Both completed plan branches/predictions match the protected pre-training inventory. A's completion record, all eight registered final files, native state and training report are independently identical to its pre-B registration. The unchanged B wrapper additionally enforced full-A-subtree runtime immutability; the retrospective registration does not claim a separately persisted pre-B snapshot of every A intermediate-checkpoint file. No test prediction files are present in the frozen prediction directories. Original source/seal/packing identities remain unchanged.

Machine evidence contains both full native Trainer states/log histories, both complete training reports, startup/final/source/policy/preflight hashes and all checks:
`__EVIDENCE_SOURCE_ROOT__\04\execution\stage4b_B_and_paired_training_completed_20261018.json`.
CPU-only registrar: `__EVIDENCE_SOURCE_ROOT__\04\execution\register_stage4b_B_result.py`.
The prior A-only registration is preserved without rewriting its historical B-NOT_STARTED state.

## Paths And Hashes

Code checkout: `__DEV_ROOT__`.
Canonical training code: `__DEV_ROOT__\src\training_25k\cag_stage4b_execution.py`.
Wrapper: `__DEV_ROOT__\src\training_25k\cag_run_stage4b_only.sh`.
Frozen data/import/output checkout: `__RUN_SOURCE_ROOT__`.

A final: `__RUN_SOURCE_ROOT__/outputs/exposure_policy_s42/arm_A/stage4b`.
B final: `__RUN_SOURCE_ROOT__/outputs/exposure_policy_s42/arm_B/stage4b`.
B Windows access: `__RUN_SOURCE_ROOT__\outputs\exposure_policy_s42\arm_B\stage4b`.
Each directory contains final adapter/config/tokenizer files, `trainer_state.json`, `training_report.json`, `STARTED.json`, `PACKING_ACTUALS.json` and `COMPLETE.json`.

Execution fingerprint: `5d0b3ea3718f8f035c3cd8808ca66481e8e8574866266f9caa9d98582ad47291`.
Common initial Stage4 adapter SHA256: `ea70a898cb6e0fa50ec001553e1358d7c88d31e9674aaf9ae8e18319709875f7`.
A final adapter SHA256: `d6be94e295ff8373994a0c21e52d420d51feb2a907860e5fe92d4d2e8026003a`.
B final adapter SHA256: `66d1bd91a281928fd857280d6dae1ae91e676da484e1f0c10d0b42f28819e856`.
Both final adapters are73911112 bytes. Source hashes remain those registered in record14 and the source-bound machine evidence; no training code was changed for B result registration.

## Interpretation And Next Boundary

B training completed successfully. B's final validation loss is slightly lower (B minus A = -0.0000573666766285896), while its mean train loss is slightly higher. Neither difference establishes superior deployed behavior: training prompts differ by arm and this shared validation uses GT plans rather than each arm's generated plans. The PEFT vocabulary/config warning did not prevent a verified final adapter from being saved. No significance or equivalence claim follows from these losses.

The **training portion** of Review/04 is complete, not the full experiment. Preserve both final adapters, all plan models/predictions, frozen roles, the shared cache and the runtime amendment. Do not rerun any training or add a seed/arm based on these losses.

Next prepare/audit an overlay-aware inference-only entrypoint that validates both new Stage4b finals, then manually generate the original2500 test IDs for each of STEP/point/text/image per arm (10000 cases per arm). Keep final same-arm plan model/prefix, greedy decoding, P1a plan canonicalization and program repair=false. Test prompts must not depend on reference-code content/length or the target-aware training packer. The original full wrapper/generic final validator must not be used to bypass the new completion fingerprint. After predictions, run the unchanged gate/geometry evaluators and register the4x2 modality results and paired comparisons. This remains a one-seed exposure-policy diagnostic, not a pure-order-only or broad robustness claim.
