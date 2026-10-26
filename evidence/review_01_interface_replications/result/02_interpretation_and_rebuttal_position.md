> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Interpretation And Rebuttal Position

Date: 2026-09-29

## Decision

```yaml
A1E/B2P frozen multi-seed replication: CLOSED
Additional seeds 5/6: NOT PLANNED
Primary reviewer target: Reviewer 1 / Reviewer 2 central comparison criticism
Recommended next revision focus:
  - qualitative success/failure gallery
  - Fusion 360 failure analysis
  - construction-disjoint diagnostic
  - STEP/global-descriptor wording
  - editability claim narrowing
  - Stage 3b curriculum discussion
```

The four-seed frozen exact-match comparison is now strong enough to serve as the main response to the central comparison objection. The important result is not that one seed is unusually favorable, but that all four independently trained frozen seeds have the same qualitative direction under the matched protocol.

## Why This Directly Addresses The Reviewer Critique

Reviewer 1 and Reviewer 2 objected that the original B1a/B2-Pred comparison mixed several factors:

- single training seed;
- 3000 vs 3125 update mismatch;
- different checkpoint-selection rules;
- test-sample resampling but no training-run variability estimate;
- continuous-adapter vs native textual-interface asymmetry.

The new comparison removes the controllable confounds:

- four random seeds;
- same 25,000 training rows per arm;
- 3125 updates for A1E and 3125 updates for B2P;
- final-checkpoint selection for both arms;
- identical decoding settings;
- same 500 STEP-query evaluation slice;
- repair disabled for both arms.

The remaining structural asymmetry is still real: A1E uses a continuous adapter, while B2P uses the language model's native textual interface. This should be acknowledged rather than hidden. The correct claim is therefore about the controlled STEP setting, not a universal superiority claim for textual planning.

## Main Result To Use

Coverage is the strongest result.

| Metric | Seed 1 | Seed 2 | Seed 3 | Seed 4 | Mean |
|---|---:|---:|---:|---:|---:|
| Build delta, B2P-A1E | +26.4 pp | +18.4 pp | +14.0 pp | +8.6 pp | +16.85 pp |
| STEP export delta, B2P-A1E | +26.6 pp | +18.2 pp | +14.0 pp | +8.6 pp | +16.85 pp |

Four-seed mean coverage:

| Arm | Mean Build | Mean STEP export |
|---|---:|---:|
| A1E | 73.80% | 73.05% |
| B2P | 90.65% | 89.90% |

Recommended main-text wording:

> In the controlled STEP setting, the textual-plan pathway consistently achieved higher executable coverage than continuous latent conditioning across four independently trained seeds.

This use of "consistently" is supported because all four seed-level deltas have the same direction.

## Geometry Interpretation

Jointly scoreable paired geometry also favors B2P in every seed.

| Metric | Seed 1 | Seed 2 | Seed 3 | Seed 4 | Mean |
|---|---:|---:|---:|---:|---:|
| Paired CD delta, B2P-A1E | -0.5037 | -0.1083 | -0.0914 | -0.1049 | -0.2021 |
| Paired F@1 delta, B2P-A1E | +2.00 pp | +0.80 pp | +0.36 pp | +0.37 pp | +0.88 pp |
| Seed-level sign-test p | 1.732e-07 | 0.0004117 | 0.04089 | 0.2330 | - |

Recommended wording:

> We did not observe a fidelity penalty from textualisation in any of the four seeds; the observed paired geometry differences instead favored B2P in all four runs.

Use this in the paired-geometry context only. Do not merge it with the full scored-set conditional F@1 table, because full scored-set median F@1 is mixed across seeds due to different scoreable subsets.

## Seed-To-Seed Variation

The four runs also show lower coverage variation for B2P:

| Arm | Build mean | Build SD | Build range |
|---|---:|---:|---:|
| A1E | 73.80% | 6.41 pp | 66.0-81.4% |
| B2P | 90.65% | 3.24 pp | 86.4-93.8% |

This can be reported as an observation:

> B2P also showed lower seed-to-seed variation in executable coverage in these four runs.

Do not promote this into a new primary claim such as "textualisation improves training stability"; four seeds support the observation, but a stability claim would need a dedicated design or more seeds.

## Change In Framing

Do not keep the old equivalence/no-material-loss framing as the main story.

The old framing invited the Reviewer 1 critique about post-hoc equivalence margins. The new result is simpler and stronger:

- B2P has higher coverage in all four seeds;
- B2P has lower paired CD in all four seeds;
- B2P has higher paired F@1 in all four seeds;
- B2P has higher unconditional mean F@1 in all four seeds.

Preferred framing:

> Under exact matched training conditions, textualisation did not show the fidelity penalty suggested as a possible concern. Across the four replicated runs, B2P had consistently higher executable coverage, while paired geometry metrics were also directionally better in every seed.

Avoid claiming:

- textual planning is universally superior;
- textualisation improves all modalities;
- the experiment proves human inspectability or editability benefits;
- the result fixes external Fusion 360 point-cloud weakness;
- pooled 2000-prediction tests are a substitute for model-level seed analysis.

## Statistical Cautions

Do not treat 2000 predictions as 2000 independent training replicates.

The pooled paired sign-test is useful only as a descriptive paired-case summary. The primary evidence for the reviewer response should be:

- seed-level table;
- four-seed mean and SD;
- explicit statement that all four seed-level coverage deltas have the same direction;
- explicit statement that all four paired geometry medians favor B2P.

Also keep the distinction among:

- full-set conditional fidelity over each arm's own scored outputs;
- jointly scoreable paired fidelity;
- unconditional fidelity accounting for failures.

The full scored-set median F@1 is mixed across seeds, while paired F@1 and unconditional mean F@1 favor B2P in all four seeds.

## Rebuttal Draft

> We agree with the concern that the original single-run B1a/B2-Pred comparison did not isolate training-run variability and used mismatched update/checkpoint conditions. We therefore repeated the central STEP comparison from scratch across four random seeds using identical training rows, 3,125 updates for both arms, final-checkpoint selection, identical decoding settings, no repair, and the same 500-query evaluation slice. B2P achieved higher Build and STEP-export coverage in all four seeds. Mean Build success was 90.65% for B2P versus 73.80% for A1E, and mean STEP-export success was 89.90% versus 73.05%. On the jointly scoreable subset, median CD was lower and median F@1 was higher for B2P in every seed. We therefore replaced the previous single-checkpoint equivalence framing with a four-seed replicated comparison and report seed-level variability explicitly.

## Final Status

This item should be considered one of the strongest completed reviewer-response items in the revision.

Do not spend additional GPU time on A1E/B2P seeds unless a new reviewer or coauthor explicitly requests it. The next highest-value work is now qualitative evidence, external failure analysis, construction-disjoint diagnostics, and claim/wording corrections.
