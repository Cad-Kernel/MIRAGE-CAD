> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Seed 2 Closed Record -- Frozen A1E/B2P Comparison

Date: 2026-09-27

## Status

```yaml
Training: COMPLETE
Prediction: COMPLETE
Gate evaluation: COMPLETE
Geometry scoring: COMPLETE
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

## Seed 2 Result

| Arm | n | Build | STEP export | Scored | Median CD | Median F@1 | Unconditional mean F@1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| A1E_s2 | 500 | 75.4% | 74.8% | 370 / 500 | 2.436 | 20.17% | 15.23% |
| B2P_s2 | 500 | 93.8% | 93.0% | 462 / 500 | 2.281 | 19.90% | 19.10% |

Paired geometry:

| Joint n | A1E paired CD | B2P paired CD | A1E paired F@1 | B2P paired F@1 | A1E closer | Sign-test p |
|---:|---:|---:|---:|---:|---:|---:|
| 351 | 2.446 | 2.338 | 20.20% | 21.00% | 142 / 351 | 0.0004117 |

Gate summary:

| Arm | n | Syntax OK | Build | STEP export |
|---|---:|---:|---:|---:|
| A1E_s2 | 500 | 95.0% | 75.4% | 74.8% |
| B2P_s2 | 500 | 96.0% | 93.8% | 93.0% |

## Provenance Files

Training and prediction:

```text
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/cag_seed_2_preflight.json
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/cag_seed_2_actuals.json
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/gen_code_step_A1E_s2.jsonl
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/gen_code_step_B2P_s2.jsonl
```

Geometry and summary:

```text
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/geom_input_step_A1E_s2.jsonl
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/geom_input_step_B2P_s2.jsonl
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/cag_seed_2_geometry_prep_manifest.json
__DEV_ROOT__\scratch\exec_e1_step_A1E_s2\execution_rows.jsonl
__DEV_ROOT__\scratch\exec_e1_step_B2P_s2\execution_rows.jsonl
__DEV_ROOT__\scratch\geom_e1_step_A1E_s2\geometry_nbest_rows.jsonl
__DEV_ROOT__\scratch\geom_e1_step_B2P_s2\geometry_nbest_rows.jsonl
__DEV_ROOT__\scratch\cag_seed_2_a1e_b2p_eval_summary.json
```

## Conclusion

Seed 2 supports B2P primarily through much higher coverage:

- B2P builds and exports substantially more programs than A1E.
- B2P produces more scorable outputs.
- B2P has better unconditional mean F@1.
- On the jointly scoreable subset, B2P has better median CD and median F@1, with a significant sign-test result.

Reviewer-facing wording for this seed:

> In the second frozen replicate, B2P again achieved substantially higher Build/STEP coverage than A1E under the exact same update count, checkpoint rule, decoding configuration, and 500-row STEP evaluation slice. On the jointly scoreable subset, B2P also improved paired CD and F@1.

Important limitation:

> This is still only the second seed. Do not claim method-level stability until seeds 3 and 4 are completed under the same frozen protocol.
