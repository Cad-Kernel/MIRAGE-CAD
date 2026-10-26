> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# 10 -- Seed 2 Closed Record

Date: 2026-10-11

## Status

```yaml
Experiment: Review/03 B0 vs B2 full-stack multi-seed replication
Seed: 2
Training: COMPLETE
Prediction: COMPLETE
Gate evaluation: COMPLETE
Geometry scoring: COMPLETE
Seed status: CLOSED
```

Seed 2 is now complete. Do not edit its protocol, sample slice, checkpoint rule, decoding, or repair policy after this point.

## Source And Output Paths

```yaml
Windows source checkout:
  __DEV_ROOT__\src

WSL execution checkout:
  __RUN_SOURCE_ROOT__

Review package:
  __EVIDENCE_SOURCE_ROOT__\03

B0 prediction:
  outputs/b0_b2_fullstack_s2/predictions/gen_step_B0_s2.jsonl

B2 prediction:
  outputs/b0_b2_fullstack_s2/predictions/gen_step_B2_s2.jsonl

B0 gate:
  __DEV_ROOT__\scratch\exec_b0b2_step_B0_s2

B2 gate:
  __DEV_ROOT__\scratch\exec_b0b2_step_B2_s2

B0 geometry:
  __DEV_ROOT__\scratch\geom_b0b2_step_B0_s2

B2 geometry:
  __DEV_ROOT__\scratch\geom_b0b2_step_B2_s2
```

Result file hashes:

```yaml
B0 execution_summary.json:
  sha256: 18f995a4b1c7a42b2c1069d16bf548e76cc1771782d24161d3ecfe51ef5f40d9

B2 execution_summary.json:
  sha256: 0c2b191e3a0d31d3af361b899387b822d904356c1f928c3a9aed3714f66bafef

B0 geometry_nbest_rows.jsonl:
  sha256: 3cad9d728c1ae7ef80a49bbe2a7b586e6fd2a1b849d074040c8061e062ec2da1

B2 geometry_nbest_rows.jsonl:
  sha256: b36b6a326a477971e457a792058e273a3d5c923e8b79f6fde635712ee02a8150
```

## Gate Results

```yaml
B0:
  rows: 2500
  syntax_ok: 2442 / 2500 = 97.68%
  exec_ok: 1297 / 2500 = 51.88%
  build_ok: 1297 / 2500 = 51.88%
  solid_valid: 1297 / 2500 = 51.88%
  step_export_ok: 1219 / 2500 = 48.76%
  kernel_crash_count: 0

B2:
  rows: 2500
  syntax_ok: 2385 / 2500 = 95.40%
  exec_ok: 1440 / 2500 = 57.60%
  build_ok: 1440 / 2500 = 57.60%
  solid_valid: 1440 / 2500 = 57.60%
  step_export_ok: 1422 / 2500 = 56.88%
  kernel_crash_count: 0
```

Seed-2 coverage deltas:

```yaml
B2 - B0 syntax: -2.28 pp
B2 - B0 exec: +5.72 pp
B2 - B0 build: +5.72 pp
B2 - B0 solid_valid: +5.72 pp
B2 - B0 STEP export: +8.12 pp
```

Paired gate comparison on the same 2500 samples:

```yaml
syntax_ok:
  both: 2328
  B2_only: 57
  B0_only: 114
  neither: 1
  discordant: 171
  exact_McNemar_p: 1.560e-05

build_ok:
  both: 838
  B2_only: 602
  B0_only: 459
  neither: 601
  discordant: 1061
  exact_McNemar_p: 1.267e-05

step_export_ok:
  both: 809
  B2_only: 613
  B0_only: 410
  neither: 668
  discordant: 1023
  exact_McNemar_p: 2.360e-10
```

## Geometry Results

```yaml
B0:
  rows: 2500
  scoreable: 1206 / 2500 = 48.24%
  conditional_CD_mean: 13.545793099642259
  conditional_CD_median: 4.271995119236208
  conditional_F@1_mean: 16.529368896874852%
  conditional_F@1_median: 17.327794894366197%
  unconditional_F@1_mean: 7.973767555852429%
  unconditional_F@1_median: 0.0%

B2:
  rows: 2500
  scoreable: 1355 / 2500 = 54.20%
  conditional_CD_mean: 128165251.36611037
  conditional_CD_median: 2.5214314715839485
  conditional_F@1_mean: 19.87240816546748%
  conditional_F@1_median: 20.16495157384988%
  unconditional_F@1_mean: 10.770845225683374%
  unconditional_F@1_median: 6.051537298387097%
```

