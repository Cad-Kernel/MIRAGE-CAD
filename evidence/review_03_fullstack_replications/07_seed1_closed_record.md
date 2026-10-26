> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# 07 -- Seed 1 Closed Record

Date: 2026-10-08

## Status

```yaml
Experiment: Review/03 B0 vs B2 full-stack multi-seed replication
Seed: 1
Training: COMPLETE
Prediction: COMPLETE
Gate evaluation: COMPLETE
Geometry scoring: COMPLETE
Seed status: CLOSED
```

Seed 1 is now complete. Do not edit its protocol, sample slice, checkpoint rule, decoding, or repair policy after this point.

## Source And Output Paths

```yaml
Windows source checkout:
  __DEV_ROOT__\src

WSL execution checkout:
  __RUN_SOURCE_ROOT__

Review package:
  __EVIDENCE_SOURCE_ROOT__\03

B0 prediction:
  outputs/b0_b2_fullstack_s1/predictions/gen_step_B0_s1.jsonl

B2 prediction:
  outputs/b0_b2_fullstack_s1/predictions/gen_step_B2_s1.jsonl

B0 gate:
  __DEV_ROOT__\scratch\exec_b0b2_step_B0_s1

B2 gate:
  __DEV_ROOT__\scratch\exec_b0b2_step_B2_s1

B0 geometry:
  __DEV_ROOT__\scratch\geom_b0b2_step_B0_s1

B2 geometry:
  __DEV_ROOT__\scratch\geom_b0b2_step_B2_s1
```

Result file hashes:

```yaml
B0 execution_summary.json:
  sha256: b09a9336d0fb055d8da6d969bbd670187299801c1ca9ce95cdefdcfc53776d1e

B2 execution_summary.json:
  sha256: 383f97d777c6ca5db6ad8ba49fa4482dc7fb1b7df2b2a9759267cdd5fbbaa851

B0 geometry_nbest_rows.jsonl:
  sha256: 28c4dbc37ec5d19806144b79c1042140e68cd978a3080e412ff42cb32a12fd15

B2 geometry_nbest_rows.jsonl:
  sha256: 4f70dd07def2f7cae193cbdc4413d5ccc264f088aebb4fb09382901fb3786967
```

## Gate Results

```yaml
B0:
  rows: 2500
  syntax_ok: 2423 / 2500 = 96.92%
  exec_ok: 1392 / 2500 = 55.68%
  build_ok: 1392 / 2500 = 55.68%
  solid_valid: 1392 / 2500 = 55.68%
  step_export_ok: 1375 / 2500 = 55.00%
  kernel_crash_count: 0

B2:
  rows: 2500
  syntax_ok: 2414 / 2500 = 96.56%
  exec_ok: 1719 / 2500 = 68.76%
  build_ok: 1719 / 2500 = 68.76%
  solid_valid: 1719 / 2500 = 68.76%
  step_export_ok: 1707 / 2500 = 68.28%
  kernel_crash_count: 0
```

Seed-1 coverage deltas:

```yaml
B2 - B0 syntax: -0.36 pp
B2 - B0 exec: +13.08 pp
B2 - B0 build: +13.08 pp
B2 - B0 solid_valid: +13.08 pp
B2 - B0 STEP export: +13.28 pp
```

Paired gate comparison on the same 2500 samples:

```yaml
syntax_ok:
  both: 2342
  B2_only: 72
  B0_only: 81
  neither: 5
  discordant: 153
  exact_McNemar_p: 0.518

build_ok:
  both: 1115
  B2_only: 604
  B0_only: 277
  neither: 504
  discordant: 881
  exact_McNemar_p: 1.071e-28

step_export_ok:
  both: 1100
  B2_only: 607
  B0_only: 275
  neither: 518
  discordant: 882
  exact_McNemar_p: 1.607e-29
```

## Geometry Results

```yaml
B0:
  rows: 2500
  scoreable: 1374 / 2500 = 54.96%
  conditional_CD_mean: 9.505413681204102
  conditional_CD_median: 3.347859868360917
  conditional_F@1_mean: 15.613018039520166%
  conditional_F@1_median: 16.787222928779073%
  unconditional_F@1_mean: 8.580914714520282%
  unconditional_F@1_median: 2.4086814413265305%

B2:
  rows: 2500
  scoreable: 1676 / 2500 = 67.04%
  conditional_CD_mean: 269635092.47724086
  conditional_CD_median: 2.905941882504827
  conditional_F@1_mean: 18.499405204045188%
  conditional_F@1_median: 18.699004569190603%
  unconditional_F@1_mean: 12.402001248791894%
  unconditional_F@1_median: 9.59311295306511%
```

