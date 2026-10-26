> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# 13 -- Seed 3 Closed Record

Date: 2026-10-13

## Status

```yaml
Experiment: Review/03 B0 vs B2 full-stack multi-seed replication
Seed: 3
Training: COMPLETE
Prediction: COMPLETE
Gate evaluation: COMPLETE
Geometry scoring: COMPLETE
Seed status: CLOSED
```

Seed 3 is now complete. Do not edit its protocol, sample slice, checkpoint rule, decoding, or repair policy after this point.

## Source And Output Paths

```yaml
Windows source checkout:
  __DEV_ROOT__\src

WSL execution checkout:
  __RUN_SOURCE_ROOT__

Review package:
  __EVIDENCE_SOURCE_ROOT__\03

B0 prediction:
  outputs/b0_b2_fullstack_s3/predictions/gen_step_B0_s3.jsonl

B2 prediction:
  outputs/b0_b2_fullstack_s3/predictions/gen_step_B2_s3.jsonl

B0 gate:
  __DEV_ROOT__\scratch\exec_b0b2_step_B0_s3

B2 gate:
  __DEV_ROOT__\scratch\exec_b0b2_step_B2_s3

B0 geometry:
  __DEV_ROOT__\scratch\geom_b0b2_step_B0_s3

B2 geometry:
  __DEV_ROOT__\scratch\geom_b0b2_step_B2_s3
```

Result file hashes:

```yaml
B0 execution_summary.json:
  sha256: fb8bcd2689fb3fa8824eda310359cec77c91ae0525f986c86e06c89e8beb477c

B2 execution_summary.json:
  sha256: 4b6960f60862555c3aa2d07505a3860543e640d168002a0baf11258d895f4005

B0 geometry_nbest_rows.jsonl:
  sha256: b6c742448fc93a141a756c32d10a2c12af7ce747ba00acde0a0c1076ee02167e

B2 geometry_nbest_rows.jsonl:
  sha256: ff39b6feeeabee1b9d5b8622667f8e5af4c2f65bb375e2b202bbf5886754f942
```

## Gate Results

```yaml
B0:
  rows: 2500
  syntax_ok: 2405 / 2500 = 96.20%
  exec_ok: 1078 / 2500 = 43.12%
  build_ok: 1078 / 2500 = 43.12%
  solid_valid: 1078 / 2500 = 43.12%
  step_export_ok: 1069 / 2500 = 42.76%
  kernel_crash_count: 0

B2:
  rows: 2500
  syntax_ok: 2403 / 2500 = 96.12%
  exec_ok: 1569 / 2500 = 62.76%
  build_ok: 1569 / 2500 = 62.76%
  solid_valid: 1569 / 2500 = 62.76%
  step_export_ok: 1540 / 2500 = 61.60%
  kernel_crash_count: 0
```

Seed-3 coverage deltas:

```yaml
B2 - B0 syntax: -0.08 pp
B2 - B0 exec: +19.64 pp
B2 - B0 build: +19.64 pp
B2 - B0 solid_valid: +19.64 pp
B2 - B0 STEP export: +18.84 pp
```

Paired gate comparison on the same 2500 samples:

```yaml
syntax_ok:
  both: 2311
  B2_only: 92
  B0_only: 94
  neither: 3
  discordant: 186
  exact_McNemar_p: 0.942

build_ok:
  both: 827
  B2_only: 742
  B0_only: 251
  neither: 680
  discordant: 993
  exact_McNemar_p: 6.818e-57

step_export_ok:
  both: 809
  B2_only: 731
  B0_only: 260
  neither: 700
  discordant: 991
  exact_McNemar_p: 2.098e-52
```

## Geometry Results

```yaml
B0:
  rows: 2500
  scoreable: 1065 / 2500 = 42.60%
  conditional_CD_mean: 13.60400382770544
  conditional_CD_median: 7.2562532481980355
  conditional_F@1_mean: 15.34840280841597%
  conditional_F@1_median: 15.96664755351682%
  unconditional_F@1_mean: 6.538419596385203%
  unconditional_F@1_median: 0.0%

B2:
  rows: 2500
  scoreable: 1524 / 2500 = 60.96%
  conditional_CD_mean: 412844042.2779511
  conditional_CD_median: 3.3985335272319546
  conditional_F@1_mean: 18.21762671065642%
  conditional_F@1_median: 18.841078367875647%
  unconditional_F@1_mean: 11.105465242816154%
  unconditional_F@1_median: 8.295036764705883%
```

