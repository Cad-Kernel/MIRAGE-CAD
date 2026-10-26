> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# B0 vs B2 Four-Seed Full Results

Review/03; audited 2026-10-16. Seeds 1, 2, 3, 4; 2500 identical STEP queries per seed.

Training, prediction, gate evaluation, and geometry scoring are complete for all four seeds.

## Per-Seed Coverage

| Seed | Arm | Syntax | Execute | Build | Solid | STEP export | Scoreable |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | B0 | 2423/2500 (96.92%) | 1392/2500 (55.68%) | 1392/2500 (55.68%) | 1392/2500 (55.68%) | 1375/2500 (55.00%) | 1374/2500 (54.96%) |
| 1 | B2 | 2414/2500 (96.56%) | 1719/2500 (68.76%) | 1719/2500 (68.76%) | 1719/2500 (68.76%) | 1707/2500 (68.28%) | 1676/2500 (67.04%) |
| 2 | B0 | 2442/2500 (97.68%) | 1297/2500 (51.88%) | 1297/2500 (51.88%) | 1297/2500 (51.88%) | 1219/2500 (48.76%) | 1206/2500 (48.24%) |
| 2 | B2 | 2385/2500 (95.40%) | 1440/2500 (57.60%) | 1440/2500 (57.60%) | 1440/2500 (57.60%) | 1422/2500 (56.88%) | 1355/2500 (54.20%) |
| 3 | B0 | 2405/2500 (96.20%) | 1078/2500 (43.12%) | 1078/2500 (43.12%) | 1078/2500 (43.12%) | 1069/2500 (42.76%) | 1065/2500 (42.60%) |
| 3 | B2 | 2403/2500 (96.12%) | 1569/2500 (62.76%) | 1569/2500 (62.76%) | 1569/2500 (62.76%) | 1540/2500 (61.60%) | 1524/2500 (60.96%) |
| 4 | B0 | 2384/2500 (95.36%) | 1371/2500 (54.84%) | 1371/2500 (54.84%) | 1371/2500 (54.84%) | 1355/2500 (54.20%) | 1338/2500 (53.52%) |
| 4 | B2 | 2288/2500 (91.52%) | 1463/2500 (58.52%) | 1463/2500 (58.52%) | 1463/2500 (58.52%) | 1433/2500 (57.32%) | 1340/2500 (53.60%) |

## Equal-Weight Seed Aggregates

All SD values use sample SD (ddof=1), with four training runs per arm. Percentages and F@1 are shown in 0-100 units.

| Metric | B0 mean +/- SD | B2 mean +/- SD | Delta mean +/- SD | B2-favorable seeds | Seed-level sign p |
| --- | ---: | ---: | ---: | ---: | ---: |
| syntax_ok_pct | 96.54 +/- 0.99196774 | 94.9 +/- 2.3035046 | -1.64 +/- 1.7627252 | 0/4 | 0.125 |
| exec_ok_pct | 51.38 +/- 5.7427984 | 61.91 +/- 5.0896365 | 10.53 +/- 7.2927635 | 4/4 | 0.125 |
| build_ok_pct | 51.38 +/- 5.7427984 | 61.91 +/- 5.0896365 | 10.53 +/- 7.2927635 | 4/4 | 0.125 |
| solid_valid_pct | 51.38 +/- 5.7427984 | 61.91 +/- 5.0896365 | 10.53 +/- 7.2927635 | 4/4 | 0.125 |
| step_export_ok_pct | 50.18 +/- 5.6705555 | 61.02 +/- 5.2875199 | 10.84 +/- 6.7564882 | 4/4 | 0.125 |
| scoreable_pct | 49.83 +/- 5.6194306 | 58.95 +/- 6.3422709 | 9.12 +/- 7.870756 | 4/4 | 0.125 |
| conditional_mean_cd | 12.233101 +/- 1.9187459 | 2.026611e+08 +/- 1.7821666e+08 | 2.0266109e+08 +/- 1.7821666e+08 | 0/4 | 0.125 |
| conditional_median_cd | 5.3626534 +/- 1.8532165 | 3.0792452 +/- 0.45193584 | -2.2834082 +/- 1.504826 | 4/4 | 0.125 |
| conditional_mean_f1_pct | 15.295072 +/- 1.1839603 | 18.475734 +/- 1.0596653 | 3.1806622 +/- 0.36810546 | 4/4 | 0.125 |
| conditional_median_f1_pct | 15.436269 +/- 2.5767358 | 18.911729 +/- 0.92401569 | 3.4754597 +/- 1.9209911 | 4/4 | 0.125 |
| unconditional_mean_f1_pct | 7.6049305 +/- 0.87625874 | 10.889587 +/- 1.2830638 | 3.2846561 +/- 1.1463299 | 4/4 | 0.125 |
| unconditional_median_f1_pct | 1.0046325 +/- 1.2050191 | 7.3642083 +/- 1.9121717 | 6.3595758 +/- 1.8739399 | 4/4 | 0.125 |
| paired_mean_cd | 11.35671 +/- 2.1815062 | 1.0431866e+08 +/- 2.086373e+08 | 1.0431865e+08 +/- 2.086373e+08 | 1/4 | 0.625 |
| paired_median_cd | 5.2194418 +/- 2.1064031 | 2.8616101 +/- 0.45207462 | -2.3578317 +/- 1.9684396 | 4/4 | 0.125 |
| paired_mean_f1_pct | 15.806121 +/- 1.1535777 | 20.144145 +/- 1.6848525 | 4.3380242 +/- 0.86569814 | 4/4 | 0.125 |
| paired_median_f1_pct | 16.730552 +/- 1.4312787 | 20.555717 +/- 1.671935 | 3.8251649 +/- 0.55801352 | 4/4 | 0.125 |
| conditional_mean_bbox_err | 1.3238745 +/- 0.49649247 | 430.94818 +/- 385.28354 | 429.6243 +/- 385.6863 | 1/4 | 0.625 |
| conditional_median_bbox_err | 0.30432357 +/- 0.37065344 | 0.17072732 +/- 0.11020228 | -0.13359626 +/- 0.45375987 | 2/4 | 1 |

## Interpretation Boundaries

- CD is the evaluator's symmetric mean squared nearest-neighbour distance, without rescaling in this analysis. F@1 is F-score at a threshold of 1% of the target bounding-box diagonal. Bounding-box error is mean absolute axis-extent error.
- Report all endpoints, including syntax, raw mean CD, and bbox outcomes. A lower median CD does not imply better tails or a lower mean CD.
- Raw means include catastrophic geometric outliers. Use medians and paired win counts alongside these means; do not retrospectively remove outliers or present robust metrics as proof of uniform superiority.
- Full-set conditional metrics are calculated over each arm's own scoreable outputs. Paired metrics restrict both arms to the same jointly scoreable queries. Unconditional F@1 uses all 2500 queries, assigning zero to non-scoreable outputs.
- Query-level sign/McNemar tests are within-run descriptive paired-case evidence. There are four training replicates, not 10000 independent model replications. Four same-direction seeds alone give a two-sided seed sign-test p of 0.125.
- This is a replication of complete deployed conditions, not a fully compute-matched isolation of plan text. B2 has extra alignment/prior/plan stages and a code continuation. B0 trains with max_length 2048 while B2 code training uses 1536.
- B2 Stage 4b mixes have seed-dependent row counts after grammar filtering. Preserve the actual counts and resulting update budgets. Do not claim identical total updates or total compute across B0/B2.
- Program/code repair is disabled in both arms. B2 P1a plan canonicalization remains enabled and is logged. Do not describe all repair as disabled.
- Scope is the fixed in-corpus STEP evaluation. These results do not establish broad external generalization or universal representation superiority.

## Training And P1a Actuals

| Seed | B2 Stage 4b rows | P1a ADD | P1a CUT | Touched samples |
| --- | ---: | ---: | ---: | ---: |
| 1 | 2987 | 82 | 120 | 112 |
| 2 | 3103 | 65 | 24 | 71 |
| 3 | 2997 | 13 | 53 | 51 |
| 4 | 3130 | 15 | 24 | 26 |

## Reproducibility

Source checkout: `__DEV_ROOT__\src`.
WSL training checkout: `__RUN_SOURCE_ROOT__`.
Train/generation wrapper: `training_25k/cag_run_b0_b2_fullstack_seed.sh` (frozen original hash retained in every generation actuals JSON).
Analysis script: `__DEV_ROOT__\src\training_25k\cag_summarize_b0_b2_fullstack_eval.py`.
Analysis script SHA256: `cc7c5ccc753e99765a69b211c6f48bdae377d9781b9aa85c54b1c05edcf3f898`.
Per-seed JSON includes all gate summaries, source-file hashes, metric distributions, exact error counts, extreme cases, paired subset IDs, and generation actuals. Paired-case JSONL preserves per-sample evaluation fields for all queries. Original raw outputs and CLI logs remain in their recorded scratch directories.

## Full Per-Seed Detail

# Seed 1 Evaluation Record

Audit: PASS. Evaluation complete.

| Seed | Arm | Syntax | Execute | Build | Solid | STEP export | Scoreable |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | B0 | 2423/2500 (96.92%) | 1392/2500 (55.68%) | 1392/2500 (55.68%) | 1392/2500 (55.68%) | 1375/2500 (55.00%) | 1374/2500 (54.96%) |
| 1 | B2 | 2414/2500 (96.56%) | 1719/2500 (68.76%) | 1719/2500 (68.76%) | 1719/2500 (68.76%) | 1707/2500 (68.28%) | 1676/2500 (67.04%) |

## Geometry

| Metric | B0 | B2 | B2 - B0 |
| --- | ---: | ---: | ---: |
| conditional_mean_cd | 9.505413681 | 269635092.5 | 269635083 |
| conditional_median_cd | 3.347859868 | 2.905941883 | -0.4419179859 |
| conditional_mean_f1_pct | 15.61301804 | 18.4994052 | 2.886387165 |
| conditional_median_f1_pct | 16.78722293 | 18.69900457 | 1.91178164 |
| unconditional_mean_f1_pct | 8.580914715 | 12.40200125 | 3.821086534 |
| unconditional_median_f1_pct | 2.408681441 | 9.593112953 | 7.184431512 |
| paired_mean_cd | 9.257464337 | 417274612.4 | 417274603.2 |
| paired_median_cd | 3.541080602 | 2.56690699 | -0.9741736127 |
| paired_mean_f1_pct | 15.7454948 | 20.89937196 | 5.153877161 |
| paired_median_f1_pct | 17.03975645 | 21.48037997 | 4.440623525 |
| conditional_mean_bbox_err | 0.7704678584 | 598.1563732 | 597.3859053 |
| conditional_median_bbox_err | 0.09000059446 | 0.2062127823 | 0.1162121878 |

Percent metrics above use 0-100 units. CD/bbox remain in evaluator units. Conditional full-set and jointly scoreable metrics use different subsets.

## Paired Tests

Within-seed query-level tests below do not measure uncertainty across training seeds.

| Gate | Both | B0 only | B2 only | Neither | Delta pp | Exact McNemar p |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| syntax_ok | 2342 | 81 | 72 | 5 | -0.36 | 0.51792103 |
| exec_ok | 1115 | 277 | 604 | 504 | 13.08 | 1.0713944e-28 |
| build_ok | 1115 | 277 | 604 | 504 | 13.08 | 1.0713944e-28 |
| solid_valid | 1115 | 277 | 604 | 504 | 13.08 | 1.0713944e-28 |
| step_export_ok | 1100 | 275 | 607 | 518 | 13.28 | 1.606947e-29 |

Jointly scoreable: 1083.

| Metric | B2 wins | B0 wins | Ties | Median paired difference B2 - B0 | Exact sign p |
| --- | ---: | ---: | ---: | ---: | ---: |
| cd | 686 | 397 | 0 | -0.1672058279 | 1.324267e-18 |
| f_score_1pct | 671 | 411 | 1 | 0.01626295131 | 2.5408447e-15 |
| bbox_err | 415 | 487 | 181 | 0 | 0.018027848 |

F@1 paired differences in the last table use raw 0-1 units. Multiply by 100 for percentage points.

## Distributions And Failures

No CD values were removed, clipped, or winsorized. CD > 1000 is a retrospective audit flag, not an exclusion rule.

### B0

```json
{
  "rows": 2500,
  "scoreable": 1374,
  "scoreable_pct": 54.96,
  "gate_counts_from_geometry_run": {
    "syntax_ok": 2423,
    "exec_ok": 1392,
    "build_ok": 1392,
    "solid_valid": 1392,
    "step_export_ok": 1375
  },
  "missing_target_rows": 0,
  "conditional": {
    "cd": {
      "n": 1374,
      "mean": 9.505413681204102,
      "median": 3.347859868360917,
      "sd_sample": 17.853140892335027,
      "min": 0.059262029821460685,
      "max": 297.7606901133478,
      "q25": 1.804596011089142,
      "q75": 8.941845150547085,
      "q95": 41.125153405043264,
      "q99": 75.32589901437571
    },
    "f_score_1pct": {
      "n": 1374,
      "mean": 0.15613018039520166,
      "median": 0.16787222928779072,
      "sd_sample": 0.09838597484432374,
      "min": 0.0,
      "max": 0.47216342425025853,
      "q25": 0.05520015361793588,
      "q75": 0.22412002995642702,
      "q95": 0.32273491329442605,
      "q99": 0.3737864962840739
    },
    "bbox_err": {
      "n": 1374,
      "mean": 0.7704678583691252,
      "median": 0.0900005944569912,
      "sd_sample": 2.331139457250466,
      "min": 0.0,
      "max": 35.911292016387044,
      "q25": 1.1966788685905763e-07,
      "q75": 0.33333396928737097,
      "q95": 4.067249949759431,
      "q99": 12.769116967454602
    },
    "bbox_ratio_to_gt": {
      "n": 1374,
      "mean": 0.9992756141142246,
      "median": 0.9999999997869191,
      "sd_sample": 0.05525839775605888,
      "min": 0.1629901366307251,
      "max": 1.5678655933309156,
      "q25": 0.9985296490112057,
      "q75": 1.0000209424474544,
      "q95": 1.026799652937597,
      "q99": 1.1752143191788471
    }
  },
  "unconditional_f_score_1pct": {
    "n": 2500,
    "mean": 0.08580914714520282,
    "median": 0.024086814413265305,
    "sd_sample": 0.10655926062648167,
    "min": 0.0,
    "max": 0.47216342425025853,
    "q25": 0.0,
    "q75": 0.17626006319252077,
    "q95": 0.2880569716631356,
    "q99": 0.3577807679779428
  },
  "non_scoreable_error_counts": {
    "exec error: topology reference 'join_001:top_face:b9ce48e7f7b9' did not resolve any face": 131,
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'profile'": 119,
    "exec error: Part.linear_pattern() got an unexpected keyword argument 'target_offset'": 69,
    "exec error: mirror: plane must be 'YZ', 'XZ', or 'XY'": 67,
    "exec error: target must be a FeatureHandle": 45,
    "exec error: offset must be a 3D sequence": 44,
    "exec error: 'Part' object has no attribute 'lobed_gasket_profile'": 42,
    "exec error: Part.rectangular_pocket() got an unexpected keyword argument 'height'": 38,
    "exec error: 'pocket_depth'": 35,
    "exec error: topology reference 'chamfer_001:top_outer_edges:1c8e3f3146f4' did not resolve any edge_set": 28,
    "exec error: Part.__init__() got an unexpected keyword argument 'semantic_type'": 28,
    "exec error: Part.sketch_on_face() got an unexpected keyword argument 'min_x'": 26,
    "exec error: 'Part' object has no attribute 'ribbed_plate'": 25,
    "SyntaxError: unterminated string literal (detected at line 10) (<unknown>, line 10)": 23,
    "exec error: Part.plate() got an unexpected keyword argument 'radius'": 22,
    "exec error: 'Part' object has no attribute 'cone_bushing'": 20,
    "STEP export error: OCCT build failed": 17,
    "exec error: name 'thickness' is not defined": 17,
    "exec error: 'Part' object has no attribute 'loft_shell'": 15,
    "exec error: 'Part' object has no attribute 'disk'": 14,
    "exec error: Part.__init__() got an unexpected keyword argument 'params'": 14,
    "exec error: Part.clamp_pad_plate() got an unexpected keyword argument 'pocket_width'": 12,
    "exec error: Parameters.add() takes 3 positional arguments but 5 positional arguments (and 3 keyword-only arguments) were given": 11,
    "SyntaxError: '(' was never closed (<unknown>, line 20)": 11,
    "exec error: 'FeatureHandle' object has no attribute 'chamfer'": 10,
    "exec error: Part.linear_pattern() got an unexpected keyword argument 'template'": 10,
    "exec error: Part.bossed_plate() got an unexpected keyword argument 'chamfer_distance'": 9,
    "SyntaxError: '[' was never closed (<unknown>, line 7)": 9,
    "exec error: 'Part' object has no attribute 'path'": 8,
    "SyntaxError: invalid syntax. Perhaps you forgot a comma? (<unknown>, line 18)": 8,
    "exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'diameter'": 7,
    "exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'offset_x'": 7,
    "SyntaxError: '[' was never closed (<unknown>, line 14)": 7,
    "exec error: Part.loft() got an unexpected keyword argument 'profile'": 6,
    "exec error: Part.revolved_bushing() got an unexpected keyword argument 'inner_height'": 5,
    "exec error: 'width'": 5,
    "exec error: Parameters.add() takes 3 positional arguments but 5 positional arguments (and 1 keyword-only argument) were given": 5,
    "exec error: Part.revolved_bushing() got an unexpected keyword argument 'section_offset'": 5,
    "exec error: unsupported operand type(s) for *: 'ParameterRef' and 'float'": 4,
    "exec error: Part.pin_cluster() got an unexpected keyword argument 'thickness'": 4,
    "exec error: Part.cone() got an unexpected keyword argument 'radius_bottom'": 4,
    "exec error: 'inner_radius'": 4,
    "exec error: topology reference 'hole_002:top_face:40c6147e08ec' did not resolve any face": 4,
    "exec error: Part.ribbed_support_plate() got an unexpected keyword argument 'hole_offset_x'": 4,
    "exec error: 'Part' object has no attribute 'lug_plate'": 4,
    "exec error: can't multiply sequence by non-int of type 'ParameterRef'": 3,
    "exec error: 'bbox_radius * 2.28'": 3,
    "exec error: 'path_width'": 3,
    "exec error: 'height'": 3,
    "exec error: Part.pin_cluster() got an unexpected keyword argument 'radius_step'": 3,
    "exec error: target must be a TopologyReference from a FeatureHandle": 3,
    "exec error: Part.boss() got an unexpected keyword argument 'profile'": 3,
    "SyntaxError: invalid syntax (<unknown>, line 12)": 2,
    "exec error: hole pattern positions must be 2D or 3D sequences": 2,
    "exec error: 'Part' object has no attribute 'pocket'": 2,
    "exec error: 'Part' object has no attribute 'pocket_and_fill'": 2,
    "exec error: Part.__init__() got an unexpected keyword argument 'sample_count'": 2,
    "exec error: name 'profiles' is not defined": 2,
    "exec error: 'Part' object has no attribute 'chamfered_bolt_hole_plate'": 2,
    "exec error: 'Part' object has no attribute 'sketch_sphere'": 2,
    "exec error: 'Part' object has no attribute 'clamp_plate'": 2,
    "exec error: 'Part' object has no attribute 'clipped_stock'": 2,
    "exec error: Part.boolean_join() got an unexpected keyword argument 'operation'": 2,
    "SyntaxError: unterminated string literal (detected at line 16) (<unknown>, line 16)": 2,
    "exec error: unsupported operand type(s) for *: 'ParameterRef' and 'ParameterRef'": 2,
    "SyntaxError: '(' was never closed (<unknown>, line 9)": 2,
    "exec error: 'Part' object has no attribute 'bearing_block'": 2,
    "exec error: 'Part' object has no attribute 'conical_bushing'": 2,
    "SyntaxError: invalid character '\u2212' (U+2212) (<unknown>, line 7)": 1,
    "exec error: 'Part' object has no attribute 'path_on_plate'": 1,
    "SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 15)": 1,
    "exec error: 'Part' object has no attribute 'paths'": 1,
    "exec error: Part.__init__() got an unexpected keyword argument 'style_name'": 1,
    "exec error: 'bbox_radius * 2.24'": 1,
    "exec error: 'Part' object has no attribute 'conical_boss_plate'": 1,
    "exec error: Part.linear_pattern() got an unexpected keyword argument 'target_expression'": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 15)": 1,
    "exec error: 'path_profile'": 1,
    "exec error: Part.rotate() got an unexpected keyword argument 'axis'": 1,
    "exec error: 'Part' object has no attribute 'finned_straight_plate'": 1,
    "exec error: Part.bossed_plate() got an unexpected keyword argument 'boss_width'": 1,
    "SyntaxError: invalid syntax (<unknown>, line 13)": 1,
    "exec error: 'Part' object has no attribute 'sketch_paths'": 1,
    "exec error: 'Part' object has no attribute 'profile_from_path'": 1,
    "exec error: 'Part' object has no attribute 'chamfered_tube'": 1,
    "exec error: unsupported sketch_on_face profile [[-7.98, -8.7], [7.98, -8.7], [7.98, 8.7], [2.05, 8.7], [2.05, -3.23], [-7.98, -3.23], [-7.98, 8.7], [-2.05, 8.7], [-2.05, 3.23]]": 1,
    "SyntaxError: closing parenthesis ']' does not match opening parenthesis '(' (<unknown>, line 15)": 1,
    "exec error: unsupported sketch_on_face profile [[-8.2, -7.6], [8.2, -7.6], [8.2, 7.6], [2.0, 7.6], [2.0, -2.94], [-8.2, -2.94], [-8.2, 7.6], [-2.0, 7.6], [-2.0, 2.94]]": 1,
    "exec error: topology reference 'chamfer_001:top_face:f40479b908d2' did not resolve any face": 1,
    "exec error: unsupported sketch_on_face profile [[-6.96, -10.375], [6.96, -10.375], [6.96, 10.375], [2.05, 10.375], [2.05, -3.74], [-6.96, -3.74], [-6.96, 10.375], [-2.05, 10.375], [-2.05, 3.74]]": 1,
    "exec error: Part.boolean_cut() got an unexpected keyword argument 'offset'": 1,
    "point cloud sampling failed on generated part": 1,
    "exec error: unsupported sketch_on_face profile [[-9.9, -8.45], [9.9, -8.45], [19.8, 5.8], [12.6, 5.8], [6.3, 13.65], [-6.3, 13.65], [-12.6, 5.8], [-19.8, -5.8]]": 1,
    "exec error: unsupported sketch_on_face profile [[-7.98, -7.7], [0.0, -10.4], [8.16, -7.0], [7.98, 0.5], [3.12, 7.7], [-0.0, 10.4], [-8.16, 7.0]]": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 15)": 1,
    "exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'hole_diameter'": 1,
    "exec error: unsupported sketch_on_face profile [[-7.4, -8.4], [7.4, -8.4], [7.4, 8.4], [-7.4, 8.4]]": 1,
    "SyntaxError: invalid syntax (<unknown>, line 23)": 1,
    "exec error: unsupported sketch_on_face profile [[-7.46, -8.7], [7.46, -8.7], [7.46, 8.7], [2.05, 8.7], [2.05, -3.23], [-2.05, -3.23], [-2.05, 8.7], [-7.46, 8.7]]": 1,
    "exec error: unsupported sketch_on_face profile [[-6.96, -9.9], [6.96, -9.9], [6.96, 9.9], [2.05, 9.9], [2.05, -5.34], [-6.96, -5.34], [-6.96, 9.9], [-2.05, 9.9], [-2.05, 5.34]]": 1,
    "exec error: unsupported sketch_on_face profile [[-30.07, -31.94], [30.07, -31.94], [30.07, 31.94], [-30.07, 31.94]]": 1,
    "exec error: 'thickness'": 1,
    "exec error: unsupported sketch_on_face profile [[-8.2, -8.68], [8.2, -8.68], [8.2, 8.68], [2.05, 8.68], [2.05, -3.41], [-8.2, -3.41], [-8.2, 8.68], [-2.05, 8.68], [-2.05, 3.41]]": 1,
    "SyntaxError: unterminated string literal (detected at line 8) (<unknown>, line 8)": 1,
    "exec error: Part.__init__() got an unexpected keyword argument 'sample_name'": 1,
    "exec error: unsupported sketch_on_face profile [[-31.64, -20.06], [31.64, -20.06], [31.64, 17.94], [18.4, 17.94], [18.4, -10.22], [-31.64, -10.22], [-31.64, 20.06]]": 1,
    "exec error: unsupported sketch_on_face profile [[-6.48, -9.4], [6.48, -9.4], [6.48, 9.4], [2.03, 9.4], [2.03, -4.94], [-6.48, -4.94], [-6.48, 9.4], [-2.03, 9.4], [-2.03, 4.94]]": 1,
    "exec error: unsupported sketch_on_face profile [[-7.58, -7.35], [7.58, -7.35], [7.58, 7.35], [2.0, 7.35], [2.0, -2.83], [-7.58, -2.83], [-7.58, 7.35], [-2.0, 7.35], [-2.0, 2.83]]": 1,
    "SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 18)": 1,
    "exec error: 'Part' object has no attribute 'standoff_plate'": 1,
    "exec error: 'Part' object has no attribute 'sketch'": 1,
    "exec error: 'Part' object has no attribute 'sketch_on_profile'": 1,
    "exec error: Part.linear_pattern() got an unexpected keyword argument 'length'": 1,
    "exec error: unsupported sketch_on_face profile [[-7.7, -5.7], [7.7, -5.7], [7.7, 5.7], [-7.7, 5.7]]": 1,
    "exec error: 'Part' object has no attribute 'sweep_on_path'": 1,
    "exec error: 'Part' object has no attribute 'number_value'": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 21)": 1,
    "exec error: Part.clipped_offset_stock() got an unexpected keyword argument 'offset_mode'": 1,
    "exec error: box() got an unexpected keyword argument 'name'": 1,
    "exec error: 'length'": 1,
    "exec error: unsupported sketch_on_face profile [[-7.54, -8.5], [7.54, -8.5], [7.54, 8.5], [2.0, 8.5], [2.0, -3.1], [-2.0, -3.1], [-2.0, 8.5], [-7.54, 8.5]]": 1,
    "exec error: unsupported sketch_on_face profile [[-7.0, -7.05], [7.0, -7.05], [7.0, 7.05], [-7.0, 7.05]]": 1,
    "exec error: 'Part' object has no attribute 'cone_pocket'": 1,
    "exec error: unsupported sketch_on_face profile [[-7.74, -10.47], [7.74, -10.47], [7.74, 10.47], [2.05, 10.47], [2.05, -3.79], [-7.74, -3.79], [-7.74, 10.47], [-2.05, 10.47], [-2.05, 3.79]]": 1,
    "exec error: Part.__init__() takes 2 positional arguments but 3 positional arguments (and 1 keyword-only argument) were given": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 17)": 1,
    "exec error: unsupported sketch_on_face profile [[-6.9, -9.3], [6.9, -9.3], [6.9, 9.3], [2.05, 9.3], [2.05, -4.64], [-6.9, -4.64], [-6.9, 9.3], [-2.05, 9.3]]": 1,
    "exec error: 'Part' object has no attribute 'l_bracket'": 1,
    "exec error: Part.extrude() got an unexpected keyword argument 'target'": 1,
    "exec error: 'sketch_profile'": 1,
    "exec error: topology reference 'join_002:top_outer_edges:4d857136f852' did not resolve any edge_set": 1,
    "exec error: Part.sphere() got an unexpected keyword argument 'height'": 1,
    "SyntaxError: unterminated string literal (detected at line 9) (<unknown>, line 9)": 1,
    "exec error: 'Part' object has no attribute 'box_pattern'": 1,
    "exec error: unsupported sketch_on_face profile [[-8.1, -7.28], [8.1, -7.28], [8.1, 7.28], [2.05, 7.28], [2.05, -2.74], [-8.1, -2.74], [-8.1, 7.28], [-2.05, 7.28]]": 1,
    "exec error: unsupported sketch_on_face profile [[-7.3, -8.1], [7.3, -8.1], [7.3, 8.1], [2.0, 8.1], [2.0, -3.14], [-2.0, -3.14], [-2.0, 8.1], [-7.3, 8.1]]": 1,
    "exec error: Part.sweep() got an unexpected keyword argument 'target'": 1,
    "exec error: unsupported sketch_on_face profile [[-7.7, -6.6], [7.7, -6.6], [7.7, 6.6], [-7.7, 6.6]]": 1,
    "SyntaxError: invalid syntax (<unknown>, line 15)": 1
  },
  "extreme_cd_cases_gt_1000": [],
  "export_but_unscoreable_ids": [
    "flluma_0093569"
  ]
}
```

