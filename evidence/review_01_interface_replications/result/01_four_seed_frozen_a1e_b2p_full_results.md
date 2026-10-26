> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Four-Seed Frozen A1E/B2P Results

Date: 2026-09-29

Purpose: record all available results from the registered frozen A1E/B2P exact-match comparison for later use in the revised manuscript, appendix, and reviewer responses.

## Reviewer Questions Addressed

This result set is most directly relevant to:

- Reviewer 1, Weakness 1: B1a vs B2-Pred was not sufficiently controlled; update counts, checkpoint selection, interface, and single-seed variance were concerns.
- Reviewer 2, Comments 4-5: the prior B1a/B2-Pred comparison had update/checkpoint mismatch and no training-seed variance estimate.
- Reviewer 4, Validation: the controlled STEP comparison should be qualified and strengthened; current evidence should not overclaim practical editing usefulness.

This experiment addresses the update count, checkpoint rule, decoding configuration, and seed-variance concerns for the STEP A1E/B2P comparison. It does not by itself address qualitative examples, external benchmark competitiveness, semantic edit correctness, or user-study evidence.

## Frozen Protocol

All four seeds used the same protocol:

| Item | Value |
|---|---|
| Modality | STEP |
| A1E training rows | 25,000 |
| B2P training rows | 25,000 |
| Validation rows | 2,500 |
| Evaluation slice | same 500 STEP rows |
| A1E updates | 3125 |
| B2P updates | 3125 |
| Epochs | 1 |
| Batch size | 16 |
| Gradient accumulation | 8 |
| Expected update formula | `ceil(train_rows / grad_accum) * epochs` |
| Checkpoint selection | final |
| Decoding | same settings |
| Repair | false |
| Base model | `Qwen/Qwen2.5-Coder-1.5B` |
| A1E prefix length | 4 |
| Geometry scorer | same evaluator configuration for both arms |

All actuals files passed validation:

```yaml
a_final_artifacts_present: true
a_prediction_complete: true
b_final_artifacts_present: true
b_prediction_complete: true
```

## Seed Status

| Seed | Training | Prediction | Gate | Geometry | Summary JSON | Review record | Status |
|---:|---|---|---|---|---|---|---|
| 1 | COMPLETE | COMPLETE | COMPLETE | COMPLETE | COMPLETE | COMPLETE | CLOSED |
| 2 | COMPLETE | COMPLETE | COMPLETE | COMPLETE | COMPLETE | COMPLETE | CLOSED |
| 3 | COMPLETE | COMPLETE | COMPLETE | COMPLETE | COMPLETE | COMPLETE | CLOSED |
| 4 | COMPLETE | COMPLETE | COMPLETE | COMPLETE | COMPLETE | COMPLETE | CLOSED |

## Training And Prediction Metadata

### A1E

| Seed | Output dir | Prediction rows | Prediction SHA256 | Eval loss sequence | Final normal loss | Zero-prefix loss |
|---:|---|---:|---|---|---:|---:|
| 1 | `outputs/b1_1epoch_step_s1` | 500 | `f2a260c4ad9ccfa863de2a39aa0088cec5f6f7328525464e5f757819f76e745d` | 0.1388, 0.1185, 0.1107, 0.1013, 0.09784, 0.09332, 0.09346 | 0.09343888287842274 | 0.12276154728233814 |
| 2 | `outputs/b1_1epoch_step_s2` | 500 | `27da5691a2953cd63187ddb8ec4c4af21e1cf35517bc69f354ff3b8685d2bd45` | 0.1301, 0.1137, 0.1431, 0.1083, 0.09798, 0.09441, 0.09449 | 0.09448662717938423 | 0.12994160720258952 |
| 3 | `outputs/b1_1epoch_step_s3` | 500 | `0567ae5513f0ac9eb34d1c6ddd144ed7932117912c51a31d30afa9541e50ea05` | 0.1299, 0.1133, 0.1085, 0.0993, 0.09629, 0.09298, 0.09341 | 0.09340079989433289 | 0.12753954612612725 |
| 4 | `outputs/b1_1epoch_step_s4` | 500 | `1f4fb102de36587ebcd25ee4acd8bec422af96286f7ea18e185e220b2c818f8f` | 0.1341, 0.1223, 0.1160, 0.1094, 0.1080, 0.1038, 0.1036 | 0.10364610483944416 | 0.13445708744078874 |

