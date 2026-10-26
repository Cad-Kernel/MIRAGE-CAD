> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# 18 -- Four-Seed B0/B2 Replication Closed

Date: 2026-10-16

```yaml
Experiment: B0 vs B2 full-stack multi-seed replication
Seeds: [1, 2, 3, 4]
Training: COMPLETE
Prediction: COMPLETE
Gate evaluation: COMPLETE
Geometry scoring: COMPLETE
Per-seed JSON: COMPLETE
Four-seed JSON: COMPLETE
Full result package: COMPLETE
Audit: PASS
Experiment status: CLOSED
Additional seeds: NOT_PLANNED
```

## Result Package

- [Complete four-seed results](result/01_four_seed_full_results.md): every gate endpoint, geometry distributions, per-seed paired tests, all failure counts, and outlier records.
- [Aggregate JSON](result/cag_b0_b2_four_seed_eval_summary.json): equal-weight means, sample SD, deltas, and direction counts.
- [Seed 4 closure](17_seed4_closed_record.md): final seed results and scoreability/tail caveats.
- [Reproduction instructions](result/README.md): source checkout, analysis command, paths, and file inventory.

Each seed also has a full JSON and 2500-row paired-case JSONL. All eight raw gate row files and eight raw geometry row files retain their original paths in the summaries. Earlier seed records remain historical; the recomputed JSON/full result package is the reference for exact numbers and terminology.

## Per-Seed Coverage

| Seed | B0 Build | B2 Build | Delta pp | B0 export | B2 export | Delta pp | B0 scoreable | B2 scoreable |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 55.68% | 68.76% | +13.08 | 55.00% | 68.28% | +13.28 | 54.96% | 67.04% |
| 2 | 51.88% | 57.60% | +5.72 | 48.76% | 56.88% | +8.12 | 48.24% | 54.20% |
| 3 | 43.12% | 62.76% | +19.64 | 42.76% | 61.60% | +18.84 | 42.60% | 60.96% |
| 4 | 54.84% | 58.52% | +3.68 | 54.20% | 57.32% | +3.12 | 53.52% | 53.60% |

## Four-Seed Mean And Sample SD

SD uses the four independently retrained conditions, ddof=1. It is not an uncertainty estimate from 10000 independent model runs.

| Endpoint | B0 mean +/- SD | B2 mean +/- SD | Mean delta B2 - B0 |
| --- | ---: | ---: | ---: |
| Syntax | 96.54% +/- 0.99 pp | 94.90% +/- 2.30 pp | -1.64 pp |
| Execute / Build / Solid | 51.38% +/- 5.74 pp | 61.91% +/- 5.09 pp | +10.53 pp |
| STEP export | 50.18% +/- 5.67 pp | 61.02% +/- 5.29 pp | +10.84 pp |
| Scoreable | 49.83% +/- 5.62 pp | 58.95% +/- 6.34 pp | +9.12 pp |
| Full-set conditional median CD | 5.3627 +/- 1.8532 | 3.0792 +/- 0.4519 | -2.2834 |
| Full-set conditional median F@1 | 15.44% +/- 2.58 pp | 18.91% +/- 0.92 pp | +3.48 pp |
| Unconditional mean F@1 | 7.60% +/- 0.88 pp | 10.89% +/- 1.28 pp | +3.28 pp |
| Paired-subset median CD | 5.2194 +/- 2.1064 | 2.8616 +/- 0.4521 | -2.3578 |
| Paired-subset median F@1 | 16.73% +/- 1.43 pp | 20.56% +/- 1.67 pp | +3.83 pp |

The median rows above are means/SDs of per-seed medians, not a single pooled median. Full-set conditional and paired subsets differ.

The unfavorable mean-CD result must also be reported: mean of the four per-seed conditional mean CD values is 12.2331013874 for B0 versus 202661099.9518 for B2. B2's full-set conditional mean CD is worse in all four seeds, and its paired mean CD is worse in three of four. Severe finite outliers in seeds 1-3 dominate the aggregate. Seed 4 also has a worse mean CD without a 1e11-scale outlier. All original CD values are retained.

## Paired Direction Consistency

| Seed | Jointly scoreable | CD B2/B0 wins | F@1 B2/B0 wins | F@1 ties | Paired median CD B0/B2 | Paired median F@1 B0/B2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 1083 | 686 / 397 | 671 / 411 | 1 | 3.5411 / 2.5669 | 17.04% / 21.48% |
| 2 | 747 | 458 / 289 | 484 / 263 | 0 | 3.8255 / 2.5043 | 18.50% / 22.07% |
| 3 | 801 | 535 / 266 | 544 / 257 | 0 | 8.1397 / 2.8826 | 16.29% / 20.40% |
| 4 | 830 | 515 / 315 | 509 / 321 | 0 | 5.3716 / 3.4926 | 15.08% / 18.27% |

B2 has higher Build, export, and unconditional mean F@1 in every seed. Paired median CD is lower and paired median F@1 is higher in every seed. There are 3461 jointly scoreable seed-query cases in total; this is a descriptive count, not a count of independent training replications.

All-four direction consistency has a two-sided seed-level exact sign-test p of 0.125. Small within-seed query-level p-values should not be presented as proof of model-level statistical significance across four seeds.

## Limits And Protocol Details

1. This is a full deployed-condition replication. It does not isolate plan text at equal total computation. B2 has alignment, four priors, Stage 3/3b plan training, and Stage 4/4b code training; B0 has direct no-plan code training.
2. Source train/val/test files, base code model, seed labels, final selection rule, STEP evaluation IDs, greedy decoding, and evaluator recipe are controlled. Total trainable stages and total compute differ by condition. B0 trains at max_length 2048; B2 code training uses 1536.
3. Grammar filtering produces Stage 4b row counts of 2987, 3103, 2997, and 3130. The resulting continuation budgets vary by seed. Do not call this an identical-total-updates or identical-total-row-count comparison.
4. Program repair is disabled. B2 retains the frozen P1a plan-stage canonicalization. State both facts explicitly.
5. B2 syntax is lower in all four seeds. Mean CD and bbox outcomes are not uniformly favorable; do not claim uniformly better geometry or no fidelity penalty on every statistic.
6. Seed 4 scoreability is nearly tied because 93 B2 exports and 17 B0 exports fail generated point sampling. Unconditional F@1 keeps these outputs at zero.
7. Results concern the fixed in-corpus STEP slice. They do not establish external or broad compositional generalization, and they do not transfer automatically to all modalities.

## Reviewer-Facing Wording

> We repeated the B0/B2 STEP comparison over four independently retrained seeds, retraining all trainable components of each condition. The source splits, final-checkpoint rule, decoding settings, and 2500-query test slice were fixed. Across seeds, B2 achieved higher Build and STEP-export rates in every run, with mean Build of 61.91% versus 51.38% and mean STEP export of 61.02% versus 50.18%. Unconditional mean F@1 was also higher in every seed (four-seed means: 10.89% versus 7.60%). On jointly scoreable queries, median CD and median F@1 favored B2 in all four runs. These gains coexist with lower syntax rates and worse mean CD, including severe geometric outliers. We therefore report seed variability, conditional and unconditional metrics, and the failure tails explicitly. This is a comparison of the complete trained conditions rather than a claim of equal total training computation.

## Work Status

The Review/03 B0/B2 four-seed replication is CLOSED. No further commands or additional seeds are required for this experiment. The next planned training-dependent item remains the curriculum control; its detailed mapping/protocol should be checked before any new training is launched.