### B2

```json
{
  "rows": 2500,
  "scoreable": 1676,
  "scoreable_pct": 67.04,
  "gate_counts_from_geometry_run": {
    "syntax_ok": 2414,
    "exec_ok": 1719,
    "build_ok": 1719,
    "solid_valid": 1719,
    "step_export_ok": 1707
  },
  "missing_target_rows": 0,
  "conditional": {
    "cd": {
      "n": 1676,
      "mean": 269635092.47724086,
      "median": 2.905941882504827,
      "sd_sample": 6370346834.439492,
      "min": 0.027049981743364485,
      "max": 154348704090.14868,
      "q25": 1.7855555871444928,
      "q75": 6.166754279727926,
      "q95": 23.272272103032673,
      "q99": 245.50365276260004
    },
    "f_score_1pct": {
      "n": 1676,
      "mean": 0.18499405204045188,
      "median": 0.18699004569190603,
      "sd_sample": 0.10338014168745557,
      "min": 0.0,
      "max": 0.45207250607451405,
      "q25": 0.09373982747395833,
      "q75": 0.26693898537477145,
      "q95": 0.35204604065533984,
      "q99": 0.3974826971160368
    },
    "bbox_err": {
      "n": 1676,
      "mean": 598.1563731848053,
      "median": 0.20621278227933743,
      "sd_sample": 14094.174452822012,
      "min": 0.0,
      "max": 333332.6474866731,
      "q25": 0.004193406563059554,
      "q75": 0.9068316717541913,
      "q95": 7.712645289589052,
      "q99": 20.50029266461055
    },
    "bbox_ratio_to_gt": {
      "n": 1676,
      "mean": 41.180589076466276,
      "median": 1.0000000000014584,
      "sd_sample": 949.8922835956988,
      "min": 0.1442760203172557,
      "max": 23140.507288671968,
      "q25": 0.9978080794035137,
      "q75": 1.0037218391401053,
      "q95": 1.0352922378983338,
      "q99": 1.196604571745869
    }
  },
  "unconditional_f_score_1pct": {
    "n": 2500,
    "mean": 0.12402001248791894,
    "median": 0.0959311295306511,
    "sd_sample": 0.12136097608875024,
    "min": 0.0,
    "max": 0.45207250607451405,
    "q25": 0.0,
    "q75": 0.22505634829175705,
    "q95": 0.3330294701885011,
    "q99": 0.38673080348368677
  },
  "non_scoreable_error_counts": {
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'height'": 55,
    "exec error: Part.extrude_on_face() got an unexpected keyword argument 'profile'": 50,
    "exec error: 'Part' object has no attribute 'threaded_bearing_hole_on_face'": 36,
    "exec error: topology reference 'join_001:top_face:b9ce48e7f7b9' did not resolve any face": 35,
    "exec error: Part.sketch_on_face() got an unexpected keyword argument 'size'": 32,
    "point cloud sampling failed on generated part": 31,
    "exec error: Part.boolean_cut() got an unexpected keyword argument 'depth'": 30,
    "exec error: 'list' object has no attribute 'strip'": 29,
    "exec error: unsupported operand type(s) for *: 'ParameterRef' and 'float'": 24,
    "exec error: extrude_on_face cut requires depth": 23,
    "SyntaxError: invalid syntax (<unknown>, line 1)": 18,
    "exec error: 'Part' object has no attribute 'rectangular_cut'": 17,
    "SyntaxError: unmatched ']' (<unknown>, line 1)": 17,
    "exec error: Part.profile_cut_on_face() got an unexpected keyword argument 'width'": 16,
    "exec error: Part.revolve() got an unexpected keyword argument 'angle'": 16,
    "exec error: 'Part' object has no attribute 'lofted_transition'": 13,
    "exec error: 'Part' object has no attribute 'sweep_pipe_bracket'": 12,
    "exec error: Part.rotate() got an unexpected keyword argument 'angle'": 12,
    "exec error: target must be a FeatureHandle": 12,
    "STEP export error: OCCT build failed": 12,
    "exec error: Part.revolved_bushing() got an unexpected keyword argument 'revolve_angle'": 11,
    "exec error: 'Part' object has no attribute 'sweep_plate'": 10,
    "exec error: target must be a TopologyReference from a FeatureHandle": 10,
    "exec error: Part.profile_cut_on_face() got an unexpected keyword argument 'distance'": 8,
    "exec error: direction must be 'inward' or 'outward'": 8,
    "exec error: Part.revolve() got an unexpected keyword argument 'axis'": 7,
    "exec error: name 'path_length' is not defined": 7,
    "exec error: 'Part' object has no attribute 'boolean_pocket'": 7,
    "exec error: Part.circular_pattern() got an unexpected keyword argument 'step'": 7,
    "exec error: topology reference 'join_002:top_face:323af5d41048' did not resolve any face": 6,
    "exec error: 'Part' object has no attribute 'extrude_solid'": 6,
    "exec error: 'height'": 6,
    "exec error: 'width'": 6,
    "exec error: Part.loft() got an unexpected keyword argument 'height'": 5,
    "SyntaxError: invalid syntax (<unknown>, line 2)": 5,
    "exec error: Part.bossed_plate() missing 2 required keyword-only arguments: 'hole_radius' and 'hole_positions'": 5,
    "exec error: unsupported operand type(s) for /: 'ParameterRef' and 'float'": 4,
    "SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers (<unknown>, line 1)": 4,
    "exec error: offset must be a 3D sequence": 4,
    "exec error: 'Part' object has no attribute 'revolved_hub_mount'": 4,
    "exec error: name 'solid' is not defined": 4,
    "exec error: Part.plate() got an unexpected keyword argument 'radius'": 4,
    "exec error: Part.circular_pattern() got an unexpected keyword argument 'radius'": 4,
    "exec error: topology reference 'loft_001:top_face:b95a905e855a' did not resolve any face": 3,
    "exec error: 'Part' object has no attribute 'translate_many'": 3,
    "exec error: Part.shell() got an unexpected keyword argument 'box'": 3,
    "exec error: Part.loft() got an unexpected keyword argument 'profile'": 3,
    "exec error: 'FeatureHandle' object has no attribute 'cut_face'": 3,
    "exec error: Part.revolve() got an unexpected keyword argument 'radius'": 3,
    "exec error: 'Part' object has no attribute 'clamp_plate'": 3,
    "exec error: unsupported operand type(s) for +: 'ParameterRef' and 'float'": 3,
    "exec error: 'Part' object has no attribute 'boolean_cover'": 3,
    "SyntaxError: '[' was never closed (<unknown>, line 8)": 2,
    "SyntaxError: invalid syntax. Maybe you meant '==' or ':=' instead of '='? (<unknown>, line 1)": 2,
    "exec error: 'Part' object has no attribute 'ribbed_heat_sink'": 2,
    "exec error: 'Part' object has no attribute 'profile_cut'": 2,
    "SyntaxError: '(' was never closed (<unknown>, line 38)": 2,
    "exec error: Part.pin_cluster() got an unexpected keyword argument 'x'": 2,
    "exec error: Part.rectangular_pocket() got an unexpected keyword argument 'height'": 2,
    "exec error: Part.bossed_plate() got an unexpected keyword argument 'boss_profile_length'": 2,
    "exec error: 'ParameterRef' object is not subscriptable": 2,
    "SyntaxError: '(' was never closed (<unknown>, line 39)": 2,
    "exec error: 'Part' object has no attribute 'rectangular_cover'": 2,
    "SyntaxError: '[' was never closed (<unknown>, line 34)": 2,
    "exec error: mirror: plane must be 'YZ', 'XZ', or 'XY'": 2,
    "exec error: 'Part' object has no attribute 'sweep_pipe'": 2,
    "SyntaxError: '(' was never closed (<unknown>, line 36)": 2,
    "exec error: 'flange_height'": 2,
    "exec error: 'Part' object has no attribute 'hole'": 2,
    "exec error: bad operand type for unary -: 'ParameterRef'": 2,
    "exec error: Part.bossed_plate() got an unexpected keyword argument 'chamfer_distance'": 2,
    "exec error: 'Part' object has no attribute 'place_on_faces'": 2,
    "exec error: 'Part' object has no attribute 'hub_body'": 2,
    "exec error: 'Part' object has no attribute 'hollow_revolved_hub'": 2,
    "SyntaxError: '[' was never closed (<unknown>, line 7)": 2,
    "SyntaxError: '(' was never closed (<unknown>, line 40)": 2,
    "exec error: 'flange_radius'": 2,
    "exec error: 'Part' object has no attribute 'boolean_fit'": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 19)": 1,
    "exec error: Part.__init__() got an unexpected keyword argument 'minimum'": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 35)": 1,
    "SyntaxError: unterminated string literal (detected at line 34) (<unknown>, line 34)": 1,
    "exec error: Part.__init__() got an unexpected keyword argument 'description'": 1,
    "exec error: 'lug_radius_projected'": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 16)": 1,
    "exec error: Part.box() got an unexpected keyword argument 'size'": 1,
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'length'": 1,
    "exec error: Part.hole_pattern() got an unexpected keyword argument 'position'": 1,
    "exec error: name 'pocket_tool' is not defined": 1,
    "exec error: unsupported operand type(s) for +: 'ParameterRef' and 'ParameterRef'": 1,
    "exec error: Part.sketch_circle() got an unexpected keyword argument 'points'": 1,
    "exec error: Part.mirrored_lug_plate() got an unexpected keyword argument 'lug_offset_y'": 1,
    "exec error: topology reference 'cut_001:top_face:e6c86e3e481d' did not resolve any face": 1,
    "exec error: Part.translate() got an unexpected keyword argument 'angle'": 1,
    "exec error: Part.bossed_plate() got an unexpected keyword argument 'hole_offsets'": 1,
    "exec error: 'pocket_length_2'": 1,
    "exec error: Part.translate() got an unexpected keyword argument 'x'": 1,
    "exec error: 'Part' object has no attribute 'bearing_block_plate'": 1,
    "exec error: 'Part' object has no attribute 'cut_path'": 1,
    "exec error: 'FeatureHandle' object has no attribute 'join'": 1,
    "exec error: keyword argument repeated: radius (<candidate>, line 23)": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 32)": 1,
    "SyntaxError: invalid syntax (<unknown>, line 37)": 1,
    "exec error: 'TopologyReference' object is not iterable": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 20)": 1,
    "exec error: 'Part' object has no attribute 'boolean_hole'": 1,
    "exec error: 'Part' object has no attribute 'rectangular_pocket_profile'": 1,
    "exec error: Part.rail_mount_plate() got an unexpected keyword argument 'boss_radius'": 1,
    "exec error: name 'template' is not defined": 1,
    "SyntaxError: invalid syntax (<unknown>, line 19)": 1,
    "exec error: Part.revolved_bushing() got an unexpected keyword argument 'profile_segments'": 1,
    "exec error: Part.box() got an unexpected keyword argument 'depth'": 1,
    "SyntaxError: unterminated string literal (detected at line 37) (<unknown>, line 37)": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 42)": 1,
    "exec error: Part.linear_pattern() got an unexpected keyword argument 'spacing'": 1,
    "exec error: 'FeatureHandle' object has no attribute 'top_edge'": 1,
    "exec error: unsupported operand type(s) for -: 'ParameterRef' and 'float'": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 37)": 1,
    "exec error: Part.rectangular_pocket() got an unexpected keyword argument 'x_offset'": 1,
    "exec error: 'Part' object has no attribute 'torus_adapter'": 1,
    "exec error: 'FeatureHandle' object has no attribute 'create_offset_pocket'": 1,
    "exec error: 'Part' object has no attribute 'sweep_on_path'": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 27)": 1,
    "exec error: 'tube_radius'": 1,
    "exec error: Part.boolean_cut() got an unexpected keyword argument 'offset'": 1,
    "exec error: 'FeatureHandle' object has no attribute 'edge_loop'": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 40)": 1,
    "exec error: Part.translate() got an unexpected keyword argument 'point'": 1,
    "exec error: 'Part' object has no attribute 'circle'": 1,
    "exec error: Part.revolve() got an unexpected keyword argument 'path_radius'": 1,
    "exec error: 'Part' object has no attribute 'places'": 1,
    "exec error: Part.revolved_bushing() got an unexpected keyword argument 'work_height'": 1,
    "exec error: depth must resolve to a number, got 'through'": 1,
    "exec error: 'Part' object has no attribute 'sweep_profile'": 1,
    "exec error: 'FeatureHandle' object has no attribute 'top_hole'": 1,
    "exec error: Part.bossed_plate() got an unexpected keyword argument 'boss_overlap'": 1,
    "exec error: 'Part' object has no attribute 'cap_pattern'": 1,
    "exec error: 'bbox_size'": 1,
    "exec error: Part.bossed_plate() got an unexpected keyword argument 'hole_depth'": 1,
    "exec error: name 'mirror_4' is not defined": 1,
    "exec error: 'Part' object has no attribute 'fin_on_plate'": 1,
    "exec error: 'plate_width'": 1,
    "exec error: Part.clamp_pad_plate() got an unexpected keyword argument 'clamp_pad_radius'": 1,
    "exec error: Part.sensor_mount_plate() got an unexpected keyword argument 'boss_top_position'": 1,
    "exec error: Part.clamp_pad_plate() got an unexpected keyword argument 'radius'": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 16)": 1,
    "exec error: Part.revolved_bushing() got an unexpected keyword argument 'work_radius'": 1,
    "exec error: 'Part' object has no attribute 'clamp'": 1,
    "exec error: Part.loft() got an unexpected keyword argument 'lower_radius'": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 14)": 1,
    "exec error: Part.translate() got an unexpected keyword argument 'positions'": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 41)": 1,
    "exec error: Part.__init__() got an unexpected keyword argument 'title'": 1,
    "exec error: 'flange_width'": 1,
    "SyntaxError: invalid syntax (<unknown>, line 35)": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 38)": 1,
    "exec error: 'Part' object has no attribute 'linear_ribbed_plate'": 1,
    "exec error: could not convert string to float: 'circle_radius'": 1,
    "exec error: 'Part' object has no attribute 'cut_pattern'": 1,
    "exec error: Part.rectangular_pocket() got an unexpected keyword argument 'profile'": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 12)": 1,
    "exec error: 'FeatureHandle' object has no attribute 'lower_profile'": 1,
    "exec error: float() argument must be a string or a real number, not 'list'": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 43)": 1,
    "SyntaxError: unterminated string literal (detected at line 36) (<unknown>, line 36)": 1,
    "exec error: topology reference 'hole_002:top_face:40c6147e08ec' did not resolve any face": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 36)": 1,
    "exec error: 'Part' object has no attribute 'sketch_to_shell'": 1,
    "exec error: parameter 'pocket_width' already exists": 1,
    "exec error: step must be a 3D sequence": 1,
    "exec error: 'slot_profile'": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 20)": 1,
    "exec error: 'Part' object has no attribute 'sketch_on_plate'": 1,
    "exec error: thickness must resolve to a number, got [0.87, 4.71, 18.14, 10.04]": 1,
    "exec error: Part.bossed_plate() got an unexpected keyword argument 'boss_profile_height'": 1,
    "exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'offset_reference'": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 9)": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 22)": 1,
    "exec error: 'Part' object has no attribute 'boolean_subtract'": 1,
    "exec error: 'Part' object has no attribute 'hole_drill'": 1,
    "exec error: Part.rectangular_pocket() got an unexpected keyword argument 'position'": 1,
    "exec error: topology reference 'intersect_004:top_face:13326aa0d03f' did not resolve any face": 1,
    "exec error: workplane_polygon requires at least 3 points": 1,
    "exec error: 'Part' object has no attribute 'holes'": 1,
    "SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers (<unknown>, line 7)": 1,
    "exec error: 'Part' object has no attribute 'cross_tab'": 1,
    "exec error: topology reference 'intersect_002:top_face:35b57a3f0eb3' did not resolve any face": 1,
    "exec error: 'Part' object has no attribute 'hollow_dished_umbilical_hub'": 1,
    "exec error: Part.__init__() got an unexpected keyword argument 'minimum_fillet_radius'": 1,
    "exec error: Part.revolved_bushing() got an unexpected keyword argument 'revolve_axis_height'": 1,
    "exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'depth_max'": 1,
    "exec error: 'length'": 1
  },
  "extreme_cd_cases_gt_1000": [
    {
      "sample_id": "flluma_0091972",
      "syntax_ok": true,
      "exec_ok": true,
      "build_ok": true,
      "solid_valid": true,
      "step_export_ok": true,
      "error": "",
      "cd": 154348704090.14868,
      "bbox_err": 333332.2893706157,
      "f_score_1pct": 0.006310096153846154,
      "target_bbox_diag": 43.214501222137294,
      "gen_bbox_diag": 1000005.4805071917,
      "bbox_ratio_to_gt": 23140.507288671968,
      "has_target": true
    },
    {
      "sample_id": "flluma_0091396",
      "syntax_ok": true,
      "exec_ok": true,
      "build_ok": true,
      "solid_valid": true,
      "step_export_ok": true,
      "error": "",
      "cd": 1257.6740740081182,
      "bbox_err": 36.98833378129688,
      "f_score_1pct": 0.0224609375,
      "target_bbox_diag": 94.53604588899762,
      "gen_bbox_diag": 165.75218459465432,
      "bbox_ratio_to_gt": 1.7533225875480059,
      "has_target": true
    },
    {
      "sample_id": "flluma_0093152",
      "syntax_ok": true,
      "exec_ok": true,
      "build_ok": true,
      "solid_valid": true,
      "step_export_ok": true,
      "error": "",
      "cd": 149538513050.95206,
      "bbox_err": 333332.6474866731,
      "f_score_1pct": 0.0048828125,
      "target_bbox_diag": 46.43739631201155,
      "gen_bbox_diag": 1000003.7108606084,
      "bbox_ratio_to_gt": 21534.44831707643,
      "has_target": true
    },
    {
      "sample_id": "flluma_0091031",
      "syntax_ok": true,
      "exec_ok": true,
      "build_ok": true,
      "solid_valid": true,
      "step_export_ok": true,
      "error": "",
      "cd": 148021180925.1762,
      "bbox_err": 333331.96529092605,
      "f_score_1pct": 0.0033482142857142855,
      "target_bbox_diag": 44.06664698004512,
      "gen_bbox_diag": 1000002.0008886699,
      "bbox_ratio_to_gt": 22692.945105206323,
      "has_target": true
    }
  ],
  "export_but_unscoreable_ids": [
    "flluma_0094674",
    "flluma_0091127",
    "flluma_0096615",
    "flluma_0093847",
    "flluma_0091458",
    "flluma_0098661",
    "flluma_0090550",
    "flluma_0091413",
    "flluma_0098055",
    "flluma_0092712",
    "flluma_0099816",
    "flluma_0091789",
    "flluma_0093446",
    "flluma_0091864",
    "flluma_0093569",
    "flluma_0092623",
    "flluma_0097180",
    "flluma_0095019",
    "flluma_0090798",
    "flluma_0092463",
    "flluma_0096851",
    "flluma_0094884",
    "flluma_0099659",
    "flluma_0093807",
    "flluma_0097035",
    "flluma_0097575",
    "flluma_0090226",
    "flluma_0096445",
    "flluma_0097952",
    "flluma_0097017",
    "flluma_0095884"
  ]
}
```

## Provenance

Generation actuals: `__RUN_SOURCE_ROOT__\outputs\b0_b2_fullstack_s1\cag_b0_b2_seed_1_actuals.json`.
Generation actuals SHA256: `f260254f2f94ace974c6634e985637a7a236581fb81b6bd8de543d51ca8806f0`.
All 2500 paired-case rows: `__EVIDENCE_SOURCE_ROOT__\03\result\cag_b0_b2_seed_1_paired_cases.jsonl`.

B0 files and SHA256:

```json
{
  "__DEV_ROOT__\\scratch\\exec_b0b2_step_B0_s1\\execution_rows.jsonl": "692bfaf8c45cb917d9504a6cde490547985cb6aebbee5bf753e1e506136c1107",
  "__DEV_ROOT__\\scratch\\geom_b0b2_step_B0_s1\\geometry_nbest_rows.jsonl": "28c4dbc37ec5d19806144b79c1042140e68cd978a3080e412ff42cb32a12fd15",
  "__DEV_ROOT__\\scratch\\exec_b0b2_step_B0_s1\\execution_summary.json": "b09a9336d0fb055d8da6d969bbd670187299801c1ca9ce95cdefdcfc53776d1e",
  "__RUN_SOURCE_ROOT__\\outputs\\b0_b2_fullstack_s1\\predictions\\gen_step_B0_s1.jsonl": "513d069742ae7758861d173de74e5a99046e934828760828bcf160aa3e89f132",
  "__RUN_SOURCE_ROOT__\\outputs\\b0_b2_fullstack_s1\\predictions\\geom_input_step_B0_s1.jsonl": "1fdb5f7944a2d5ed8b4ebf13dc09d1134251a5392f417f1be29069ab9c0c2b49"
}
```

B2 files and SHA256:

```json
{
  "__DEV_ROOT__\\scratch\\exec_b0b2_step_B2_s1\\execution_rows.jsonl": "2617d7f1ee668b0510bb85a8e5478ead458a083c5916762ba511e2022a51fd2d",
  "__DEV_ROOT__\\scratch\\geom_b0b2_step_B2_s1\\geometry_nbest_rows.jsonl": "4f70dd07def2f7cae193cbdc4413d5ccc264f088aebb4fb09382901fb3786967",
  "__DEV_ROOT__\\scratch\\exec_b0b2_step_B2_s1\\execution_summary.json": "383f97d777c6ca5db6ad8ba49fa4482dc7fb1b7df2b2a9759267cdd5fbbaa851",
  "__RUN_SOURCE_ROOT__\\outputs\\b0_b2_fullstack_s1\\predictions\\gen_step_B2_s1.jsonl": "4c0c070a6a82e927011332aa4dd412da9e2aa7c486729f0fb07fdda7b0b3e034",
  "__RUN_SOURCE_ROOT__\\outputs\\b0_b2_fullstack_s1\\predictions\\geom_input_step_B2_s1.jsonl": "b56c88b213bcc7de8c9e1a27117fa3040378182269786ad7034e6bf685fb60a8"
}
```

Evaluator-source hashes describe files present at analysis time; they are not a historical build attestation. See the frozen generation actuals and earlier run records for training-code provenance.

# Seed 2 Evaluation Record

Audit: PASS. Evaluation complete.

| Seed | Arm | Syntax | Execute | Build | Solid | STEP export | Scoreable |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | B0 | 2442/2500 (97.68%) | 1297/2500 (51.88%) | 1297/2500 (51.88%) | 1297/2500 (51.88%) | 1219/2500 (48.76%) | 1206/2500 (48.24%) |
| 2 | B2 | 2385/2500 (95.40%) | 1440/2500 (57.60%) | 1440/2500 (57.60%) | 1440/2500 (57.60%) | 1422/2500 (56.88%) | 1355/2500 (54.20%) |

## Geometry

| Metric | B0 | B2 | B2 - B0 |
| --- | ---: | ---: | ---: |
| conditional_mean_cd | 13.5457931 | 128165251.4 | 128165237.8 |
| conditional_median_cd | 4.271995119 | 2.521431472 | -1.750563648 |
| conditional_mean_f1_pct | 16.5293689 | 19.87240817 | 3.343039269 |
| conditional_median_f1_pct | 17.32779489 | 20.16495157 | 2.837156679 |
| unconditional_mean_f1_pct | 7.973767556 | 10.77084523 | 2.79707767 |
| unconditional_median_f1_pct | 0 | 6.051537298 | 6.051537298 |
| paired_mean_cd | 12.30335074 | 6.690648388 | -5.612702354 |
| paired_median_cd | 3.825480446 | 2.504338468 | -1.321141978 |
| paired_mean_f1_pct | 17.43050404 | 21.83520203 | 4.404697991 |
| paired_median_f1_pct | 18.50469987 | 22.06858407 | 3.563884203 |
| conditional_mean_bbox_err | 1.448631338 | 247.2643057 | 245.8156744 |
| conditional_median_bbox_err | 0.1723342435 | 0.1000001909 | -0.07233405252 |

Percent metrics above use 0-100 units. CD/bbox remain in evaluator units. Conditional full-set and jointly scoreable metrics use different subsets.

## Paired Tests

Within-seed query-level tests below do not measure uncertainty across training seeds.

| Gate | Both | B0 only | B2 only | Neither | Delta pp | Exact McNemar p |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| syntax_ok | 2328 | 114 | 57 | 1 | -2.28 | 1.5596124e-05 |
| exec_ok | 838 | 459 | 602 | 601 | 5.72 | 1.2674846e-05 |
| build_ok | 838 | 459 | 602 | 601 | 5.72 | 1.2674846e-05 |
| solid_valid | 838 | 459 | 602 | 601 | 5.72 | 1.2674846e-05 |
| step_export_ok | 809 | 410 | 613 | 668 | 8.12 | 2.3599432e-10 |

Jointly scoreable: 747.

| Metric | B2 wins | B0 wins | Ties | Median paired difference B2 - B0 | Exact sign p |
| --- | ---: | ---: | ---: | ---: | ---: |
| cd | 458 | 289 | 0 | -0.09404826349 | 6.7221068e-10 |
| f_score_1pct | 484 | 263 | 0 | 0.01562539921 | 5.1233536e-16 |
| bbox_err | 345 | 277 | 125 | 0 | 0.0071730434 |

F@1 paired differences in the last table use raw 0-1 units. Multiply by 100 for percentage points.

## Distributions And Failures

No CD values were removed, clipped, or winsorized. CD > 1000 is a retrospective audit flag, not an exclusion rule.

### B0

```json
{
  "rows": 2500,
  "scoreable": 1206,
  "scoreable_pct": 48.24,
  "gate_counts_from_geometry_run": {
    "syntax_ok": 2442,
    "exec_ok": 1297,
    "build_ok": 1297,
    "solid_valid": 1297,
    "step_export_ok": 1219
  },
  "missing_target_rows": 0,
  "conditional": {
    "cd": {
      "n": 1206,
      "mean": 13.545793099642259,
      "median": 4.271995119236208,
      "sd_sample": 33.368593590660986,
      "min": 0.05167374861965572,
      "max": 658.6353000912466,
      "q25": 2.3011643826441763,
      "q75": 14.501857286910337,
      "q95": 47.076221291453734,
      "q99": 111.47880510518559
    },
    "f_score_1pct": {
      "n": 1206,
      "mean": 0.16529368896874852,
      "median": 0.17327794894366197,
      "sd_sample": 0.09977559151727035,
      "min": 0.0,
      "max": 0.451169761228355,
      "q25": 0.07037283360272989,
      "q75": 0.23710701345138094,
      "q95": 0.33069474594796966,
      "q99": 0.38029230231974137
    },
    "bbox_err": {
      "n": 1206,
      "mean": 1.4486313376379616,
      "median": 0.17233424345381493,
      "sd_sample": 3.4783734078981827,
      "min": 0.0,
      "max": 32.12999852449284,
      "q25": 8.694330847121752e-07,
      "q75": 1.0706452088325595,
      "q95": 7.23925148454953,
      "q99": 15.836500533418484
    },
    "bbox_ratio_to_gt": {
      "n": 1206,
      "mean": 0.9946380659017438,
      "median": 1.0000000000004745,
      "sd_sample": 0.11064278549697838,
      "min": 0.25456202674827877,
      "max": 1.9682719499288839,
      "q25": 0.9974317134433409,
      "q75": 1.002510767088616,
      "q95": 1.0890645880902683,
      "q99": 1.4113142288599991
    }
  },
  "unconditional_f_score_1pct": {
    "n": 2500,
    "mean": 0.07973767555852429,
    "median": 0.0,
    "sd_sample": 0.10781965946132073,
    "min": 0.0,
    "max": 0.451169761228355,
    "q25": 0.0,
    "q75": 0.1690472821138766,
    "q95": 0.29686709750070545,
    "q99": 0.36320154652548325
  },
  "non_scoreable_error_counts": {
    "exec error: target must be a TopologyReference from a FeatureHandle": 118,
    "exec error: Part.__init__() got an unexpected keyword argument 'semantic_type'": 115,
    "exec error: Part.plate() got an unexpected keyword argument 'radius'": 92,
    "exec error: mirror: plane must be 'YZ', 'XZ', or 'XY'": 84,
    "STEP export error: OCCT build failed": 78,
    "exec error: 'Part' object has no attribute 'cover_plate'": 76,
    "exec error: Part.sketch_on_face() missing 1 required keyword-only argument: 'profile'": 59,
    "exec error: 'Part' object has no attribute 'extrude_solid'": 58,
    "exec error: target must be a FeatureHandle": 36,
    "exec error: 'Part' object has no attribute 'transform'": 34,
    "exec error: 'Part' object has no attribute 'rectangular_profile'": 33,
    "exec error: unsupported operand type(s) for *: 'ParameterRef' and 'float'": 25,
    "exec error: Part.clamp_pad_plate() got an unexpected keyword argument 'radius'": 18,
    "exec error: 'Part' object has no attribute 'repeat_on_face'": 18,
    "SyntaxError: invalid syntax. Perhaps you forgot a comma? (<unknown>, line 18)": 14,
    "exec error: unsupported extrude_on_face operation 'pocket'": 14,
    "exec error: 'Part' object has no attribute 'shelled_plate'": 14,
    "point cloud sampling failed on generated part": 13,
    "exec error: 'Part' object has no attribute 'translate_on_face'": 13,
    "exec error: Part.linear_pattern() got an unexpected keyword argument 'distance'": 12,
    "SyntaxError: unterminated string literal (detected at line 18) (<unknown>, line 18)": 12,
    "exec error: Part.rail_mount_plate() got an unexpected keyword argument 'rail_offset_y'": 11,
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'swept_length'": 10,
    "exec error: Part.plate() got an unexpected keyword argument 'length'": 10,
    "exec error: 'Part' object has no attribute 'box_on_face'": 10,
    "exec error: Part.sketch_circle() got an unexpected keyword argument 'size'": 10,
    "exec error: Part.cone() got an unexpected keyword argument 'radius_bottom'": 10,
    "exec error: 'Part' object has no attribute 'lofted_bushing'": 9,
    "exec error: topology reference 'join_001:top_face:b9ce48e7f7b9' did not resolve any face": 9,
    "exec error: Part.mirrored_lug_plate() got an unexpected keyword argument 'hole_distance'": 8,
    "exec error: name 'basic_block' is not defined": 8,
    "exec error: Part.ribbed_support_plate() got an unexpected keyword argument 'hole_offsets'": 8,
    "exec error: Part.bossed_plate() got an unexpected keyword argument 'hole_distance'": 8,
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'height'": 8,
    "exec error: Part.loft() got an unexpected keyword argument 'height'": 7,
    "exec error: Part.sketch_on_face() got an unexpected keyword argument 'closed'": 7,
    "exec error: 'Part' object has no attribute 'repeat'": 7,
    "exec error: offset must be a 3D sequence": 6,
    "exec error: unsupported sketch_on_face profile 'mirrored_slot_profile'": 6,
    "SyntaxError: '[' was never closed (<unknown>, line 13)": 6,
    "exec error: Part.bossed_plate() got an unexpected keyword argument 'chamfer_distance'": 6,
    "SyntaxError: positional argument follows keyword argument (<unknown>, line 24)": 6,
    "exec error: Part.loft() got an unexpected keyword argument 'lower_profile'": 5,
    "exec error: Part.sketch_on_face() got an unexpected keyword argument 'depth'": 5,
    "exec error: Part.sketch_circle() got an unexpected keyword argument 'position'": 5,
    "exec error: Part.hole_pattern() got an unexpected keyword argument 'chamfer_distance'": 5,
    "exec error: points[] must be a 2D sequence": 5,
    "exec error: name 'sweep_length' is not defined": 4,
    "exec error: 'Part' object has no attribute 'ribbed_cover_plate'": 4,
    "exec error: 'Part' object has no attribute 'stock_cylinder'": 4,
    "exec error: 'Part' object has no attribute 'bossed_edge_profile'": 4,
    "exec error: 'Part' object has no attribute 'profile_open_cut_on_face'": 4,
    "exec error: 'Part' object has no attribute 'profile_walk_on_path'": 4,
    "exec error: Part.clamp_pad_plate() got an unexpected keyword argument 'hole_position'": 4,
    "exec error: row_step must be a 3D sequence": 4,
    "exec error: 'Part' object has no attribute 'cast_as'": 3,
    "exec error: direction must be 'inward' or 'outward'": 3,
    "exec error: name 'upper_radius' is not defined": 3,
    "exec error: Part.bossed_plate() got an unexpected keyword argument 'radius'": 3,
    "exec error: name 'blob' is not defined": 3,
    "exec error: name 'bolt_hole_radius' is not defined": 3,
    "exec error: 'FeatureHandle' object has no attribute 'top_right_corner'": 3,
    "exec error: topology reference 'join_002:top_face:323af5d41048' did not resolve any face": 2,
    "exec error: Part.rail_mount_plate() got an unexpected keyword argument 'rail_on_all_sides'": 2,
    "exec error: 'Part' object has no attribute 'stock'": 2,
    "exec error: 'Part' object has no attribute 'polyline'": 2,
    "exec error: 'Part' object has no attribute 'cookie_plate'": 2,
    "SyntaxError: closing parenthesis ']' does not match opening parenthesis '(' (<unknown>, line 13)": 2,
    "exec error: Part.extrude_on_face() missing 1 required keyword-only argument: 'sketch'": 2,
    "exec error: 'Part' object has no attribute 'boss_pattern'": 2,
    "exec error: 'Part' object has no attribute 'extrude_boss'": 2,
    "exec error: 'Part' object has no attribute 'lofted_mean_sphere'": 2,
    "exec error: topology reference 'loft_001:top_face:b95a905e855a' did not resolve any face": 2,
    "exec error: 'Part' object has no attribute 'hole'": 2,
    "exec error: 'Part' object has no attribute 'offset_on_face'": 2,
    "exec error: 'list' object has no attribute 'strip'": 2,
    "SyntaxError: '[' was never closed (<unknown>, line 7)": 2,
    "exec error: Part.loft() got an unexpected keyword argument 'profile'": 2,
    "exec error: 'Part' object has no attribute 'clamp_pad_mount'": 2,
    "SyntaxError: unterminated string literal (detected at line 10) (<unknown>, line 10)": 2,
    "exec error: extrude_on_face join/add requires height": 2,
    "SyntaxError: '(' was never closed (<unknown>, line 11)": 2,
    "exec error: 'Part' object has no attribute 'cast_geometry'": 2,
    "exec error: 'Part' object has no attribute 'boolean_boolean'": 1,
    "SyntaxError: closing parenthesis ']' does not match opening parenthesis '(' (<unknown>, line 24)": 1,
    "exec error: Part.capsule() got an unexpected keyword argument 'target'": 1,
    "exec error: 'Part' object has no attribute 'profile_walkway'": 1,
    "SyntaxError: unmatched ')' (<unknown>, line 21)": 1,
    "exec error: 'Part' object has no attribute 'spring_board'": 1,
    "SyntaxError: invalid syntax (<unknown>, line 23)": 1,
    "exec error: 'Part' object has no attribute 'boolean_operation'": 1,
    "exec error: 'FeatureHandle' object has no attribute 'hole_center'": 1,
    "exec error: 'FeatureHandle' object has no attribute 'top_right_face'": 1,
    "exec error: 'Part' object has no attribute 'sweep_path_plate'": 1,
    "exec error: Part.translate() missing 1 required keyword-only argument: 'offset'": 1,
    "exec error: 'Part' object has no attribute 'pin_stock'": 1,
    "exec error: 'Part' object has no attribute 'primitive_stock'": 1,
    "exec error: 'Part' object has no attribute 'copy'": 1,
    "exec error: Part.__init__() got an unexpected keyword argument 'primitive_library_id'": 1,
    "exec error: 'Part' object has no attribute 'primitive_stock_plate'": 1,
    "exec error: 'Part' object has no attribute 'rail_plate'": 1,
    "exec error: topology reference 'intersect_002:top_face:35b57a3f0eb3' did not resolve any face": 1,
    "exec error: 'Part' object has no attribute 'revolved_sweep_cover_plate'": 1,
    "exec error: unsupported sketch_on_face profile FeatureHandle(part=<flluma.api.part.Part object at 0x000001C2B63C2C50>, feature_id='sketch_001', node=CSGNode(name='book_cover_plate_boss_width', type=Transform))": 1,
    "exec error: 'Part' object has no attribute 'base_plate'": 1,
    "exec error: 'Part' object has no attribute 'bossed_boss_name'": 1,
    "exec error: Part.mirror() got an unexpected keyword argument 'point'": 1,
    "exec error: 'Part' object has no attribute 'pin_array'": 1,
    "SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 13)": 1,
    "exec error: Part.boolean_join() got an unexpected keyword argument 'join_mode'": 1,
    "exec error: Part.sketch_on_face() got an unexpected keyword argument 'curves'": 1,
    "exec error: 'Part' object has no attribute 'translate_name'": 1,
    "exec error: unsupported sketch_on_face profile FeatureHandle(part=<flluma.api.part.Part object at 0x000001C2B51C6DD0>, feature_id='sketch_001', node=CSGNode(name='mount_boss_width', type=Transform))": 1,
    "exec error: Part.pin_cluster() got an unexpected keyword argument 'target'": 1,
    "exec error: 'Part' object has no attribute 'bossed_cover_area'": 1,
    "exec error: 'Part' object has no attribute 'springboard'": 1,
    "exec error: 'Part' object has no attribute 'shield'": 1,
    "exec error: Part.clamp_pad_plate() got an unexpected keyword argument 'slot_width'": 1,
    "exec error: keyword argument repeated: semantic_type (<candidate>, line 8)": 1,
    "exec error: Part.chamfer() got an unexpected keyword argument 'points'": 1,
    "exec error: name 'profile_sweep_radius' is not defined": 1,
    "exec error: 'Part' object has no attribute 'clipped_plate'": 1,
    "SyntaxError: invalid syntax. Perhaps you forgot a comma? (<unknown>, line 14)": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 20)": 1,
    "exec error: name 'basic_plate' is not defined": 1,
    "exec error: Part.cone() got an unexpected keyword argument 'section_radius'": 1,
    "exec error: 'Part' object has no attribute 'profile_walkoff_path'": 1,
    "exec error: 'hole_radius'": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 18)": 1,
    "SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 9)": 1,
    "exec error: 'Part' object has no attribute 'elliptical_plate'": 1,
    "exec error: 'Part' object has no attribute 'boolean_cap'": 1,
    "exec error: 'Part' object has no attribute 'sweep_profile'": 1,
    "exec error: Part.revolve() got an unexpected keyword argument 'target'": 1,
    "exec error: 'Part' object has no attribute 'spring_motor'": 1,
    "exec error: 'Part' object has no attribute 'threaded_hole'": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 11)": 1,
    "exec error: 'Part' object has no attribute 'clamp_pad_base'": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 24)": 1,
    "exec error: 'Part' object has no attribute 'plated_plate'": 1,
    "exec error: 'Part' object has no attribute 'gear_pattern'": 1,
    "SyntaxError: unterminated string literal (detected at line 9) (<unknown>, line 9)": 1,
    "exec error: unsupported sketch_on_face profile FeatureHandle(part=<flluma.api.part.Part object at 0x000001C2B52BA610>, feature_id='sketch_001', node=CSGNode(name='width_boss', type=Transform))": 1,
    "exec error: 'Part' object has no attribute 'rectangular_pattern'": 1,
    "exec error: 'Part' object has no attribute 'bolt_hole_pattern_plate'": 1,
    "exec error: keyword argument repeated: semantic_type (<candidate>, line 7)": 1,
    "exec error: Part.cylinder() got an unexpected keyword argument 'id'": 1,
    "SyntaxError: invalid syntax. Maybe you meant '==' or ':=' instead of '='? (<unknown>, line 21)": 1,
    "exec error: 'Part' object has no attribute 'profile_walk_arm'": 1,
    "exec error: 'Part' object has no attribute 'shield_plate'": 1,
    "exec error: height must resolve to a number, got [3.3, 5.1]": 1
  },
  "extreme_cd_cases_gt_1000": [],
  "export_but_unscoreable_ids": [
    "flluma_0091726",
    "flluma_0095556",
    "flluma_0092013",
    "flluma_0093677",
    "flluma_0096368",
    "flluma_0096952",
    "flluma_0092328",
    "flluma_0096014",
    "flluma_0094849",
    "flluma_0091641",
    "flluma_0095714",
    "flluma_0096047",
    "flluma_0096727"
  ]
}
```

### B2