Note: A1E actuals report `shuffled_loss` equal to `normal_loss` because the eval batch size was 1, so the in-batch permutation is vacuous. The actuals file explicitly marks this as not evidence about whether the prefix is read.

### B2P

| Seed | Output dir | Prediction rows | Prediction SHA256 | Eval loss sequence | Final eval loss |
|---:|---|---:|---|---|---:|
| 1 | `outputs/b2_pred_matched_step_s1` | 500 | `b144fc881d54ba71fedb7f3faa4e40b5a1cbbabe1e0482e1dfc3f19381b8b74b` | 0.03582, 0.06298, 0.06089, 0.05498, 0.05947, 0.06472, 0.06167, 0.06211, 0.06550, 0.06788, 0.06860, 0.07110, 0.07071 | 0.07071 |
| 2 | `outputs/b2_pred_matched_step_s2` | 500 | `c15ea2e49467cc0f2978cbb1db8209d21d1a8baca037fb84b8227f11a0d75f2f` | 0.05526, 0.05681, 0.05912, 0.06109, 0.06910, 0.06489, 0.06817, 0.06634, 0.07008, 0.06729, 0.06875, 0.06989, 0.07062 | 0.07062 |
| 3 | `outputs/b2_pred_matched_step_s3` | 500 | `6062f2345c07f61c63d7ef5ff30fae2f52377f1ea84a18fe63b70546223776bf` | 0.05213, 0.06021, 0.05865, 0.06546, 0.06607, 0.06269, 0.06430, 0.06516, 0.06983, 0.07383, 0.07411, 0.07454, 0.07627 | 0.07627 |
| 4 | `outputs/b2_pred_matched_step_s4` | 500 | `bb54941723473a102cdc1b54e81b9862fd8cb42c77d523c7d0ec79e83595c9e3` | 0.04259, 0.05273, 0.05114, 0.06118, 0.06147, 0.06195, 0.06532, 0.06435, 0.06798, 0.06975, 0.07273, 0.07460, 0.07450 | 0.07450 |

## Gate Evaluation Results

All rows are out of 500 predictions per arm per seed. Kernel crash count was 0 for every seed and arm.

| Seed | Arm | Rows | Runtime s | Syntax OK | Syntax OK % | Exec OK | Exec OK % | Build OK | Build OK % | Solid valid | Solid valid % | STEP export | STEP export % | Kernel crashes |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | A1E | 500 | 97.085 | 497 | 99.4 | 330 | 66.0 | 330 | 66.0 | 330 | 66.0 | 325 | 65.0 | 0 |
| 1 | B2P | 500 | 181.149 | 485 | 97.0 | 462 | 92.4 | 462 | 92.4 | 462 | 92.4 | 458 | 91.6 | 0 |
| 2 | A1E | 500 | 88.820 | 475 | 95.0 | 377 | 75.4 | 377 | 75.4 | 377 | 75.4 | 374 | 74.8 | 0 |
| 2 | B2P | 500 | 183.613 | 480 | 96.0 | 469 | 93.8 | 469 | 93.8 | 469 | 93.8 | 465 | 93.0 | 0 |
| 3 | A1E | 500 | 63.134 | 469 | 93.8 | 362 | 72.4 | 362 | 72.4 | 362 | 72.4 | 359 | 71.8 | 0 |
| 3 | B2P | 500 | 175.336 | 476 | 95.2 | 432 | 86.4 | 432 | 86.4 | 432 | 86.4 | 429 | 85.8 | 0 |
| 4 | A1E | 500 | 152.972 | 484 | 96.8 | 407 | 81.4 | 407 | 81.4 | 407 | 81.4 | 403 | 80.6 | 0 |
| 4 | B2P | 500 | 192.171 | 482 | 96.4 | 450 | 90.0 | 450 | 90.0 | 450 | 90.0 | 446 | 89.2 | 0 |

## Geometry Results

All rows are out of 500 predictions per arm per seed. `Scored` is the point-cloud scored count.

