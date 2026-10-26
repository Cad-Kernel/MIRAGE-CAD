> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Review/04 Execution Implementation Record

Date: 2026-10-16

```yaml
Scientific protocol: FROZEN_UNCHANGED
Exposure manifests: FROZEN_UNCHANGED
Stage4b role manifest: FROZEN_UNCHANGED
Common initialization: VERIFIED_UNCHANGED
Shared checkpoints: VERIFIED_UNCHANGED
Execution code: IMPLEMENTED_CPU_CONTRACTS_PASS
New CPU contract tests: 15_PASS
Real frozen encoder CPU smoke: PASS_8_CASES_REPEATED
Full shared latent cache: NOT_BUILT
Real-cache execution preflight: BLOCKED_SHARED_CACHE_NOT_BUILT
GPU training: NOT_AUTHORIZED_NOT_STARTED
Formal training command: NOT_RELEASED
```

The operator explicitly selected manual full-cache generation. No full encoder inference run and no GPU training were launched by the assistant. The original 62-file design/input seal remains unchanged. This record adds an execution implementation; it does not revise exposure policy, source IDs, fixed roles, update budgets, LR boundary, seed or checkpoint rules.

## Code And Checkout Paths

Canonical new code, for later public release:

- `__DEV_ROOT__\src\training_25k\cag_exposure_policy_core.py`
- `__DEV_ROOT__\src\training_25k\cag_exposure_policy.py`
- `__DEV_ROOT__\src\training_25k\cag_run_exposure_policy.sh`

These are new files. The existing frozen/historical trainers, scripts and checkpoints were not modified. The working tree already had unrelated tracked/untracked changes; they were left intact.

The wrapper is deliberately run directly from `__DEV_ROOT__/src/training_25k`, using the Windows source files. It changes its working directory to the frozen Linux data/import checkout `__RUN_SOURCE_ROOT__`. No new-file synchronization to WSL is required for these commands, and no historical script is substituted.

Evidence and tests:

- `execution/implementation_status.json`: exact execution hashes, readiness state, cache cardinalities, current test/smoke report references and their hashes.
- `execution/test_execution.py`: 15 CPU contract tests; no `Trainer.train`, backward or optimizer step.
- `execution/real_cpu_cache_smoke_v3.json`: current implementation's eight genuine frozen-encoder CPU cases, each encoded twice, including train and validation cases in every modality.
- `execution/test_result_*.json`: timestamped test result/provenance records; the current attested record is referenced by `implementation_status.json`.
- `execution/preflight_failed_*.json`: timestamped fail-closed attempt records, including the expected missing-full-cache barrier.
- `execution/collect_execution_status.py`: preparation-only implementation status collector, never a training launcher.

The historical preparation actuals and seal are not rewritten to pretend that execution preflight has passed. README/roadmap are live progress indexes, not part of the immutable design snapshot.

## Implemented Contracts

### Manifest-Aware Plan Training

The plan dataset consumes the frozen case manifest and the shared cache directly. It does not invoke the old Cartesian-product builder, filter failed examples, resample source IDs, reassign modalities or regenerate an exposure manifest. Every case resolves its source split, row, ID, modality and case index, and every manifest must match its frozen file hash.

| Stage | Arm A Rows | Arm B Rows | Planned Updates Per Arm | LR |
| --- | ---: | ---: | ---: | ---: |
| Phase 1 | 75024 | 75024 | 4689 | 2e-4 |
| Phase 2 | 8000 | 8000 | 500 | 1e-5 |
| Stage 4b | 3150 x 3 epochs | 3150 x 3 epochs | 1182 | 5e-5 |

The frozen seedable random DataLoader sampler is retained; it changes traversal order only, not case membership/exposure. CPU contract checks traverse real installed-Trainer DataLoaders and match the frozen epoch-index hashes. Actual training additionally hashes the indices observed at every training microbatch and checks each epoch against that frozen order. This is stronger than assuming that two seed flags produce the same order.

