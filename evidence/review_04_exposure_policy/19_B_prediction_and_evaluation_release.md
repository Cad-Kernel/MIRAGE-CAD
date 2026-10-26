> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Paired Prediction Completion And Evaluation Release

Date: 2026-10-21. Seed42. Both prediction runs were operated by the user. The assistant performed CPU-only verification, not training, real-model generation or CAD evaluation.

Later update: all8 user-run gate evaluations now verify COMPLETE. See `20_gate_results_and_geometry_release.md` for full results, native-parser audit and the current geometry command. The gate block below has already been run; do not rerun it. Prediction-release snapshots below remain historical.

```yaml
Training: COMPLETE_BOTH_ARMS_READ_ONLY_UNCHANGED
Arm A prediction: COMPLETE_VERIFIED_10000_UNCHANGED_AFTER_B
Arm B prediction: COMPLETE_VERIFIED_10000
Prediction: COMPLETE_BOTH_ARMS
Gate / geometry: NOT_STARTED
Review/04: OPEN_EVALUATION_PENDING
```

## Verified Completion

Each arm has10000 plans/code outputs,2500 STEP/point/text/image cases in the identical frozen order. Both14-file inventories, completion/startup lineage, same-arm final Phase2 adapter/prefix and final1182-step Stage4b code adapter pass verification. All modality exports and geometry inputs match the full predictions and original target point paths; no row was removed/substituted.

A's previously registered completion and14 output files remain byte/hash-identical after B. Both full training-arm snapshots (weights, intermediate checkpoints, metadata, train-role predictions) remain unchanged. The unchanged B wrapper enforced a full A-prediction-tree runtime snapshot; independent retrospective A verification binds its prior registered completion/file hashes. A fresh full paired prediction-tree inventory is saved for post-evaluation checks.

Both plan-input audit lists match the shared10000-case preflight exactly. B's10000 actual code prompts were independently reconstructed on CPU using only query evidence and generated plans; all tokenizer input/mask/prompt/latent/point hashes match. References were checked separately as output metadata, never for input construction/token budgets. A's analogous CPU audit is preserved in record18 and unchanged output hashes. No generation/model/source/decoder policy changed during registration.

No final `exec_r04_*` or `geom_r04_*` directories were present in Windows scratch at inspection. Generation and this audit did not execute CAD or score geometry. All frozen IDs, greedy decoding, point cache/FPS seed42, P1a and program repair=false remain unchanged.

## Complete Prediction Diagnostics

These are plan/prompt diagnostics, not CAD Syntax/Build/STEP-export/Scoreable/geometry results.

| Modality | Arm | Rows / Unique IDs | Plan Grammar Valid | Invalid Plan | Empty Plan / Code | P1a Text Changed | Plan-Prompt Crops | Code-Prompt Crops | Max Original Code-Prompt Tokens |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| STEP | A | 2500 / 2500 | 2414 (96.56%) | 86 | 0 / 0 | 85 | 0 | 49 | 1690 |
| STEP | B | 2500 / 2500 | 1893 (75.72%) | 607 | 0 / 0 | 33 | 0 | 381 | 1691 |
| Point | A | 2500 / 2500 | 2424 (96.96%) | 76 | 0 / 0 | 62 | 0 | 22 | 1714 |
| Point | B | 2500 / 2500 | 1787 (71.48%) | 713 | 0 / 0 | 23 | 0 | 397 | 1714 |
| Text | A | 2500 / 2500 | 2348 (93.92%) | 152 | 0 / 0 | 101 | 0 | 30 | 1675 |
| Text | B | 2500 / 2500 | 1930 (77.20%) | 570 | 0 / 0 | 7 | 0 | 331 | 1672 |
| Image | A | 2500 / 2500 | 2392 (95.68%) | 108 | 0 / 0 | 46 | 0 | 42 | 1597 |
| Image | B | 2500 / 2500 | 1864 (74.56%) | 636 | 0 / 0 | 13 | 0 | 363 | 1585 |
| All modalities | A | 10000 / 2500 shared IDs | 9578 (95.78%) | 422 | 0 / 0 | 294 | 0 | 143 | 1714 |
| All modalities | B | 10000 / 2500 shared IDs | 7474 (74.74%) | 2526 | 0 / 0 | 76 | 0 | 1472 | 1714 |

B has lower plan-grammar validity and more code-prompt crops in every modality. This agrees directionally with the earlier train-role diagnostic but does not establish downstream CAD coverage. Shared teacher-forced GT-plan validation loss does not measure the same behavior as free generation with predicted plans. Do not infer Build/geometry superiority, tune thresholds, repair/drop plans or retrain from these observations.

All2526 invalid B plans and1472 cropped B code prompts remain present. Crops follow the frozen whole-prompt1536 policy, not the target-preserving training packer; complete generated plans remain archived. Counts need not match A. The20000 arm/modality evaluation cases represent one paired seed and2500 shared source IDs, not20000 independent training replicates.