| Seed | Arm | Rows | Syntax OK | Exec OK | Build OK | Solid valid | STEP export | Scored | Scored % | Median CD | Median F@1 | Unconditional mean F@1 | Unconditional median F@1 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | A1E | 500 | 497 | 330 | 330 | 330 | 325 | 323 | 64.6 | 2.7445 | 19.87% | 12.54% | 12.23% |
| 1 | B2P | 500 | 485 | 462 | 462 | 462 | 458 | 456 | 91.2 | 2.1763 | 20.63% | 19.33% | 19.65% |
| 2 | A1E | 500 | 475 | 377 | 377 | 377 | 374 | 370 | 74.0 | 2.4358 | 20.17% | 15.23% | 16.45% |
| 2 | B2P | 500 | 480 | 469 | 469 | 469 | 465 | 462 | 92.4 | 2.2811 | 19.90% | 19.10% | 19.40% |
| 3 | A1E | 500 | 469 | 362 | 362 | 362 | 359 | 352 | 70.4 | 2.4449 | 21.12% | 14.95% | 16.77% |
| 3 | B2P | 500 | 476 | 432 | 432 | 432 | 429 | 427 | 85.4 | 2.3049 | 20.41% | 17.93% | 18.77% |
| 4 | A1E | 500 | 484 | 407 | 407 | 407 | 403 | 402 | 80.4 | 2.3916 | 20.23% | 16.30% | 18.16% |
| 4 | B2P | 500 | 482 | 450 | 450 | 450 | 446 | 445 | 89.0 | 2.1594 | 20.31% | 18.72% | 19.19% |

## Paired Geometry Results

Paired metrics are computed only on the jointly scoreable subset within each seed. `A1E closer` counts pairs where A1E had lower CD. `B2P closer` is `non_tied_pairs - A1E_cd_wins`.

| Seed | Joint n | A1E paired CD | B2P paired CD | B2P-A1E CD | A1E paired F@1 | B2P paired F@1 | B2P-A1E F@1 | A1E closer | B2P closer | Non-tied pairs | Sign-test p |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 301 | 2.7445 | 2.2408 | -0.5037 | 19.97% | 21.97% | +2.00 pp | 105 | 196 | 301 | 1.732e-07 |
| 2 | 351 | 2.4463 | 2.3380 | -0.1083 | 20.20% | 21.00% | +0.80 pp | 142 | 209 | 351 | 0.0004117 |
| 3 | 328 | 2.4032 | 2.3118 | -0.0914 | 21.24% | 21.61% | +0.36 pp | 145 | 183 | 328 | 0.04089 |
| 4 | 372 | 2.3680 | 2.2631 | -0.1049 | 20.31% | 20.68% | +0.37 pp | 174 | 198 | 372 | 0.2330 |

## Per-Seed Headline Deltas

Positive coverage and F@1 deltas favor B2P. Negative CD deltas favor B2P.

| Seed | Build delta | STEP export delta | Scored delta | Scored % delta | Median CD delta | Median F@1 delta | Unconditional mean F@1 delta | Paired CD delta | Paired F@1 delta |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | +26.4 pp | +26.6 pp | +133 | +26.6 pp | -0.5682 | +0.76 pp | +6.78 pp | -0.5037 | +2.00 pp |
| 2 | +18.4 pp | +18.2 pp | +92 | +18.4 pp | -0.1547 | -0.27 pp | +3.87 pp | -0.1083 | +0.80 pp |
| 3 | +14.0 pp | +14.0 pp | +75 | +15.0 pp | -0.1400 | -0.71 pp | +2.98 pp | -0.0914 | +0.36 pp |
| 4 | +8.6 pp | +8.6 pp | +43 | +8.6 pp | -0.2322 | +0.08 pp | +2.41 pp | -0.1049 | +0.37 pp |

## Four-Seed Totals

Totals are over 2000 predictions per arm.

| Arm | Total n | Syntax OK | Exec OK | Build OK | Solid valid | STEP export | Scored |
|---|---:|---:|---:|---:|---:|---:|---:|
| A1E | 2000 | 1925 | 1476 | 1476 | 1476 | 1461 | 1447 |
| B2P | 2000 | 1923 | 1813 | 1813 | 1813 | 1798 | 1790 |

Total-rate view:

| Arm | Syntax OK % | Exec OK % | Build OK % | Solid valid % | STEP export % | Scored % |
|---|---:|---:|---:|---:|---:|---:|
| A1E | 96.25% | 73.80% | 73.80% | 73.80% | 73.05% | 72.35% |
| B2P | 96.15% | 90.65% | 90.65% | 90.65% | 89.90% | 89.50% |
| B2P-A1E | -0.10 pp | +16.85 pp | +16.85 pp | +16.85 pp | +16.85 pp | +17.15 pp |

## Four-Seed Mean, SD, Min, Max

### A1E