```json
{
  "rows": 2500,
  "scoreable": 1355,
  "scoreable_pct": 54.2,
  "gate_counts_from_geometry_run": {
    "syntax_ok": 2385,
    "exec_ok": 1440,
    "build_ok": 1440,
    "solid_valid": 1440,
    "step_export_ok": 1422
  },
  "missing_target_rows": 0,
  "conditional": {
    "cd": {
      "n": 1355,
      "mean": 128165251.36611037,
      "median": 2.5214314715839485,
      "sd_sample": 4717804196.367004,
      "min": 0.029507835181039617,
      "max": 173663904058.20007,
      "q25": 1.6520355604096293,
      "q75": 5.33976733088255,
      "q95": 25.997576438527606,
      "q99": 141.815974038688
    },
    "f_score_1pct": {
      "n": 1355,
      "mean": 0.1987240816546748,
      "median": 0.2016495157384988,
      "sd_sample": 0.09347197760362572,
      "min": 0.0,
      "max": 0.5091420481783318,
      "q25": 0.1254711819066148,
      "q75": 0.26706395680987205,
      "q95": 0.3517864398480782,
      "q99": 0.40082486202599255
    },
    "bbox_err": {
      "n": 1355,
      "mean": 247.26430570454147,
      "median": 0.10000019093180157,
      "sd_sample": 9055.468138269742,
      "min": 0.0,
      "max": 333335.9468547896,
      "q25": 0.0008883543976227297,
      "q75": 0.6666666469167046,
      "q95": 5.172240943288581,
      "q99": 27.371066703727397
    },
    "bbox_ratio_to_gt": {
      "n": 1355,
      "mean": 15.151913090320543,
      "median": 1.0000000000182425,
      "sd_sample": 521.0976612353029,
      "min": 0.10129828357409362,
      "max": 19182.76937878015,
      "q25": 0.9995342963244196,
      "q75": 1.0026463641967596,
      "q95": 1.0485591169467163,
      "q99": 1.269604060339765
    }
  },
  "unconditional_f_score_1pct": {
    "n": 2500,
    "mean": 0.10770845225683374,
    "median": 0.06051537298387097,
    "sd_sample": 0.12058579471307865,
    "min": 0.0,
    "max": 0.5091420481783318,
    "q25": 0.0,
    "q75": 0.21006006652407194,
    "q95": 0.3252319983484605,
    "q99": 0.384232374848022
  },
  "non_scoreable_error_counts": {
    "exec error: topology reference 'join_001:top_face:b9ce48e7f7b9' did not resolve any face": 78,
    "exec error: name '__all__' is not defined": 71,
    "exec error: 'Part' object has no attribute 'extrude_face_on_profile'": 71,
    "point cloud sampling failed on generated part": 67,
    "exec error: Part.rectangular_pocket() got an unexpected keyword argument 'height'": 67,
    "exec error: name '__title__' is not defined": 64,
    "exec error: Part.box() got an unexpected keyword argument 'size'": 30,
    "exec error: Part.standoff_array_plate() got an unexpected keyword argument 'hole_center'": 24,
    "exec error: mirror: axis must be 'X', 'Y', or 'Z'": 23,
    "exec error: bad operand type for unary -: 'ParameterRef'": 23,
    "SyntaxError: invalid syntax (<unknown>, line 12)": 22,
    "exec error: Part.loft() got an unexpected keyword argument 'profile'": 20,
    "exec error: target must be a FeatureHandle": 20,
    "STEP export error: OCCT build failed": 18,
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'path_mid_height'": 18,
    "SyntaxError: '[' was never closed (<unknown>, line 7)": 17,
    "exec error: 'Part' object has no attribute 'hole'": 16,
    "exec error: 'Part' object has no attribute 'boolean_remove'": 16,
    "exec error: 'Part' object has no attribute 'sweeped_profile'": 15,
    "exec error: direction must be 'inward' or 'outward'": 15,
    "exec error: topology reference 'loft_001:top_face:b95a905e855a' did not resolve any face": 15,
    "exec error: unsupported operand type(s) for *: 'ParameterRef' and 'float'": 15,
    "SyntaxError: unmatched ']' (<unknown>, line 1)": 14,
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'path_mid_radius'": 14,
    "exec error: 'Part' object has no attribute 'rectangular_slot'": 12,
    "exec error: 'Part' object has no attribute 'profile_cut'": 11,
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'path_width'": 11,
    "SyntaxError: invalid syntax (<unknown>, line 14)": 10,
    "exec error: Part.linear_pattern() missing 1 required keyword-only argument: 'step'": 9,
    "SyntaxError: '[' was never closed (<unknown>, line 8)": 9,
    "exec error: 'path_mid_length'": 9,
    "exec error: 'Part' object has no attribute 'sweep_profile'": 9,
    "exec error: Part.clamp_pad_plate() got an unexpected keyword argument 'clamp_jaw_length'": 8,
    "exec error: Part.cone() got an unexpected keyword argument 'height_top'": 8,
    "exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'radius'": 8,
    "exec error: loft requires at least two profile features": 8,
    "exec error: 'FeatureHandle' object has no attribute 'positions'": 7,
    "exec error: target must be a TopologyReference from a FeatureHandle": 7,
    "exec error: 'Part' object has no attribute 'loft_on_target'": 7,
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'profile'": 6,
    "exec error: 'Part' object has no attribute 'loft_profile'": 6,
    "exec error: Part.revolve() got an unexpected keyword argument 'target'": 6,
    "exec error: unsupported operand type(s) for /: 'ParameterRef' and 'float'": 6,
    "SyntaxError: invalid syntax (<unknown>, line 1)": 6,
    "exec error: 'flange_radius'": 5,
    "SyntaxError: invalid syntax (<unknown>, line 30)": 5,
    "exec error: 'Part' object has no attribute 'boss_plate'": 5,
    "exec error: 'FeatureHandle' object has no attribute 'points'": 5,
    "exec error: 'Part' object has no attribute 'sweep_on_path'": 4,
    "SyntaxError: invalid syntax (<unknown>, line 18)": 4,
    "exec error: 'Part' object has no attribute 'extrude_on_profile'": 4,
    "exec error: Part.shelled_cover_plate() got an unexpected keyword argument 'slot_length'": 4,
    "exec error: 'Part' object has no attribute 'sweep_polygon'": 4,
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'path_mid_offset'": 4,
    "exec error: Part.rectangular_pocket() got an unexpected keyword argument 'radius'": 3,
    "exec error: Part.mirrored_lug_plate() got an unexpected keyword argument 'hole_spacing'": 3,
    "exec error: 'Part' object has no attribute 'booss_plate'": 3,
    "exec error: parameter 'pocket_width' already exists": 3,
    "exec error: Part.wedge() got an unexpected keyword argument 'radius'": 3,
    "exec error: 'Part' object has no attribute 'boolean_remove_on_face'": 3,
    "exec error: points[] must be a 2D sequence": 3,
    "exec error: 'Part' object has no attribute 'boolean_cut_on_face'": 3,
    "exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'pitch_offset'": 3,
    "exec error: keyword argument repeated: semantic_type (<candidate>, line 20)": 3,
    "exec error: offset must be a 3D sequence": 3,
    "exec error: 'Part' object has no attribute 'sweep_tangent_profile'": 3,
    "exec error: 'Part' object has no attribute 'threaded_bearing_hole'": 3,
    "exec error: keyword argument repeated: semantic_type (<candidate>, line 19)": 3,
    "exec error: Part.hole_pattern() missing 1 required keyword-only argument: 'positions'": 2,
    "exec error: 'Part' object has no attribute 'sweep_shell'": 2,
    "exec error: Part.wedge() got an unexpected keyword argument 'width'": 2,
    "exec error: 'Part' object has no attribute 'blob'": 2,
    "exec error: thickness must resolve to a number, got 'auto'": 2,
    "exec error: 'Part' object has no attribute 'loft_on_profile'": 2,
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'height'": 2,
    "exec error: 'Part' object has no attribute 'rectangular_cut'": 2,
    "SyntaxError: '[' was never closed (<unknown>, line 9)": 2,
    "exec error: topology reference 'join_002:top_face:323af5d41048' did not resolve any face": 2,
    "exec error: 'Part' object has no attribute 'sweep_tube_on_path'": 2,
    "exec error: 'Part' object has no attribute 'loft_on_face'": 2,
    "SyntaxError: invalid syntax (<unknown>, line 17)": 2,
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'path_profile'": 2,
    "exec error: 'width'": 2,
    "SyntaxError: '[' was never closed (<unknown>, line 18)": 2,
    "exec error: name 'Cone' is not defined": 2,
    "SyntaxError: '[' was never closed (<unknown>, line 10)": 2,
    "exec error: Part.wedge() got an unexpected keyword argument 'length'": 2,
    "exec error: 'Part' object has no attribute 'sweep_pipe_bracket'": 2,
    "exec error: 'Part' object has no attribute 'loft_on_top'": 2,
    "SyntaxError: unterminated string literal (detected at line 59) (<unknown>, line 59)": 2,
    "exec error: Part.hole_pattern() got an unexpected keyword argument 'offsets'": 2,
    "exec error: 'Part' object has no attribute 'extrude_face_profile'": 2,
    "exec error: 'Part' object has no attribute 'round_polygon'": 2,
    "SyntaxError: unterminated string literal (detected at line 19) (<unknown>, line 19)": 1,
    "exec error: keyword argument repeated: semantic_type (<candidate>, line 22)": 1,
    "exec error: name 'flluma_0067171' is not defined": 1,
    "exec error: Part.shelled_cover_plate() got an unexpected keyword argument 'holes'": 1,
    "exec error: unsupported operand type(s) for +: 'ParameterRef' and 'ParameterRef'": 1,
    "exec error: 'Part' object has no attribute 'loft_solid'": 1,
    "exec error: rectangle sketch_on_face requires width and height": 1,
    "exec error: 'path_width'": 1,
    "exec error: keyword argument repeated: semantic_type (<candidate>, line 23)": 1,
    "exec error: 'Part' object has no attribute 'path_on_face'": 1,
    "exec error: 'Part' object has no attribute 'sweep_tube_profile'": 1,
    "exec error: 'Part' object has no attribute 'move'": 1,
    "exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'hole_radius'": 1,
    "exec error: 'Part' object has no attribute 'boolean_magnetical_join'": 1,
    "exec error: object of type 'ParameterRef' has no len()": 1,
    "exec error: 'Part' object has no attribute 'threaded_hole_pattern'": 1,
    "exec error: Part.rectangular_pocket() got an unexpected keyword argument 'profile'": 1,
    "exec error: 'FeatureHandle' object has no attribute 'top'": 1,
    "exec error: parameter 'flange_length' already exists": 1,
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'path_mid_width'": 1,
    "SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 15)": 1,
    "exec error: 'Part' object has no attribute 'sweep_solid'": 1,
    "exec error: object of type 'float' has no len()": 1,
    "exec error: 'Part' object has no attribute 'ribbed_heat_sink_plate'": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 12)": 1,
    "exec error: 'Part' object has no attribute 'blob_blob_profile'": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 11)": 1,
    "exec error: Part.shelled_cover_plate() got an unexpected keyword argument 'hole_center'": 1,
    "exec error: Part.hole_pattern() got an unexpected keyword argument 'length'": 1,
    "exec error: topology reference 'fillet_001:top_face:0796be5e0297' did not resolve any face": 1,
    "exec error: 'Part' object has no attribute 'repeat'": 1,
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'target'": 1,
    "exec error: unsupported operand type(s) for -: 'int' and 'ParameterRef'": 1,
    "exec error: name 'pi' is not defined": 1,
    "SyntaxError: cannot assign to literal (<unknown>, line 1)": 1,
    "exec error: unsupported operand type(s) for +: 'ParameterRef' and 'float'": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 19)": 1,
    "exec error: 'Part' object has no attribute 'boolean_pocket'": 1,
    "exec error: 'Part' object has no attribute 'path_segment'": 1,
    "exec error: 'Part' object has no attribute 'lobed_gasket_profile'": 1,
    "exec error: Part.linear_pattern() got an unexpected keyword argument 'offset'": 1,
    "exec error: 'upper_flange_height'": 1,
    "exec error: Part.hole_pattern() got an unexpected keyword argument 'distance'": 1,
    "exec error: Part.mirrored_lug_plate() got an unexpected keyword argument 'lug_offset_y'": 1,
    "exec error: 'path_radius'": 1,
    "exec error: Part.clamp_pad_plate() got an unexpected keyword argument 'jaw_offset'": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 16)": 1,
    "SyntaxError: unterminated string literal (detected at line 3) (<unknown>, line 3)": 1,
    "exec error: 'Part' object has no attribute 'boolean_fill'": 1,
    "exec error: Part.rail_mount_plate() got an unexpected keyword argument 'rail_plate_length'": 1,
    "SyntaxError: invalid decimal literal (<unknown>, line 3)": 1,
    "exec error: 'Part' object has no attribute 'periodic_pattern'": 1,
    "exec error: 'Part' object has no attribute 'square_profile'": 1,
    "exec error: 'Part' object has no attribute 'pocket'": 1,
    "SyntaxError: invalid syntax (<unknown>, line 31)": 1,
    "exec error: 'Part' object has no attribute 'clamp_plate'": 1,
    "exec error: keyword argument repeated: semantic_type (<candidate>, line 17)": 1,
    "exec error: 'Part' object has no attribute 'loft_quad_primitive'": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 32)": 1,
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'path_profile_id'": 1,
    "exec error: 'hole_radius'": 1,
    "exec error: 'Part' object has no attribute 'square_plate'": 1,
    "SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 16)": 1,
    "exec error: 'FeatureHandle' object has no attribute 'pocket_center'": 1,
    "no `part` variable after execution": 1,
    "exec error: 'Part' object has no attribute 'loft_on_edges'": 1,
    "exec error: hole depth must be a number or 'through'": 1,
    "exec error: 'Part' object has no attribute 'sweeped_swept_plate'": 1,
    "exec error: Part.shelled_cover_plate() got an unexpected keyword argument 'fill_hole_radius'": 1,
    "exec error: 'FeatureHandle' object has no attribute 'pins'": 1,
    "exec error: 'Part' object has no attribute 'path'": 1,
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'path_radius'": 1,
    "exec error: name 'flluma_0065771' is not defined": 1,
    "exec error: 'Part' object has no attribute 'sweep_plate'": 1,
    "exec error: Parameters.add() got an unexpected keyword argument 'category'": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 40)": 1,
    "exec error: parameter 'path_length' already exists": 1,
    "exec error: hole pattern positions must be 2D or 3D sequences": 1,
    "exec error: keyword argument repeated: semantic_type (<candidate>, line 16)": 1,
    "exec error: 'FeatureHandle' object has no attribute 'width'": 1,
    "exec error: unsupported operand type(s) for -: 'ParameterRef' and 'ParameterRef'": 1,
    "SyntaxError: unterminated string literal (detected at line 23) (<unknown>, line 23)": 1,
    "exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'offset_vector'": 1,
    "exec error: Part.boss() missing 1 required keyword-only argument: 'target'": 1,
    "SyntaxError: invalid syntax (<unknown>, line 25)": 1,
    "SyntaxError: invalid syntax (<unknown>, line 34)": 1,
    "exec error: 'lower_thickness'": 1,
    "exec error: unsupported operand type(s) for -: 'ParameterRef' and 'float'": 1,
    "exec error: topology reference 'hole_001:top_face:9014e73e3f7b' did not resolve any face": 1,
    "SyntaxError: unterminated string literal (detected at line 47) (<unknown>, line 47)": 1,
    "SyntaxError: unterminated string literal (detected at line 27) (<unknown>, line 27)": 1,
    "exec error: 'Part' object has no attribute 'rectangular_pocket_hole'": 1,
    "exec error: unsupported operand type(s) for *: 'float' and 'ParameterRef'": 1
  },
  "extreme_cd_cases_gt_1000": [
    {
      "sample_id": "flluma_0090587",
      "syntax_ok": true,
      "exec_ok": true,
      "build_ok": true,
      "solid_valid": true,
      "step_export_ok": true,
      "error": "",
      "cd": 173663904058.20007,
      "bbox_err": 333335.9468547896,
      "f_score_1pct": 0.00390625,
      "target_bbox_diag": 52.13120124025058,
      "gen_bbox_diag": 1000020.8108305047,
      "bbox_ratio_to_gt": 19182.76937878015,
      "has_target": true
    }
  ],
  "export_but_unscoreable_ids": [
    "flluma_0091718",
    "flluma_0097058",
    "flluma_0096533",
    "flluma_0090398",
    "flluma_0097889",
    "flluma_0092884",
    "flluma_0097403",
    "flluma_0091407",
    "flluma_0094538",
    "flluma_0096264",
    "flluma_0096659",
    "flluma_0092802",
    "flluma_0094827",
    "flluma_0098055",
    "flluma_0095448",
    "flluma_0091292",
    "flluma_0092712",
    "flluma_0094805",
    "flluma_0095101",
    "flluma_0095870",
    "flluma_0094051",
    "flluma_0095418",
    "flluma_0098449",
    "flluma_0095962",
    "flluma_0094058",
    "flluma_0090657",
    "flluma_0094849",
    "flluma_0091367",
    "flluma_0097560",
    "flluma_0098409",
    "flluma_0097450",
    "flluma_0094194",
    "flluma_0094657",
    "flluma_0092663",
    "flluma_0090940",
    "flluma_0095229",
    "flluma_0094952",
    "flluma_0093573",
    "flluma_0094735",
    "flluma_0099307",
    "flluma_0097668",
    "flluma_0097812",
    "flluma_0092424",
    "flluma_0093222",
    "flluma_0095189",
    "flluma_0097063",
    "flluma_0092049",
    "flluma_0097460",
    "flluma_0094108",
    "flluma_0091898",
    "flluma_0097597",
    "flluma_0098040",
    "flluma_0095334",
    "flluma_0090391",
    "flluma_0097198",
    "flluma_0092641",
    "flluma_0093277",
    "flluma_0093430",
    "flluma_0099730",
    "flluma_0094451",
    "flluma_0097465",
    "flluma_0094081",
    "flluma_0096445",
    "flluma_0092446",
    "flluma_0090543",
    "flluma_0092921",
    "flluma_0094756"
  ]
}
```

## Provenance

Generation actuals: `__RUN_SOURCE_ROOT__\outputs\b0_b2_fullstack_s2\cag_b0_b2_seed_2_actuals.json`.
Generation actuals SHA256: `05283789c417d595c8a533b1f7a1b330f6a206b7e67f4ff68d677ecc40c53ba8`.
All 2500 paired-case rows: `__EVIDENCE_SOURCE_ROOT__\03\result\cag_b0_b2_seed_2_paired_cases.jsonl`.

B0 files and SHA256:

```json
{
  "__DEV_ROOT__\\scratch\\exec_b0b2_step_B0_s2\\execution_rows.jsonl": "5fa5c649e7d493aa95fcba813f3410a86abd8b221bd1ee898263c61a687d8de8",
  "__DEV_ROOT__\\scratch\\geom_b0b2_step_B0_s2\\geometry_nbest_rows.jsonl": "3cad9d728c1ae7ef80a49bbe2a7b586e6fd2a1b849d074040c8061e062ec2da1",
  "__DEV_ROOT__\\scratch\\exec_b0b2_step_B0_s2\\execution_summary.json": "18f995a4b1c7a42b2c1069d16bf548e76cc1771782d24161d3ecfe51ef5f40d9",
  "__RUN_SOURCE_ROOT__\\outputs\\b0_b2_fullstack_s2\\predictions\\gen_step_B0_s2.jsonl": "8ad1a5d5f88f911b2728c51399080ff2de06cc35555e4b8c09ba6e50cd72a52d",
  "__RUN_SOURCE_ROOT__\\outputs\\b0_b2_fullstack_s2\\predictions\\geom_input_step_B0_s2.jsonl": "1cd13a44a46a6436a231b8f0131182a9f82ced64213bb609c8885219f4c754d0"
}
```

B2 files and SHA256:

```json
{
  "__DEV_ROOT__\\scratch\\exec_b0b2_step_B2_s2\\execution_rows.jsonl": "89d70c60e8f2cf7ab89f1c726ccc224afab418dc202ca32e1e9e2e7c031d0c89",
  "__DEV_ROOT__\\scratch\\geom_b0b2_step_B2_s2\\geometry_nbest_rows.jsonl": "b36b6a326a477971e457a792058e273a3d5c923e8b79f6fde635712ee02a8150",
  "__DEV_ROOT__\\scratch\\exec_b0b2_step_B2_s2\\execution_summary.json": "0c2b191e3a0d31d3af361b899387b822d904356c1f928c3a9aed3714f66bafef",
  "__RUN_SOURCE_ROOT__\\outputs\\b0_b2_fullstack_s2\\predictions\\gen_step_B2_s2.jsonl": "a18fd8f25344ba649aa4bc1fcd3e579d786ef6b97f58846c0e8ae84d9aa9b354",
  "__RUN_SOURCE_ROOT__\\outputs\\b0_b2_fullstack_s2\\predictions\\geom_input_step_B2_s2.jsonl": "7b48b716ac7e88b3f3c524997d1df546937edc1e40545a1e5384dd507f70e114"
}
```

Evaluator-source hashes describe files present at analysis time; they are not a historical build attestation. See the frozen generation actuals and earlier run records for training-code provenance.

# Seed 3 Evaluation Record

Audit: PASS. Evaluation complete.

| Seed | Arm | Syntax | Execute | Build | Solid | STEP export | Scoreable |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | B0 | 2405/2500 (96.20%) | 1078/2500 (43.12%) | 1078/2500 (43.12%) | 1078/2500 (43.12%) | 1069/2500 (42.76%) | 1065/2500 (42.60%) |
| 3 | B2 | 2403/2500 (96.12%) | 1569/2500 (62.76%) | 1569/2500 (62.76%) | 1569/2500 (62.76%) | 1540/2500 (61.60%) | 1524/2500 (60.96%) |

## Geometry

| Metric | B0 | B2 | B2 - B0 |
| --- | ---: | ---: | ---: |
| conditional_mean_cd | 13.60400383 | 412844042.3 | 412844028.7 |
| conditional_median_cd | 7.256253248 | 3.398533527 | -3.857719721 |
| conditional_mean_f1_pct | 15.34840281 | 18.21762671 | 2.869223902 |
| conditional_median_f1_pct | 15.96664755 | 18.84107837 | 2.874430814 |
| unconditional_mean_f1_pct | 6.538419596 | 11.10546524 | 4.567045646 |
| unconditional_median_f1_pct | 0 | 8.295036765 | 8.295036765 |
| paired_mean_cd | 13.971357 | 18.25101099 | 4.279653986 |
| paired_median_cd | 8.139654167 | 2.882568014 | -5.257086153 |
| paired_mean_f1_pct | 15.27649372 | 19.94423176 | 4.667738035 |
| paired_median_f1_pct | 16.29397455 | 20.40268017 | 4.108705623 |
| conditional_mean_bbox_err | 1.13457781 | 877.0764941 | 875.9419163 |
| conditional_median_bbox_err | 0.09745979361 | 0.30990286 | 0.2124430664 |

Percent metrics above use 0-100 units. CD/bbox remain in evaluator units. Conditional full-set and jointly scoreable metrics use different subsets.

## Paired Tests

Within-seed query-level tests below do not measure uncertainty across training seeds.

| Gate | Both | B0 only | B2 only | Neither | Delta pp | Exact McNemar p |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| syntax_ok | 2311 | 94 | 92 | 3 | -0.08 | 0.94157485 |
| exec_ok | 827 | 251 | 742 | 680 | 19.64 | 6.8181058e-57 |
| build_ok | 827 | 251 | 742 | 680 | 19.64 | 6.8181058e-57 |
| solid_valid | 827 | 251 | 742 | 680 | 19.64 | 6.8181058e-57 |
| step_export_ok | 809 | 260 | 731 | 700 | 18.84 | 2.0982772e-52 |

Jointly scoreable: 801.

| Metric | B2 wins | B0 wins | Ties | Median paired difference B2 - B0 | Exact sign p |
| --- | ---: | ---: | ---: | ---: | ---: |
| cd | 535 | 266 | 0 | -0.6057797925 | 1.173028e-21 |
| f_score_1pct | 544 | 257 | 0 | 0.03076714877 | 1.6668913e-24 |
| bbox_err | 263 | 374 | 164 | 0 | 1.2497047e-05 |

F@1 paired differences in the last table use raw 0-1 units. Multiply by 100 for percentage points.

## Distributions And Failures

No CD values were removed, clipped, or winsorized. CD > 1000 is a retrospective audit flag, not an exclusion rule.

### B0

