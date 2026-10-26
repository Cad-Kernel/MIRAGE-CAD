> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Seed 4 Closed Record -- Frozen A1E/B2P Comparison

Date: 2026-09-29

## Status

```yaml
Training: COMPLETE
Prediction: COMPLETE
Gate evaluation: COMPLETE
Geometry scoring: COMPLETE
Summary JSON: COMPLETE
Review record: COMPLETE
Seed status: CLOSED
```

## Frozen Protocol

This seed was run under the frozen exact-match A1E/B2P protocol:

- Modality: STEP
- Training rows: 25,000
- Evaluation slice: same 500 STEP rows
- A1E updates: 3125
- B2P updates: 3125
- Epochs: 1
- Gradient accumulation: 8
- Checkpoint selection: final checkpoint
- Decoding: same decoding settings
- Repair: false
- Geometry scorer: same evaluator configuration for both arms

## Seed 4 Result

| Arm | n | Build | STEP export | Scored | Median CD | Median F@1 | Unconditional mean F@1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| A1E_s4 | 500 | 81.4% | 80.6% | 402 / 500 | 2.392 | 20.23% | 16.30% |
| B2P_s4 | 500 | 90.0% | 89.2% | 445 / 500 | 2.159 | 20.31% | 18.72% |

Paired geometry:

| Joint n | A1E paired CD | B2P paired CD | A1E paired F@1 | B2P paired F@1 | A1E closer | Sign-test p |
|---:|---:|---:|---:|---:|---:|---:|
| 372 | 2.368 | 2.263 | 20.31% | 20.68% | 174 / 372 | 0.233 |

Gate summary:

| Arm | n | Syntax OK | Build | STEP export |
|---|---:|---:|---:|---:|
| A1E_s4 | 500 | 96.8% | 81.4% | 80.6% |
| B2P_s4 | 500 | 96.4% | 90.0% | 89.2% |

## Provenance Files

Training and prediction:

```text
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/cag_seed_4_preflight.json
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/cag_seed_4_actuals.json
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/gen_code_step_A1E_s4.jsonl
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/gen_code_step_B2P_s4.jsonl
```

Geometry and summary:

```text
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/geom_input_step_A1E_s4.jsonl
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/geom_input_step_B2P_s4.jsonl
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/cag_seed_4_geometry_prep_manifest.json
__DEV_ROOT__\scratch\exec_e1_step_A1E_s4\execution_rows.jsonl
__DEV_ROOT__\scratch\exec_e1_step_B2P_s4\execution_rows.jsonl
__DEV_ROOT__\scratch\geom_e1_step_A1E_s4\geometry_nbest_rows.jsonl
__DEV_ROOT__\scratch\geom_e1_step_B2P_s4\geometry_nbest_rows.jsonl
__DEV_ROOT__\scratch\cag_seed_4_a1e_b2p_eval_summary.json
```

## Conclusion

Seed 4 again supports B2P primarily through higher coverage:

- B2P builds and exports more programs than A1E.
- B2P produces more scorable outputs.
- B2P has better unconditional mean F@1.
- On the jointly scoreable subset, B2P has better paired median CD and paired median F@1.

Reviewer-facing wording for this seed:

> In the fourth frozen replicate, B2P again achieved higher Build/STEP coverage than A1E under the exact same update count, checkpoint rule, decoding configuration, and 500-row STEP evaluation slice. On the jointly scoreable subset, B2P also had slightly better paired CD and F@1.

Four-seed note:

> Seeds 1-4 are now complete under the frozen protocol. Across all four frozen replicates, B2P consistently improves Build/STEP coverage over A1E, while paired geometry is also better on median CD and median F@1 in each seed.
