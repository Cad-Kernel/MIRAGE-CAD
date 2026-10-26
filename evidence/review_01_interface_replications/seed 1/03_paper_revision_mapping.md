> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Paper Revision Mapping From Seed 1 And Four-Seed Plan

This file records where the seed-1 result and the registered four-seed plan should be reflected later in the manuscript. It is not a rewrite draft yet; it is a checklist for the final paper editing stage.

## Abstract

Required change:

- Do not claim method-level superiority from seed 1 alone.
- After seeds 1-4 are complete, summarize the replicated comparison conservatively.

Possible final wording direction:

> We additionally repeat the exact-match continuous-vs-textual comparison across four training seeds, using identical update counts, stopping rules, checkpoint selection, decoding, and no repair.

Only add "textual-plan pathway is more stable" if seeds 2-4 support that conclusion.

## Introduction / Contributions

Required change:

- Reframe the A1E/B2P experiment as a controlled representation-interface study.
- State that the revision adds an explicit multi-seed frozen replication to answer reviewer concerns about training-run variance.

Avoid:

- "B2P is better" as a broad claim.
- "Textualization does not degrade fidelity" without mentioning the replicated seed evidence and the denominator.

## Method / Experimental Protocol

Required change:

- Add a short frozen-protocol paragraph:
  - same 25k rows
  - same 500 STEP evaluation slice
  - 3125 vs 3125 updates
  - final checkpoint
  - same decoding
  - no repair
  - four seeds: 1, 2, 3, 4

Also state:

> We report seed-level results rather than relying only on test-set bootstrap, because bootstrap over test samples does not estimate training-run variance.

This directly addresses Reviewer 1 and Reviewer 2.

## Results Section

Required additions:

1. Per-seed frozen comparison table.
2. Across-seed mean +/- SD table.
3. Paired geometry table on jointly scoreable subset.
4. Unconditional F@1 table where failed/unscored outputs count as 0.

Seed 1 row to include after all seeds are complete:

| Seed | A1E Build | B2P Build | A1E Export | B2P Export | Joint n | A1E paired CD | B2P paired CD | A1E paired F@1 | B2P paired F@1 | A1E uncond F@1 | B2P uncond F@1 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 66.0 | 92.4 | 65.0 | 91.6 | 301 | 2.745 | 2.241 | 19.97 | 21.97 | 12.54 | 19.33 |

Seed 1 interpretation, if kept as one row inside a multi-seed table:

> Seed 1 shows a large B2P coverage advantage and better paired geometry, but it is reported as one replicate rather than a standalone method-level conclusion.

## Discussion

Required change:

- Discuss training-seed variability explicitly.
- If seeds 2-4 support seed 1:
  - say the textual-plan pathway maintained high coverage across replicated runs.
  - say the continuous interface showed larger training-seed variability.
- If seeds 2-4 do not support seed 1:
  - say the seed-1 advantage is not stable.
  - preserve the more cautious claim that the exact-match study reveals nontrivial seed dependence.

Either outcome is useful for the revision because it answers the reviewer concern honestly.

## Limitations

Required change:

- State that four seeds improve evidence for training stability but still do not exhaust all sources of variance.
- Keep the claim separate from external generalization, editability, and topology-aware B-Rep limitations.

## Rebuttal / Response Letter

Reviewer 1 response should mention:

- The original B1a/B2-Pred comparison had update/checkpoint/seed limitations.
- The revision freezes a new exact-match comparison.
- Seeds are registered as [1, 2, 3, 4] before running seed 2.
- Each seed is evaluated with gate metrics, geometry, paired subset, and unconditional F@1.

Reviewer 2 response should mention:

- The revised analysis separates test-sample uncertainty from training-run uncertainty.
- Bootstrap/McNemar/sign tests are not used as substitutes for training-seed variance.
- Stage 3b/curriculum claims remain separate from the A1E/B2P frozen comparison.

Reviewer 4 response should mention:

- Geometry is reported alongside validity.
- The seed-1 result is not only a Build result; it includes CD/F@1 and unconditional F@1.

## Do Not Write Until All Four Seeds Finish

Avoid these sentences for now:

- "B2P is more stable than A1E."
- "Textualization improves Build by 26.4 pp."
- "The textual-plan interface is method-level superior."

Safe current statement:

> Seed 1 is a strong replicate-level result: under the frozen matched protocol, B2P achieved higher coverage and better geometry than A1E. The registered four-seed replication will determine whether this effect is stable across training seeds.