```json
{
  "rows": 2500,
  "scoreable": 1065,
  "scoreable_pct": 42.6,
  "gate_counts_from_geometry_run": {
    "syntax_ok": 2405,
    "exec_ok": 1078,
    "build_ok": 1078,
    "solid_valid": 1078,
    "step_export_ok": 1069
  },
  "missing_target_rows": 0,
  "conditional": {
    "cd": {
      "n": 1065,
      "mean": 13.60400382770544,
      "median": 7.2562532481980355,
      "sd_sample": 21.68953584962021,
      "min": 0.0794506457301507,
      "max": 258.60458210910093,
      "q25": 2.635668903577299,
      "q75": 14.237439178828414,
      "q95": 46.929474162626924,
      "q99": 112.14368038312354
    },
    "f_score_1pct": {
      "n": 1065,
      "mean": 0.1534840280841597,
      "median": 0.1596664755351682,
      "sd_sample": 0.1049473530976768,
      "min": 0.0,
      "max": 0.4609188791048729,
      "q25": 0.04783163265306122,
      "q75": 0.21719627808988765,
      "q95": 0.3460468910616528,
      "q99": 0.4102320502277317
    },
    "bbox_err": {
      "n": 1065,
      "mean": 1.1345778096812407,
      "median": 0.09745979361246467,
      "sd_sample": 3.4366557110881297,
      "min": 0.0,
      "max": 33.68672454167318,
      "q25": 3.178914379139049e-07,
      "q75": 0.41632855733235896,
      "q95": 4.808140510145681,
      "q99": 20.56454930570406
    },
    "bbox_ratio_to_gt": {
      "n": 1065,
      "mean": 0.9880548726795036,
      "median": 1.0000000000009874,
      "sd_sample": 0.08237922178612296,
      "min": 0.21954751311005571,
      "max": 2.051895368296789,
      "q25": 0.9991211238340766,
      "q75": 1.0019003360198337,
      "q95": 1.0134363883834359,
      "q99": 1.052426354625755
    }
  },
  "unconditional_f_score_1pct": {
    "n": 2500,
    "mean": 0.06538419596385203,
    "median": 0.0,
    "sd_sample": 0.10223528412028912,
    "min": 0.0,
    "max": 0.4609188791048729,
    "q25": 0.0,
    "q75": 0.135188684566787,
    "q95": 0.28464520192969234,
    "q99": 0.38130698151633274
  },
  "non_scoreable_error_counts": {
    "exec error: topology reference 'join_001:top_face:b9ce48e7f7b9' did not resolve any face": 212,
    "exec error: Part.boolean_join() got an unexpected keyword argument 'operation'": 157,
    "exec error: 'height'": 59,
    "exec error: Part.bossed_plate() missing 2 required keyword-only arguments: 'width' and 'height'": 56,
    "exec error: Part.sketch_circle() got an unexpected keyword argument 'size'": 51,
    "exec error: Part.plate() got an unexpected keyword argument 'size'": 48,
    "exec error: extrude_on_face cut requires depth": 45,
    "exec error: bad operand type for unary -: 'ParameterRef'": 39,
    "exec error: Part.ribbed_support_plate() got an unexpected keyword argument 'hole_offset_x'": 38,
    "exec error: Part.boolean_cut() got an unexpected keyword argument 'profile'": 36,
    "exec error: Part.hole_pattern() got an unexpected keyword argument 'spacing'": 34,
    "exec error: 'FeatureHandle' object has no attribute 'sara_edges'": 33,
    "exec error: unsupported operand type(s) for *: 'ParameterRef' and 'float'": 32,
    "exec error: Part.bossed_plate() got an unexpected keyword argument 'hole_offset_x'": 31,
    "exec error: parameter 'height' already exists": 27,
    "exec error: Part.sketch_circle() got an unexpected keyword argument 'count'": 22,
    "exec error: Part.sketch_circle() got an unexpected keyword argument 'position'": 21,
    "exec error: direction must be 'inward' or 'outward'": 21,
    "exec error: Part.bossed_plate() got an unexpected keyword argument 'size'": 21,
    "exec error: Part.clamp_pad_plate() got an unexpected keyword argument 'slot_length'": 17,
    "exec error: Part.profile_cut_on_face() got an unexpected keyword argument 'distance_pattern'": 16,
    "exec error: Part.torus() got an unexpected keyword argument 'radius'": 15,
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'inner_radius'": 15,
    "exec error: mirror: plane must be 'YZ', 'XZ', or 'XY'": 15,
    "SyntaxError: invalid syntax (<unknown>, line 18)": 14,
    "exec error: 'Part' object has no attribute 'shelled_mount_block'": 12,
    "exec error: Part.bossed_plate() got an unexpected keyword argument 'boss_width'": 12,
    "SyntaxError: invalid syntax (<unknown>, line 22)": 12,
    "exec error: 'Part' object has no attribute 'pin_cluster_plate'": 11,
    "SyntaxError: invalid syntax (<unknown>, line 8)": 11,
    "exec error: Part.cylinder() got an unexpected keyword argument 'target'": 10,
    "exec error: 'Part' object has no attribute 'rectangular_profile_array'": 10,
    "exec error: 'Part' object has no attribute 'face_add_on_name'": 9,
    "STEP export error: OCCT build failed": 9,
    "exec error: Part.sketch_circle() got an unexpected keyword argument 'mode'": 9,
    "exec error: 'Part' object has no attribute 'lug_plate'": 8,
    "exec error: Part.bossed_plate() got an unexpected keyword argument 'boss_radius_min'": 8,
    "exec error: Part.plate() got an unexpected keyword argument 'inner_radius'": 7,
    "exec error: length must resolve to a number, got 'bbox_size_x'": 6,
    "exec error: Part.standoff_array_plate() got an unexpected keyword argument 'standoff_depth'": 6,
    "SyntaxError: invalid syntax (<unknown>, line 14)": 6,
    "SyntaxError: invalid syntax (<unknown>, line 5)": 6,
    "exec error: 'Part' object has no attribute 'cover_plate_shell'": 5,
    "exec error: Part.shell() got an unexpected keyword argument 'shell_width'": 5,
    "exec error: 'Part' object has no attribute 'boolean_clip'": 5,
    "exec error: Part.sensor_mount_plate() got an unexpected keyword argument 'hole_offset_x'": 5,
    "exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'position'": 5,
    "exec error: 'Part' object has no attribute 'top_face'": 5,
    "exec error: 'Part' object has no attribute 'path_on_profile'": 5,
    "exec error: target must be a TopologyReference from a FeatureHandle": 5,
    "exec error: 'Part' object has no attribute 'clip'": 5,
    "exec error: box() got an unexpected keyword argument 'name'": 5,
    "SyntaxError: unterminated string literal (detected at line 20) (<unknown>, line 20)": 4,
    "point cloud sampling failed on generated part": 4,
    "exec error: Part.prism() got an unexpected keyword argument 'length'": 4,
    "exec error: topology reference 'cut_001:top_face:e6c86e3e481d' did not resolve any face": 4,
    "SyntaxError: invalid syntax (<unknown>, line 21)": 4,
    "SyntaxError: '[' was never closed (<unknown>, line 7)": 4,
    "SyntaxError: invalid syntax. Perhaps you forgot a comma? (<unknown>, line 5)": 3,
    "SyntaxError: positional argument follows keyword argument (<unknown>, line 13)": 3,
    "exec error: 'Part' object has no attribute 'rectangular_profile'": 3,
    "exec error: Part.standoff_array_plate() got an unexpected keyword argument 'standoff_thickness'": 3,
    "exec error: topology reference 'join_002:top_face:323af5d41048' did not resolve any face": 3,
    "exec error: target must be a FeatureHandle": 3,
    "exec error: Part.bossed_plate() got an unexpected keyword argument 'fillet_radius'": 3,
    "SyntaxError: invalid syntax (<unknown>, line 24)": 3,
    "exec error: threaded_hole_on_face: offset_mode must be 'world' or 'face'. Prefer offset_world=(x, y, z) for world offsets or offset_uv=(u, v) for face-local offsets.": 3,
    "exec error: Part.shell() got an unexpected keyword argument 'faces_to_add'": 2,
    "exec error: 'Part' object has no attribute 'cylinder_pattern'": 2,
    "SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 18)": 2,
    "SyntaxError: invalid syntax (<unknown>, line 16)": 2,
    "exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'pattern'": 2,
    "exec error: Part.loft() got an unexpected keyword argument 'sketches'": 2,
    "exec error: 'Part' object has no attribute 'ribbed_heat_sink'": 2,
    "exec error: Part.cone() got an unexpected keyword argument 'radius_bottom'": 2,
    "exec error: 'Part' object has no attribute 'boolean_add'": 2,
    "exec error: Part.plate() got an unexpected keyword argument 'radius'": 2,
    "exec error: 'Part' object has no attribute 'cover_plate'": 2,
    "SyntaxError: invalid syntax (<unknown>, line 19)": 2,
    "exec error: Part.loft() got an unexpected keyword argument 'segment_count'": 2,
    "exec error: Part.circular_pattern() got an unexpected keyword argument 'radius'": 2,
    "SyntaxError: invalid syntax (<unknown>, line 9)": 2,
    "exec error: 'Part' object has no attribute 'solid_from_profile'": 2,
    "exec error: Part.sensor_mount_plate() got an unexpected keyword argument 'hole_offsets'": 1,
    "exec error: Part.linear_pattern() got an unexpected keyword argument 'distance'": 1,
    "SyntaxError: invalid syntax. Perhaps you forgot a comma? (<unknown>, line 18)": 1,
    "exec error: Part.cylinder() got an unexpected keyword argument 'mode'": 1,
    "exec error: unsupported operand type(s) for -: 'ParameterRef' and 'ParameterRef'": 1,
    "SyntaxError: positional argument follows keyword argument (<unknown>, line 9)": 1,
    "exec error: unsupported operand type(s) for +: 'ParameterRef' and 'float'": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 13)": 1,
    "exec error: Part.__init__() got an unexpected keyword argument 'sample_method'": 1,
    "exec error: Part.standoff_array_plate() got an unexpected keyword argument 'standoff_length'": 1,
    "exec error: 'FeatureHandle' object has no attribute 'top_outermost_shell'": 1,
    "exec error: 'FeatureHandle' object has no attribute 'safetail_edges'": 1,
    "exec error: Part.bossed_plate() got an unexpected keyword argument 'hole_distances'": 1,
    "exec error: Part.bossed_plate() got an unexpected keyword argument 'boss_height_min'": 1,
    "exec error: 'Part' object has no attribute 'offset_hole_plate'": 1,
    "SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 21)": 1,
    "exec error: Part.rectangular_pocket() got an unexpected keyword argument 'parent'": 1,
    "exec error: 'Part' object has no attribute 'boolean_close'": 1,
    "exec error: 'Part' object has no attribute 'sketch_profile'": 1,
    "exec error: 'Part' object has no attribute 'threaded_hole'": 1,
    "exec error: 'Part' object has no attribute 'boolean_join_name'": 1,
    "exec error: 'Part' object has no attribute 'sweep_plate'": 1,
    "exec error: Part.loft() got an unexpected keyword argument 'height'": 1,
    "exec error: 'Part' object has no attribute 'stepped_cover_plate'": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 26)": 1,
    "exec error: Part.cone() got an unexpected keyword argument 'length'": 1,
    "exec error: 'Part' object has no attribute 'lug'": 1,
    "exec error: 'Part' object has no attribute 'clipped_stock'": 1,
    "exec error: 'Part' object has no attribute 'centered_symmetric_hole_plate'": 1,
    "exec error: Part.shell() got an unexpected keyword argument 'stock'": 1,
    "exec error: 'Part' object has no attribute 'rectangular_pocket_profile'": 1,
    "SyntaxError: invalid syntax (<unknown>, line 36)": 1,
    "exec error: name 'Sample' is not defined": 1,
    "exec error: Part.loft() got an unexpected keyword argument 'style'": 1,
    "exec error: keyword argument repeated: pocket_height (<candidate>, line 11)": 1,
    "exec error: Part.standoff_array_plate() missing 2 required keyword-only arguments: 'width' and 'standoff_height'": 1,
    "exec error: Part.torus() got an unexpected keyword argument 'radius_inner'": 1,
    "exec error: topology reference 'hole_002:top_face:40c6147e08ec' did not resolve any face": 1,
    "exec error: Part.translate() got an unexpected keyword argument 'angle'": 1,
    "exec error: Part.profile_cut_on_face() got an unexpected keyword argument 'distance'": 1,
    "exec error: name 'Box' is not defined": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 39)": 1,
    "SyntaxError: unterminated string literal (detected at line 23) (<unknown>, line 23)": 1,
    "exec error: Part.__init__() got an unexpected keyword argument 'task_type'": 1,
    "exec error: Part.rectangular_pocket() missing 1 required keyword-only argument: 'target'": 1,
    "SyntaxError: unterminated string literal (detected at line 5) (<unknown>, line 5)": 1,
    "SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 16)": 1,
    "exec error: 'ParameterRef' object cannot be interpreted as an integer": 1,
    "exec error: 'flange_height'": 1,
    "exec error: Part.prism() got an unexpected keyword argument 'size'": 1,
    "exec error: threaded_hole_on_face failed: Threaded hole parameters are invalid: Thread helix exceeds max_helix_segments (estimated=772, max=600, turns=32.1042, segments_per_turn=24). Reduce length, increase pitch, lower segments_per_turn, or set max_helix_segments to at least 772. Diagnostics: Face selector query '>Z |Z' matched 1 face. Available faces: 11 (11 planar, 0 curved). First matches: #2 center=(-1.63205e-15, -6.25863e-16, 20.5) normal=(0, 0, 1) type=planar": 1,
    "exec error: 'Part' object has no attribute 'clip_offset_clipped_section_plate'": 1,
    "SyntaxError: invalid syntax. Perhaps you forgot a comma? (<unknown>, line 8)": 1,
    "SyntaxError: invalid syntax. Maybe you meant '==' or ':=' instead of '='? (<unknown>, line 21)": 1,
    "exec error: 'Part' object has no attribute 'clipped_offset_clip'": 1,
    "exec error: 'FeatureHandle' object has no attribute 'top_path_on_face'": 1,
    "SyntaxError: expression cannot contain assignment, perhaps you meant \"==\"? (<unknown>, line 13)": 1,
    "SyntaxError: invalid syntax. Perhaps you forgot a comma? (<unknown>, line 6)": 1,
    "exec error: Part.standoff_array_plate() got an unexpected keyword argument 'standoff_width'": 1,
    "exec error: 'mode_height'": 1,
    "exec error: 'Part' object has no attribute 'clipped_offset_name'": 1,
    "exec error: Part.linear_pattern() got an unexpected keyword argument 'direction'": 1,
    "SyntaxError: invalid non-printable character U+00A0 (<unknown>, line 19)": 1,
    "exec error: 'Part' object has no attribute 'offset_profile'": 1,
    "exec error: 'Part' object has no attribute 'lofted_loft_plate'": 1,
    "exec error: Part.bossed_plate() got an unexpected keyword argument 'holes'": 1,
    "exec error: 'Part' object has no attribute 'pin_rowwraps'": 1,
    "exec error: 'Part' object has no attribute 'threaded_hole_pattern'": 1,
    "SyntaxError: invalid syntax (<unknown>, line 32)": 1,
    "exec error: 'Part' object has no attribute 'boolean_union'": 1,
    "exec error: 'slot_width'": 1,
    "exec error: 'Part' object has no attribute 'extrude_on_path'": 1,
    "exec error: name 'flluma_lofted_cone_top_face' is not defined": 1,
    "exec error: 'Part' object has no attribute 'boolean_offset'": 1,
    "SyntaxError: unterminated string literal (detected at line 55) (<unknown>, line 55)": 1
  },
  "extreme_cd_cases_gt_1000": [],
  "export_but_unscoreable_ids": [
    "flluma_0097257",
    "flluma_0094892",
    "flluma_0098494",
    "flluma_0097610"
  ]
}
```

### B2

```json
{
  "rows": 2500,
  "scoreable": 1524,
  "scoreable_pct": 60.96,
  "gate_counts_from_geometry_run": {
    "syntax_ok": 2403,
    "exec_ok": 1569,
    "build_ok": 1569,
    "solid_valid": 1569,
    "step_export_ok": 1540
  },
  "missing_target_rows": 0,
  "conditional": {
    "cd": {
      "n": 1524,
      "mean": 412844042.2779511,
      "median": 3.3985335272319546,
      "sd_sample": 8056451022.725291,
      "min": 0.02687572243760469,
      "max": 161406165524.9492,
      "q25": 1.7062795801529576,
      "q75": 8.409697988591567,
      "q95": 76.10932118120296,
      "q99": 421.76392477918824
    },
    "f_score_1pct": {
      "n": 1524,
      "mean": 0.1821762671065642,
      "median": 0.18841078367875647,
      "sd_sample": 0.09308190436003107,
      "min": 0.0,
      "max": 0.4398758324084351,
      "q25": 0.11262277337132975,
      "q75": 0.24929863319471623,
      "q95": 0.32991486246746216,
      "q99": 0.3850033506081453
    },
    "bbox_err": {
      "n": 1524,
      "mean": 877.076494067386,
      "median": 0.30990286000651224,
      "sd_sample": 17060.57930628478,
      "min": 0.0,
      "max": 333347.2316665809,
      "q25": 0.019672104294067072,
      "q75": 1.3512505444154441,
      "q95": 13.695834365924448,
      "q99": 29.52282361812188
    },
    "bbox_ratio_to_gt": {
      "n": 1524,
      "mean": 39.117167264356375,
      "median": 0.9999999999987301,
      "sd_sample": 784.1404816621402,
      "min": 0.0612688289076983,
      "max": 22701.62792522266,
      "q25": 0.9946565581606048,
      "q75": 1.0031925493277505,
      "q95": 1.096797430320757,
      "q99": 1.3509868916019847
    }
  },
  "unconditional_f_score_1pct": {
    "n": 2500,
    "mean": 0.11105465242816154,
    "median": 0.08295036764705882,
    "sd_sample": 0.11481251905643357,
    "min": 0.0,
    "max": 0.4398758324084351,
    "q25": 0.0,
    "q75": 0.20782900528169015,
    "q95": 0.31061549418035955,
    "q99": 0.36620544929677085
  },
  "non_scoreable_error_counts": {
    "exec error: topology reference 'join_001:top_face:b9ce48e7f7b9' did not resolve any face": 87,
    "exec error: Part.boolean_cut() got an unexpected keyword argument 'depth'": 79,
    "exec error: loft requires at least two profile features": 68,
    "SyntaxError: invalid syntax (<unknown>, line 1)": 36,
    "exec error: Part.rectangular_pocket() missing 1 required keyword-only argument: 'depth'": 31,
    "exec error: target must be a TopologyReference from a FeatureHandle": 30,
    "STEP export error: OCCT build failed": 29,
    "exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'major_count'": 24,
    "SyntaxError: unmatched ']' (<unknown>, line 1)": 23,
    "exec error: target must be a FeatureHandle": 23,
    "exec error: 'Part' object has no attribute 'boss_on_plate'": 18,
    "point cloud sampling failed on generated part": 16,
    "exec error: Part.boolean_join() got an unexpected keyword argument 'operation'": 14,
    "exec error: 'thickness'": 13,
    "exec error: Part.profile_cut_on_face() got an unexpected keyword argument 'offset_profile'": 12,
    "exec error: Part.extrude_on_face() got an unexpected keyword argument 'profile'": 12,
    "exec error: Part.revolve() got an unexpected keyword argument 'axis'": 12,
    "exec error: direction must be 'inward' or 'outward'": 11,
    "exec error: Part.hole_pattern() got an unexpected keyword argument 'profile'": 11,
    "exec error: unsupported operand type(s) for *: 'ParameterRef' and 'float'": 11,
    "exec error: topology reference 'revolve_001:top_face:d95ca6795e31' did not resolve any face": 10,
    "exec error: 'Part' object has no attribute 'loft_solid'": 9,
    "exec error: unsupported operand type(s) for /: 'ParameterRef' and 'float'": 9,
    "exec error: Part.rectangular_pocket() got an unexpected keyword argument 'height'": 9,
    "exec error: 'list' object has no attribute 'strip'": 9,
    "exec error: 'width'": 8,
    "exec error: 'Part' object has no attribute 'profile_plain'": 8,
    "exec error: 'Part' object has no attribute 'rectangular_slot'": 7,
    "exec error: 'height'": 7,
    "exec error: keyword argument repeated: semantic_type (<candidate>, line 9)": 7,
    "SyntaxError: invalid syntax (<unknown>, line 20)": 7,
    "exec error: 'Part' object has no attribute 'loft_loft_profile'": 6,
    "exec error: Part.shell() got an unexpected keyword argument 'depth'": 6,
    "exec error: Part.mirrored_lug_plate() got an unexpected keyword argument 'lug_offset_y'": 6,
    "exec error: offset must be a 3D sequence": 6,
    "exec error: keyword argument repeated: semantic_type (<candidate>, line 6)": 6,
    "exec error: 'Part' object has no attribute 'pin_row'": 6,
    "exec error: Part.revolve() got an unexpected keyword argument 'tool'": 5,
    "exec error: Part.revolved_bushing() got an unexpected keyword argument 'thickness'": 5,
    "exec error: Part.revolved_bushing() got an unexpected keyword argument 'section_offset'": 5,
    "SyntaxError: invalid syntax (<unknown>, line 23)": 5,
    "exec error: Part.loft() got an unexpected keyword argument 'segments'": 5,
    "exec error: 'Part' object has no attribute 'profile_rectangle'": 5,
    "SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers (<unknown>, line 1)": 5,
    "exec error: 'wall_thickness'": 4,
    "exec error: 'Part' object has no attribute 'loft_sketch_to_loft_profile'": 4,
    "exec error: 'Part' object has no attribute 'hole'": 4,
    "exec error: Part.revolve() got an unexpected keyword argument 'solid'": 4,
    "exec error: Part.sketch_on_face() got an unexpected keyword argument 'sketch_to_use'": 4,
    "exec error: Part.box() got an unexpected keyword argument 'size'": 4,
    "exec error: 'Part' object has no attribute 'loft_sketch_to_box'": 4,
    "exec error: 'Part' object has no attribute 'crescent_lug_profile'": 3,
    "exec error: unsupported operand type(s) for -: 'ParameterRef' and 'ParameterRef'": 3,
    "exec error: 'FeatureHandle' object has no attribute 'top_edge'": 3,
    "exec error: Part.linear_pattern() got an unexpected keyword argument 'length'": 3,
    "exec error: 'Part' object has no attribute 'fillet_on_face'": 3,
    "exec error: hole depth must be a number or 'through'": 3,
    "exec error: Part.cylinder() got an unexpected keyword argument 'positions'": 3,
    "exec error: Part.translate() got an unexpected keyword argument 'pos'": 3,
    "exec error: 'Part' object has no attribute 'loft_polygon'": 3,
    "exec error: 'Part' object has no attribute 'boolean_cut_on_face'": 3,
    "exec error: Part.cylinder() got an unexpected keyword argument 'length'": 3,
    "exec error: 'Part' object has no attribute 'loft_square_to_round'": 3,
    "SyntaxError: '(' was never closed (<unknown>, line 21)": 3,
    "exec error: Part.mirror() got an unexpected keyword argument 'position'": 3,
    "exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'radius'": 3,
    "exec error: Part.boolean_join() got an unexpected keyword argument 'depth'": 2,
    "exec error: topology reference 'cut_001:top_face:e6c86e3e481d' did not resolve any face": 2,
    "exec error: Part.hole_pattern() got an unexpected keyword argument 'offset'": 2,
    "exec error: 'Part' object has no attribute 'profile_pic'": 2,
    "exec error: Part.rotate() got an unexpected keyword argument 'angle'": 2,
    "exec error: Part.revolve() got an unexpected keyword argument 'target'": 2,
    "exec error: 'FeatureHandle' object has no attribute 'top_profile'": 2,
    "exec error: Part.chamfer() got an unexpected keyword argument 'length'": 2,
    "exec error: 'slot_length'": 2,
    "SyntaxError: '[' was never closed (<unknown>, line 7)": 2,
    "exec error: Part.shell() got an unexpected keyword argument 'height'": 2,
    "no `part` variable after execution": 2,
    "exec error: 'FeatureHandle' object has no attribute 'pocket_profile'": 2,
    "exec error: 'Part' object has no attribute 'loft_rectangle_profile'": 2,
    "exec error: 'Part' object has no attribute 'offset_profile_name'": 2,
    "exec error: 'flange_height'": 2,
    "exec error: 'hub_body_height'": 2,
    "exec error: 'ParameterRef' object is not iterable": 2,
    "exec error: Part.sketch_on_face() got an unexpected keyword argument 'sketch_type'": 2,
    "exec error: Part.extrude() got an unexpected keyword argument 'thickness'": 2,
    "SyntaxError: invalid syntax (<unknown>, line 2)": 2,
    "exec error: unsupported extrude_on_face operation 'extrude'": 2,
    "exec error: Part.boss() got an unexpected keyword argument 'lift'": 2,
    "exec error: Part.cone() got an unexpected keyword argument 'radius_bottom'": 2,
    "exec error: name 'phere' is not defined": 2,
    "exec error: Part.extrude_on_face() got an unexpected keyword argument 'sketch_2d'": 2,
    "exec error: 'Part' object has no attribute 'profile_extrude'": 2,
    "exec error: Part.bossed_plate() got an unexpected keyword argument 'text'": 2,
    "exec error: Part.revolved_bushing() got an unexpected keyword argument 'wheel_radius'": 2,
    "exec error: 'Part' object has no attribute 'boolean_shell'": 2,
    "exec error: name 'holes' is not defined": 2,
    "exec error: keyword argument repeated: semantic_type (<candidate>, line 8)": 2,
    "exec error: 'Part' object has no attribute 'profile_path'": 2,
    "exec error: width must resolve to a number, got '79.4'": 1,
    "exec error: 'Part' object has no attribute 'boolean_cut_ex'": 1,
    "exec error: width must resolve to a number, got '54.1'": 1,
    "exec error: topology reference 'extrude_001:top_face:b9ec9b032ae6' did not resolve any face": 1,
    "exec error: 'Part' object has no attribute 'offset_radius'": 1,
    "exec error: Part.circular_pattern() got an unexpected keyword argument 'radius'": 1,
    "exec error: topology reference 'join_002:top_face:323af5d41048' did not resolve any face": 1,
    "exec error: 'Part' object has no attribute 'loft_lofted_rectangle_profile'": 1,
    "exec error: 'lower_height'": 1,
    "exec error: parameter 'pin_row_width_total' already exists": 1,
    "exec error: keyword argument repeated: semantic_type (<candidate>, line 11)": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 19)": 1,
    "exec error: Part.profile_cut_on_face() got an unexpected keyword argument 'offset_frequency'": 1,
    "exec error: name 'join_1' is not defined": 1,
    "exec error: name 'local_x' is not defined": 1,
    "exec error: 'Part' object has no attribute 'loft_sketch_to_bracket_profile'": 1,
    "exec error: 'Part' object has no attribute 'sketch_on_profile'": 1,
    "exec error: 'outer_profile_width'": 1,
    "exec error: 'Part' object has no attribute 'pin_pattern'": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 40)": 1,
    "exec error: width must resolve to a number, got '84.3'": 1,
    "exec error: 'Part' object has no attribute 'box_profile'": 1,
    "exec error: name 'holes_top_face' is not defined": 1,
    "exec error: Part.loft() got an unexpected keyword argument 'thickness'": 1,
    "SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 14)": 1,
    "exec error: 'Part' object has no attribute 'profile_patch'": 1,
    "exec error: 'Part' object has no attribute 'profile_hollow_cone'": 1,
    "exec error: 'slot_depth'": 1,
    "exec error: 'Part' object has no attribute 'rail_plate'": 1,
    "exec error: Part.boolean_join() got an unexpected keyword argument 'offset'": 1,
    "SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 13)": 1,
    "exec error: topology reference 'intersect_002:top_face:35b57a3f0eb3' did not resolve any face": 1,
    "exec error: width must resolve to a number, got '56.7'": 1,
    "exec error: 'Part' object has no attribute 'loft_square_profile_to_lofted_solid'": 1,
    "exec error: Part.loft() got an unexpected keyword argument 'lower_profile'": 1,
    "exec error: width must resolve to a number, got '75.9'": 1,
    "exec error: width must resolve to a number, got '59.9'": 1,
    "exec error: Part.hole_pattern() missing 1 required keyword-only argument: 'positions'": 1,
    "exec error: 'length'": 1,
    "exec error: 'Part' object has no attribute 'sweep_mount'": 1,
    "exec error: Part.extrude() got an unexpected keyword argument 'size'": 1,
    "exec error: width must resolve to a number, got '72.6'": 1,
    "exec error: Part.plate() got an unexpected keyword argument 'radius'": 1,
    "SyntaxError: unterminated string literal (detected at line 22) (<unknown>, line 22)": 1,
    "exec error: 'Part' object has no attribute 'loft_sketch_to_bracket'": 1,
    "exec error: Part.shell() got an unexpected keyword argument 'profile'": 1,
    "exec error: 'Part' object has no attribute 'profile_polygon'": 1,
    "exec error: 'Part' object has no attribute 'profile_match'": 1,
    "exec error: Part.rail_mount_plate() missing 2 required keyword-only arguments: 'hole_radius' and 'hole_positions'": 1,
    "exec error: 'Part' object has no attribute 'profile_from_sketch'": 1,
    "exec error: 'Part' object has no attribute 'hub_mount_hub'": 1,
    "SyntaxError: invalid syntax (<unknown>, line 14)": 1,
    "exec error: parameter 'hole_radius' already exists": 1,
    "SyntaxError: unmatched ')' (<unknown>, line 8)": 1,
    "exec error: 'Part' object has no attribute 'profile_from_profile_pic'": 1,
    "exec error: topology reference 'pocket_001:top_outer_edges:0501fba53d98' did not resolve any edge_set": 1,
    "exec error: 'Part' object has no attribute 'loft_sketch_to_solid'": 1,
    "exec error: 'Part' object has no attribute 'boxed_pocket'": 1,
    "exec error: width must resolve to a number, got '82.8'": 1,
    "exec error: width must resolve to a number, got '70.6'": 1,
    "exec error: 'Part' object has no attribute 'profile'": 1,
    "SyntaxError: unterminated string literal (detected at line 23) (<unknown>, line 23)": 1,
    "exec error: 'hub_rev_height'": 1,
    "exec error: Parameters.add() got an unexpected keyword argument 'enum'": 1,
    "exec error: Part.clamp_pad_plate() got an unexpected keyword argument 'jaw_offset_y'": 1,
    "exec error: Part.loft() got an unexpected keyword argument 'target'": 1,
    "exec error: 'Part' object has no attribute 'loft_bracket_profile'": 1,
    "exec error: Part.shell() got an unexpected keyword argument 'tool'": 1,
    "exec error: 'Part' object has no attribute 'angle_bracket'": 1,
    "exec error: 'flange_radius'": 1,
    "exec error: 'Part' object has no attribute 'boolean_cut_face'": 1,
    "exec error: parameter 'lower_width' already exists": 1,
    "SyntaxError: positional argument follows keyword argument (<unknown>, line 15)": 1,
    "exec error: Part.pin_cluster() got an unexpected keyword argument 'target'": 1,
    "SyntaxError: unterminated string literal (detected at line 16) (<unknown>, line 16)": 1,
    "exec error: 'Part' object has no attribute 'loft_profiled_loft'": 1,
    "exec error: 'Part' object has no attribute 'stepped_machined_profile'": 1,
    "exec error: 'lower_width'": 1,
    "exec error: 'Part' object has no attribute 'loft_lofted_transition_bracket_profile'": 1,
    "exec error: Part.rectangular_pocket() got an unexpected keyword argument 'profile'": 1,
    "exec error: Part.sketch_on_face() got an unexpected keyword argument 'sketch'": 1,
    "exec error: 'Part' object has no attribute 'lofted_plate'": 1,
    "SyntaxError: invalid syntax. Perhaps you forgot a comma? (<unknown>, line 21)": 1,
    "exec error: 'Part' object has no attribute 'place_on_face'": 1,
    "exec error: width must resolve to a number, got '77.6'": 1,
    "exec error: 'Part' object has no attribute 'loft_rectangle_profiled_bracket'": 1,
    "exec error: topology reference 'hole_002:top_face:40c6147e08ec' did not resolve any face": 1,
    "exec error: 'upper_width'": 1,
    "exec error: mirror: plane must be 'YZ', 'XZ', or 'XY'": 1,
    "exec error: 'Part' object has no attribute 'boolean_cover'": 1,
    "exec error: 'Part' object has no attribute 'lobed_gasket_profile'": 1,
    "exec error: 'Part' object has no attribute 'profile_section'": 1,
    "exec error: topology reference 'intersect_001:top_face:b46cd3dfad93' did not resolve any face": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 23)": 1,
    "exec error: 'Part' object has no attribute 'profile_plate'": 1,
    "exec error: 'Part' object has no attribute 'boolean_intersection'": 1,
    "exec error: name 'target' is not defined": 1,
    "SyntaxError: only single target (not tuple) can be annotated (<unknown>, line 1)": 1,
    "exec error: 'FeatureHandle' object has no attribute 'id'": 1,
    "exec error: 'Part' object has no attribute 'boolean_difference'": 1,
    "exec error: width must resolve to a number, got '55.7'": 1,
    "exec error: width must resolve to a number, got '85.2'": 1,
    "exec error: Part.threaded_hole_on_face() got an unexpected keyword argument 'length'": 1,
    "exec error: width must resolve to a number, got '74.3'": 1,
    "exec error: unsupported operand type(s) for +: 'ParameterRef' and 'float'": 1,
    "exec error: 'FeatureHandle' object has no attribute 'path'": 1,
    "exec error: 'Part' object has no attribute 'boss_on_face'": 1,
    "exec error: Part.linear_pattern() got an unexpected keyword argument 'profile'": 1,
    "exec error: 'Part' object has no attribute 'hub_on_mount_plate'": 1,
    "exec error: 'Part' object has no attribute 'loft_on_profile'": 1,
    "exec error: 'Part' object has no attribute 'profile_on_sketch'": 1,
    "exec error: name 'plate' is not defined": 1,
    "exec error: Part.revolve() got an unexpected keyword argument 'primitive'": 1,
    "exec error: Part.cylinder() got an unexpected keyword argument 'thickness'": 1,
    "SyntaxError: unterminated string literal (detected at line 11) (<unknown>, line 11)": 1,
    "exec error: width must resolve to a number, got '70.7'": 1
  },
  "extreme_cd_cases_gt_1000": [
    {
      "sample_id": "flluma_0094438",
      "syntax_ok": true,
      "exec_ok": true,
      "build_ok": true,
      "solid_valid": true,
      "step_export_ok": true,
      "error": "",
      "cd": 161340357314.26804,
      "bbox_err": 333337.19333434216,
      "f_score_1pct": 0.00390625,
      "target_bbox_diag": 73.40287702923594,
      "gen_bbox_diag": 1000020.2620591536,
      "bbox_ratio_to_gt": 13623.720248197511,
      "has_target": true
    },
    {
      "sample_id": "flluma_0094542",
      "syntax_ok": true,
      "exec_ok": true,
      "build_ok": true,
      "solid_valid": true,
      "step_export_ok": true,
      "error": "",
      "cd": 161406165524.9492,
      "bbox_err": 333339.7766669635,
      "f_score_1pct": 0.0068359375,
      "target_bbox_diag": 88.70575804765623,
      "gen_bbox_diag": 1000023.1826526069,
      "bbox_ratio_to_gt": 11273.486689729374,
      "has_target": true
    },
    {
      "sample_id": "flluma_0096583",
      "syntax_ok": true,
      "exec_ok": true,
      "build_ok": true,
      "solid_valid": true,
      "step_export_ok": true,
      "error": "",
      "cd": 146867515889.75748,
      "bbox_err": 333335.18535976624,
      "f_score_1pct": 0.004971590909090909,
      "target_bbox_diag": 44.04979256789268,
      "gen_bbox_diag": 1000002.001059538,
      "bbox_ratio_to_gt": 22701.62792522266,
      "has_target": true
    },
    {
      "sample_id": "flluma_0091100",
      "syntax_ok": true,
      "exec_ok": true,
      "build_ok": true,
      "solid_valid": true,
      "step_export_ok": true,
      "error": "",
      "cd": 159560253107.05212,
      "bbox_err": 333347.2316665809,
      "f_score_1pct": 0.0033482142857142855,
      "target_bbox_diag": 95.03589298265676,
      "gen_bbox_diag": 1000028.206832141,
      "bbox_ratio_to_gt": 10522.637031617493,
      "has_target": true
    }
  ],
  "export_but_unscoreable_ids": [
    "flluma_0097660",
    "flluma_0099626",
    "flluma_0090550",
    "flluma_0099686",
    "flluma_0090967",
    "flluma_0096823",
    "flluma_0090602",
    "flluma_0099162",
    "flluma_0091437",
    "flluma_0096851",
    "flluma_0097718",
    "flluma_0098734",
    "flluma_0097297",
    "flluma_0099418",
    "flluma_0097677",
    "flluma_0099193"
  ]
}
```