| Metric | Mean | SD | Min | Max |
|---|---:|---:|---:|---:|
| Build OK % | 73.80 | 6.41 | 66.00 | 81.40 |
| STEP export % | 73.05 | 6.49 | 65.00 | 80.60 |
| Scored % | 72.35 | 6.62 | 64.60 | 80.40 |
| Median CD | 2.5042 | 0.1619 | 2.3916 | 2.7445 |
| Median F@1 | 20.35% | 0.54 pp | 19.87% | 21.12% |
| Unconditional mean F@1 | 14.76% | 1.59 pp | 12.54% | 16.30% |
| Unconditional median F@1 | 15.90% | 2.56 pp | 12.23% | 18.16% |

### B2P

| Metric | Mean | SD | Min | Max |
|---|---:|---:|---:|---:|
| Build OK % | 90.65 | 3.24 | 86.40 | 93.80 |
| STEP export % | 89.90 | 3.15 | 85.80 | 93.00 |
| Scored % | 89.50 | 3.07 | 85.40 | 92.40 |
| Median CD | 2.2304 | 0.0732 | 2.1594 | 2.3049 |
| Median F@1 | 20.31% | 0.31 pp | 19.90% | 20.63% |
| Unconditional mean F@1 | 18.77% | 0.61 pp | 17.93% | 19.33% |
| Unconditional median F@1 | 19.25% | 0.37 pp | 18.77% | 19.65% |

### B2P-A1E Delta

| Metric | Mean delta | SD | Min | Max |
|---|---:|---:|---:|---:|
| Build OK % | +16.85 pp | 7.52 pp | +8.60 pp | +26.40 pp |
| STEP export % | +16.85 pp | 7.60 pp | +8.60 pp | +26.60 pp |
| Scored % | +17.15 pp | 7.50 pp | +8.60 pp | +26.60 pp |
| Median CD | -0.2738 | 0.2004 | -0.5682 | -0.1400 |
| Median F@1 | -0.03 pp | 0.62 pp | -0.71 pp | +0.76 pp |
| Unconditional mean F@1 | +4.01 pp | 1.94 pp | +2.41 pp | +6.78 pp |
| Unconditional median F@1 | +3.35 pp | 2.82 pp | +1.03 pp | +7.42 pp |

## Paired Four-Seed Aggregate

This aggregate sums the jointly scoreable paired comparisons across the four seeds.

| Metric | Value |
|---|---:|
| Total jointly scoreable pairs | 1352 |
| A1E CD wins | 566 |
| B2P CD wins | 786 |
| B2P CD win rate | 58.14% |
| Exact two-sided sign-test p over pooled pairs | 2.390e-09 |
| Mean paired A1E CD | 2.4905 |
| Mean paired B2P CD | 2.2884 |
| Mean paired CD delta, B2P-A1E | -0.2021 |
| SD of paired CD delta across seeds | 0.2012 |
| Mean paired A1E F@1 | 20.43% |
| Mean paired B2P F@1 | 21.31% |
| Mean paired F@1 delta, B2P-A1E | +0.88 pp |
| SD of paired F@1 delta across seeds | 0.77 pp |

Important caution: the pooled sign-test treats all paired cases as exchangeable and does not replace a model-level hierarchical analysis. It is useful as a descriptive paired-case summary, while the four-seed table is the more direct answer to the reviewer concern about training-run variability.

## Provenance Hashes

Execution and geometry row SHA256 values from the summary JSON files.

| Seed | Arm | Execution rows SHA256 | Geometry rows SHA256 |
|---:|---|---|---|
| 1 | A1E | `d379160b389efa4b7ad250689cab7b7e3d2929675951cb57102a01f314305181` | `e7d89b70996f949e7ba1931f572ff56a7b0c85b85d1948775bf8942589ccde52` |
| 1 | B2P | `8224452657c9a927b04bfea66e41ca93a65e4bcb8be702667bf5f24a15a19a99` | `1eaf5db6a3cb363c46d497a7c5fe5337b7e890871061ac4ae7d9dc2d43eeab7d` |
| 2 | A1E | `fd70e9f48bca73c64a03361a260afe1e911eddb546708648375c945f163a0cc7` | `3496ee7433737f390fcf239a8ecfe1695928da6ddf0baa70da23a79b7b810aea` |
| 2 | B2P | `550a89ad911cc56423b6c30c46ca84a1cd826c768ae3bb4d87ed111d519f1b06` | `8b027f23f320707ca7814f744c6ce632f830b666055d796b7442726ad92e3e79` |
| 3 | A1E | `aaba9084922871f243bcb80802b20f0f3b54449b2c30ba099841c3aa0fa78e66` | `fe06225cc22a64b18d627041783a77efa9c9e2df97134a8856105f1f74971701` |
| 3 | B2P | `2039bd39d27ab36306fc7f846b83536eec8e332a5c94aad6917d42ec2b63f379` | `a532fe05dc0e8e34f6410c7b719c0e00f9f2bfdadb0e440fe1286b4a36db8249` |
| 4 | A1E | `6d6bb120ab017acdac5f052655e1ca342bc2cb946fb378c40074257be745ff82` | `f5a73caca23c0582274c288735e9b74db2d212cb7cf1530ad0e3749fae933d4d` |
| 4 | B2P | `b24639342402bc5857c50343246c2866f6debb6c383a7cb29185673f5b39875b` | `1a1cd6c89813bfa6e38fb15b671330d747b6b73e3e1366fa33eefaf60ed9e55d` |

