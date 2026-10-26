> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# 06 -- Seed 1 Gate and Partial Geometry Record

Date: 2026-10-08

## Status

```yaml
Experiment: Review/03 B0 vs B2 full-stack multi-seed replication
Seed: 1
Training: COMPLETE
Prediction: COMPLETE
Gate evaluation: COMPLETE
B0 geometry scoring: COMPLETE
B2 geometry scoring: MISSING
Seed status: NOT_CLOSED
```

Important: seed 1 is not closed yet because `geom_b0b2_step_B2_s1` is not present in the scratch directory.

## Output Presence Check

Observed scratch outputs:

```yaml
B0 gate:
  path: __DEV_ROOT__\scratch\exec_b0b2_step_B0_s1
  status: COMPLETE

B2 gate:
  path: __DEV_ROOT__\scratch\exec_b0b2_step_B2_s1
  status: COMPLETE

B0 geometry:
  path: __DEV_ROOT__\scratch\geom_b0b2_step_B0_s1
  status: COMPLETE

B2 geometry:
  path: __DEV_ROOT__\scratch\geom_b0b2_step_B2_s1
  status: MISSING
```

## Gate Results

```yaml
B0:
  rows: 2500
  runtime_seconds: 210.279
  syntax_ok: 2423 / 2500 = 96.92%
  exec_ok: 1392 / 2500 = 55.68%
  build_ok: 1392 / 2500 = 55.68%
  solid_valid: 1392 / 2500 = 55.68%
  step_export_ok: 1375 / 2500 = 55.00%
  kernel_crash_count: 0

B2:
  rows: 2500
  runtime_seconds: 482.675
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
B2 - B0 STEP_export: +13.28 pp
```

## B0 Geometry Result

```yaml
B0 geometry rows: 2500
B0 scoreable rows: 1374
B0 scoreable rate: 54.96%

B0 conditional CD:
  mean: 9.505413681204102
  median: 3.347859868360917
  min: 0.059262029821460685
  max: 297.7606901133478

B0 conditional F@1:
  mean: 15.613018039520166%
  median: 16.787222928779073%
  min: 0.0%
  max: 47.21634242502585%

B0 conditional bbox_err:
  mean: 0.7704678583691252
  median: 0.0900005944569912
  min: 0.0
  max: 35.911292016387044

B0 unconditional F@1:
  mean: 8.580914714520282%
  median: 2.4086814413265305%
```

Top B0 non-scoreable / failed geometry causes:

```yaml
topology reference 'join_001:top_face:b9ce48e7f7b9' did not resolve any face: 131
Part.sweep_tube() got an unexpected keyword argument 'profile': 119
Part.linear_pattern() got an unexpected keyword argument 'target_offset': 69
mirror: plane must be 'YZ', 'XZ', or 'XY': 67
target must be a FeatureHandle: 45
offset must be a 3D sequence: 44
'Part' object has no attribute 'lobed_gasket_profile': 42
Part.rectangular_pocket() got an unexpected keyword argument 'height': 38
'pocket_depth': 35
topology reference 'chamfer_001:top_outer_edges:1c8e3f3146f4' did not resolve any edge_set: 28
```

## Analysis

The coverage result is already directionally favorable for B2 in seed 1. B2 is nearly tied with B0 on syntax, but gains substantially once the code must execute and build valid CAD: `+13.08 pp` for Build and `+13.28 pp` for STEP export. This is exactly the reviewer-relevant coverage endpoint for the B0/B2 comparison.

However, the seed cannot be closed yet because B2 geometry scoring is missing. Without B2 geometry, we cannot compute:

```yaml
B2 scoreable count
B2 conditional CD / F@1
B2 unconditional F@1
B0 vs B2 paired geometry comparison
```

So the correct interpretation at this point is:

> Seed 1 supports a B2 coverage advantage over B0, but the geometry part of the seed-1 record is incomplete until B2 geometry is run.

## Required Next Command

Run only the missing B2 geometry command in Windows PowerShell:

```powershell
$Root = "__RUN_SOURCE_ROOT__"

& "__DEV_ROOT__\src\scripts\evaluate_geometry_nbest.ps1" `
  -InputJsonl "$Root\outputs\b0_b2_fullstack_s1\predictions\geom_input_step_B2_s1.jsonl" `
  -OutputDir "__DEV_ROOT__\scratch\geom_b0b2_step_B2_s1"
```

After this finishes, summarize/register seed 1 before starting seed 2.
