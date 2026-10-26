> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Plan Branches And Paired Stage4b Preflight Results

Date: 2026-10-18. Seed:42. Reviewer target: R2 exposure-policy diagnostic.

Execution-release update: the subsequent Stage4b-only implementation passed26 CPU contracts and actual packed-data traversal; manual A command is now recorded in record14, B conditional on A completion. NOT_RELEASED statements below describe this earlier result-registration snapshot, not the current release state. No Stage4b has been trained by the assistant.

## Verified Current State

```yaml
Arm A plan Phase1: COMPLETE_ACTUAL_STEP_4689
Arm A plan Phase2: COMPLETE_ACTUAL_STEP_500
Arm A train-role plans: COMPLETE_945_UNCHANGED
Arm B plan Phase1: COMPLETE_ACTUAL_STEP_4689
Arm B plan Phase2: COMPLETE_ACTUAL_STEP_500
Arm B train-role plans: COMPLETE_945
A output protection: PASS_69_FILES_UNCHANGED
Locked packing policy: UNCHANGED
A/B actual-plan Stage4b paired preflight: PASS
Stage4b A: NOT_STARTED
Stage4b B: NOT_STARTED
Stage4b training command: NOT_RELEASED
Four-modality final code predictions: NOT_STARTED
Gate / geometry: NOT_STARTED
Review/04 experiment: OPEN
```

The operator completed the B-only command; this inspection did not run GPU training or generate replacement plans. Both native trainer states, final model/prefix files, actual startup lineage and completion/provenance hashes verify. B's final wrapper record is `B_ONLY_COMPLETE.json`, status `PLAN_BRANCHES_COMPLETE_STAGE4B_NOT_STARTED`. The original scientific protocol,62-file seal, original execution fingerprint and separate packing lock remain intact.

The two arms are STEP-first then balanced continuation (A) and balanced exposure from the start (B). This remains one paired-seed exposure-policy diagnostic, not a pure order-only ablation or multi-seed stability experiment.

## Actual Plan Training

| Arm | Phase | Rows | Actual Updates | Aggregate Train Loss | Last Logged Eval Loss | Eval Step | Train Runtime Seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A | Phase1 | 75024 | 4689 | 0.1365201605 | 0.2809993029 | 4689 | 43658.8489 |
| A | Phase2 | 8000 | 500 | 0.1458696134 | 0.1561374813 | 500 | 3241.2963 |
| B | Phase1 | 75024 | 4689 | 0.1576593534 | 0.1428770721 | 4689 | 29702.7582 |
| B | Phase2 | 8000 | 500 | 0.1140543659 | 0.1446952075 | 500 | 3134.1245 |

All checkpoints use final selection, with the common initialization followed by same-arm Phase1 final LoRA/prefix, fresh Phase2 optimizer/scheduler and the original RNG/LR boundary. The saved exposure/sampler/LR traces are retained in the native reports and machine actuals. Validation is the fixed800-row, four-modality plan-supervision set, not final code execution or geometric reconstruction.

B's last logged mixed-validation loss is lower after both phases. Phase1 aggregate train losses are not directly comparable as an efficacy endpoint because exposure differs. Lower teacher-forced validation loss does not establish higher free-generation plan validity or CAD accuracy. Updates/example counts are matched; wall time and realized token lengths are not claimed equal.

## Full Generated-Plan Diagnostics

These are **945 fixed train-role STEP cases**, generated for subsequent Stage4b adaptation. Grammar refers to the complete P1a-canonicalized plan **before conditioning-plan truncation**, not executed Python syntax. This is not held-out plan accuracy and not a four-modality test result.

| Metric | A | B |
| --- | ---: | ---: |
| Plans / fixed IDs in order | 945 | 945 |
| Empty plans | 0 | 0 |
| Grammar-valid plans | 908 (96.0847%) | 707 (74.8148%) |
| Grammar-invalid plans | 37 | 238 |
| Rows whose text changed under P1a | 26 | 11 |
| Max P1a plan re-encoded tokens | 1536 | 1536 |
| Plans with re-encoded length >=1536 | 8 | 158 |

Grammar issue counts (a case can have multiple issues; columns do not sum to unique invalid cases):

| Issue | A | B |
| --- | ---: | ---: |
| bad_feature_line | 19 | 60 |
| bad_param_line | 6 | 1 |
| degenerate_repetition | 5 | 19 |
| missing_end | 18 | 159 |
| unknown_line_prefix | 0 | 3 |

B has21.2698 percentage points lower plan-grammar validity on this STEP training-role diagnostic. Longer plans and more missing-END issues warrant reporting. Re-encoding a P1a plan is not identical to observing the raw decoder's stopping reason; these lengths alone do not prove which generations hit the decoder limit. Do not change max_new_tokens, repair/filter plans, replace invalid plans with GT or alter the fixed roles after observing these outcomes.

This is a meaningful upstream observation, not evidence that final B Build or geometry is worse. Conversely, lower mixed-validation loss is not evidence that B is better. A modality trade-off is plausible, but must be tested using the frozen four-modality end-to-end evaluation after matched Stage4b adaptation.

## Paired Actual-Plan Packing

The original locked policy was reused unchanged:1536 cap, full code/EOS and protected scaffold/evidence, deterministic right truncation of the construction-plan field for both roles and validation. The previous A-only report remains preserved separately.

