> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Evaluation-Only Preflight And Manual Release

Date: 2026-10-18. Seed42. Training is complete; all trained weights remain read-only. No real model forward, prediction, gate or geometry evaluation was run by the assistant.

Later update,2026-10-19: A's operator-run10000-case prediction is COMPLETE and independently verified; see `18_arm_A_prediction_result_and_B_release.md`. Do not rerun A or the absent-output preflight. The current next step is the B prediction command in record18. The release-time NOT_STARTED states below are preserved as historical snapshots.

```yaml
Training: COMPLETE_BOTH_ARMS_VERIFIED
Inference implementation: COMPLETE
Inference CPU contracts: 35_PASS
Actual test-input CPU preflight: PASS_10000
A prediction: NOT_STARTED_MANUAL_READY
B prediction: NOT_STARTED_GATED_ON_A_GENERATION_COMPLETE
Gate and geometry: NOT_STARTED
Review/04: OPEN
```

## Implementation And Provenance

Canonical checkout: `__DEV_ROOT__`.
Data/import/output checkout: `__RUN_SOURCE_ROOT__`.
Git HEAD inspected: `052392b6c7dc0305d04033b1f56d19b12fffb0a2`. New sources are uncommitted; HEAD alone does not contain or identify this implementation. Preserve the source files and their SHA256 for publication/reproduction.

| Source | SHA256 |
| --- | --- |
| `src/training_25k/cag_exposure_inference.py` | `852abdde1542b16a0c330723a469cb70b995d5dd053ac81425057c561229e02e` |
| `src/training_25k/cag_run_exposure_inference.sh` | `0af2dd8b39e67cdd980e603b37b5f988237e98ac25a8ed59ec6b756bfbf7bde6` |

Inference fingerprint: `191cdcd6571ba58887f9d193a874613823ee71a8bc64e13bec211229e81acba9`.

The new overlay validates the registered native1182-step Stage4b A/B finals through `cag_stage4b_execution.final_stage4b`, retaining the training parent/amendment lineage. Same-arm final Phase2 LoRA and prefix are loaded through the original final validator. Original training scripts, three original execution source files, Stage4b execution/packing modules, frozen manifests and62-file preparation seal are not changed.

The original generic Stage4b final validator cannot accept the amended completion fingerprint. Do not bypass its guards, rewrite completion metadata, or invoke the original full training wrapper. The new wrapper exposes only `preflight` and explicitly confirmed one-arm `run`; no training, resume, limit, retrieval or repair option exists.

## CPU Evidence

- `execution/test_exposure_inference.py` and `exposure_inference_contract_tests_v1.json`:35 PASS. Guards, fixed10000-case order, source/final binding, output isolation, empty/invalid plan retention, reference poisoning, real frozen tokenizer parity, four-token prefix/mask parity, all eight modality exports and CPU stub-only generation. No real language model was instantiated or forwarded. The earlier31-test attempt1 is retained as a historical, earlier-source report.
- `execution/exposure_inference_preflight_v1.json`:actual test-input PASS; model generation is still pending.
- `execution/exposure_inference_preflight_v1.rows.jsonl`:all10000 ordered query-input audits, including prompt/token/mask/latent/point hashes.
- `execution/exposure_inference_preflight_v1.weights.json`:full A/B training-arm snapshots, including saved plan/code weights, intermediate checkpoint files, metadata and train-role predictions. Runtime compares bytes/hash/mtime without chmod or model-file writes.
- `execution/exposure_inference_manual_release_v1.json`:separate manual command registration; `register_exposure_inference_release.py` only verifies/registers, never predicts.

| Actual Preflight Item | Result |
| --- | --- |
| Rows / unique test IDs | 10000 / 2500 |
| STEP / point / text / image rows | 2500 / 2500 / 2500 / 2500 |
| Batches per modality, batch8 | 313 each; last batch4 |
| Test cache byte/tensor entries reverified | 10000 |
| Actual plan-input prompt truncations | 0 |
| Greedy beams / return sequences / do_sample | 1 / 1 / false |
| Input max_length / max_new_tokens | 1536 / 1536 |
| pad_token_id / padding / truncation | 151643 / left / right |
| Point sampling | frozen1024-point FPS cache, seed42; no resampling |
| Point evidence at plan / code stage | off / original query-derived evidence |
| P1a / program repair / retrieval | same P1a / false / false |

Ordered query-audit SHA256: `3e5bcdd48b25e688cf2eb5545ff8d2914de033a820ccf9313c2370ec162a3bca`.
Test-ID order SHA256: `d902a194c8b00140258b8001df1e1083082f6478aa098cab574f0ebb188117ab`.

All10000 cached prompts/evidence were reconstructed from query-only sources and checked against the cache. A/B must match these same preflight token/mask/latent/point hashes at runtime. No encoder/prior inference or point sampling runs again. The full cache index/identity coverage is checked, but this preflight does not claim a new83997-entry tensor scan or a full raw-resource byte scan; the manual run rehashes frozen raw resources before GPU loading.