Geometry deltas:

```yaml
B2 - B0 scoreable: +459 rows = +18.36 pp
B2 - B0 conditional median CD: -3.857719720966081
B2 - B0 conditional median F@1: +2.874430814358827 pp
B2 - B0 unconditional mean F@1: +4.567045646430951 pp
B2 - B0 unconditional median F@1: +8.295036764705883 pp
```

Robust CD quantiles:

```yaml
B0_CD:
  q25: 2.635668903577299
  median: 7.2562532481980355
  q75: 14.237439178828414
  q95: 46.92947416262693
  q99: 112.14368038312354
  cd_gt_1000: 0

B2_CD:
  q25: 1.7062795801529576
  median: 3.3985335272319546
  q75: 8.409697988591567
  q95: 76.10932118120296
  q99: 421.7639247791882
  cd_gt_1000: 4
```

Important caveat: B2 again has better robust geometry statistics but its raw mean CD is dominated by severe outliers, with maximum CD approximately `1.614e11`. For seed-level reporting, median CD, quantiles, paired win counts, and F@1 are more informative than raw mean CD.

## Paired Geometry

Jointly scoreable samples:

```yaml
joint_scoreable: 801
```

Paired CD, lower is better:

```yaml
B2_wins: 535
B0_wins: 266
ties: 0
non_tied: 801
sign_test_p: 1.173e-21
median_delta_B2_minus_B0: -0.6057797925090054
```

Paired F@1, higher is better:

```yaml
B2_wins: 544
B0_wins: 257
ties: 0
non_tied: 801
sign_test_p: 1.667e-24
median_delta_B2_minus_B0: +3.0767148771715408 pp
```

Paired bbox error, lower is better:

```yaml
B2_wins: 263
B0_wins: 374
ties: 164
non_tied: 637
sign_test_p: 1.250e-05
median_delta_B2_minus_B0: 0.0
```

The primary paired geometry metrics favor B2: CD favors B2 in `535/801` jointly scoreable cases, and F@1 favors B2 in `544/801` cases. Bbox error win count favors B0, but median bbox delta is zero and bbox error is not the primary geometry endpoint.

## Failure Notes

Top B0 non-scoreable / failed geometry causes:

```yaml
"topology reference 'join_001:top_face:b9ce48e7f7b9' did not resolve any face": 212
"Part.boolean_join() got an unexpected keyword argument 'operation'": 157
"'height'": 59
"Part.bossed_plate() missing 2 required keyword-only arguments: 'width' and 'height'": 56
"Part.sketch_circle() got an unexpected keyword argument 'size'": 51
```

Top B2 non-scoreable / failed geometry causes:

```yaml
"topology reference 'join_001:top_face:b9ce48e7f7b9' did not resolve any face": 87
"Part.boolean_cut() got an unexpected keyword argument 'depth'": 79
"loft requires at least two profile features": 68
"SyntaxError: invalid syntax (<unknown>, line 1)": 36
"Part.rectangular_pocket() missing 1 required keyword-only argument: 'depth'": 31
```

## Interpretation

Seed 3 is a strong favorable result for B2. B2 has nearly identical syntax rate to B0, but much higher executable coverage: `+19.64 pp` Build and `+18.84 pp` STEP export.

Geometry again favors B2 on the robust endpoints. B2 has substantially more scoreable rows, better conditional median CD, better conditional median F@1, better unconditional F@1, and favorable paired CD/F@1 win counts on the jointly scoreable subset. As in seeds 1 and 2, raw mean CD is not a good main statistic because B2 includes severe geometric outliers.

Recommended seed-3 wording:

> In seed 3 of the full-stack B0/B2 replication, B2 again achieved higher executable coverage than B0 under the same 2500-row STEP slice, with Build increasing from 43.12% to 62.76% and STEP export from 42.76% to 61.60%. Paired geometry on the jointly scoreable subset also favored B2 by median CD and F@1, while mean CD was unstable due to severe B2 outliers.

Do not make the final multi-seed conclusion yet. Continue to seed 4 using the frozen protocol.

## Next Command

Seed 3 is closed. The next allowed command is seed 4 training:

```bash
cd ~/workspace/MIRAGE/src
SEED=4 bash training_25k/cag_run_b0_b2_fullstack_seed.sh
```
