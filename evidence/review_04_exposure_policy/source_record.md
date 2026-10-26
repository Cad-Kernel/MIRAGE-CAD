> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Review/04 -- Training Exposure-Policy Diagnostic

Date: 2026-10-22

```yaml
Reviewer target: Reviewer 2, comment 3
Historical Stage 3 / Stage 3b mapping: COMPLETE
Historical checkpoint audit: COMPLETE
Proposed comparison: one paired seed, 42
Protocol: FROZEN_DESIGN_AND_INPUTS
Data / exposure manifests: FROZEN
CPU preparation preflight: PASS
Preparation regression tests: 7_PASS
Execution CPU contract tests: 15_PASS
Real CPU encoder smoke: PASS
Full shared cache: COMPLETE_83997_REVERIFIED
Initial real-cache execution preflight: PASS_HISTORICAL_ROLE_CONTRACT
Actual Stage4b input preflight: PASS_PAIRED_A_B_AND_VALIDATION
Training release: COMPLETED_BY_OPERATOR_BOTH_ARMS_VERIFIED
Arm A plan phases: COMPLETE_4689_AND_500_ACTUAL_STEPS
Arm A train-role predictions: COMPLETE_945
Arm A Stage4b: COMPLETE_VERIFIED_NATIVE_1182
Arm B: COMPLETE_4689_AND_500_ACTUAL_STEPS_945_PLANS
Arm B Stage4b: COMPLETE_VERIFIED_NATIVE_1182
Packing amendment: OPERATOR_CONFIRMED_POLICY_HASH_LOCKED
New Stage4b packing tests: 14_PASS
B-only continuation: V2_24_CPU_TESTS_PASS_REAL_DRY_RUN_PASS
Stage4b-only execution: 26_CPU_TESTS_PASS_ACTUAL_PACKED_DATA_TRAVERSAL_PASS
Training wrapper: DO_NOT_RERUN_ORIGINAL_FULL_COMMAND
Training: COMPLETE_BOTH_ARMS
Inference implementation: 35_CPU_TESTS_PASS_ACTUAL_10000_INPUT_PREFLIGHT_PASS
Arm A evaluation predictions: COMPLETE_VERIFIED_10000
Arm B evaluation predictions: COMPLETE_VERIFIED_10000
Prediction: COMPLETE_BOTH_ARMS
Gate evaluation: COMPLETE_VERIFIED_ALL8_GROUPS_2500_ROWS_EACH
Gate audit: 12_CPU_TESTS_PASS_NATIVE311_AST_ALL20000_MATCH
Geometry evaluation: COMPLETE_VERIFIED_ALL8_GROUPS_2500_ROWS_EACH
Final audit: 20_CPU_TESTS_PASS_INDEPENDENT_NUMPY_SCIPY_PASS
Original frozen preparation seal: PASS_62_FILES_UNCHANGED
Evaluation: COMPLETE_BOTH_ARMS_FOUR_MODALITIES
Review/04: CLOSED
```

The experiment compares STEP-first exposure followed by a four-modality continuation against balanced exposure from the start, using a fixed shared upstream stack and matched optimization schedules. It is a one-seed diagnostic of exposure policy, not a new multi-seed robustness claim or a pure ordering-only causal experiment.

## Files

