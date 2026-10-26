> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Review/04 Manual Training Release Record

Date: 2026-10-16

```yaml
Scientific protocol: FROZEN_UNCHANGED
Exposure / role manifests: FROZEN_UNCHANGED
Full shared cache: COMPLETE_REVERIFIED
Cache entries: 83997
Real-cache CPU execution preflight: PASS_REVERIFIED
Execution / input / initialization hashes: PASS
Training output directories: ALL_ABSENT_AT_RELEASE
Manual training command: RELEASED
Training: NOT_STARTED_AT_RELEASE
Training executed by assistant: NO
Observed trained global_steps: NONE
Gate / geometry evaluation: NOT_STARTED
```

The operator completed full frozen-encoder cache inference and real-cache CPU preflight, then requested the next step. This record releases the manual training command after independent read-only revalidation. It does not start a training process, change the frozen scientific protocol, or claim any new model result.

## Verified Evidence

- `execution/real_cache_preflight.json`: actual on-disk PASS report, not only pasted console output.
- `execution/training_release_actuals.json`: fresh verification of frozen seal, runtime/source/component/initialization hashes, tested execution hashes, full cache, preflight budgets and absent future training outputs.
- `execution/register_training_release.py`: reproducible registration tool; reads/verifies and records release only, never trains.

Current execution fingerprint: `905782583273b437e9e82d11882583d81167738baa4d988712c2263a2e643d73`.

Cache root: `__RUN_SOURCE_ROOT__/data/exposure_policy_s42/frozen_query_cache`.

Cache index SHA256: `93e0060b697ccb98c0be3af51db70bb60ae0babbe294224ee9c7b3cf60718441`.

Cache completion SHA256: `d8ef8c2f538451d8ed1cfcbf13403c4af2eccb8536679c0a4c73037e4a07b715`.

All 83997 cache entries were re-read and checked for byte/tensor hashes, identity/key coverage, finite FP32 latent/point arrays and nonempty reference targets. The cache is the unchanged shared union of required train/validation/test queries; it does not add training examples or change source-split membership. The preflight and current execution hashes match the previously tested implementation.

## Budget And Data Checks

| Arm / Stage | Rows | Epochs | Planned Updates | Actual Trained Updates |
| --- | ---: | ---: | ---: | --- |
| A / Phase 1 | 75024 | 1 | 4689 | NOT_STARTED |
| A / Phase 2 | 8000 | 1 | 500 | NOT_STARTED |
| B / Phase 1 | 75024 | 1 | 4689 | NOT_STARTED |
| B / Phase 2 | 8000 | 1 | 500 | NOT_STARTED |
| A / Stage 4b role contract | 3150 | 3 | 1182 | NOT_STARTED |
| B / Stage 4b role contract | 3150 | 3 | 1182 | NOT_STARTED |

All materialized plan inputs and reference targets retain supervised tokens after tokenization. Plan validation has 800 cases and code validation has 2500 cases, both checked. First/last batch shapes and actual sampler-index hashes match the frozen budget preflight. Shared Phase 1 identities between A and B use the same cached tensors; the report records 14464 such overlapping source/modality pairs.

Stage 4b's pre-training check is correctly labeled a **role contract** with empty-plan fixtures, not actual model predictions. Actual same-arm final Phase 2 train-role predictions do not exist yet. Their exact 945 IDs/order, provenance, empty/invalid-plan retention and supervised-target tokenization remain mandatory runtime gates before real Stage 4b training. No rows may be filtered or replaced to bypass those gates.

## Manual Command

Run in WSL Ubuntu, with `ai_dev` active:

```bash
cd ~/workspace/MIRAGE/src
bash __DEV_ROOT__/src/training_25k/cag_run_exposure_policy.sh run --confirm-training
```

This is the formal training action, unlike the previous `cache` and `preflight` actions. The explicit confirmation is supplied by the human operator. It does not require changing `05_execution_spec.json` or the original preparation reports: their `training_authorized: false` records the earlier preparation-only state and is deliberately preserved under the original seal.

The canonical new execution files remain in `__DEV_ROOT__\src\training_25k`, accessed through `/mnt/c` by this command. Data, frozen imports and output working directory remain `__RUN_SOURCE_ROOT__`. No copy to an unverified WSL version of the wrapper is needed.

## Run Sequence And Outputs

The wrapper performs A Phase 1 -> A Phase 2 -> A train-role plan generation -> A Stage 4b -> A four-modality evaluation prediction generation, then the corresponding B sequence. No extra seed or third arm is run. Shared alignment, priors and GT-plan Stage 4 remain fixed; only the predeclared plan branches and Stage 4b continuations train.

New outputs:

- `outputs/exposure_policy_s42/arm_A/plan_phase1`
- `outputs/exposure_policy_s42/arm_A/plan_phase2`
- `outputs/exposure_policy_s42/arm_A/stage4b`
- `outputs/exposure_policy_s42/arm_A/predictions`
- Corresponding `arm_B` directories.

Every trained stage records `STARTED.json`, `training_report.json`, native `trainer_state.json`, final adapter/prefix as applicable, and a completion marker only after the actual-step checks. Final actual global steps must be 4689, 500 and 1182 in each arm. Optimizer/scheduler and RNG reset at the frozen phase boundary; phase transfers accept only same-arm final LoRA/prefix. No best/final mixing or implicit resume is allowed.

Prediction output contains per-modality `test_code_{modality}.jsonl` and `geom_input_{modality}.jsonl`, with 2500 ordered test IDs each. Completion of training/generation is **not** closure of the experiment: the existing Windows gate and geometry evaluators must still run, followed by result registration and analysis.

## Operator Cautions

Startup rechecks the frozen source resources and cache, then materializes/checks the first real dataset before GPU training. This can take time before a training progress bar appears. Do not change library versions merely to remove the existing compatibility/deprecation warnings; the runtime is frozen and guarded.

If any command or runtime assertion fails, stop and retain the error/output paths. Do not delete partial outputs, edit IDs/manifests, change LR/budgets, remove guards, or rerun the complete command as an implicit resume. Register and diagnose an execution bug first. GPU training and generation have not yet been exercised in this control; the successful CPU preflight is not a guarantee against every CUDA/runtime failure.

This record supersedes the live readiness state reported in `08_execution_implementation.md` and `execution/implementation_status.json`, which remain historical pre-cache implementation snapshots. It does not supersede or alter any frozen scientific definition.
