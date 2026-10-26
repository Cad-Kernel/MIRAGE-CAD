> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Four-Seed Frozen Replication Registration

Date registered: 2026-09-26

This registration is written before running seed 2. Its purpose is to fix the replication plan in advance and avoid any appearance that additional seeds were chosen after inspecting later results.

## Primary Objective

Assess training-seed stability of the exact-match A1E vs B2P comparison requested by Reviewer 1 and Reviewer 2.

The central question is:

> Under identical data, update budgets, stopping rules, checkpoint-selection rules, decoding settings, and no-repair evaluation, how stable is the comparison between the continuous A1E interface and the textual-plan B2P interface across independent training seeds?

## Registered Seeds

Primary frozen replication:

```yaml
seeds: [1, 2, 3, 4]
```

Current status:

| Seed | Status |
|---:|---|
| 1 | CLOSED |
| 2 | PLANNED |
| 3 | PLANNED |
| 4 | PLANNED |

## Fixed Protocol Across All Seeds

- Modality: STEP
- A1E training rows: 25,000
- B2P training rows: 25,000
- Evaluation slice: same 500 STEP rows
- A1E updates: 3125
- B2P updates: 3125
- Epochs: 1
- Gradient accumulation: 8
- Checkpoint selection: final checkpoint
- Decoding: same decoding configuration
- Repair: false
- Gate evaluator: same execution evaluator
- Geometry scorer: same geometry scoring configuration
- Per-seed workflow: close one seed completely before launching the next seed

## Per-Seed Required Outputs

Each seed must produce:

- Training provenance
- Prediction provenance
- Gate evaluation rows and summary
- Geometry input manifest
- Geometry scoring rows
- Per-seed evaluation summary JSON
- Review log entry

Per-seed reporting columns:

| Field | Meaning |
|---|---|
| Syntax | syntax success rate |
| Build | executable build success rate |
| STEP export | STEP export success rate |
| Scoreable count | outputs with geometry score |
| Jointly scoreable n | intersection scored by both A1E and B2P |
| Paired median CD | median CD on jointly scoreable subset |
| Paired median F@1 | median F@1 on jointly scoreable subset |
| Unconditional mean F@1 | F@1 averaged over all 500 inputs, failed/unscored outputs counted as 0 |

## Across-Seed Reporting

After seeds 1-4 are closed, report:

- A1E Build mean +/- SD
- B2P Build mean +/- SD
- A1E STEP export mean +/- SD
- B2P STEP export mean +/- SD
- A1E unconditional mean F@1 mean +/- SD
- B2P unconditional mean F@1 mean +/- SD
- Per-seed paired median CD differences
- Per-seed paired median F@1 differences
- A clear statement of training-seed variability

Do not report only pooled rows. The reviewer concern is training-run variance, so seed-level variation must remain visible.

## Planned Final Table

| Seed | A1E Build | B2P Build | Delta Build | A1E Export | B2P Export | Joint n | Delta CD | Delta F@1 | Delta Uncond F@1 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 66.0 | 92.4 | +26.4 | 65.0 | 91.6 | 301 | B2P better | B2P better | +6.79 pp |
| 2 | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| 3 | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| 4 | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

## Execution Rule

Run seeds mechanically in order:

```text
seed 2: training -> prediction -> gate evaluation -> geometry -> summary -> close
seed 3: training -> prediction -> gate evaluation -> geometry -> summary -> close
seed 4: training -> prediction -> gate evaluation -> geometry -> summary -> close
```

Do not change the protocol after seeing seed 2. If a bug is discovered, document the bug, fix the evaluator or runner, and rerun affected seeds symmetrically.