- `01_frozen_protocol.md`: frozen scientific design and input-artifact protocol. Current manual-start release is recorded separately in `09_training_release_record.md`; the original frozen preparation snapshot is not rewritten.
- `02_stage3_stage3b_mapping.md`: verified code/checkpoint mapping, historical budgets, actual mixture policy, reuse decision, and evaluation paths.
- `03_stage_mapping_actuals.json`: machine-readable snapshot of the inspected scripts, data, checkpoints, hashes, and CPU tensor comparisons.
- `collect_stage_mapping.py`: reproducible inspection-only collector. It does not initialize models for training or invoke any training/generation command.
- `04_preflight_actuals.json`: all six preparation checks PASS, exact manifest/resource/checkpoint/initialization hashes, actual CPU Trainer budget and sampler checks. No training or optimizer steps were run.
- `05_execution_spec.json`: frozen settings, optimizer/LR boundaries, decoder adaptation roles, validation/evaluation policy, isolated future output paths and required runtime assertions.
- `06_preflight_record.md`: human-readable preparation result, counts, limitations, artifact locations and next-step boundary.
- `07_frozen_package_seal.json`: timestamped SHA256 inventory of the frozen package, created after final verification. Verify rather than overwrite this seal.
- `prepare_exposure_policy.py`: deterministic manifest generator and CPU-only audit. Re-running accepts identical content and fails rather than replaces different frozen manifest content.
- `test_prepare_exposure_policy.py`: seven small regression tests, including ID leakage, role/order mutation and overwrite rejection.
- `seal_preparation.py`: create or verify the frozen preparation-package seal; no training actions.
- `manifests/`: phase-1 A/B cases, shared phase-2 cases, Stage 4b roles, validation/evaluation cases, source IDs, resource/code inventories and exact LR vectors.
- `artifacts/initialization/arm_A` and `arm_B`: saved untrained LoRA/prefix/tokenizer files with identical per-file hashes.
- `08_execution_implementation.md`: new execution implementation, exact source/output paths, tests, known release boundary, and manual cache/preflight commands.
- `execution/implementation_status.json`: historical pre-cache implementation attestation with execution-code hashes, 15-test report and real CPU encoding smoke references. Its old readiness fields are superseded by the release record, not edited in place.
- `09_training_release_record.md`: reverified full cache/preflight, formal manual command, run order, paths, remaining runtime gates and explicit NOT_STARTED-at-release state.
- `execution/training_release_actuals.json`: fresh machine-readable release verification and artifact hashes; no training executed.
- `10_stage4b_runtime_truncation_amendment.md`: operator-confirmed, separately hash-locked Stage4b packing correction; versioned implementation and A/validation CPU acceptance recorded. It does not release Stage4b training; B-plan manual release is separate in record12.
- `11_stage4b_validation_checklist.md`: incident evidence and future policy/unit-test/continuation/paired-preflight/runtime acceptance gates, with current statuses.
- `execution/stage4b_A_token_budget_actuals.json` and `stage4b_A_token_budget_rows.jsonl`: all 3150 actual A role rows; 19 zero-supervision cases, 211 predicted + 413 GT cases needing shorter prompts for complete targets.
- `execution/stage4b_validation_token_budget_actuals.json` and corresponding row JSONL: all 2500 fixed Stage 4b validation rows; 459 need shorter GT-plan prompts for complete targets.
- `execution/audit_stage4b_token_budget.py`: CPU-only feasibility audit; no production-tokenization change or model training.
- `execution/stage4b_packing_v1_preflight/`: new-policy actual A/validation per-row audit and hashed identity; B is explicitly pending, no paired PASS.
- `execution/test_stage4b_packing_v1.py` and `stage4b_packing_v1_tests.json`: 14 new CPU tests PASS; separate from the original 15-test execution regression suite, which was also rerun PASS.
- `12_b_only_continuation_release.md`: current B-only manual command, canonical checkout/commit/source hashes, guards, dry-run evidence and expected stop point. It supersedes the old full-wrapper command for this partial run; no Stage4b release.
- `execution/b_only_contract_tests_v2.json`, `b_only_preflight_v2.json` and `b_only_manual_release_v2.json`: 24 current tests, full actual-input CPU dry-run and separately registered manual release. Initial v1 reports remain historical.
- `execution/stage4b_policy_lock_v1.json`: unchanged common packing/tokenizer/prompt identity locked before B plan generation; original62-file seal and execution fingerprint are not rewritten.
- `13_plan_branches_and_paired_preflight_results.md`: current verified A/B plan-training results, native losses, STEP train-role grammar diagnostics, complete paths, paired packing counts and next boundary. Final CAD quality is not yet evaluated.
- `execution/stage4b_packing_v1_preflight_after_B/`: actual A/B paired PASS, all8800 train/validation row audits and frozen1182-update CPU DataLoader budget.
- `execution/plan_branches_and_paired_preflight_20261018/`: independently verified completion/startup lineage, all native log histories, standardized full-target/EOS/manifest hashes, and per-arm945-row plan diagnostics.
- `14_stage4b_execution_and_manual_release.md`: current one-arm Stage4b commands, overlay completion schema/fingerprint, common initialization, runtime guards and future inference boundary. Run A first; B requires A's actual1182-step final.
- `execution/stage4b_execution_contract_tests_v2.json`, `stage4b_execution_preflight_v1.json` and `stage4b_manual_release_v1.json`:26 current CPU contracts, actual A/B packed-data three-epoch traversal and manual release (not executed by assistant).
- `execution/stage4b_execution_preflight_v1.protected_inventory.json`: complete plan-branch/prediction snapshots, excluding only the authorized direct Stage4b output subtrees.
- `15_stage4b_A_result.md` and `execution/stage4b_A_completed_20261018.json`: historical A-only verification, native1182 steps/9450 presentations, complete native loss history, final/source/startup hashes and B's then-passing manual-start gate. Current B completion is recorded separately in record16.
- `16_stage4b_B_and_paired_training_results.md` and `execution/stage4b_B_and_paired_training_completed_20261018.json`: current A/B training-complete record, both native1182 finals, full native histories/reports, paired exposure/startup checks and A's registered final unchanged. Record15's B-NOT_STARTED state is historical; four-modality prediction/evaluation remains pending.
- `17_inference_only_preflight_and_manual_release.md`: current evaluation-only source/provenance,35-test and actual10000-input CPU acceptance, runtime limits, isolated output paths and manual A-first prediction command. No real model forward/prediction was run by the assistant.
- `execution/exposure_inference_contract_tests_v1.json`, `exposure_inference_preflight_v1.json`, corresponding `.rows.jsonl`/`.weights.json`, and `exposure_inference_manual_release_v1.json`: source-bound CPU tests, complete test query-input audit, full read-only training-arm snapshots and separate manual inference registration.
- `18_arm_A_prediction_result_and_B_release.md` and `execution/exposure_prediction_A_completed_20261019.json`: current verified A10000-case generation, all output/model/input provenance, exact CPU reconstruction of actual code prompts, per-modality diagnostics and B's passing manual-start gate. No gate/geometry results yet.
- `19_B_prediction_and_evaluation_release.md` and `execution/exposure_prediction_B_and_paired_completed_20261021.json`: current paired prediction-complete record, B actual-input reconstruction, A prior outputs unchanged, full eight-row plan/prompt diagnostics and separate manual gate/geometry commands. `execution/exposure_predictions_read_only_20261021.json` saves both prediction-tree hashes/mtimes for post-evaluation checks.
- `20_gate_results_and_geometry_release.md` and `execution/exposure_gate_completed_20261021.json`: all8 gate groups independently verified, all native endpoints/error histograms/failure IDs and paired gate tables, exact evaluator staging/prediction association, interpreter provenance and next8 sequential geometry calls. `exposure_gate_native311_syntax_20261021.json` preserves the matching native3.11.11 AST audit; the current gate-audit v2 suite passes12 tests.
- `21_final_results_and_closed_summary.md`: final closure, eight-group primary table, modality-specific interpretation, caveats, publication draft and complete code/model/result path index. No further Review/04 run is needed.
- `result/01_complete_evaluation_results.md` and `result/cag_exposure_policy_eval_summary.json`: complete native gate/geometry endpoints, all distributions/tails/failure IDs/errors, paired tests, exact source/input/output hashes and immutability checks. `result/paired_cases_{step,point,text,image}.jsonl` contains all2500 ordered paired raw outcomes per modality, not just selected successes.
- `execution/register_exposure_final_results.py`, `test_exposure_final_audit.py` and `exposure_final_audit_tests_20261022.json`: current20 CPU contracts PASS, source-bound final registrar; the date21 test record is an earlier historical snapshot.
- `execution/verify_exposure_final_summary.py` and `exposure_final_independent_verification_20261022.json`: independent NumPy/SciPy recomputation of every coverage/distribution/paired statistic directly from native results, and full per-case archive/raw-row equality checks. Original62-file seal also reverified unchanged.
- `execution/seal_final_evidence.py` and `execution/final_evidence_inventory_20261022.json`: post-result hash inventory of final reports/archives/live indexes and a strict relative-tolerance verification of all32 exact-test tails with zero absolute tolerance. This evidence inventory does not replace or modify the original scientific freeze.
- Canonical `MIRAGE-V2/src/training_25k/cag_stage4b_packing_v1.py` and `cag_preflight_stage4b_packing.py`: isolated Stage4b packing overlay/CPU audit; original three execution files remain intact.
- `../05_qualitative/`: qualitative case schema, empty CSV registry and reviewer-backed path/asset convention; no cases or renders selected yet.

