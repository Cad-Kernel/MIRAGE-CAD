> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

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