Geometry deltas:

```yaml
B2 - B0 scoreable: +149 rows = +5.96 pp
B2 - B0 conditional median CD: -1.7505636476522594
B2 - B0 conditional median F@1: +2.837156679483683 pp
B2 - B0 unconditional mean F@1: +2.797077669830945 pp
B2 - B0 unconditional median F@1: +6.051537298387097 pp
```

Robust CD quantiles:

```yaml
B0_CD:
  q25: 2.3011643826441768
  median: 4.271995119236208
  q75: 14.501857286910337
  q95: 47.076221291453734
  q99: 111.47880510518559
  cd_gt_1000: 0

B2_CD:
  q25: 1.6520355604096293
  median: 2.5214314715839485
  q75: 5.33976733088255
  q95: 25.997576438527606
  q99: 141.815974038688
  cd_gt_1000: 1
```

Important caveat: as in seed 1, B2 has better robust geometry statistics but its raw mean CD is dominated by a severe outlier, with maximum CD approximately `1.737e11`. For seed-level reporting, median CD, quantiles, paired win counts, and F@1 are more informative than raw mean CD.

## Paired Geometry

Jointly scoreable samples:

```yaml
joint_scoreable: 747
```

Paired CD, lower is better:

```yaml
B2_wins: 458
B0_wins: 289
ties: 0
non_tied: 747
sign_test_p: 6.722e-10
median_delta_B2_minus_B0: -0.09404826348661066
```

Paired F@1, higher is better:

```yaml
B2_wins: 484
B0_wins: 263
ties: 0
non_tied: 747
sign_test_p: 5.123e-16
median_delta_B2_minus_B0: +1.5625399207971402 pp
```

Paired bbox error, lower is better:

```yaml
B2_wins: 345
B0_wins: 277
ties: 125
non_tied: 622
sign_test_p: 0.00717
median_delta_B2_minus_B0: 0.0
```

The primary paired geometry metrics again favor B2: CD favors B2 in `458/747` jointly scoreable cases, and F@1 favors B2 in `484/747` cases.

## Failure Notes

Top B0 non-scoreable / failed geometry causes:

```yaml
"target must be a TopologyReference from a FeatureHandle": 118
"Part.__init__() got an unexpected keyword argument 'semantic_type'": 115
"Part.plate() got an unexpected keyword argument 'radius'": 92
"mirror: plane must be 'YZ', 'XZ', or 'XY'": 84
"STEP export error: OCCT build failed": 78
```

Top B2 non-scoreable / failed geometry causes:

```yaml
"topology reference 'join_001:top_face:b9ce48e7f7b9' did not resolve any face": 78
"name '__all__' is not defined": 71
"'Part' object has no attribute 'extrude_face_on_profile'": 71
"point cloud sampling failed on generated part": 67
"Part.rectangular_pocket() got an unexpected keyword argument 'height'": 67
```

## Interpretation

Seed 2 is also favorable for B2, though the coverage margin is smaller than seed 1. B2 has a lower syntax rate than B0, but once execution and CAD validity are required, B2 achieves higher Build and STEP export rates: `+5.72 pp` Build and `+8.12 pp` STEP export.

Geometry again favors B2 on the robust endpoints. B2 has more scoreable rows, better conditional median CD, better conditional median F@1, better unconditional F@1, and favorable paired CD/F@1 win counts on the jointly scoreable subset. As in seed 1, raw mean CD is not a good main statistic because B2 includes a severe geometric outlier.

Recommended seed-2 wording:

> In seed 2 of the full-stack B0/B2 replication, B2 again achieved higher executable coverage than B0 under the same 2500-row STEP slice, with Build increasing from 51.88% to 57.60% and STEP export from 48.76% to 56.88%. Paired geometry on the jointly scoreable subset also favored B2 by median CD and F@1, while mean CD was unstable due to a severe B2 outlier.

Do not make the final multi-seed conclusion yet. Continue to seed 3 using the frozen protocol.

## Next Command

Seed 2 is closed. The next allowed command is seed 3 training:

```bash
cd ~/workspace/MIRAGE/src
SEED=3 bash training_25k/cag_run_b0_b2_fullstack_seed.sh
```