## Mapping Findings

Historical plan training: 4689 Stage 3 updates + 500 Stage 3b updates = 5189. Stage 3b expands the first 2000 train IDs into four modality copies, with 2000 rows per modality, then shuffles the concatenated dataset through Trainer. This is balanced in dataset counts, not a guarantee of 25% per optimizer update.

Historical Stage 3b starts a new optimizer and scheduler at LR 1e-5 after Stage 3's LR 2e-4. Both new arms must retain the same boundary, reset, and LR schedule; a single uninterrupted balanced run would change more than modality exposure.

The original Stage 3 root currently contains final-step LoRA weights but an earlier-step prefix. A direct strict reuse of that historical Arm A is therefore not accepted. The proposed control retrains both plan branches from a saved common initialization, while sharing alignment, four priors, and the GT-plan Stage 4 code decoder. Both arms also need their own matched Stage 4b adaptation.

## Next Action

Preparation is complete. Phase 1 is 75024 presentations / 4689 updates; Phase 2 is 8000 / 500; Stage 4b is 3150 rows x three epochs / 1182 updates. The preflight uses installed Trainer planning and real DataLoader traversal, not a trained final `global_step`.

Historical incident: A Phase1/2 completed at actual steps4689/500 and945 train-role plans before the original Stage4b tokenization guard stopped prior to training. The early preflight was an empty-plan role contract, not actual generated-plan acceptance. Completed A artifacts were retained unchanged.