## Provenance

Generation actuals: `__RUN_SOURCE_ROOT__\outputs\b0_b2_fullstack_s3\cag_b0_b2_seed_3_actuals.json`.
Generation actuals SHA256: `cf6b602eb784ae4db69972b3e89bd6e10bdb2311a251cd6743e7967b781fca09`.
All 2500 paired-case rows: `__EVIDENCE_SOURCE_ROOT__\03\result\cag_b0_b2_seed_3_paired_cases.jsonl`.

B0 files and SHA256:

```json
{
  "__DEV_ROOT__\\scratch\\exec_b0b2_step_B0_s3\\execution_rows.jsonl": "21c3224e490b9ad1dd0e430421e988c621dcc936182a8cc74a4d99e5410cac4c",
  "__DEV_ROOT__\\scratch\\geom_b0b2_step_B0_s3\\geometry_nbest_rows.jsonl": "b6c742448fc93a141a756c32d10a2c12af7ce747ba00acde0a0c1076ee02167e",
  "__DEV_ROOT__\\scratch\\exec_b0b2_step_B0_s3\\execution_summary.json": "fb8bcd2689fb3fa8824eda310359cec77c91ae0525f986c86e06c89e8beb477c",
  "__RUN_SOURCE_ROOT__\\outputs\\b0_b2_fullstack_s3\\predictions\\gen_step_B0_s3.jsonl": "0a9c6d70a396a04605100f3dd2bf5094bd8020317af5e7a33b935ed3e834bcdb",
  "__RUN_SOURCE_ROOT__\\outputs\\b0_b2_fullstack_s3\\predictions\\geom_input_step_B0_s3.jsonl": "fb802cdb9d9d8e04d3c669faff5e8e390f893edec56c3c84fe289d789a31c911"
}
```

B2 files and SHA256:

```json
{
  "__DEV_ROOT__\\scratch\\exec_b0b2_step_B2_s3\\execution_rows.jsonl": "ac47fef0de39c4c71ea9b62fa1fb2f194cf7cadc2a83531cc0631d1ef95267ff",
  "__DEV_ROOT__\\scratch\\geom_b0b2_step_B2_s3\\geometry_nbest_rows.jsonl": "ff39b6feeeabee1b9d5b8622667f8e5af4c2f65bb375e2b202bbf5886754f942",
  "__DEV_ROOT__\\scratch\\exec_b0b2_step_B2_s3\\execution_summary.json": "4b6960f60862555c3aa2d07505a3860543e640d168002a0baf11258d895f4005",
  "__RUN_SOURCE_ROOT__\\outputs\\b0_b2_fullstack_s3\\predictions\\gen_step_B2_s3.jsonl": "d50a9ff77e489ee7497b32e34385bf8f0d3e97bfe7afcc728ca3890d919434ad",
  "__RUN_SOURCE_ROOT__\\outputs\\b0_b2_fullstack_s3\\predictions\\geom_input_step_B2_s3.jsonl": "b95c79b831a9cae42aa5c821d1b704c3144867a00d120bfed84f5ca05154b93a"
}
```

Evaluator-source hashes describe files present at analysis time; they are not a historical build attestation. See the frozen generation actuals and earlier run records for training-code provenance.

# Seed 4 Evaluation Record

Audit: PASS. Evaluation complete.

| Seed | Arm | Syntax | Execute | Build | Solid | STEP export | Scoreable |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 4 | B0 | 2384/2500 (95.36%) | 1371/2500 (54.84%) | 1371/2500 (54.84%) | 1371/2500 (54.84%) | 1355/2500 (54.20%) | 1338/2500 (53.52%) |
| 4 | B2 | 2288/2500 (91.52%) | 1463/2500 (58.52%) | 1463/2500 (58.52%) | 1463/2500 (58.52%) | 1433/2500 (57.32%) | 1340/2500 (53.60%) |

## Geometry

| Metric | B0 | B2 | B2 - B0 |
| --- | ---: | ---: | ---: |
| conditional_mean_cd | 12.27719494 | 13.68590956 | 1.408714615 |
| conditional_median_cd | 6.574505246 | 3.491073769 | -3.083431477 |
| conditional_mean_f1_pct | 13.68949938 | 17.31349776 | 3.623998376 |
| conditional_median_f1_pct | 11.66341146 | 17.94188108 | 6.278469624 |
| unconditional_mean_f1_pct | 7.32662007 | 9.280034799 | 1.953414729 |
| unconditional_median_f1_pct | 1.609848485 | 5.517146018 | 3.907297533 |
| paired_mean_cd | 9.894667405 | 14.7752277 | 4.880560291 |
| paired_median_cd | 5.371551933 | 3.492626897 | -1.878925036 |
| paired_mean_f1_pct | 14.77199166 | 17.89777531 | 3.125783653 |
| paired_median_f1_pct | 15.08377695 | 18.27122326 | 3.187446309 |
| conditional_mean_bbox_err | 1.941821021 | 1.295532591 | -0.6462884296 |
| conditional_median_bbox_err | 0.8574996594 | 0.06679342982 | -0.7907062296 |

Percent metrics above use 0-100 units. CD/bbox remain in evaluator units. Conditional full-set and jointly scoreable metrics use different subsets.

## Paired Tests

Within-seed query-level tests below do not measure uncertainty across training seeds.

| Gate | Both | B0 only | B2 only | Neither | Delta pp | Exact McNemar p |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| syntax_ok | 2200 | 184 | 88 | 28 | -3.84 | 5.8960009e-09 |
| exec_ok | 942 | 429 | 521 | 608 | 3.68 | 0.0031324221 |
| build_ok | 942 | 429 | 521 | 608 | 3.68 | 0.0031324221 |
| solid_valid | 942 | 429 | 521 | 608 | 3.68 | 0.0031324221 |
| step_export_ok | 921 | 434 | 512 | 633 | 3.12 | 0.012257255 |

Jointly scoreable: 830.

| Metric | B2 wins | B0 wins | Ties | Median paired difference B2 - B0 | Exact sign p |
| --- | ---: | ---: | ---: | ---: | ---: |
| cd | 515 | 315 | 0 | -0.29261963 | 3.9077567e-12 |
| f_score_1pct | 509 | 321 | 0 | 0.01608305926 | 7.116862e-11 |
| bbox_err | 452 | 253 | 125 | -0.01981431 | 6.0649388e-14 |

F@1 paired differences in the last table use raw 0-1 units. Multiply by 100 for percentage points.

## Distributions And Failures

No CD values were removed, clipped, or winsorized. CD > 1000 is a retrospective audit flag, not an exclusion rule.

### B0