Geometry deltas:

```yaml
B2 - B0 scoreable: +302 rows = +12.08 pp
B2 - B0 conditional median CD: -0.441917985856090
B2 - B0 conditional median F@1: +1.91178164041153 pp
B2 - B0 unconditional mean F@1: +3.821086534271612 pp
B2 - B0 unconditional median F@1: +7.184431511738579 pp
```

Robust CD quantiles:

```yaml
B0_CD:
  q25: 1.804596011089142
  median: 3.347859868360917
  q75: 8.941845150547085
  q95: 41.125153405043264
  q99: 75.32589901437571
  cd_gt_1000: 0

B2_CD:
  q25: 1.7855555871444928
  median: 2.905941882504827
  q75: 6.166754279727926
  q95: 23.272272103032677
  q99: 245.50365276260004
  cd_gt_1000: 4
```

Important caveat: B2 has a better median CD and better q25/q75/q95 CD than B0, but B2's conditional mean CD is dominated by four extreme outliers, including a maximum CD of approximately `1.543e11`. For seed-level reporting, the median CD and paired win counts are much more informative than the raw mean CD.

## Paired Geometry

Jointly scoreable samples:

```yaml
joint_scoreable: 1083
```

Paired CD, lower is better:

```yaml
B2_wins: 686
B0_wins: 397
ties: 0
non_tied: 1083
sign_test_p: 1.324e-18
median_delta_B2_minus_B0: -0.16720582792480965
```

Paired F@1, higher is better:

```yaml
B2_wins: 671
B0_wins: 411
ties: 1
non_tied: 1082
sign_test_p: 2.541e-15
median_delta_B2_minus_B0: +1.626295130745048 pp
```

Paired bbox error, lower is better:

```yaml
B2_wins: 415
B0_wins: 487
ties: 181
non_tied: 902
sign_test_p: 0.0180
median_delta_B2_minus_B0: 0.0
```

The primary paired geometry metrics favor B2: CD favors B2 in `686/1083` jointly scoreable cases, and F@1 favors B2 in `671/1082` non-tied cases. Bbox error is mixed and slightly favors B0 by win count, but median bbox delta is zero and bbox is not the primary geometry endpoint.

## Failure Notes

Top B0 non-scoreable / failed geometry causes:

```yaml
"topology reference 'join_001:top_face:b9ce48e7f7b9' did not resolve any face": 131
"Part.sweep_tube() got an unexpected keyword argument 'profile'": 119
"Part.linear_pattern() got an unexpected keyword argument 'target_offset'": 69
"mirror: plane must be 'YZ', 'XZ', or 'XY'": 67
"target must be a FeatureHandle": 45
```

Top B2 non-scoreable / failed geometry causes:

```yaml
"Part.sweep_tube() got an unexpected keyword argument 'height'": 55
"Part.extrude_on_face() got an unexpected keyword argument 'profile'": 50
"'Part' object has no attribute 'threaded_bearing_hole_on_face'": 36
"topology reference 'join_001:top_face:b9ce48e7f7b9' did not resolve any face": 35
"Part.sketch_on_face() got an unexpected keyword argument 'size'": 32
```

## Interpretation

Seed 1 is a favorable result for B2. B2 has nearly identical syntax rate to B0, but substantially higher executable coverage: `+13.08 pp` Build and `+13.28 pp` STEP export. This directly supports the B0/B2 comparison endpoint Reviewer 2 asked to replicate across seeds.

Geometry also favors B2 on the main robust endpoints. B2 has more scoreable rows, better conditional median CD, better conditional median F@1, better unconditional F@1, and favorable paired CD/F@1 win counts on the jointly scoreable subset. The only caution is that B2 has a few severe geometric outliers, so mean CD should not be used as the primary seed-level geometry statement.

Recommended seed-1 wording:

> In seed 1 of the full-stack B0/B2 replication, B2 achieved higher executable coverage than B0 under the same 2500-row STEP slice, with Build increasing from 55.68% to 68.76% and STEP export from 55.00% to 68.28%. On the jointly scoreable subset, paired geometry also favored B2 by median CD and F@1, although a small number of severe B2 outliers made raw mean CD unstable.

Do not make the final multi-seed conclusion yet. Continue to seed 2 using the frozen protocol.

## Next Command

Seed 1 is closed. The next allowed command is seed 2 training:

```bash
cd ~/workspace/MIRAGE/src
SEED=2 bash training_25k/cag_run_b0_b2_fullstack_seed.sh
```