Actual generated test plans do not exist yet, so actual code-prompt lengths cannot be accepted in advance. Twelve disclosed synthetic probes (empty, invalid and long plan per modality) test the unchanged whole-prompt tokenizer. They are not model predictions. Actual code prompts are audited and saved during generation, using only query evidence and that arm's generated plan.

## Test-Time Policy

Reference-code content/length and reference IR never participate in prompt construction, token budgeting, plan substitution or generation. Cache integrity still reads the existing metadata with references; a query-only object explicitly separates allowed inference fields. References are attached to output records only after code generation for evaluation compatibility.

Do not use the Stage4b target-preserving training packer at inference. Keep the original1536-token whole-prompt right truncation, including its potential to truncate late evidence/output cues for long generated plans. Record all actual prompt truncation counts; do not change the policy after inspecting A/B lengths or results. The complete generated plan is preserved in the prediction record even when the code model receives a truncated prompt.

Base inference remains the original local pinned Qwen revision in BF16, not a new quantization recipe. Each model/prefix is eval-only, requires_grad=false and runs under `torch.inference_mode()`. Seed42, same batch boundaries, same four-prefix-token plan construction, greedy decoding, P1a canonicalization and raw stripped code output follow the original frozen generation behavior. Empty and grammar-invalid plans/code are retained, without GT fallback, filtering or program repair.

## Manual Command: A First

CPU preflight is already PASS; no need to rerun it. In WSL Ubuntu:

```bash
cd ~/workspace/MIRAGE/src
conda activate ai_dev
bash __DEV_ROOT__/src/training_25k/cag_run_exposure_inference.sh run --arm A --confirm-generation
```

This performs only A's four-modality test plan generation and code generation, then exports per-modality evaluator inputs and stops. It does not train, execute CAD or score geometry. Checksums/raw-resource verification occur before GPU progress appears. Models use A's final plan LoRA/prefix and A's final Stage4b adapter, with no checkpoint selection from these evaluation outputs.

After A completes, inspect its completion/IDs/hashes before manually invoking the separately conditional B command:

```bash
cd ~/workspace/MIRAGE/src
conda activate ai_dev
bash __DEV_ROOT__/src/training_25k/cag_run_exposure_inference.sh run --arm B --confirm-generation
```

B validates same-fingerprint A generation, all output hashes and all fixed IDs before loading a model. B additionally snapshots A's completed prediction tree. Both commands compare the full training-arm snapshots before/after generation. GPU loading/generation is not claimed tested by the CPU preflight; any real runtime failure must be inspected without silently changing batch size/precision/decoding or the protocol.

Outputs are isolated from training under:
`__RUN_SOURCE_ROOT__/outputs/exposure_policy_s42/evaluation_v1/arm_A`
and the corresponding `arm_B`.
Windows access starts at `__RUN_SOURCE_ROOT__\outputs\exposure_policy_s42\evaluation_v1`.

Each arm writes `STARTED.json`, `test_plans.jsonl`, `test_plans.p1a_log.json`, `test_code.jsonl`, `plan_input_audit.jsonl`, `code_input_audit.jsonl`, `test_code_{step,point,text,image}.jsonl`, `geom_input_{step,point,text,image}.jsonl` and `COMPLETE.json`. Completion binds14 file hashes,10000 outputs,2500 per modality and the inference/preflight identity. Geometry inputs retain the original reference point path and exactly one candidate, even for empty code.

Any existing/partial arm output directory blocks rerun; no overwrite or implicit resume. On interruption, keep `.building` files and all logs; request inspection, not deletion/retraining. Do not rerun the absent-output paired preflight after prediction starts. No trained weight, saved initialization or cached tensor is to be edited.

## Gate, Geometry And Closure

The completed generation command prints exact Windows PowerShell calls to the unchanged `evaluate_execution.ps1` and `evaluate_geometry_nbest.ps1`, sequentially per modality. Prediction inputs are the new per-modality files; output naming is `MIRAGE-V2/scratch/exec_r04_{modality}_{A|B}` and `geom_r04_{modality}_{A|B}`, avoiding earlier experiment staging directories. These commands are printed for later manual use, not executed by the wrapper or this release.

After both arms' predictions verify, run gate then geometry and preserve every endpoint/log. Register an8-row modality/arm table, a B-minus-A delta table, jointly scoreable paired comparisons and failure patterns. Report Syntax/Execute/Build/Solid-validity/STEP-export, scoreable counts/rates, conditional geometry and unconditional F@1 with distinct denominators; failed cases remain in the fixed2500-case denominator. Do not pool the four modalities as independent training replicates. Do not introduce post-hoc equivalence/materiality thresholds or infer broad curriculum robustness from this one paired seed.

Review/04 remains OPEN until prediction, complete evaluator coverage, result audits and final records all pass. This release authorizes only operator-run inference, not new seeds, retraining, external adaptation, changed weights or automatic evaluation.