```json
{
  "rows": 2500,
  "scoreable": 1338,
  "scoreable_pct": 53.52,
  "gate_counts_from_geometry_run": {
    "syntax_ok": 2384,
    "exec_ok": 1371,
    "build_ok": 1371,
    "solid_valid": 1371,
    "step_export_ok": 1355
  },
  "missing_target_rows": 0,
  "conditional": {
    "cd": {
      "n": 1338,
      "mean": 12.277194940913216,
      "median": 6.57450524599837,
      "sd_sample": 21.87607258093098,
      "min": 0.056222711078634496,
      "max": 397.02177671323165,
      "q25": 2.7043936001272857,
      "q75": 16.009820546714607,
      "q95": 33.0984299680449,
      "q99": 88.37293478059411
    },
    "f_score_1pct": {
      "n": 1338,
      "mean": 0.13689499383259165,
      "median": 0.11663411458333334,
      "sd_sample": 0.10448093536911346,
      "min": 0.0,
      "max": 0.3983202167585784,
      "q25": 0.04094005766369048,
      "q75": 0.2133755542048055,
      "q95": 0.3262217644919661,
      "q99": 0.3689774512235449
    },
    "bbox_err": {
      "n": 1338,
      "mean": 1.9418210210996352,
      "median": 0.8574996593748778,
      "sd_sample": 3.138497258221199,
      "min": 0.0,
      "max": 30.46815188424495,
      "q25": 0.08397951481923585,
      "q75": 2.2383333843347963,
      "q95": 8.536451509231508,
      "q99": 13.402146728353967
    },
    "bbox_ratio_to_gt": {
      "n": 1338,
      "mean": 0.9769260480477842,
      "median": 0.9998472934629548,
      "sd_sample": 0.0944339985922736,
      "min": 0.22891894506467408,
      "max": 1.479830564893359,
      "q25": 0.9855375274519838,
      "q75": 1.0017567035019073,
      "q95": 1.0429639469822893,
      "q99": 1.1001257486319327
    }
  },
  "unconditional_f_score_1pct": {
    "n": 2500,
    "mean": 0.07326620069920306,
    "median": 0.016098484848484848,
    "sd_sample": 0.10248931911057417,
    "min": 0.0,
    "max": 0.3983202167585784,
    "q25": 0.0,
    "q75": 0.13424146645385304,
    "q95": 0.30313034671900163,
    "q99": 0.35301540363299777
  },
  "non_scoreable_error_counts": {
    "exec error: target must be a FeatureHandle": 139,
    "exec error: 'Part' object has no attribute 'sketch'": 90,
    "exec error: 'flange_height'": 70,
    "exec error: Part.bossed_plate() got an unexpected keyword argument 'hole_offset_x'": 45,
    "exec error: 'Part' object has no attribute 'threaded_hole'": 44,
    "SyntaxError: unmatched ')' (<unknown>, line 17)": 32,
    "exec error: 'width'": 30,
    "exec error: 'Part' object has no attribute 'join'": 28,
    "exec error: Part.linear_pattern() got an unexpected keyword argument 'length'": 22,
    "exec error: Part.box() got an unexpected keyword argument 'thickness'": 18,
    "point cloud sampling failed on generated part": 17,
    "exec error: 'Part' object has no attribute 'profile_pocket'": 17,
    "exec error: Part.bossed_plate() got an unexpected keyword argument 'chamfer_distance'": 16,
    "STEP export error: OCCT build failed": 16,
    "exec error: name 'plate' is not defined": 15,
    "exec error: unsupported operand type(s) for *: 'ParameterRef' and 'float'": 14,
    "exec error: Part.bossed_plate() got an unexpected keyword argument 'hole_position'": 13,
    "exec error: 'Part' object has no attribute 'lofted_transition_bracket'": 13,
    "exec error: Part.revolved_bushing() got an unexpected keyword argument 'section_radius'": 12,
    "exec error: topology reference 'join_001:top_face:b9ce48e7f7b9' did not resolve any face": 11,
    "exec error: target must be a TopologyReference from a FeatureHandle": 11,
    "exec error: Parameters.add() takes 3 positional arguments but 5 positional arguments (and 1 keyword-only argument) were given": 11,
    "exec error: Part.plate() got an unexpected keyword argument 'radius_x'": 10,
    "exec error: 'Part' object has no attribute 'flange'": 9,
    "exec error: 'Part' object has no attribute 'shelled_plate'": 9,
    "exec error: 'Part' object has no attribute 'rect_profile'": 8,
    "exec error: Part.sketch_on_face() got an unexpected keyword argument 'sketch'": 8,
    "SyntaxError: '[' was never closed (<unknown>, line 7)": 8,
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'profile_radius'": 7,
    "exec error: Part.sketch_on_face() got an unexpected keyword argument 'profile_type'": 7,
    "exec error: 'Part' object has no attribute 'mirrored_clearance_pocket_plate'": 7,
    "exec error: Part.plate() got an unexpected keyword argument 'radius'": 7,
    "exec error: Part.rectangular_pocket() got an unexpected keyword argument 'height'": 7,
    "exec error: Part.plate() got an unexpected keyword argument 'length'": 6,
    "exec error: Part.linear_pattern() got an unexpected keyword argument 'offset'": 6,
    "SyntaxError: '[' was never closed (<unknown>, line 9)": 6,
    "exec error: 'Part' object has no attribute 'pin_cluster_plate'": 6,
    "exec error: unsupported operand type(s) for /: 'ParameterRef' and 'float'": 6,
    "SyntaxError: '(' was never closed (<unknown>, line 17)": 6,
    "exec error: Part.sketch_on_face() missing 1 required keyword-only argument: 'profile'": 5,
    "exec error: 'Part' object has no attribute 'rectangular_clamp_jaws'": 5,
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'path_length_var'": 5,
    "exec error: 'Part' object has no attribute 'revolved_hub_mount'": 5,
    "SyntaxError: invalid syntax. Perhaps you forgot a comma? (<unknown>, line 17)": 5,
    "exec error: parameter 'flange_thickness' already exists": 5,
    "exec error: name 'hole' is not defined": 5,
    "exec error: 'plate_width'": 5,
    "exec error: 'Part' object has no attribute 'sketch_on_plate'": 5,
    "exec error: 'Part' object has no attribute 'boolean_pocket'": 5,
    "exec error: Part.pin_cluster() got an unexpected keyword argument 'radial_offset'": 5,
    "exec error: Part.ribbed_support_plate() got an unexpected keyword argument 'rib_offset'": 5,
    "exec error: Part.clipped_offset_stock() got an unexpected keyword argument 'sphere_center'": 5,
    "exec error: Part.rectangular_pocket() got an unexpected keyword argument 'profile'": 4,
    "exec error: 'flange_length'": 4,
    "SyntaxError: unterminated string literal (detected at line 18) (<unknown>, line 18)": 4,
    "exec error: Part.sensor_mount_plate() got an unexpected keyword argument 'hole_offset_x'": 4,
    "exec error: Part.rotate() got an unexpected keyword argument 'angle'": 3,
    "exec error: name 'boss' is not defined": 3,
    "exec error: 'Part' object has no attribute 'sketch_linear_pattern'": 3,
    "SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 20)": 3,
    "exec error: 'Part' object has no attribute 'pocket'": 3,
    "exec error: 'plate_length'": 3,
    "exec error: Part.cone() got an unexpected keyword argument 'height_top'": 3,
    "exec error: 'Part' object has no attribute 'clipped_stock'": 3,
    "SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 18)": 3,
    "SyntaxError: '(' was never closed (<unknown>, line 18)": 2,
    "exec error: topology reference 'revolve_001:top_face:d95ca6795e31' did not resolve any face": 2,
    "SyntaxError: '(' was never closed (<unknown>, line 15)": 2,
    "SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 24)": 2,
    "exec error: Part.ellipsoid() got an unexpected keyword argument 'center'": 2,
    "SyntaxError: '(' was never closed (<unknown>, line 20)": 2,
    "SyntaxError: unexpected character after line continuation character (<unknown>, line 11)": 2,
    "exec error: 'Part' object has no attribute 'round_prism'": 2,
    "SyntaxError: invalid syntax (<unknown>, line 14)": 2,
    "exec error: name 'partstandoff_plate' is not defined": 2,
    "exec error: 'Part' object has no attribute 'path_tube'": 2,
    "SyntaxError: '[' was never closed (<unknown>, line 20)": 2,
    "SyntaxError: unterminated string literal (detected at line 9) (<unknown>, line 9)": 2,
    "SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 8)": 2,
    "exec error: 'Part' object has no attribute 'u_channel'": 2,
    "exec error: unsupported sketch_on_face profile [[-25.09, -21.03], [25.09, -21.03], [25.09, 21.03], [-25.09, 21.03]]": 1,
    "exec error: 'Part' object has no attribute 'linear_ribbed_plate'": 1,
    "exec error: unsupported sketch_on_face profile [[-14.42, -23.1], [14.42, -23.1], [14.42, 23.1], [-14.42, 23.1]]": 1,
    "exec error: unsupported sketch_on_face profile [[-8.19, -10.1], [8.19, -10.1], [8.19, 10.1], [-8.19, 10.1]]": 1,
    "exec error: unsupported sketch_on_face profile [[-8.19, -15.02], [8.19, -15.02], [8.19, 15.02], [-8.19, 15.02]]": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 32)": 1,
    "SyntaxError: unterminated string literal (detected at line 26) (<unknown>, line 26)": 1,
    "exec error: unsupported sketch_on_face profile [[-35.22, -25.2], [35.22, -25.2], [35.22, 25.2], [-35.22, 25.2]]": 1,
    "exec error: unsupported sketch_on_face profile [[-15.09, -16.96], [15.09, -16.96], [15.09, 16.96], [-15.09, 16.96]]": 1,
    "SyntaxError: unterminated string literal (detected at line 38) (<unknown>, line 38)": 1,
    "exec error: unsupported sketch_on_face profile [[-30.03, -20.2], [30.03, -20.2], [30.03, 18.6], [-30.03, 18.6]]": 1,
    "exec error: unsupported sketch_on_face profile [[-30.18, -20.54], [30.18, -20.54], [30.18, 20.54], [-30.18, 20.54]]": 1,
    "exec error: unsupported sketch_on_face profile [[-35.05, -20.12], [35.05, -20.12], [35.05, 19.94], [-35.05, 19.94]]": 1,
    "exec error: 'Part' object has no attribute 'capsule_stock'": 1,
    "exec error: unsupported sketch_on_face profile [[-11.62, -13.9], [11.62, -13.9], [11.62, 13.9], [-11.62, 13.9]]": 1,
    "exec error: unsupported sketch_on_face profile [[-41.06, -25.51], [41.06, -25.51], [41.06, 25.51], [-41.06, 25.51]]": 1,
    "exec error: Part.boolean_join() got an unexpected keyword argument 'tool_side'": 1,
    "exec error: unsupported sketch_on_face profile [[-11.93, -10.09], [11.93, -10.09]]": 1,
    "exec error: unsupported sketch_on_face profile [[-24.43, -20.38], [24.43, -20.38], [24.43, 18.96], [-24.43, 18.96]]": 1,
    "exec error: unsupported sketch_on_face profile [[-12.496, -13.05], [12.496, -13.05], [12.496, 13.05], [-12.496, 13.05]]": 1,
    "exec error: 'pin_length'": 1,
    "SyntaxError: invalid syntax (<unknown>, line 24)": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 39)": 1,
    "exec error: unsupported sketch_on_face profile [[-30.02, -17.8], [30.02, -17.8], [30.02, 17.8], [-30.02, 17.8]]": 1,
    "exec error: unsupported sketch_on_face profile FeatureHandle(part=<flluma.api.part.Part object at 0x00000225A9721750>, feature_id='sketch_001', node=CSGNode(name='service_cover_boss_width', type=Transform))": 1,
    "exec error: unsupported sketch_on_face profile [[-30.16, -25.9], [30.16, -25.9], [30.16, 25.9], [-30.16, 25.9]]": 1,
    "exec error: unsupported sketch_on_face profile FeatureHandle(part=<flluma.api.part.Part object at 0x00000225D378FF90>, feature_id='sketch_001', node=CSGNode(name='service_cover_boss_width', type=Transform))": 1,
    "SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 22)": 1,
    "SyntaxError: unterminated string literal (detected at line 55) (<unknown>, line 55)": 1,
    "exec error: unsupported sketch_on_face profile [[-9.8, -21.1], [9.8, -21.1], [9.8, 21.1], [-9.8, 21.1]]": 1,
    "exec error: unsupported sketch_on_face profile [[-23.22, -15.58], [23.22, -15.58], [23.22, 15.58], [-23.22, 15.58]]": 1,
    "exec error: 'FeatureHandle' object has no attribute 'box'": 1,
    "SyntaxError: invalid character '\uff0c' (U+FF0C) (<unknown>, line 11)": 1,
    "exec error: unsupported sketch_on_face profile [[-13.93, -14.0], [13.93, -14.0], [13.93, 14.0], [-13.93, 14.0]]": 1,
    "exec error: unsupported sketch_on_face profile [[-35.07, -18.54], [35.07, -18.54], [35.07, 18.54], [-35.07, 18.54]]": 1,
    "exec error: unsupported sketch_on_face profile [[-11.98, -20.55], [11.98, -20.55], [11.98, 18.9], [-11.98, 18.9]]": 1,
    "exec error: 'FeatureHandle' object has no attribute 'to_profile'": 1,
    "exec error: unsupported sketch_on_face profile [[-32.03, -24.09], [32.03, -24.09], [32.03, 24.09], [-32.03, 24.09]]": 1,
    "exec error: unsupported sketch_on_face profile [[-9.84, -22.08], [9.84, -22.08], [9.84, 22.08], [-9.84, 22.08]]": 1,
    "exec error: unsupported sketch_on_face profile [[-13.57, -16.02], [13.57, -16.02], [13.57, 16.02], [-13.57, 16.02]]": 1,
    "exec error: unsupported sketch_on_face profile FeatureHandle(part=<flluma.api.part.Part object at 0x00000225D25EDF90>, feature_id='sketch_001', node=CSGNode(name='service_cover_boss_width', type=Transform))": 1,
    "exec error: unsupported sketch_on_face profile FeatureHandle(part=<flluma.api.part.Part object at 0x00000225D25E7ED0>, feature_id='sketch_001', node=CSGNode(name='service_cover_boss_width', type=Transform))": 1,
    "SyntaxError: unterminated string literal (detected at line 58) (<unknown>, line 58)": 1,
    "exec error: topology reference 'chamfer_001:top_face:f40479b908d2' did not resolve any face": 1,
    "exec error: unsupported sketch_on_face profile [[-29.94, -21.32], [29.94, -21.32], [29.94, 21.32], [-29.94, 21.32]]": 1,
    "exec error: unsupported sketch_on_face profile [[-13.6, -13.38], [13.6, -13.38], [13.6, 13.38], [-13.6, 13.38]]": 1,
    "exec error: unsupported sketch_on_face profile [[-36.05, -17.18], [36.05, -17.18], [36.05, 17.18], [-36.05, 17.18]]": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 16)": 1,
    "SyntaxError: invalid syntax. Perhaps you forgot a comma? (<unknown>, line 15)": 1,
    "exec error: 'Part' object has no attribute 'hole'": 1,
    "exec error: unsupported operand type(s) for *: 'int' and 'ParameterRef'": 1,
    "exec error: unsupported sketch_on_face profile [[-25.94, -15.86], [25.94, -15.86], [25.94, 15.86], [-25.94, 15.86]]": 1,
    "SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 11)": 1,
    "exec error: Part.bossed_plate() missing 4 required keyword-only arguments: 'width', 'height', 'hole_radius', and 'hole_positions'": 1,
    "exec error: unsupported sketch_on_face profile [[-10.92, -24.92], [10.92, -24.92], [10.92, 24.92], [-10.92, 24.92]]": 1,
    "exec error: 'Part' object has no attribute 'path_profile_flange'": 1,
    "exec error: unsupported sketch_on_face profile [[-9.13, -11.36], [9.13, -11.36], [9.13, 11.36], [-9.13, 11.36]]": 1,
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'path_length_variability'": 1,
    "exec error: Part.ribbed_support_plate() got an unexpected keyword argument 'rib_step'": 1,
    "exec error: unsupported sketch_on_face profile [[-30.08, -13.23], [30.08, -13.23], [30.08, 13.23], [-30.08, 13.23]]": 1,
    "exec error: 'Part' object has no attribute 'rectangular_clamp_jaw_array'": 1,
    "exec error: 'Part' object has no attribute 'line_segment'": 1,
    "exec error: unsupported sketch_on_face profile [[-9.69, -13.22], [9.69, -13.22], [9.69, 13.22], [-9.69, 13.22]]": 1,
    "SyntaxError: unterminated string literal (detected at line 36) (<unknown>, line 36)": 1,
    "exec error: unsupported sketch_on_face profile [[-40.02, -19.06], [40.02, -19.06], [40.02, 19.06], [-40.02, 19.06]]": 1,
    "exec error: unsupported sketch_on_face profile [[-29.02, -21.32], [29.02, -21.32], [29.02, 21.32], [-29.02, 21.32]]": 1,
    "exec error: 'Part' object has no attribute 'ribbed_shell_profile_name'": 1,
    "exec error: 'Part' object has no attribute 'top'": 1,
    "exec error: unsupported sketch_on_face profile [[-8.53, -22.29], [8.53, -22.29], [8.53, 22.29], [-8.53, 22.29]]": 1,
    "exec error: unsupported sketch_on_face profile [[-30.02, -25.51], [30.02, -25.51], [30.02, 25.51], [-30.02, 25.51]]": 1,
    "exec error: 'Part' object has no attribute 'pocket_pattern'": 1,
    "exec error: unsupported sketch_on_face profile [[-11.78, -9.9], [11.78, -9.9], [11.78, 9.9], [-11.78, 9.9]]": 1,
    "exec error: unsupported sketch_on_face profile [[-35.03, -22.14], [35.03, -22.14], [35.03, 22.14], [-35.03, 22.14]]": 1,
    "exec error: unsupported sketch_on_face profile [[-11.74, 7.06], [11.74, 7.06]]": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 68)": 1,
    "exec error: unsupported sketch_on_face profile [[-39.98, -23.2], [39.98, -23.2], [39.98, 23.2], [-39.98, 23.2]]": 1,
    "exec error: unsupported sketch_on_face profile [[-10.99, -22.58], [10.99, -22.58], [10.99, 22.58], [-10.99, 22.58]]": 1,
    "exec error: unsupported sketch_on_face profile [[-12.85, -24.22], [12.85, -24.22], [12.85, 24.22], [-12.85, 24.22]]": 1,
    "exec error: unsupported sketch_on_face profile [[-24.17, -17.64], [24.17, -17.64], [24.17, 17.64], [-24.17, 17.64]]": 1,
    "SyntaxError: invalid syntax. Perhaps you forgot a comma? (<unknown>, line 18)": 1,
    "exec error: 'Part' object has no attribute 'platemark'": 1,
    "exec error: unsupported sketch_on_face profile [[-10.05, -21.17], [10.05, -21.17], [10.05, 21.17], [-10.05, 21.17]]": 1,
    "exec error: unsupported sketch_on_face profile [[-40.02, -20.07], [40.02, -20.07], [40.02, 19.94], [-40.02, 19.94]]": 1,
    "exec error: unsupported sketch_on_face profile [[-35.06, -21.57], [35.06, -21.57], [35.06, 21.57], [-35.06, 21.57]]": 1,
    "exec error: unsupported sketch_on_face profile [[-9.49, -15.58], [9.49, -15.58], [9.49, 15.58], [-9.49, 15.58]]": 1,
    "exec error: unsupported sketch_on_face profile [[-30.02, -22.14], [30.02, -22.14], [30.02, 22.14], [-30.02, 22.14]]": 1,
    "exec error: unsupported sketch_on_face profile [[-12.55, -17.06], [12.55, -17.06], [12.55, 17.06], [-12.55, 17.06]]": 1,
    "exec error: unsupported sketch_on_face profile [[-8.09, -23.71], [8.09, -23.71], [8.09, 23.71], [-8.09, 23.71]]": 1,
    "exec error: unsupported sketch_on_face profile [[-30.06, -19.01], [30.06, -19.01], [30.06, 19.01], [-30.06, 19.01]]": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 45)": 1,
    "exec error: unsupported sketch_on_face profile [[-9.54, -13.32], [9.54, -13.32], [9.54, 13.32], [-9.54, 13.32]]": 1,
    "exec error: unsupported sketch_on_face profile [[[-9.24, -4.56], [9.24, -4.56], [9.24, 4.56], [-9.24, 4.56]]]": 1,
    "exec error: unsupported sketch_on_face profile [[-30.02, -29.01], [30.02, -29.01], [30.02, 29.01], [-30.02, 29.01]]": 1,
    "exec error: unsupported sketch_on_face profile [[-11.94, -13.4], [11.94, -13.4], [11.94, 13.4], [-11.94, 13.4]]": 1,
    "exec error: unsupported sketch_on_face profile [[-39.62, -22.32], [39.62, -22.32], [39.62, 22.32], [-39.62, 22.32]]": 1,
    "exec error: unsupported sketch_on_face profile [[-25.38, -22.02], [25.38, -22.02], [25.38, 22.02], [-25.38, 22.02]]": 1,
    "exec error: unsupported sketch_on_face profile [[-9.23, -18.36], [9.23, -18.36], [9.23, 18.36], [-9.23, 18.36]]": 1,
    "exec error: unsupported sketch_on_face profile [[-10.09, -16.13], [10.09, -16.13], [10.09, 16.13], [-10.09, 16.13]]": 1,
    "exec error: unsupported sketch_on_face profile [[-31.03, -20.31], [31.03, -20.31], [31.03, 18.61], [-31.03, 18.61]]": 1,
    "SyntaxError: invalid syntax (<unknown>, line 17)": 1,
    "exec error: unsupported sketch_on_face profile [[-9.34, -21.73], [9.34, -21.73], [9.34, 21.73], [-9.34, 21.73]]": 1,
    "exec error: name 'Lar' is not defined": 1,
    "exec error: unsupported sketch_on_face profile [[-10.36, -11.34], [10.36, -11.34], [10.36, 11.34], [-10.36, 11.34]]": 1,
    "exec error: unsupported sketch_on_face profile [[-15.02, -20.0], [15.02, -20.0], [15.02, 19.8], [-15.02, 19.8]]": 1,
    "exec error: unsupported sketch_on_face profile [[-9.8, -17.1], [9.8, -17.1], [9.8, 17.1], [-9.8, 17.1]]": 1,
    "exec error: unsupported sketch_on_face profile [[-10.404, -11.92], [10.404, -11.92], [10.404, 11.92], [-10.404, 11.92]]": 1,
    "exec error: unsupported sketch_on_face profile [[-9.34, -20.12], [9.34, -20.12], [9.34, 18.64], [-9.34, 18.64]]": 1,
    "exec error: Part.rectangular_pocket() got an unexpected keyword argument 'offset'": 1,
    "exec error: unsupported sketch_on_face profile [[-10.944, -11.04], [10.944, -11.04], [10.944, 11.04], [-10.944, 11.04]]": 1,
    "exec error: unsupported sketch_on_face profile [[-35.07, -22.03], [35.07, -22.03], [35.07, 22.03], [-35.07, 22.03]]": 1,
    "exec error: unsupported sketch_on_face profile [[-25.94, -20.0], [25.94, -20.0], [25.94, 19.8], [-25.94, 19.8]]": 1,
    "exec error: 'Part' object has no attribute 'profile_to_brep'": 1,
    "exec error: 'Part' object has no attribute 'lidge_profile'": 1,
    "exec error: unsupported sketch_on_face profile [[-24.43, -20.01], [24.43, -20.01], [24.43, 19.94], [-24.43, 19.94]]": 1,
    "exec error: unsupported sketch_on_face profile [[-34.01, -21.08], [34.01, -21.08], [34.01, 21.08], [-34.01, 21.08]]": 1,
    "exec error: unsupported sketch_on_face profile [[-27.46, -32.02], [27.46, -32.02], [27.46, 32.02], [-27.46, 32.02]]": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 22)": 1,
    "exec error: unsupported sketch_on_face profile [[-30.85, -28.3], [30.85, -28.3], [30.85, 28.3], [-30.85, 28.3]]": 1,
    "exec error: unsupported sketch_on_face profile [[[-14.68, -8.4], [14.68, -8.4], [14.68, 8.4], [-14.68, 8.4]]]": 1,
    "SyntaxError: unterminated string literal (detected at line 43) (<unknown>, line 43)": 1,
    "exec error: 'FeatureHandle' object has no attribute 'length'": 1,
    "SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 15)": 1,
    "exec error: unsupported sketch_on_face profile [[-39.55, -25.38], [39.55, -25.38], [39.55, 25.38], [-39.55, 25.38]]": 1,
    "exec error: unsupported sketch_on_face profile [[-14.01, -10.09], [14.01, -10.09]]": 1,
    "exec error: unsupported sketch_on_face profile [[-30.02, -24.74], [30.02, -24.74], [30.02, 24.74], [-30.02, 24.74]]": 1,
    "exec error: unsupported sketch_on_face profile [[-30.02, -20.64], [30.02, -20.64], [30.02, 20.64], [-30.02, 20.64]]": 1,
    "exec error: unsupported sketch_on_face profile [[-30.02, -19.73], [30.02, -19.73], [30.02, 19.73], [-30.02, 19.73]]": 1,
    "exec error: unsupported sketch_on_face profile [[-11.544, -13.06], [11.544, -13.06], [11.544, 13.06], [-11.544, 13.06]]": 1,
    "exec error: unsupported sketch_on_face profile [[-39.08, -15.55], [39.08, -15.55], [39.08, 15.55], [-39.08, 15.55]]": 1,
    "exec error: 'Part' object has no attribute 'ribbed_plate'": 1,
    "exec error: unsupported sketch_on_face profile [[-8.004, -10.98], [8.004, -10.98], [8.004, 10.98], [-8.004, 10.98]]": 1,
    "exec error: unsupported operand type(s) for -: 'ParameterRef' and 'ParameterRef'": 1,
    "exec error: unsupported sketch_on_face profile [[-11.34, -10.06], [11.34, -10.06], [11.34, 10.06], [-11.34, 10.06]]": 1,
    "exec error: 'Part' object has no attribute 'profile_path'": 1,
    "exec error: 'Part' object has no attribute 'rounded_slot_profile'": 1,
    "exec error: unsupported sketch_on_face profile [[-23.02, -20.78], [23.02, -20.78], [23.02, 20.78], [-23.02, 20.78]]": 1,
    "exec error: unsupported sketch_on_face profile [[-9.22, -21.02], [9.22, -21.02], [9.22, 21.02], [-9.22, 21.02]]": 1,
    "exec error: 'Part' object has no attribute 'ribbed_shell_plate'": 1,
    "exec error: unsupported sketch_on_face profile [[-9.22, -14.72], [9.22, -14.72], [9.22, 14.72], [-9.22, 14.72]]": 1,
    "exec error: keyword argument repeated: semantic_type (<candidate>, line 17)": 1,
    "exec error: Part.bossed_plate() got an unexpected keyword argument 'position'": 1,
    "exec error: 'Part' object has no attribute 'bossed_service_plate'": 1,
    "exec error: unsupported sketch_on_face profile [[-40.15, -21.06], [40.15, -21.06], [40.15, 21.06], [-40.15, 21.06]]": 1,
    "exec error: unsupported sketch_on_face profile [[-35.02, -19.02], [35.02, -19.02], [35.02, 19.02], [-35.02, 19.02]]": 1,
    "exec error: unsupported sketch_on_face profile [[-24.02, -23.04], [24.02, -23.04], [24.02, 23.04], [-24.02, 23.04]]": 1,
    "exec error: unsupported sketch_on_face profile [[-12.09, -19.66], [12.09, -19.66], [12.09, 19.66], [-12.09, 19.66]]": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 8)": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 42)": 1,
    "exec error: unsupported sketch_on_face profile [[-33.02, -18.52], [33.02, -18.52], [33.02, 18.52], [-33.02, 18.52]]": 1,
    "exec error: unsupported sketch_on_face profile [[-43.05, -18.02], [43.05, -18.02], [43.05, 18.02], [-43.05, 18.02]]": 1,
    "exec error: unsupported sketch_on_face profile [[-12.69, -23.2], [12.69, -23.2], [12.69, 23.2], [-12.69, 23.2]]": 1,
    "exec error: unsupported sketch_on_face profile [[-36.01, -19.32], [36.01, -19.32], [36.01, 19.32], [-36.01, 19.32]]": 1,
    "exec error: unsupported sketch_on_face profile [[-11.73, -13.06], [11.73, -13.06], [11.73, 13.06], [-11.73, 13.06]]": 1,
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'path_offset_2'": 1,
    "exec error: unsupported sketch_on_face profile [[-11.564, -15.14], [11.564, -15.14], [11.564, 15.14], [-11.564, 15.14]]": 1,
    "exec error: unsupported sketch_on_face profile [[-24.02, -16.9], [24.02, -16.9], [24.02, 16.9], [-24.02, 16.9]]": 1,
    "exec error: unsupported sketch_on_face profile [[-32.08, -19.2], [32.08, -19.2], [32.08, 19.2], [-32.08, 19.2]]": 1,
    "exec error: unsupported sketch_on_face profile [[-43.18, -20.06], [43.18, -20.06], [43.18, 19.84], [-43.18, 19.84]]": 1,
    "exec error: Part.pin_cluster() got an unexpected keyword argument 'width'": 1,
    "exec error: unsupported sketch_on_face profile [[-36.02, -20.06], [36.02, -20.06], [36.02, 19.84], [-36.02, 19.84]]": 1,
    "exec error: unsupported sketch_on_face profile [[-11.23, -11.9], [11.23, -11.9], [11.23, 11.9], [-11.23, 11.9]]": 1,
    "exec error: unsupported sketch_on_face profile [[-9.71, -15.74], [9.71, -15.74], [9.71, 15.74], [-9.71, 15.74]]": 1,
    "exec error: unsupported sketch_on_face profile [[-35.43, -27.94], [35.43, -27.94], [35.43, 27.94], [-35.43, 27.94]]": 1,
    "exec error: unsupported sketch_on_face profile [[-9.75, -17.98], [9.75, -17.98], [9.75, 17.98], [-9.75, 17.98]]": 1,
    "exec error: unsupported sketch_on_face profile [[-36.06, -19.13], [36.06, -19.13], [36.06, 19.13], [-36.06, 19.13]]": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 17)": 1,
    "exec error: unsupported sketch_on_face profile [[-21.02, -27.12], [21.02, -27.12], [21.02, 27.12], [-21.02, 27.12]]": 1,
    "exec error: unsupported sketch_on_face profile [[-40.74, -19.02], [40.74, -19.02], [40.74, 19.02], [-40.74, 19.02]]": 1,
    "exec error: unsupported sketch_on_face profile [[-11.94, -17.74], [11.94, -17.74], [11.94, 17.74], [-11.94, 17.74]]": 1,
    "exec error: 'thickness'": 1,
    "exec error: unsupported sketch_on_face profile [[-25.22, -21.08], [25.22, -21.08], [25.22, 21.08], [-25.22, 21.08]]": 1,
    "exec error: unsupported sketch_on_face profile [[-14.59, -19.37], [14.59, -19.37], [14.59, 19.37], [-14.59, 19.37]]": 1,
    "exec error: 'FeatureHandle' object has no attribute 'top_left_corner'": 1,
    "exec error: unsupported sketch_on_face profile [[-15.69, -23.12], [15.69, -23.12], [15.69, 23.12], [-15.69, 23.12]]": 1,
    "exec error: unsupported sketch_on_face profile [[-40.92, -18.52], [40.92, -18.52], [40.92, 18.52], [-40.92, 18.52]]": 1,
    "exec error: unsupported sketch_on_face profile [[-13.33, -17.25], [13.33, -17.25], [13.33, 17.25], [-13.33, 17.25]]": 1,
    "exec error: unsupported sketch_on_face profile [[-39.82, -22.02], [39.82, -22.02], [39.82, 22.02], [-39.82, 22.02]]": 1,
    "SyntaxError: invalid syntax. Perhaps you forgot a comma? (<unknown>, line 2)": 1,
    "exec error: unsupported sketch_on_face profile [[-31.06, -22.02], [31.06, -22.02], [31.06, 22.02], [-31.06, 22.02]]": 1,
    "exec error: unsupported sketch_on_face profile [[-34.97, -23.04], [34.97, -23.04], [34.97, 23.04], [-34.97, 23.04]]": 1,
    "exec error: unsupported sketch_on_face profile [[-24.93, -19.08], [24.93, -19.08], [24.93, 19.08], [-24.93, 19.08]]": 1,
    "exec error: unsupported sketch_on_face profile [[-12.55, -13.3], [12.55, -13.3], [12.55, 13.3], [-12.55, 13.3]]": 1,
    "exec error: unsupported sketch_on_face profile [[-30.02, -17.94], [30.02, -17.94], [30.02, 17.94], [-30.02, 17.94]]": 1,
    "exec error: unsupported sketch_on_face profile [[-11.73, -11.12], [11.73, -11.12], [11.73, 11.12], [-11.73, 11.12]]": 1,
    "exec error: mirror: plane must be 'YZ', 'XZ', or 'XY'": 1,
    "exec error: unsupported sketch_on_face profile [[-7.41, -9.92], [7.41, -9.92], [7.41, 9.92], [-7.41, 9.92]]": 1,
    "exec error: unsupported sketch_on_face profile [[-11.93, -10.07], [11.93, -10.07]]": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 44)": 1,
    "exec error: 'Part' object has no attribute 'sketch_offset'": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 15)": 1,
    "exec error: unsupported sketch_on_face profile [[-13.1, -23.02], [13.1, -23.02], [13.1, 23.02], [-13.1, 23.02]]": 1,
    "exec error: 'FeatureHandle' object has no attribute 'top_outer_edge'": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 39)": 1,
    "exec error: 'Part' object has no attribute 'boolean_insert'": 1,
    "exec error: unsupported sketch_on_face profile [[-11.94, -17.13], [11.94, -17.13], [11.94, 17.13], [-11.94, 17.13]]": 1,
    "exec error: unsupported sketch_on_face profile [[-11.544, -10.18], [11.544, -10.18], [11.544, 10.18], [-11.544, 10.18]]": 1,
    "exec error: unsupported sketch_on_face profile [[-11.06, -15.61], [11.06, -15.61], [11.06, 15.61], [-11.06, 15.61]]": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 36)": 1,
    "exec error: unsupported sketch_on_face profile [[-9.63, -11.04], [9.63, -11.04], [9.63, 11.04], [-9.63, 11.04]]": 1,
    "exec error: Part.sketch_on_face() got an unexpected keyword argument 'options'": 1,
    "exec error: Part.plate() got an unexpected keyword argument 'overall_width'": 1,
    "exec error: unsupported sketch_on_face profile [[-9.67, -21.12], [9.67, -21.12], [9.67, 21.12], [-9.67, 21.12]]": 1,
    "exec error: unsupported sketch_on_face profile [[-36.95, -18.01], [36.95, -18.01], [36.95, 18.01], [-36.95, 18.01]]": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 66)": 1,
    "exec error: unsupported sketch_on_face profile [[-11.008, -13.02], [11.008, -13.02], [11.008, 13.02], [-11.008, 13.02]]": 1,
    "exec error: unsupported sketch_on_face profile [[-23.01, -18.56], [23.01, -18.56], [23.01, 18.56], [-23.01, 18.56]]": 1,
    "exec error: 'Part' object has no attribute 'tube'": 1,
    "SyntaxError: unterminated string literal (detected at line 16) (<unknown>, line 16)": 1,
    "exec error: name 'aus_params' is not defined": 1,
    "exec error: 'FeatureHandle' object has no attribute 'top_left_face'": 1,
    "exec error: 'Part' object has no attribute 'line_pattern'": 1,
    "exec error: unsupported sketch_on_face profile [[-28.23, -21.1], [28.23, -21.1], [28.23, 21.1], [-28.23, 21.1]]": 1,
    "exec error: unsupported sketch_on_face profile [[-11.31, -13.98], [11.31, -13.98], [11.31, 13.98], [-11.31, 13.98]]": 1,
    "exec error: unsupported sketch_on_face profile [[-40.07, -21.96], [40.07, -21.96], [40.07, 21.96], [-40.07, 21.96]]": 1,
    "exec error: unsupported sketch_on_face profile [[-11.85, -18.08], [11.85, -18.08], [11.85, 18.08], [-11.85, 18.08]]": 1,
    "SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 17)": 1,
    "exec error: unsupported sketch_on_face profile [[-27.91, -28.1], [27.91, -28.1], [27.91, 28.1], [-27.91, 28.1]]": 1
  },
  "extreme_cd_cases_gt_1000": [],
  "export_but_unscoreable_ids": [
    "flluma_0091229",
    "flluma_0091990",
    "flluma_0093646",
    "flluma_0094261",
    "flluma_0091733",
    "flluma_0097501",
    "flluma_0090333",
    "flluma_0095556",
    "flluma_0095328",
    "flluma_0098137",
    "flluma_0094194",
    "flluma_0094106",
    "flluma_0091641",
    "flluma_0090465",
    "flluma_0091307",
    "flluma_0093430",
    "flluma_0092657"
  ]
}
```

### B2

