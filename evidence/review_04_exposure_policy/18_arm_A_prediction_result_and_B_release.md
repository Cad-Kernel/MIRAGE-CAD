> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Arm A Prediction Result And B Manual Start

Date: 2026-10-19. Seed42. Operator-run inference; independent CPU-only completion/input verification.

Later update,2026-10-21: B has also completed and both predictions verify in `19_B_prediction_and_evaluation_release.md`. The B command below has already been run; do not rerun it. A's original machine result/pre-B snapshot are preserved. Next run the separate Windows gate block in record19.

```yaml
Training: COMPLETE_BOTH_ARMS_READ_ONLY_UNCHANGED
Arm A prediction: COMPLETE_VERIFIED_10000
Arm B prediction: NOT_STARTED_MANUAL_START_GUARD_PASS
Gate / geometry: NOT_STARTED
Review/04: OPEN
```

## Completion Audit

A generated10000 test plans and10000 code outputs, with exactly2500 cases per modality. All14 output-file hashes, complete record/startup provenance, same-arm final plan LoRA/prefix/code adapter, original test IDs/order and per-modality exports pass. All geometry inputs match the generated code and original reference point paths. Both training-arm trees, including intermediate checkpoints and train-role predictions, match the pre-inference protected snapshots.

Actual A plan-input audits exactly match the shared CPU preflight. All10000 actual code prompts were independently reconstructed on CPU from query-only evidence and A's generated plans, tokenized with the same original batch8 boundaries/right-truncation/left-padding policy, and compared with recorded prompt/input-ID/mask/latent/point hashes. Evaluation references were checked separately against cached references. No reference-dependent token budget, target-aware training packer, GT fallback, row drop, role swap or program repair was introduced.

The first independent registration attempt was launched outside the data checkout and correctly stopped when a relative STEP-resource path produced different query evidence. Only the CPU registrar's working directory was corrected to `__RUN_SOURCE_ROOT__`, matching the original generation wrapper/main. The complete recheck then passed. No official inference source, model/cache/prediction artifact or scientific policy was changed; A generation did not need rerunning.

The B output directory is absent. The actual B startup guard validates A's complete prediction files/IDs/hashes and passes. No `exec_r04_*` or `geom_r04_*` final evaluator directories were present in the Windows scratch directory at inspection. Neither generation nor this registration invokes those evaluators.

## Per-Modality Diagnostics

These are prediction/plan/input diagnostics, **not** CAD Syntax, Build, STEP-export, Scoreable or geometry results.

| Modality | Rows / Unique IDs | Plan Grammar Valid | Invalid Plan | Empty Plan | Empty Code | P1a Text Changed | Plan-Prompt Crops | Code-Prompt Crops | Max Original Code-Prompt Tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| STEP | 2500 / 2500 | 2414 (96.56%) | 86 | 0 | 0 | 85 | 0 | 49 | 1690 |
| Point | 2500 / 2500 | 2424 (96.96%) | 76 | 0 | 0 | 62 | 0 | 22 | 1714 |
| Text | 2500 / 2500 | 2348 (93.92%) | 152 | 0 | 0 | 101 | 0 | 30 | 1675 |
| Image | 2500 / 2500 | 2392 (95.68%) | 108 | 0 | 0 | 46 | 0 | 42 | 1597 |
| Total | 10000 / 2500 shared source IDs | 9578 (95.78%) | 422 | 0 | 0 | 294 | 0 | 143 | 1714 |

All422 grammar-invalid plans were retained. The143 code-prompt crops follow the frozen whole-prompt1536 cap, not the Stage4b target-preserving training amendment. Complete generated plan text remains in each output record, and every cropped model input was verified. Do not change truncation/evidence rules based on these counts. Four modality copies of each source are not independent training replicates. No downstream CAD-quality conclusion follows from nonempty code or plan grammar validity.

Every modality uses the same test-ID order SHA256:
`d902a194c8b00140258b8001df1e1083082f6478aa098cab574f0ebb188117ab`.

## Paths And Evidence

Code checkout: `__DEV_ROOT__`.
Canonical inference code/wrapper: `__DEV_ROOT__\src\training_25k\cag_exposure_inference.py` and `cag_run_exposure_inference.sh`.
Frozen data/import checkout: `__RUN_SOURCE_ROOT__`.
A prediction root: `__RUN_SOURCE_ROOT__/outputs/exposure_policy_s42/evaluation_v1/arm_A`.
Windows access: `__RUN_SOURCE_ROOT__\outputs\exposure_policy_s42\evaluation_v1\arm_A`.

Preserved outputs include `test_plans.jsonl`, `test_plans.p1a_log.json`, `test_code.jsonl`, `plan_input_audit.jsonl`, `code_input_audit.jsonl`, all four `test_code_{modality}.jsonl`, all four `geom_input_{modality}.jsonl`, `STARTED.json` and `COMPLETE.json`. Source sample/reference paths remain resolvable through the frozen evaluation manifest and source test JSONL. Existing outputs were only read, not rewritten by the audit.

Machine result: `__EVIDENCE_SOURCE_ROOT__\04\execution\exposure_prediction_A_completed_20261019.json`.
CPU registrar: `__EVIDENCE_SOURCE_ROOT__\04\execution\register_exposure_A_prediction_result.py`.
The machine record binds all14 output files, native completion/startup metadata, current sources/dependencies/models, all per-modality diagnostic counts and B's passing startup gate. Full10000-row model-input audits remain hashed at their original output paths.

Inference fingerprint: `191cdcd6571ba58887f9d193a874613823ee71a8bc64e13bec211229e81acba9`.
A completion SHA256: `d01a7a1fabb781da654b30cc7daffdbed737f340878f6356d15d0e3223b6d074`.
A final plan-adapter SHA256: `fe84daa1861646736919c038279f73a08936605f0da8812498b2ce976a388d44`.
A final plan-prefix SHA256: `2f89934a9d310e5aa5fdb099631c2625a20229d2a410a8c33df3c58f81393ba4`.
A final code-adapter SHA256: `d6be94e295ff8373994a0c21e52d420d51feb2a907860e5fe92d4d2e8026003a`.
Official inference source/wrapper SHA256 remain those recorded in record17; no generation code change was made during this completion registration.

## Next Manual Command

Next run **B prediction only** in WSL Ubuntu:

```bash
cd ~/workspace/MIRAGE/src
conda activate ai_dev
bash __DEV_ROOT__/src/training_25k/cag_run_exposure_inference.sh run --arm B --confirm-generation
```

The unchanged command independently revalidates A, both trained finals, source/cache/frozen manifests and output isolation, then uses B's own final plan/prefix/code models for2500 STEP/point/text/image cases each. It does not retrain or run gate/geometry. B additionally protects A's completed prediction tree.

Do not rerun A or the absent-output paired preflight. Do not execute the printed PowerShell evaluator loop yet: follow the agreed sequence, verify B generation first, then run unchanged gate/geometry for both arms and register8-row/delta/paired/failure results. Preserve all partial outputs on any error; no automatic deletion, resume or parameter change. Review/04 remains OPEN until downstream evaluation closes.
