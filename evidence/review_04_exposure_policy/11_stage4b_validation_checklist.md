> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Stage 4b Amendment Validation Checklist

Date: 2026-10-22. Amendment: `10_stage4b_runtime_truncation_amendment.md`, `R04-S4B-PACK-01`.

This checklist does not itself release training. Both trained arms/predictions and all8 gate/all8 geometry evaluations are complete and verified. Record21 and `result/` close Review/04. All2500 ordered cases per group, staged prediction/source/result associations, raw metrics, paired/conditional/unconditional endpoints and immutability pass. No further run is needed. Earlier snapshots remain historical.

## Completed Checks

- [x] A final Phase1/Phase2 actual steps4689/500 and original-parent LoRA/prefix hashes verified.
- [x] All945 A predictions have the fixed train-only IDs/order and final same-arm model/prefix provenance.
- [x] At the initial packing audit both Stage4b directories were absent and B plan training was not started. No A weights/plans or formerly zero-supervision rows were deleted. Current state supersedes that historical snapshot below.
- [x] Original length audit distinguishes19 zero-supervision rows from211 predicted/413 GT full-target overflows and459 validation overflows.
- [x] Operator confirmed the common policy for all Stage4b plan fields, GT/predicted and train/validation; max_length remains1536.
- [x] Independent Stage4b module added; original `tokenize_supervised`, PlanDataset and three original execution source files unchanged.
- [x] Fitting inputs have exact legacy input-ID/label parity. Exact1536 boundary retains complete target/EOS.
- [x] Overflow truncates only a literal plan-text prefix; full-prompt re-encoding protects instruction, modality, evidence and output cue.
- [x] Unmasked labels equal the entire unchanged reference-code+EOS ID sequence, not merely a nonempty subset.
- [x] Empty/invalid predictions remain fixed-role inputs without GT fallback, grammar filtering or repair. Missing target/plan fails.
- [x] Unicode and actual frozen BPE tokenizer tests pass; offsets preserve literal text without replacement characters or synthesized END.
- [x] Packing is deterministic across RNG/call order; model-empty and budget-emptied plans are separately logged.
- [x] Empty-plan scaffold+target overflow hard fails with identity/counts; no larger cap, clipped target or row drop.
- [x] Collator masks prompt/padding only and preserves complete target/EOS; actual first/last/cropped-role batches pass.
- [x] All3150 A rows retained,945 predicted/2205 GT; crops211 predicted/413 GT; zero failures/zero-supervision/hard overflow.
- [x] All2500 shared GT validation rows retained;459 crops; zero failures/zero-supervision/hard overflow.
- [x] Per-row exact prefix, original/retained lengths, target-ID/scaffold/evidence hashes and policy provenance saved.
- [x] CPU DataLoader retains frozen sampler hashes:1182 planned updates,1179 groups of8 plus3 groups of6 over3epochs. No actual Stage4b step claimed.
- [x] Original62-file seal unchanged; original fingerprint/initialization/A artifacts verify. Full cache index/identity coverage and consumed entry bytes/tensors pass; no fresh83997-entry tensor scan claimed.
- [x] New packing suite14 PASS. Original15 regression tests rerun PASS, including corruption/role/order/output guards, budget traversal and adapter-only save.
- [x] Disclose post-freeze timing and changed target-label exposure; historical/new validation losses are not directly comparable.

Evidence: `execution/stage4b_packing_v1_tests.json`, `execution/stage4b_packing_v1_preflight/preflight_actuals.json`, `A_rows.jsonl`, `validation_rows.jsonl`, original length-audit files and `execution/test_result_20261017T114847694493Z.json`.

## Approval And B Continuation

- [x] Operator-confirmed policy/tokenizer/prompt identity locked in `execution/stage4b_policy_lock_v1.json`, before B starts. This is not a Stage4b training release.
- [x] Independent v2 B-only entrypoint implemented;24 CPU tests and full real dry-run PASS. Parent/amendment lineage is explicit; original hashes/markers/guards remain intact.
- [x] Recheck36 shared/base/initialization files, full83997-entry cache, actual A startup chain, A's69-file snapshot and unstarted B paths; preserve original plan data/sampler/LR/reset code.
- [x] Operator completed B at actual steps4689/500; native reports, startup hashes and fresh phase-boundary state verify.
- [x] B generated945 fixed-order train-role P1a plans with final model/prefix provenance. All238 grammar-invalid plans remain; no empty plans observed.
- [x] Locked packing identity is unchanged after B lengths became available; no plan repair/filter/role/budget/threshold adjustment introduced.

## Paired Actual-Plan Gate

- [x] Both datasets contain3150 rows,945 predicted+2205 GT, same ordered IDs/roles and shared2500 GT validation cases.
- [x] Full targets/EOS survive all8800 A/B/validation rows, all sequences<=1536, zero failures/zero-supervision/hard overflow, no filtering.
- [x] Actual B crops320 predicted+413 GT plans, A211+413; GT inputs/packing and shared validation match. Counts were not equalized.
- [x] Paired full target-ID/scaffold/evidence hashes match; each arm has1,898,764 full target tokens per pass and5,696,292 over3 planned train epochs.
- [x] Actual B first/last/cropped-role batches and frozen1182-update CPU sampler traversal pass.
- [x] New immutable paired PASS report saved in `execution/stage4b_packing_v1_preflight_after_B/`; original A-only audit preserved.