The operator confirmed a uniform rule for all Stage4b plan fields, GT and predicted, train and validation. A separate versioned packer now preserves full code/EOS and scaffold under the unchanged 1536 cap. Actual CPU preflight retains all 3150 A rows and all 2500 validation rows: A crops 211 predicted + 413 GT plans; validation crops 459 GT plans; zero supervision, hard overflow and packing failures are all zero. The frozen DataLoader still plans 1182 updates. Fourteen new packing tests and the original 15 regression tests pass; the original 62-file seal verifies unchanged.

The operator completed B-only v2: actual steps4689/500 and945 plans, with valid `B_ONLY_COMPLETE.json`. A's69-file tree remained unchanged. Actual A/B paired packing preflight passes with3150 rows/945 predicted+2205 GT per arm; full target/EOS survives all rows. A crops211 predicted+413 GT plans; B crops320+413; shared validation crops459/2500. Both arms retain1,898,764 supervised target tokens per pass. Original manifests/policy/source fingerprints remain unchanged. Neither Stage4b had started at that paired-preflight snapshot.

Upstream diagnostics are mixed: B has lower mixed-validation plan loss, but lower grammar validity on the945 STEP train-role plans (707/945 vs A908/945). These are not final code syntax/Build/geometry results. Record13 preserves both observations and all paths; do not select a winner before the frozen four-modality evaluation.

The dedicated Stage4b-only entrypoint is now implemented and audited with26 CPU tests and real packed-data three-epoch traversal. The first LR-length guard was corrected to accept the original1183 values for1182 updates, including the terminal endpoint; no frozen vector/schedule changed. Both arms retain5,696,292 full supervised target tokens over3 epochs and the same frozen sampler hashes.

Both human-run Stage4b arms are independently verified COMPLETE: native1182 updates,3 epochs/9450 presentations and5,696,292 full target tokens each. Both final adapter hashes, common initialization, paired exposure and protected plan branches verify; A's registered final files remain unchanged after B. Train loss A/B is0.06388404345149316/0.06474417716567286; final GT-plan validation loss is0.008523370139300823/0.008466003462672234. These are not final CAD metrics and do not establish a winner. Record16 preserves both full native histories/reports and all paths.

Both operator-run predictions and all8 gate/all8 geometry evaluations are now complete and independently verified,2500 cases per group. Every geometry row has a readable reference, exactly one candidate and the frozen ordered ID. Staged inputs/results/logs and evaluator sources match their frozen/exported associations. Both training/prediction trees and all prior gate outputs remain unchanged. Native geometry-run gate flags match standalone gate flags for all20000 cases; no kernel crashes. Final20 CPU contracts and independent NumPy/SciPy raw-result recomputation pass; the original62-file seal is unchanged. Review/04 is CLOSED; see record21 and `result/`.

Build A/B is STEP60.96/57.88, Point52.60/54.32, Text50.44/53.92, Image54.08/56.84 percent. Scoreable A/B is1463/1325,1267/1188,1233/1192,1283/1264 respectively. A is better on STEP; B improves Point/Image geometry; Text is mixed across paired/conditional/unconditional endpoints. B has lower syntax and scoreable coverage in every modality. Severe raw-CD outliers are retained. This demonstrates an exposure-policy trade-off under one paired seed, not balanced-from-start uniform superiority or seed robustness. Historical release commands in records17-20 are not pending work. Do not rerun any training, prediction or evaluator.

Keep A completed weights, predictions, the 83997-entry cache and every frozen ID/role. Do not rerun the old full wrapper, delete cases, replace empty predictions with GT or alter max_length. Original sealed protocol files remain intact; this live index points to the separate amendment rather than invalidating the seal by adding links to a sealed file. Review/03 remains CLOSED.