| Check | A Train | B Train | Shared GT Validation |
| --- | ---: | ---: | ---: |
| Rows total | 3150 | 3150 | 2500 |
| Predicted roles | 945 | 945 | 0 |
| GT roles | 2205 | 2205 | 2500 |
| Plans truncated, total | 624 | 733 | 459 |
| Predicted plans truncated | 211 | 320 | 0 |
| GT plans truncated | 413 | 413 | 459 |
| Code targets truncated | 0 | 0 | 0 |
| Zero-supervision rows | 0 | 0 | 0 |
| Hard scaffold+target overflow | 0 | 0 | 0 |
| Packing failures | 0 | 0 | 0 |
| Full target/EOS preserved | all3150 | all3150 | all2500 |
| Maximum packed sequence tokens | 1536 | 1536 | 1536 |
| Full supervised target tokens / pass | 1898764 | 1898764 | 1528910 |
| Full supervised target tokens /3 planned train epochs | 5696292 | 5696292 | not applicable |

No rows or roles were deleted/replaced. No plan was emptied by budget. Ordered IDs/roles, code target-ID hashes, scaffold/evidence hashes and total target supervision match across A/B; GT packing is identical. The differing predicted-plan crop counts are allowed and are not equalized. Original unamended packing would have yielded19 zero-supervision A rows and164 B rows; those are historical-rule diagnostics, not failures under the amended policy.

The same installed CPU DataLoader traversal plans1182 updates per arm:1179 groups of8 and3 groups of6 over3epochs. First/last/cropped-role batches pass. This is planned budget only: **actual Stage4b global_step does not exist yet**.

The audit reverified cache index/identity coverage and metadata/tensor bytes for all consumed train/validation entries. It is not described as a new full83997-entry byte scan. Complete target/EOS and packing-ID hashes were independently checked again for all8800 A/B/validation rows during registration.

## Paths And Reproducibility

Canonical execution-code checkout:
`__DEV_ROOT__\src\training_25k`

Training/data/output checkout:
`__RUN_SOURCE_ROOT__`

Plan output base:
`__RUN_SOURCE_ROOT__/outputs/exposure_policy_s42`

For each `arm_A` / `arm_B`:

```text
plan_phase1/adapter_model.safetensors
plan_phase1/soft_prefix.pt
plan_phase1/trainer_state.json
plan_phase1/training_report.json
plan_phase1/COMPLETE.json
plan_phase2/adapter_model.safetensors
plan_phase2/soft_prefix.pt
plan_phase2/trainer_state.json
plan_phase2/training_report.json
plan_phase2/COMPLETE.json
predictions/train_roles_plans.jsonl
predictions/train_roles_plans.complete.json
predictions/train_roles_plans.p1a_log.json
```

B-only continuation provenance is in `arm_B/B_ONLY_STARTED.json`, all three `B_ONLY_AFTER_*.json` records, and `B_ONLY_COMPLETE.json`. The original startup, final-step, file/hash and native loss histories remain available. Code checkout/base commit and wrapper hashes at release are in record12 and `execution/b_only_manual_release_v2.json`; new files are identified by hashes, not assumed present in the base commit.

Review evidence files:

- `execution/stage4b_packing_v1_preflight_after_B/preflight_actuals.json`: actual paired PASS, policy/tokenizer/prompt hashes, evaluator-independent packing checks and DataLoader sampler evidence.
- Same directory `A_rows.jsonl`, `B_rows.jsonl`, `validation_rows.jsonl`: all8800 case-level packed-prefix/token/target-identity audit rows.
- `execution/plan_branches_and_paired_preflight_20261018/actuals.json`: independently verified completion/startup lineage, full native training log histories, standardized packing counts/EOS checks, source-ID and role manifest hashes, all checkpoint/result paths and hashes.
- Same directory `A_train_role_plan_diagnostics.jsonl`, `B_train_role_plan_diagnostics.jsonl`: all945 per-arm IDs, grammar issues, empty/P1a/length/crop diagnostics.
- `execution/register_plan_branches_and_paired_preflight.py`: CPU-only registration collector, no training action.
- `execution/stage4b_policy_lock_v1.json`: unchanged pre-B policy identity; packing source SHA256 `611a21ef38c3086bdfa05d57d77726b0ea115d570f2750d7e274903d085d5b8c`.

All sources/manifests remain frozen; no evaluation results selected or used to change the split, training exposure or truncation rule.

## Conclusion And Next Gate

**B-only plan training/generation is complete; actual A/B Stage4b paired preflight passes.** This closes the upstream-readiness step, not Review/04 or its reviewer-facing performance comparison.

Next prepare and audit a dedicated Stage4b-only entrypoint using `Stage4bPackedDataset` with the locked policy, identical historical Stage4 initialization and all original runtime sampler/LR/finiteness guards. The old full wrapper still uses the original code dataset and must not be rerun. No Stage4b training command is released by this result record.

After separately released manual Stage4b A/B runs each reach actual1182 updates, generate the fixed2500 test IDs for STEP/point/text/image, run unchanged gate/geometry evaluation, then produce the4x2 exposure-policy table. Until then, no statement about Build/STEP-export/CD/F@1 or which exposure policy is better is supported.
