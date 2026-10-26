> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Eight-Group Gate Results And Geometry Release

Later update, 2026-10-22: all8 geometry groups are now complete and verified,2500 ordered rows/targets each. Review/04 is CLOSED; see `21_final_results_and_closed_summary.md` and `result/`. The state/commands below preserve the historical gate-release snapshot and are not instructions to rerun evaluation. The immutable gate machine record remains unchanged.

Date: 2026-10-21. Seed42; one paired exposure-policy diagnostic. Gate was manually run by the user. Registration performed no CAD execution, model forward, training or generation.

```yaml
Training: COMPLETE_BOTH_ARMS_READ_ONLY
Prediction: COMPLETE_BOTH_ARMS_VERIFIED_UNCHANGED
Gate: COMPLETE_VERIFIED_ALL8_GROUPS_2500_ROWS_EACH
Geometry: NOT_STARTED
Review/04: OPEN_GEOMETRY_PENDING
```

## Gate Integrity

All8 groups contain exactly2500 unique frozen IDs in the same order. Native counts/rates/crash counts were independently recomputed from every row. Monotonic gate flags and first-failure categories pass. Every local Windows staged `input.jsonl` is byte-identical to the corresponding frozen prediction; local/exported row and summary hashes match. Staged evaluator code and current PS/Python sources match the pre-evaluation release hashes. All original model/source/seal checks pass; both full training trees and the paired prediction-tree snapshot remain unchanged.

No geometry result directories existed at inspection. Scoreable/CD/F@1 are therefore still pending; Build/export must not be substituted for geometry coverage or fidelity.

Machine record: `__EVIDENCE_SOURCE_ROOT__\04\execution\exposure_gate_completed_20261021.json`.
Registrar: `__EVIDENCE_SOURCE_ROOT__\04\execution\register_exposure_gate_results.py`.
The machine record preserves every native summary field, exact error-frequency table, all failure IDs by first stage, complete paired gate tables, file/input/source hashes and retained resume-log lines. Raw2500-row files and full logs remain at their hashed scratch paths, not rewritten by registration.

## All Native Results

Each count has denominator2500. Runtime is native summary seconds, not training/GPU time or necessarily total wall time across retries. Retained last-attempt logs contain no resume messages; crash counts are zero in all groups.

| Modality | Arm | Syntax Count (%) | Execute Count (%) | Build Count (%) | Solid Valid Count (%) | STEP Export Count (%) | Runtime Seconds | Kernel Crashes |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| STEP | A | 2432 (97.28) | 1524 (60.96) | 1524 (60.96) | 1524 (60.96) | 1502 (60.08) | 424.516 | 0 |
| STEP | B | 2087 (83.48) | 1447 (57.88) | 1447 (57.88) | 1447 (57.88) | 1384 (55.36) | 851.186 | 0 |
| Point | A | 2436 (97.44) | 1315 (52.60) | 1315 (52.60) | 1315 (52.60) | 1294 (51.76) | 202.480 | 0 |
| Point | B | 2064 (82.56) | 1358 (54.32) | 1358 (54.32) | 1358 (54.32) | 1256 (50.24) | 686.930 | 0 |
| Text | A | 2459 (98.36) | 1261 (50.44) | 1261 (50.44) | 1261 (50.44) | 1245 (49.80) | 252.055 | 0 |
| Text | B | 2124 (84.96) | 1348 (53.92) | 1348 (53.92) | 1348 (53.92) | 1295 (51.80) | 570.902 | 0 |
| Image | A | 2426 (97.04) | 1352 (54.08) | 1352 (54.08) | 1352 (54.08) | 1321 (52.84) | 166.269 | 0 |
| Image | B | 2119 (84.76) | 1421 (56.84) | 1421 (56.84) | 1421 (56.84) | 1337 (53.48) | 1000.127 | 0 |

## B Minus A

All entries are percentage-point differences, not relative percent gains.

| Modality | Syntax | Execute | Build | Solid Valid | STEP Export |
| --- | ---: | ---: | ---: | ---: | ---: |
| STEP | -13.80 | -3.08 | -3.08 | -3.08 | -4.72 |
| Point | -14.88 | +1.72 | +1.72 | +1.72 | -1.52 |
| Text | -13.40 | +3.48 | +3.48 | +3.48 | +2.00 |
| Image | -12.28 | +2.76 | +2.76 | +2.76 | +0.64 |

Equal-modality descriptive means are A/B Syntax97.53%/83.94%, Execute/Build/Solid54.52%/55.74%, and STEP export53.62%/52.72%. Thus the descriptive mean Build delta is+1.22pp, but export delta is-0.90pp. Do not headline an overall improvement or treat these four modality copies as training-seed replicates. Per-modality tables are primary; no multi-seed SD is estimated here.

## First Failure Stage

Counts are mutually exclusive, including final success; each row sums to2500. There were no build-stage, validity-stage or kernel-crash failures in these gate runs. Exact messages and all failure sample IDs are retained in the machine record and native row files, not replaced by this coarse table.