```json
{
  "rows": 2500,
  "scoreable": 1340,
  "scoreable_pct": 53.6,
  "gate_counts_from_geometry_run": {
    "syntax_ok": 2288,
    "exec_ok": 1463,
    "build_ok": 1463,
    "solid_valid": 1463,
    "step_export_ok": 1433
  },
  "missing_target_rows": 0,
  "conditional": {
    "cd": {
      "n": 1340,
      "mean": 13.68590955550415,
      "median": 3.491073769373434,
      "sd_sample": 60.420239490867395,
      "min": 0.02838557823666111,
      "max": 1251.8406333454122,
      "q25": 1.845658828955066,
      "q75": 8.196986110939154,
      "q95": 43.38399640944167,
      "q99": 100.54877938527609
    },
    "f_score_1pct": {
      "n": 1340,
      "mean": 0.17313497759020519,
      "median": 0.1794188108196785,
      "sd_sample": 0.07585704160415546,
      "min": 0.0,
      "max": 0.4032990314769976,
      "q25": 0.11859005272633745,
      "q75": 0.22116877069536423,
      "q95": 0.3008708341774716,
      "q99": 0.3556598848869537
    },
    "bbox_err": {
      "n": 1340,
      "mean": 1.2955325914814495,
      "median": 0.06679342982187893,
      "sd_sample": 3.8293402094234317,
      "min": 0.0,
      "max": 36.97079868303263,
      "q25": 5.202197256674405e-07,
      "q75": 0.8531570921291903,
      "q95": 5.435681392117683,
      "q99": 19.40256616017093
    },
    "bbox_ratio_to_gt": {
      "n": 1340,
      "mean": 0.9882281628309953,
      "median": 0.9999999999984901,
      "sd_sample": 0.09630800501113146,
      "min": 0.05136727444887218,
      "max": 1.2166324623736362,
      "q25": 0.9985341299344223,
      "q75": 1.0009990308879797,
      "q95": 1.0498206606894194,
      "q99": 1.1174616061650242
    }
  },
  "unconditional_f_score_1pct": {
    "n": 2500,
    "mean": 0.09280034798834998,
    "median": 0.05517146017699115,
    "sd_sample": 0.10267081490188419,
    "min": 0.0,
    "max": 0.4032990314769976,
    "q25": 0.0,
    "q75": 0.18358985413896278,
    "q95": 0.2714536378709532,
    "q99": 0.3386401296829971
  },
  "non_scoreable_error_counts": {
    "exec error: target must be a TopologyReference from a FeatureHandle": 109,
    "point cloud sampling failed on generated part": 93,
    "exec error: unsupported operand type(s) for *: 'ParameterRef' and 'float'": 90,
    "SyntaxError: invalid syntax (<unknown>, line 1)": 74,
    "exec error: 'list' object has no attribute 'strip'": 59,
    "exec error: target must be a FeatureHandle": 56,
    "STEP export error: OCCT build failed": 30,
    "exec error: Part.loft() got an unexpected keyword argument 'segments'": 26,
    "exec error: bad operand type for unary -: 'ParameterRef'": 25,
    "exec error: 'Part' object has no attribute 'sweep_pipe_bracket'": 24,
    "exec error: 'Part' object has no attribute 'threaded_bearing_block'": 22,
    "no `part` variable after execution": 21,
    "exec error: 'width'": 20,
    "exec error: 'flange_radius'": 17,
    "exec error: 'Part' object has no attribute 'bearing_block'": 16,
    "exec error: Part.extrude() got an unexpected keyword argument 'target'": 15,
    "SyntaxError: unmatched ']' (<unknown>, line 1)": 15,
    "SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 15)": 13,
    "exec error: Part.box() got an unexpected keyword argument 'target'": 11,
    "exec error: Part.shell() got an unexpected keyword argument 'wall_thickness'": 11,
    "exec error: Part.loft() got an unexpected keyword argument 'profile'": 10,
    "exec error: Parameters.add() got an unexpected keyword argument 'category'": 10,
    "exec error: offset must be a 3D sequence": 9,
    "exec error: Part.cylinder() got an unexpected keyword argument 'target'": 9,
    "exec error: Part.extrude() got an unexpected keyword argument 'operation'": 8,
    "exec error: unsupported operand type(s) for /: 'ParameterRef' and 'float'": 8,
    "exec error: topology reference 'join_001:top_face:b9ce48e7f7b9' did not resolve any face": 8,
    "exec error: 'Part' object has no attribute 'sweep_profile'": 7,
    "exec error: extrude_on_face join/add requires height": 7,
    "exec error: object of type 'ParameterRef' has no len()": 6,
    "SyntaxError: closing parenthesis ']' does not match opening parenthesis '(' (<unknown>, line 8)": 5,
    "exec error: direction must be 'inward' or 'outward'": 5,
    "exec error: 'Part' object has no attribute 'boolean_hole'": 5,
    "exec error: topology reference 'extrude_001:top_face:b9ec9b032ae6' did not resolve any face": 5,
    "exec error: hole depth must be a number or 'through'": 5,
    "SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 11)": 5,
    "exec error: 'Part' object has no attribute 'cuboid'": 5,
    "exec error: topology reference 'hole_001:top_face:9014e73e3f7b' did not resolve any face": 5,
    "SyntaxError: leading zeros in decimal integer literals are not permitted; use an 0o prefix for octal integers (<unknown>, line 1)": 4,
    "exec error: Part.fillet() got an unexpected keyword argument 'segments'": 4,
    "exec error: Part.extrude_on_face() got an unexpected keyword argument 'offset'": 4,
    "exec error: Part.boolean_cut() got an unexpected keyword argument 'depth'": 4,
    "exec error: Part.shell() got an unexpected keyword argument 'wall_width'": 4,
    "exec error: 'wall_thickness'": 4,
    "exec error: Part.shell() got an unexpected keyword argument 'walls_to_remove'": 4,
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'length'": 4,
    "SyntaxError: unterminated string literal (detected at line 28) (<unknown>, line 28)": 3,
    "SyntaxError: invalid syntax (<unknown>, line 2)": 3,
    "SyntaxError: unterminated string literal (detected at line 24) (<unknown>, line 24)": 3,
    "SyntaxError: '(' was never closed (<unknown>, line 31)": 3,
    "SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 17)": 3,
    "exec error: Part.hole_pattern() got an unexpected keyword argument 'distance'": 3,
    "exec error: 'Part' object has no attribute 'cut'": 3,
    "exec error: Part.wedge() got an unexpected keyword argument 'width'": 3,
    "exec error: 'Part' object has no attribute 'boolean_cut_on_face'": 3,
    "exec error: 'Part' object has no attribute 'mount_block'": 3,
    "exec error: Part.rotate() got an unexpected keyword argument 'angle'": 3,
    "SyntaxError: '[' was never closed (<unknown>, line 33)": 3,
    "SyntaxError: '(' was never closed (<unknown>, line 35)": 3,
    "exec error: Part.sweep() got an unexpected keyword argument 'radius'": 3,
    "SyntaxError: '(' was never closed (<unknown>, line 36)": 3,
    "exec error: 'Part' object has no attribute 'extrude_on_sketch'": 3,
    "SyntaxError: unterminated string literal (detected at line 31) (<unknown>, line 31)": 3,
    "SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 14)": 3,
    "exec error: 'Part' object has no attribute 'rectangular_cut'": 3,
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'path_width'": 3,
    "SyntaxError: unterminated string literal (detected at line 20) (<unknown>, line 20)": 3,
    "SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 18)": 3,
    "SyntaxError: unterminated string literal (detected at line 25) (<unknown>, line 25)": 3,
    "exec error: Part.hole_pattern() got an unexpected keyword argument 'height'": 3,
    "exec error: 'Part' object has no attribute 'profile_cut'": 3,
    "SyntaxError: unterminated string literal (detected at line 21) (<unknown>, line 21)": 3,
    "SyntaxError: '[' was never closed (<unknown>, line 30)": 2,
    "exec error: Part.profile_cut_on_face() got an unexpected keyword argument 'width'": 2,
    "SyntaxError: '[' was never closed (<unknown>, line 14)": 2,
    "exec error: Part.loft() got an unexpected keyword argument 'target'": 2,
    "SyntaxError: unterminated string literal (detected at line 32) (<unknown>, line 32)": 2,
    "exec error: 'Part' object has no attribute 'boolean_fillet'": 2,
    "exec error: Part.extrude() got an unexpected keyword argument 'thickness'": 2,
    "exec error: Part.shell() got an unexpected keyword argument 'shell_faces_to_remove'": 2,
    "exec error: Part.shell() got an unexpected keyword argument 'walls'": 2,
    "exec error: 'Part' object has no attribute 'service_coating'": 2,
    "exec error: Part.hole_pattern() missing 1 required keyword-only argument: 'positions'": 2,
    "exec error: 'Part' object has no attribute 'threaded_bearing_block_on_face'": 2,
    "exec error: 'hole_radius'": 2,
    "exec error: 'Part' object has no attribute 'path'": 2,
    "exec error: Part.hole_pattern() got an unexpected keyword argument 'distance_step'": 2,
    "SyntaxError: '(' was never closed (<unknown>, line 30)": 2,
    "exec error: Part.boolean_cut() got an unexpected keyword argument 'sketch'": 2,
    "exec error: Part.loft() got an unexpected keyword argument 'targets'": 2,
    "exec error: Part.boolean_join() got an unexpected keyword argument 'operation'": 2,
    "exec error: Part.boolean_join() got an unexpected keyword argument 'depth'": 2,
    "exec error: 'Part' object has no attribute 'mount_bearing'": 2,
    "SyntaxError: unterminated string literal (detected at line 22) (<unknown>, line 22)": 2,
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'path_segments'": 2,
    "exec error: loft requires at least two profile features": 2,
    "exec error: extrude_on_face cut requires depth": 2,
    "exec error: Part.extrude_on_face() got an unexpected keyword argument 'profile'": 2,
    "exec error: Part.shell() got an unexpected keyword argument 'wall_height'": 2,
    "SyntaxError: unterminated string literal (detected at line 18) (<unknown>, line 18)": 2,
    "SyntaxError: unterminated string literal (detected at line 40) (<unknown>, line 40)": 2,
    "SyntaxError: '(' was never closed (<unknown>, line 28)": 2,
    "exec error: 'center_hole_radius_2'": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 39)": 1,
    "exec error: Part.mirrored_lug_plate() got an unexpected keyword argument 'lug_offset_y'": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 25)": 1,
    "SyntaxError: unterminated string literal (detected at line 37) (<unknown>, line 37)": 1,
    "SyntaxError: unterminated string literal (detected at line 45) (<unknown>, line 45)": 1,
    "SyntaxError: unterminated string literal (detected at line 51) (<unknown>, line 51)": 1,
    "SyntaxError: closing parenthesis ']' does not match opening parenthesis '(' (<unknown>, line 14)": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 34)": 1,
    "SyntaxError: invalid syntax. Perhaps you forgot a comma? (<unknown>, line 15)": 1,
    "exec error: Part.linear_pattern() got an unexpected keyword argument 'start'": 1,
    "SyntaxError: unterminated string literal (detected at line 16) (<unknown>, line 16)": 1,
    "SyntaxError: unmatched ']' (<unknown>, line 33)": 1,
    "exec error: Part.profile_cut_on_face() missing 1 required keyword-only argument: 'profile'": 1,
    "SyntaxError: unterminated string literal (detected at line 39) (<unknown>, line 39)": 1,
    "exec error: 'FeatureHandle' object has no attribute 'pocket'": 1,
    "exec error: 'Part' object has no attribute 'mount'": 1,
    "exec error: 'Part' object has no attribute 'radius'": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 13)": 1,
    "exec error: topology reference 'hole_004:top_face:6bf7b79bd715' did not resolve any face": 1,
    "SyntaxError: invalid syntax. Maybe you meant '==' or ':=' instead of '='? (<unknown>, line 1)": 1,
    "exec error: name 'process_units' is not defined": 1,
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'min_tube_radius'": 1,
    "exec error: Parameters.add() takes 3 positional arguments but 6 positional arguments (and 4 keyword-only arguments) were given": 1,
    "exec error: 'Part' object has no attribute 'sketch_arc'": 1,
    "SyntaxError: unterminated string literal (detected at line 34) (<unknown>, line 34)": 1,
    "SyntaxError: invalid decimal literal (<unknown>, line 12)": 1,
    "SyntaxError: unterminated string literal (detected at line 38) (<unknown>, line 38)": 1,
    "exec error: Part.pin_cluster() got an unexpected keyword argument 'row_width'": 1,
    "exec error: 'Part' object has no attribute 'profile_project_on_face'": 1,
    "exec error: 'Part' object has no attribute 'face'": 1,
    "exec error: Part.plate() got an unexpected keyword argument 'target'": 1,
    "SyntaxError: invalid syntax. Perhaps you forgot a comma? (<unknown>, line 26)": 1,
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'offset_distance'": 1,
    "exec error: Part.rectangular_pocket() got an unexpected keyword argument 'height'": 1,
    "SyntaxError: unmatched ')' (<unknown>, line 30)": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 37)": 1,
    "exec error: 'Part' object has no attribute 'rectangular_pocket_on_face'": 1,
    "exec error: Part.plate() got an unexpected keyword argument 'wall_height'": 1,
    "exec error: 'FeatureHandle' object has no attribute 'body'": 1,
    "exec error: 'Part' object has no attribute 'fold'": 1,
    "exec error: Part.chamfer() got an unexpected keyword argument 'radius'": 1,
    "exec error: Part.sweep() got an unexpected keyword argument 'target'": 1,
    "SyntaxError: invalid syntax (<unknown>, line 3)": 1,
    "SyntaxError: unterminated string literal (detected at line 13) (<unknown>, line 13)": 1,
    "SyntaxError: unterminated string literal (detected at line 33) (<unknown>, line 33)": 1,
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'path_radius'": 1,
    "exec error: Part.rectangular_pocket() got an unexpected keyword argument 'profile'": 1,
    "exec error: 'center_hole_radius_3'": 1,
    "exec error: 'bolt_radius'": 1,
    "exec error: Part.shell() got an unexpected keyword argument 'segments'": 1,
    "SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 20)": 1,
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'height'": 1,
    "exec error: 'boss_radius'": 1,
    "exec error: Part.standoff_array_plate() got an unexpected keyword argument 'vertices'": 1,
    "exec error: Part.box() got an unexpected keyword argument 'size'": 1,
    "exec error: 'Part' object has no attribute 'join'": 1,
    "exec error: unsupported operand type(s) for +: 'ParameterRef' and 'float'": 1,
    "exec error: 'Part' object has no attribute 'lobed_gasket_plate'": 1,
    "exec error: 'slot_depth'": 1,
    "exec error: Part.box() got an unexpected keyword argument 'thickness'": 1,
    "exec error: 'Part' object has no attribute 'rectangular_slot'": 1,
    "exec error: 'Part' object has no attribute 'pocket'": 1,
    "exec error: topology reference 'fillet_001:top_face:0796be5e0297' did not resolve any face": 1,
    "exec error: 'Part' object has no attribute 'rectangular_slot_pattern'": 1,
    "exec error: Part.standoff_array_plate() got an unexpected keyword argument 'distance_between_standoffs'": 1,
    "exec error: Part.rectangular_pocket() missing 1 required keyword-only argument: 'depth'": 1,
    "exec error: 'Part' object has no attribute 'sketch_face'": 1,
    "exec error: 'FeatureHandle' object has no attribute 'wires'": 1,
    "exec error: 'Part' object has no attribute 'place_on'": 1,
    "exec error: 'FeatureHandle' object has no attribute 'outer_profile'": 1,
    "exec error: Part.hole_pattern() got an unexpected keyword argument 'position'": 1,
    "exec error: topology reference 'chamfer_001:top_face:f40479b908d2' did not resolve any face": 1,
    "SyntaxError: unmatched ')' (<unknown>, line 24)": 1,
    "exec error: Part.hole_pattern() got an unexpected keyword argument 'pattern'": 1,
    "exec error: name 'holes_' is not defined": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 43)": 1,
    "exec error: 'center_hole_width'": 1,
    "exec error: Part.sweep() got an unexpected keyword argument 'path_segments'": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 32)": 1,
    "SyntaxError: closing parenthesis ')' does not match opening parenthesis '[' (<unknown>, line 19)": 1,
    "exec error: Part.hole_pattern() got an unexpected keyword argument 'distance_min'": 1,
    "exec error: Part.sweep() got an unexpected keyword argument 'width'": 1,
    "exec error: 'Part' object has no attribute 'face_extrude_cut'": 1,
    "exec error: Part.sweep_tube() got an unexpected keyword argument 'path_segment'": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 44)": 1,
    "exec error: 'Part' object has no attribute 'sweep_polygon'": 1,
    "exec error: 'Part' object has no attribute 'bubble_pattern'": 1,
    "exec error: Part.mirrored_lug_plate() missing 4 required keyword-only arguments: 'lug_length', 'lug_width', 'lug_height', and 'lug_offset_x'": 1,
    "exec error: 'Part' object has no attribute 'solid_face'": 1,
    "SyntaxError: unterminated string literal (detected at line 19) (<unknown>, line 19)": 1,
    "SyntaxError: '[' was never closed (<unknown>, line 31)": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 15)": 1,
    "exec error: 'Part' object has no attribute 'lug_pattern'": 1,
    "SyntaxError: closing parenthesis ']' does not match opening parenthesis '(' (<unknown>, line 9)": 1,
    "exec error: Part.sketch_rectangle() got an unexpected keyword argument 'points'": 1,
    "exec error: name 'join_170' is not defined": 1,
    "exec error: Part.circular_pattern() got an unexpected keyword argument 'offset'": 1,
    "SyntaxError: unterminated string literal (detected at line 23) (<unknown>, line 23)": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 45)": 1,
    "exec error: Part.sketch_circle() got an unexpected keyword argument 'height'": 1,
    "exec error: 'Part' object has no attribute 'boolean_fill'": 1,
    "exec error: 'Part' object has no attribute 'lobed_plate'": 1,
    "SyntaxError: unmatched ')' (<unknown>, line 12)": 1,
    "exec error: unsupported operand type(s) for -: 'ParameterRef' and 'float'": 1,
    "exec error: Part.shell() got an unexpected keyword argument 'height'": 1,
    "exec error: 'Part' object has no attribute 'bolt_pattern'": 1,
    "exec error: 'Part' object has no attribute 'outer_boundary'": 1,
    "exec error: Part.hole_pattern() got an unexpected keyword argument 'center'": 1,
    "exec error: name 'params' is not defined": 1,
    "exec error: Part.boolean_cut() got an unexpected keyword argument 'profile'": 1,
    "SyntaxError: unmatched ')' (<unknown>, line 9)": 1,
    "SyntaxError: unterminated string literal (detected at line 15) (<unknown>, line 15)": 1,
    "exec error: 'Part' object has no attribute 'stack'": 1,
    "exec error: unsupported operand type(s) for +: 'ParameterRef' and 'ParameterRef'": 1,
    "exec error: Part.wedge() missing 1 required keyword-only argument: 'ltx'": 1,
    "exec error: keyword argument repeated: semantic_type (<candidate>, line 28)": 1,
    "exec error: 'Part' object has no attribute 'face_feature_coating'": 1,
    "SyntaxError: '(' was never closed (<unknown>, line 40)": 1,
    "exec error: Part.boolean_intersect() got an unexpected keyword argument 'operation'": 1,
    "exec error: 'Part' object has no attribute 'cut_on_face'": 1
  },
  "extreme_cd_cases_gt_1000": [
    {
      "sample_id": "flluma_0093240",
      "syntax_ok": true,
      "exec_ok": true,
      "build_ok": true,
      "solid_valid": true,
      "step_export_ok": true,
      "error": "",
      "cd": 1251.8406333454122,
      "bbox_err": 31.5799999234611,
      "f_score_1pct": 0.0,
      "target_bbox_diag": 80.57506741559332,
      "gen_bbox_diag": 15.068841696759579,
      "bbox_ratio_to_gt": 0.18701618478377313,
      "has_target": true
    }
  ],
  "export_but_unscoreable_ids": [
    "flluma_0097058",
    "flluma_0095179",
    "flluma_0096039",
    "flluma_0096043",
    "flluma_0099438",
    "flluma_0091127",
    "flluma_0099937",
    "flluma_0090691",
    "flluma_0092343",
    "flluma_0091407",
    "flluma_0092183",
    "flluma_0090129",
    "flluma_0090626",
    "flluma_0098661",
    "flluma_0092210",
    "flluma_0095971",
    "flluma_0093503",
    "flluma_0090832",
    "flluma_0094472",
    "flluma_0094917",
    "flluma_0095827",
    "flluma_0097019",
    "flluma_0097322",
    "flluma_0095257",
    "flluma_0095370",
    "flluma_0092458",
    "flluma_0094051",
    "flluma_0091091",
    "flluma_0091278",
    "flluma_0094058",
    "flluma_0093363",
    "flluma_0096014",
    "flluma_0091232",
    "flluma_0096351",
    "flluma_0094000",
    "flluma_0098199",
    "flluma_0091246",
    "flluma_0093207",
    "flluma_0092623",
    "flluma_0097450",
    "flluma_0090552",
    "flluma_0096648",
    "flluma_0091089",
    "flluma_0092193",
    "flluma_0092230",
    "flluma_0098955",
    "flluma_0091402",
    "flluma_0094494",
    "flluma_0095276",
    "flluma_0091417",
    "flluma_0099307",
    "flluma_0093280",
    "flluma_0095274",
    "flluma_0091862",
    "flluma_0091699",
    "flluma_0099299",
    "flluma_0099042",
    "flluma_0093708",
    "flluma_0094267",
    "flluma_0096382",
    "flluma_0098093",
    "flluma_0097648",
    "flluma_0097812",
    "flluma_0097949",
    "flluma_0094785",
    "flluma_0095208",
    "flluma_0097063",
    "flluma_0094390",
    "flluma_0099209",
    "flluma_0093746",
    "flluma_0094108",
    "flluma_0095288",
    "flluma_0094698",
    "flluma_0094587",
    "flluma_0094665",
    "flluma_0092044",
    "flluma_0099376",
    "flluma_0095988",
    "flluma_0099730",
    "flluma_0094372",
    "flluma_0090226",
    "flluma_0090565",
    "flluma_0097934",
    "flluma_0099375",
    "flluma_0098195",
    "flluma_0096445",
    "flluma_0098905",
    "flluma_0095549",
    "flluma_0097952",
    "flluma_0094950",
    "flluma_0093285",
    "flluma_0094579",
    "flluma_0098151"
  ]
}
```

## Provenance

Generation actuals: `__RUN_SOURCE_ROOT__\outputs\b0_b2_fullstack_s4\cag_b0_b2_seed_4_actuals.json`.
Generation actuals SHA256: `658924a2af68a79f09ee7ba19241a817f67c254c64ea376a74e61e279c88b1e9`.
All 2500 paired-case rows: `__EVIDENCE_SOURCE_ROOT__\03\result\cag_b0_b2_seed_4_paired_cases.jsonl`.

B0 files and SHA256:

```json
{
  "__DEV_ROOT__\\scratch\\exec_b0b2_step_B0_s4\\execution_rows.jsonl": "cb603cef7dee6e2d25cfcee6e1f4ec519729f59fbadfd32d71070d9a2d09c757",
  "__DEV_ROOT__\\scratch\\geom_b0b2_step_B0_s4\\geometry_nbest_rows.jsonl": "ec179ec51abf6dc26f226b9b5579445b0e318077dbb6fbe3bba5560257ba6eac",
  "__DEV_ROOT__\\scratch\\exec_b0b2_step_B0_s4\\execution_summary.json": "8ea1ce3cbc307321875665b4995dcbe8dfef9e2b25435b30978fab60268a5eed",
  "__RUN_SOURCE_ROOT__\\outputs\\b0_b2_fullstack_s4\\predictions\\gen_step_B0_s4.jsonl": "f22c42cf81754a1eb0dce87a853f6bb038d74bd595131c6b1f43d0618fab9782",
  "__RUN_SOURCE_ROOT__\\outputs\\b0_b2_fullstack_s4\\predictions\\geom_input_step_B0_s4.jsonl": "a037788dd7e75fdc80d6c455dc5e5cc6652e92fd9a5e710d95468ed4491616cb"
}
```

B2 files and SHA256:

```json
{
  "__DEV_ROOT__\\scratch\\exec_b0b2_step_B2_s4\\execution_rows.jsonl": "faf8464b625f4985d719eeb4d2f1ef0cb31ddcc3ffc1a3326e97a614ab2da8cb",
  "__DEV_ROOT__\\scratch\\geom_b0b2_step_B2_s4\\geometry_nbest_rows.jsonl": "f0935b37940a083e0c91361288dc5ba534c88f9a688a28c88fd1274b64123b4e",
  "__DEV_ROOT__\\scratch\\exec_b0b2_step_B2_s4\\execution_summary.json": "e774399355f3450278425f221583b66516d17caf470458da37084e07c68ecc0b",
  "__RUN_SOURCE_ROOT__\\outputs\\b0_b2_fullstack_s4\\predictions\\gen_step_B2_s4.jsonl": "24a0cd2c31b5a519f6fa229741b559c2d5d0be614e5e96f8a8c0a6143a24f325",
  "__RUN_SOURCE_ROOT__\\outputs\\b0_b2_fullstack_s4\\predictions\\geom_input_step_B2_s4.jsonl": "12877e966e87ffcba18e9601f8caf078e13d0e83997a4867bc18241cc8aa5a8e"
}
```

Evaluator-source hashes describe files present at analysis time; they are not a historical build attestation. See the frozen generation actuals and earlier run records for training-code provenance.