### Shared Cache

Cache root: `__RUN_SOURCE_ROOT__/data/exposure_policy_s42/frozen_query_cache`.

Cache identity is `(source_split, sample_id, modality)`; the cryptographic key also incorporates encoder/prior hashes, point count/seed/effective FPS policy, the frozen specification/resource/code inventories and execution-code fingerprint. Each entry stores lossless FP32 latent/point arrays, train/inference plan prompts, exact evidence text, and reference targets. Metadata/file hashes and independent tensor hashes are checked on read. A/B and both phases resolve a shared identity to the same entry rather than recomputing preprocessing.

Point training evidence is retained in the training prompt. Point-plan inference evidence remains `off`, as frozen; the cache saves the distinct inference prompt rather than silently fixing that historical mismatch. Code-generation evidence uses the same saved evidence/point realization. STEP evidence fallback is rejected.

The full cache has **83997 unique entries**:

| Split | STEP | Point | Text | Image | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Train | 25000 | 15344 | 15294 | 15259 | 70897 |
| Validation | 2500 | 200 | 200 | 200 | 3100 |
| Test | 2500 | 2500 | 2500 | 2500 | 10000 |
| Total | 30000 | 18044 | 17994 | 17959 | 83997 |

These are the union of required query identities, including validation and test preparation, not training presentations and not extra training examples. Training datasets still read only their fixed train manifests. The cache union does not change 75024/8000 exposure counts or leak test rows into training.

Cache creation uses `torch.inference_mode()`, frozen/eval upstream models, no decoder training and no optimizer. It reads and rehashes the 150000 original resources before full inference. Missing resources, nonfinite tensors, missing targets, fingerprint/shape/key/count mismatch or encoding failures abort; none are skipped.

Files are written into a `.building` directory. The final cache is published only after its index and completion marker exist; consumers also verify every entry. A partial `.building` directory is not training-ready and is not resumed/removed automatically. An existing completed cache is verified rather than overwritten. Do not delete a partial directory or edit manifests to make a guard pass; inspect and register the failure first.

### Initialization And Phase Boundary

Phase 1 loads the saved initial A/B adapter and prefix files, not two independent fresh initializations. Startup file hashes are recorded and loaded adapter/prefix tensors are compared to the selected source tensors. Phase 2 requires a same-arm `COMPLETE.json`, actual final `trainer_state.global_step == 4689`, final selection and unchanged LoRA/prefix files.

Phase 2 loads weights only. A new Trainer/optimizer/scheduler is constructed, and RNG is reset to 42 after all materialization/model loading. A callback rejects nonempty optimizer state or nonzero initial global step. Both arms reset at the same boundary; Arm B cannot take a continuous 5189-step scheduler path.

Every update's LR is checked against the frozen phase LR vector. Final actual steps must be exactly 4689, 500 or 1182, with complete exposure traces and finite trainable weights before any completion marker is written. All new components save final weights, with matching final prefix and LoRA. Actual steps are not inferred from a planned budget.

The custom Trainer saves only LoRA and prefix, avoiding full wrapped-base/tied-embedding serialization. This path was exercised on a tiny real CPU Qwen/PEFT model with tied embeddings, without training it. Periodic optimizer/RNG checkpoints are not implicitly resumed; a partial training output path remains a hard stop.

### Stage 4b Roles

The fixed 945 predicted-role IDs and 2205 GT-role IDs are read in frozen manifest order. Generated plans must have exactly the predicted IDs/order, train split, STEP modality, correct arm and final Phase 2 LoRA/prefix provenance. Prediction artifacts are hashed with completion provenance before adaptation.

An important historical-loader issue is deliberately avoided: `row.get('ir_text_for_program') or GT` would replace an empty prediction with a ground-truth plan. The new loader uses the role explicitly and preserves `""` as the predicted input. Invalid plans are retained too. There is no grammar filtering or replacement sampling. P1a canonicalization remains enabled and logs all changes, empty outcomes and grammar status. Program/code repair is false.