Paired-preflight result: **PASS_PAIRED**. B-only completion and A's69-file unchanged snapshot were independently verified before either Stage4b started. Subsequent execution release and actual training are recorded below, not backdated into that snapshot.

## Stage4b And Evaluation

- [x] Stage4b-only entrypoint implemented with26 CPU contracts and actual packed-data Trainer traversal. Manual A command released after paired PASS; B is conditional on A's same-fingerprint overlay final and actual1182 steps. Both use the same historical Stage4 adapter and frozen startup/reset rules. See record14.
- [x] A actual training independently verified before B: native1182,3 epochs/9450 presentations, all frozen sampler/LR checks,5,696,292 full target tokens, final/source/startup hashes and unchanged protected plan branches. At record15's snapshot B was absent and its startup gate passed.
- [x] B actual training independently verified; both native1182 finals, same shared Stage4/validation, frozen sampler/LR/target exposure and A's prior registered final unchanged. See record16.
- [x] Retain LR5e-5,3150rows x3epochs, accumulation8, final checkpoint selection, no program repair and fixed role order policy.
- [x] Retain actual sampler/LR/finite-loss/finite-weight guards, no row skipping/deletion or implicit resume.
- [x] Assert native `trainer_state.global_step == 1182` for each arm; planned steps do not substitute for actual training.
- [x] Save startup/final/model/source/policy hashes, actual complete-target presentations and padding/length statistics.
- [x] Implement inference-only overlay with new Stage4b final validator, no training/weight writes, same frozen IDs/order/decoding/P1a/cache and isolated outputs.35 CPU tests PASS; actual10000 test-input preflight PASS, same query-input audit required in A/B. See record17.
- [x] A generated10000 cases/2500 per modality; all output/model/ID/geometry-input hashes verify, training-arm trees unchanged, actual10000 code inputs independently reconstructed without reference-target budgeting. Record18 preserves the pre-B state.
- [x] B generated10000 cases with paired IDs/order/model/input provenance PASS; prior A output files and both training trees unchanged. Full B10000-code-input CPU reconstruction PASS. See record19 and the paired prediction inventory.
- [x] Keep target-aware packing out of test generation; no reference-code text/length enters inference. Both actual code-input audits pass independent query-only reconstruction.
- [x] All8 gate results verified:2500 unique ordered IDs each, staged input byte-identical, exported/native rows/summaries match, all rates/counts/crashes recomputed, zero crashes. Matching native3.11.11 AST audit and12 v2 unit tests PASS. Both trained/prediction trees unchanged. Geometry was pending at record20's historical snapshot; current completion is below and in record21.
- [x] Generate original2500IDs per modality, then unchanged gate/geometry evaluation. All8 geometry groups PASS:2500 ordered unique rows/targets each, N=1, native source/input/result/log hashes match; zero gate-flag differences from standalone gate, zero crashes. No third arm/new seed/evaluator change.
- [x] Register all raw/per-case/failure/tail and paired/conditional/unconditional results. Final20 CPU contracts and independent NumPy/SciPy recomputation PASS; original62-file seal unchanged. Runtime amendment, one paired seed and cumulative-exposure-vs-order limitation disclosed in record21. Review/04 CLOSED.

| Gate | Status |
| --- | --- |
| Scientific protocol / original inputs | FROZEN_UNCHANGED |
| Both-role scope | CONFIRMED_BY_OPERATOR |
| New packing tests / A+validation | 14_PASS / PASS_3150_AND_2500 |
| Original regression / seal | 15_PASS / 62_FILES_UNCHANGED |
| B-only wrapper / manual command | OPERATOR_COMPLETED_VERIFIED |
| B branch / paired preflight | COMPLETE_4689_500_945 / PASS_PAIRED |
| Stage4b-only execution preflight | 26_TESTS_PASS / REAL_PACKED_DATA_PASS |
| A Stage4b / native final | COMPLETE_VERIFIED / 1182 |
| B Stage4b / native final | COMPLETE_VERIFIED / 1182 |
| A registered final after B | UNCHANGED |
| Inference CPU contracts / actual inputs | 35_PASS / PASS_10000 |
| A / B prediction | COMPLETE_VERIFIED_10000 / COMPLETE_VERIFIED_10000 |
| A registered prediction files after B | UNCHANGED |
| Gate / geometry results | COMPLETE_VERIFIED_8_GROUPS / COMPLETE_VERIFIED_8_GROUPS |
| Gate syntax audit | NATIVE311_ALL20000_MATCH / 12_TESTS_PASS |
| Geometry audit / independent recomputation | 20_CPU_TESTS_PASS / NUMPY_SCIPY_PASS |
| Geometry / final evaluation | COMPLETE_20000_ROWS / CLOSED |