## Evidence And Paths

Code checkout: `__DEV_ROOT__`.
Frozen data/import/output checkout: `__RUN_SOURCE_ROOT__`.
Generation code/wrapper: `MIRAGE-V2/src/training_25k/cag_exposure_inference.py` and `cag_run_exposure_inference.sh`, unchanged at the source hashes/fingerprint in record17.
Prediction roots: `__RUN_SOURCE_ROOT__/outputs/exposure_policy_s42/evaluation_v1/arm_A` and the corresponding `arm_B`.
Windows root: `__RUN_SOURCE_ROOT__\outputs\exposure_policy_s42\evaluation_v1`.
Each arm retains full plans/code, four `test_code_{modality}.jsonl`, four `geom_input_{modality}.jsonl`, full input audits, P1a log and startup/completion records. Nothing was rewritten by this audit.

Machine result: `__EVIDENCE_SOURCE_ROOT__\04\execution\exposure_prediction_B_and_paired_completed_20261021.json`.
Prediction immutability inventory: `__EVIDENCE_SOURCE_ROOT__\04\execution\exposure_predictions_read_only_20261021.json`.
CPU registrar: `__EVIDENCE_SOURCE_ROOT__\04\execution\register_exposure_B_prediction_result.py`.
Prior A result remains unchanged at `execution/exposure_prediction_A_completed_20261019.json`.
The paired machine result preserves both full summaries, all completion/file/model/source records and current intended evaluator-source hashes. Evaluator files were not run or changed; recording current source hashes does not demonstrate historical binary identity.

Inference fingerprint: `191cdcd6571ba58887f9d193a874613823ee71a8bc64e13bec211229e81acba9`.
A completion SHA256: `d01a7a1fabb781da654b30cc7daffdbed737f340878f6356d15d0e3223b6d074`.
B completion SHA256: `fd55038a95f53aacd391b2d329c70ac9261f40dc78369f8e94afb23d570e95d9`.
B plan-adapter SHA256: `4ccde29dd4b6fd8267fc8973994f1936554b363d4432ad6e75720e9dccf3735d`.
B plan-prefix SHA256: `0e40e027ad1f77fec6c1fd2e17cc5a73a32a6503f8fc1af8fbf64572dad44a66`.
B code-adapter SHA256: `66d1bd91a281928fd857280d6dae1ae91e676da484e1f0c10d0b42f28819e856`.
Every arm/modality test-ID order SHA256: `d902a194c8b00140258b8001df1e1083082f6478aa098cab574f0ebb188117ab`.

## Next: Gate In Windows PowerShell

No more Bash training/prediction is needed. Run this whole block in **Windows PowerShell**, not WSL. It makes8 sequential gate calls with full2500-case inputs and distinct output/staging names:

```powershell
$ErrorActionPreference = "Stop"
$Root = "__RUN_SOURCE_ROOT__"
$Scripts = "__DEV_ROOT__\src\scripts"
$Scratch = "__DEV_ROOT__\scratch"
foreach ($arm in @("A", "B")) {
  $Pred = "$Root\outputs\exposure_policy_s42\evaluation_v1\arm_$arm"
  foreach ($m in @("step", "point", "text", "image")) {
    & "$Scripts\evaluate_execution.ps1" `
      -InputJsonl "$Pred\test_code_$m.jsonl" `
      -OutputDir "$Scratch\exec_r04_${m}_${arm}" `
      -CodeField prediction
  }
}
```

Inspect all8 gate outputs and2500-case counts before geometry. Do not modify predictions or drop failures if an evaluator stops; preserve logs and inspect the cause.

## Then: Geometry

After gate completion is inspected, run this separate block for8 sequential geometry evaluations. Do not run it concurrently with gate:

```powershell
$ErrorActionPreference = "Stop"
$Root = "__RUN_SOURCE_ROOT__"
$Scripts = "__DEV_ROOT__\src\scripts"
$Scratch = "__DEV_ROOT__\scratch"
foreach ($arm in @("A", "B")) {
  $Pred = "$Root\outputs\exposure_policy_s42\evaluation_v1\arm_$arm"
  foreach ($m in @("step", "point", "text", "image")) {
    & "$Scripts\evaluate_geometry_nbest.ps1" `
      -InputJsonl "$Pred\geom_input_$m.jsonl" `
      -OutputDir "$Scratch\geom_r04_${m}_${arm}"
  }
}
```

Preserve all evaluator rows/logs, failures and outliers. Final registration must verify2500 rows per arm/modality, retain every Syntax/Execute/Build/Solid-validity/STEP-export/Scoreable and geometry endpoint, separate conditional/paired/unconditional denominators, and produce the8-row table plus B-minus-A/paired/failure summaries. No new seeds/training, post-hoc equivalence bounds or architecture-only attribution. Review/04 remains OPEN until downstream records are complete.