Before real Stage 4b training, every actual generated-plan input is tokenized and checked for at least one supervised reference-code token. The pre-training CPU check can only exercise the complete role loader using explicitly labeled empty-plan contract fixtures: actual plan text does not exist yet. Those fixtures are never written as training artifacts or used for model training. The real generated-plan/tokenization gate remains mandatory after Phase 2.

### Wrapper Guards And Outputs

No arguments defaults to CPU preflight. Full cache generation is a separate `cache` action. Training additionally requires an explicit human confirmation flag, a current PASS real-cache preflight report, matching code/cache hashes and CUDA. No training command is released here.

Guards check the original protocol seal, source/dependency/runtime/manifest/shared-init/shared-checkpoint hashes, current tested execution hashes, cache completeness and isolated output paths. The entire future run root and every stage output must be absent at startup. No partial-output overwrite, silent resume, old-checkpoint substitution or automatic repair is allowed.

The future wrapper follows A Phase 1 -> A Phase 2 -> A train-role plans -> A Stage 4b -> A evaluation generation, then the corresponding B path. Each phase transition loads same-arm final artifacts with a fresh optimizer. No third arm or extra seed was added.

Future model outputs remain under `outputs/exposure_policy_s42/arm_{A,B}`. Generation keeps modality boundaries separate within batches and checks the original 2500 ordered test IDs per modality. It writes per-modality `predictions/test_code_{modality}.jsonl` and `geom_input_{modality}.jsonl` in the existing N=1 evaluator format. Generating these is not running gate/geometry evaluation; the result status remains `GENERATION_COMPLETE_NEEDS_GATE_AND_GEOMETRY`.

## Verification Completed

- 15 CPU tests PASS, including installed-Trainer budgets/sampler hashes, cache integrity/coverage, first/last batches, target masking, empty/invalid-plan preservation, wrong-arm/step rejection, output-directory refusal, modality batch boundaries and adapter-only save.
- Eight real source/modality CPU encodings, each repeated twice, PASS bitwise latent/point and metadata/evidence equality.
- Original frozen/source/runtime/output guards PASS; the original frozen design/input seal still verifies.
- Bash syntax check and Python compilation PASS.
- Calling real-cache preflight with the full cache absent exits nonzero with `BLOCKED: real shared latent cache is absent/incomplete`. This is the intended barrier, not a passed full-cache preflight.
- No CUDA training path, backward, optimizer step, end-to-end model training, actual Stage 4b predictions or final trained `global_step` has been tested or claimed. No full cache has been generated.

## Operator Commands: Preparation Only

Run these in **WSL Ubuntu / ai_dev**, in order. The first command can use the GPU for frozen-encoder inference only. Neither command starts training.

```bash
cd ~/workspace/MIRAGE/src
bash __DEV_ROOT__/src/training_25k/cag_run_exposure_policy.sh cache --device cuda
```

After that exits successfully:

```bash
bash __DEV_ROOT__/src/training_25k/cag_run_exposure_policy.sh preflight
```

The resource/hash phase may take time before the first encoding progress line; do not interpret that silence as training. Cache progress is printed every 100 entries. Expected success markers are `Shared real cache complete: 83997 entries; no training` and then `Real-cache CPU preflight PASS; no training authorization`.

Expected successful CPU preflight output includes both arms' `75024 -> 4689`, `8000 -> 500`, and `3150 x 3 -> 1182` planned counts. The report is `__EVIDENCE_SOURCE_ROOT__\04\execution\real_cache_preflight.json`; it has not been created successfully yet. Missing/invalid cache never triggers mock replacement or training.

Bring back the outputs after both commands. Only after reviewing the real-cache PASS report and remaining stage-specific gates should the unique formal training command be released. Do not run a historical Stage 3/3b wrapper, the old Stage 4b builder or the original preparation generator as a workaround.
