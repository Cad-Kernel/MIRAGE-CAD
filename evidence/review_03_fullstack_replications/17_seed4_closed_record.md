> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# 17 -- Seed 4 Closed Record

Date: 2026-10-16

```yaml
Seed: 4
Training: COMPLETE
Prediction: COMPLETE
Gate evaluation: COMPLETE
Geometry scoring: COMPLETE
Summary JSON: COMPLETE
Review record: COMPLETE
Audit: PASS
Seed status: CLOSED
```

## Verified Outputs

Both gate row files and both geometry row files contain all 2500 frozen sample IDs in the expected order. Gate counts recomputed from rows match each execution summary. Geometry inputs match the raw program predictions exactly. Prediction/input hashes match the generation actuals. All four seeds use the same train/val/test hashes and frozen training-script hashes.

Source checkout: `__DEV_ROOT__\src`.

Training checkout: `__RUN_SOURCE_ROOT__`.

Seed outputs: `__RUN_SOURCE_ROOT__/outputs/b0_b2_fullstack_s4`.

Evaluation directories:

```text
__DEV_ROOT__\scratch\exec_b0b2_step_B0_s4
__DEV_ROOT__\scratch\exec_b0b2_step_B2_s4
__DEV_ROOT__\scratch\geom_b0b2_step_B0_s4
__DEV_ROOT__\scratch\geom_b0b2_step_B2_s4
```

Complete results and file SHA256 values: [seed-4 JSON](result/cag_b0_b2_seed_4_eval_summary.json). All 2500 paired-case records: [paired cases](result/cag_b0_b2_seed_4_paired_cases.jsonl). Full distributions, error counts, and outlier IDs: [seed-4 full results](result/seed_4_full_results.md).

## Gate And Scoreability

| Metric | B0 | B2 | B2 - B0 |
| --- | ---: | ---: | ---: |
| Syntax | 2384/2500 (95.36%) | 2288/2500 (91.52%) | -3.84 pp |
| Execute | 1371/2500 (54.84%) | 1463/2500 (58.52%) | +3.68 pp |
| Build | 1371/2500 (54.84%) | 1463/2500 (58.52%) | +3.68 pp |
| Solid validity | 1371/2500 (54.84%) | 1463/2500 (58.52%) | +3.68 pp |
| STEP export | 1355/2500 (54.20%) | 1433/2500 (57.32%) | +3.12 pp |
| Geometry scoreable | 1338/2500 (53.52%) | 1340/2500 (53.60%) | +0.08 pp |

Kernel crashes: zero in both gate summaries. Execution-evaluation runtime: 140.158 seconds for B0, 508.724 seconds for B2. These runtimes describe the evaluator runs, not model inference latency.

Within-seed paired Build: both succeed 942, B2 only 521, B0 only 429, neither 608. Exact McNemar p = 0.0031324221.

Within-seed paired STEP export: both succeed 921, B2 only 512, B0 only 434, neither 633. Exact McNemar p = 0.012257255.

The syntax difference favors B0: both succeed 2200, B2 only 88, B0 only 184, neither 28; exact McNemar p = 5.8960009e-09.

## Geometry

Full-set conditional statistics use each arm's own scoreable set. Unconditional F@1 uses all 2500 queries and assigns zero to non-scoreable outputs.

| Metric | B0 | B2 |
| --- | ---: | ---: |
| Conditional mean CD | 12.2771949409 | 13.6859095555 |
| Conditional median CD | 6.5745052460 | 3.4910737694 |
| Conditional mean F@1 | 13.68949938% | 17.31349776% |
| Conditional median F@1 | 11.66341146% | 17.94188108% |
| Unconditional mean F@1 | 7.32662007% | 9.28003480% |
| Unconditional median F@1 | 1.60984848% | 5.51714602% |

Jointly scoreable subset: 830 queries.

| Paired Metric | B0 | B2 |
| --- | ---: | ---: |
| Mean CD | 9.8946674055 | 14.7752276961 |
| Median CD | 5.3715519331 | 3.4926268969 |
| Mean F@1 | 14.77199166% | 17.89777531% |
| Median F@1 | 15.08377695% | 18.27122326% |

CD wins: B2 515, B0 315, ties 0; exact sign p = 3.9077567e-12. Median within-query CD difference (B2 - B0) = -0.2926196300.

F@1 wins: B2 509, B0 321, ties 0; exact sign p = 7.1168620e-11. Median within-query F@1 difference = +1.60830593 pp. This differs from subtracting the two marginal paired medians (+3.18744631 pp).

Paired bbox wins: B2 452, B0 253, ties 125; exact sign p = 6.0649388e-14. The complete bbox statistics are retained in the JSON and full report.

## Failure And Tail Caveats

B2 has 93 outputs that pass STEP export but fail generated point-cloud sampling; B0 has 17. This explains why B2's export coverage advantage shrinks to a nearly tied scoreable count. The logs establish the failure stage, not the underlying geometric or sampler cause. Keep these cases as non-scoreable with unconditional F@1=0 under the fixed scoring rule.

B2's largest finite CD is 1251.8406333454122, on `flluma_0093240`, with F@1=0 and generated/target bbox diagonal ratio 0.1870161848. This case remains in every reported mean. Both full-set and paired mean CD are worse for B2 in seed 4 despite better medians and more CD wins. No clipping or post-hoc exclusion was applied.

Top B2 non-scoreable errors include invalid topology-reference arguments (109), generated point-cloud sampling failures (93), unsupported `ParameterRef * float` (90), and line-1 syntax errors (74). All error strings and counts are preserved, including singletons.

## Interpretation

Seed 4 completes the same coverage direction seen in seeds 1-3: B2 achieves higher Build and STEP export. The margin is the smallest of the four seeds. Median geometry, paired win counts, and unconditional F@1 favor B2, while syntax is lower, scoreable coverage is almost equal, and mean CD is worse.

This supports a replicated pathway comparison with meaningful trade-offs. It does not support the claim that B2 is better on all geometry statistics or eliminates geometric failures.

## Next Step

Seed 4 and the registered four-seed experiment are closed. See [four-seed closure](18_four_seed_closed_summary.md) and [complete results](result/01_four_seed_full_results.md). No seed 5 or further training is required for this package.