| Modality | Arm | Syntax Failure | Execution Failure After Syntax | Build Failure | Validity Failure | STEP Export Failure | All Gates Pass |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| STEP | A | 68 | 908 | 0 | 0 | 22 | 1502 |
| STEP | B | 413 | 640 | 0 | 0 | 63 | 1384 |
| Point | A | 64 | 1121 | 0 | 0 | 21 | 1294 |
| Point | B | 436 | 706 | 0 | 0 | 102 | 1256 |
| Text | A | 41 | 1198 | 0 | 0 | 16 | 1245 |
| Text | B | 376 | 776 | 0 | 0 | 53 | 1295 |
| Image | A | 74 | 1074 | 0 | 0 | 31 | 1321 |
| Image | B | 381 | 698 | 0 | 0 | 84 | 1337 |

## Paired Gate Tables

Every table uses the same2500 source IDs within its modality. Execute and Solid-valid paired tables equal Build exactly in these runs; their full copies are retained in the machine record. These are descriptive case tables, not seed-level inference or geometry comparisons.

| Modality | Endpoint | Both Pass | A Only | B Only | Both Fail |
| --- | --- | ---: | ---: | ---: | ---: |
| STEP | Syntax | 2042 | 390 | 45 | 23 |
| STEP | Build | 1036 | 488 | 411 | 565 |
| STEP | STEP export | 977 | 525 | 407 | 591 |
| Point | Syntax | 2018 | 418 | 46 | 18 |
| Point | Build | 876 | 439 | 482 | 703 |
| Point | STEP export | 779 | 515 | 477 | 729 |
| Text | Syntax | 2087 | 372 | 37 | 4 |
| Text | Build | 846 | 415 | 502 | 737 |
| Text | STEP export | 811 | 434 | 484 | 771 |
| Image | Syntax | 2047 | 379 | 72 | 2 |
| Image | Build | 888 | 464 | 533 | 615 |
| Image | STEP export | 819 | 502 | 518 | 661 |

## Native Python And Audit Correction

All CLI logs report embedded Python3.11.11. WSL auditing uses3.12. The first auxiliary default-AST comparison stopped on B/STEP `flluma_0090798`: a nested-quote f-string is accepted by3.12 but rejected by the deployed3.11 parser. The3.12 `feature_version` option did not fully reproduce this f-string restriction, as the first12-test report correctly exposed.

Rather than change any native result or evaluator, independent syntax parsing was run through the installed standalone Python3.11.11 at `__FLLUMA_ROOT__\build\Desktop_Qt_6_8_3_MSVC2022_64bit-Release\vcpkg_installed\x64-windows\tools\python3\python.exe`. It only called `ast.parse`, never executed generated code, loaded Flluma or ran CAD. All20000 syntax outcomes match the gate rows. Only this one B/STEP case differs from the WSL3.12 default parser; it does not explain the broad syntax gap. Keep the actual native evaluator unchanged for geometry and all comparisons.

Evidence: `execution/audit_gate_native_syntax.py`, `exposure_gate_native311_syntax_20261021.json`, `test_exposure_gate_audit.py` and current source-bound `exposure_gate_audit_tests_20261021_v2.json` (12 PASS). The initial failed test report is retained, not overwritten. Windows CLI logs are UTF16 and were decoded accordingly; original log bytes/hashes are preserved.

## Interpretation

Gate already shows a modality-dependent trade-off in this fixed seed, not uniform superiority. B is lower on STEP Build/export, higher on Point/Text/Image Build, but lower on Point export; syntax is lower in all four modalities. This supports reporting the exposure-policy-dependent modality profile, not an architecture-only or pure-order-only claim. Do not infer a fidelity winner, equivalence or broad curriculum robustness before geometry. No new seed, training, repair/filtering or post-hoc effect margin is introduced.

## Paths And Next Manual Command

Code checkout: `__DEV_ROOT__`.
Frozen prediction roots: `__RUN_SOURCE_ROOT__/outputs/exposure_policy_s42/evaluation_v1/arm_A` and corresponding `arm_B`.
Native gate outputs: `__DEV_ROOT__\scratch\exec_r04_{step|point|text|image}_{A|B}`; each contains `execution_rows.jsonl`, `execution_summary.json`, `cli.log`.
Local staging: `__TEMP_RUN_ROOT__\exec_eval\exec_r04_{modality}_{arm}`; staged inputs/scripts/results were hash-checked against the permanent predictions/evaluator/scratch outputs.
Prediction immutability authority remains `execution/exposure_predictions_read_only_20261021.json`. Gate/evaluator/input records are all bound in `execution/exposure_gate_completed_20261021.json`.

Gate is complete; do not rerun it. Next run the following whole block in **Windows PowerShell**, not WSL. It performs8 sequential geometry evaluations with the unchanged evaluator and full2500-row inputs, not only gate-successful cases:

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

Keep every row/log, including execution failures, missing/nonfinite geometry and outliers. On interruption/error preserve state and inspect; do not alter model outputs or switch parsers/evaluators. After all8 geometry groups complete, verify2500 IDs/rows per group, recheck immutability, distinguish gate vs geometry-run coverage, compute conditional/paired/unconditional geometry and register the8-row primary table/deltas/failure analysis. Review/04 remains OPEN until final evaluation/registration completes.