## Source Files

Per-seed summary JSON:

```text
__DEV_ROOT__\scratch\cag_seed_1_a1e_b2p_eval_summary.json
__DEV_ROOT__\scratch\cag_seed_2_a1e_b2p_eval_summary.json
__DEV_ROOT__\scratch\cag_seed_3_a1e_b2p_eval_summary.json
__DEV_ROOT__\scratch\cag_seed_4_a1e_b2p_eval_summary.json
```

Per-seed review records:

```text
__EVIDENCE_SOURCE_ROOT__\01\seed 1\01_seed1_closed_record.md
__EVIDENCE_SOURCE_ROOT__\01\seed 2\01_seed2_closed_record.md
__EVIDENCE_SOURCE_ROOT__\01\seed 3\01_seed3_closed_record.md
__EVIDENCE_SOURCE_ROOT__\01\seed 4\01_seed4_closed_record.md
```

Actuals and prediction files in WSL:

```text
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/cag_seed_1_actuals.json
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/cag_seed_2_actuals.json
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/cag_seed_3_actuals.json
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/cag_seed_4_actuals.json
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/gen_code_step_A1E_s1.jsonl
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/gen_code_step_B2P_s1.jsonl
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/gen_code_step_A1E_s2.jsonl
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/gen_code_step_B2P_s2.jsonl
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/gen_code_step_A1E_s3.jsonl
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/gen_code_step_B2P_s3.jsonl
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/gen_code_step_A1E_s4.jsonl
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/gen_code_step_B2P_s4.jsonl
```

## Conservative Interpretation

The strongest and most stable result is coverage:

- B2P improves Build by +8.6 to +26.4 percentage points in every seed.
- B2P improves STEP export by +8.6 to +26.6 percentage points in every seed.
- B2P improves scored-output coverage by +8.6 to +26.6 percentage points in every seed.
- Across all 2000 predictions per arm, B2P has 1813 Build successes vs 1476 for A1E, and 1798 STEP exports vs 1461 for A1E.

Geometry:

- On the full scored sets, B2P has lower median CD in every seed.
- Full-set median F@1 is mixed because the scoreable set composition changes by arm: B2P is higher in seeds 1 and 4, lower in seeds 2 and 3.
- Unconditional mean F@1 is higher for B2P in every seed, reflecting the much higher scoreability/coverage.
- On the jointly scoreable paired subset, B2P has lower median CD and higher median F@1 in every seed.
- Seed-level paired sign tests are significant in seeds 1-3 and not significant in seed 4.

Reviewer-facing sentence candidate:

> We repeated the controlled STEP A1E/B2P comparison across four random seeds using matched training rows, update counts, final-checkpoint selection, decoding settings, and the same 500-row evaluation slice. B2P consistently achieved higher executable coverage than A1E across all seeds, with mean Build/STEP-export rates of 90.65%/89.90% versus 73.80%/73.05%. On the jointly scoreable subset, B2P also had better median CD and F@1 in each seed, although the seed-level sign test was not significant for seed 4.

Do not use this result to claim:

- that textual planning is universally better than continuous conditioning for all modalities;
- that the plan interface improves human editing or inspection;
- that external point-cloud competitiveness is solved;
- that STEP input is topology-aware B-Rep encoding rather than the reported global-descriptor pathway.

Interpretation and rebuttal-position record:

```text
__EVIDENCE_SOURCE_ROOT__\01\result\02_interpretation_and_rebuttal_position.md
```
