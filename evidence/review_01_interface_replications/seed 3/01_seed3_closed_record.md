> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Seed 3 Closed Record -- Frozen A1E/B2P Comparison

Date: 2026-09-28

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

## Seed 3 Result

| Arm | n | Build | STEP export | Scored | Median CD | Median F@1 | Unconditional mean F@1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| A1E_s3 | 500 | 72.4% | 71.8% | 352 / 500 | 2.445 | 21.12% | 14.95% |
| B2P_s3 | 500 | 86.4% | 85.8% | 427 / 500 | 2.305 | 20.41% | 17.93% |

Paired geometry:

| Joint n | A1E paired CD | B2P paired CD | A1E paired F@1 | B2P paired F@1 | A1E closer | Sign-test p |
|---:|---:|---:|---:|---:|---:|---:|
| 328 | 2.403 | 2.312 | 21.24% | 21.61% | 145 / 328 | 0.04089 |

Gate summary:

| Arm | n | Syntax OK | Build | STEP export |
|---|---:|---:|---:|---:|
| A1E_s3 | 500 | 93.8% | 72.4% | 71.8% |
| B2P_s3 | 500 | 95.2% | 86.4% | 85.8% |

## Provenance Files

Training and prediction:

```text
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/cag_seed_3_preflight.json
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/cag_seed_3_actuals.json
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/gen_code_step_A1E_s3.jsonl
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/gen_code_step_B2P_s3.jsonl
```

Geometry and summary:

```text
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/geom_input_step_A1E_s3.jsonl
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/geom_input_step_B2P_s3.jsonl
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/cag_seed_3_geometry_prep_manifest.json
__DEV_ROOT__\scratch\exec_e1_step_A1E_s3\execution_rows.jsonl
__DEV_ROOT__\scratch\exec_e1_step_B2P_s3\execution_rows.jsonl
__DEV_ROOT__\scratch\geom_e1_step_A1E_s3\geometry_nbest_rows.jsonl
__DEV_ROOT__\scratch\geom_e1_step_B2P_s3\geometry_nbest_rows.jsonl
__DEV_ROOT__\scratch\cag_seed_3_a1e_b2p_eval_summary.json
```

## Conclusion

Seed 3 again supports B2P primarily through higher coverage:

- B2P builds and exports substantially more programs than A1E.
- B2P produces more scorable outputs.
- B2P has better unconditional mean F@1.
- On the jointly scoreable subset, B2P has better median CD and median F@1, with a significant sign-test result.

Reviewer-facing wording for this seed:

> In the third frozen replicate, B2P again achieved substantially higher Build/STEP coverage than A1E under the exact same update count, checkpoint rule, decoding configuration, and 500-row STEP evaluation slice. On the jointly scoreable subset, B2P also improved paired CD and F@1.

Important limitation:

> This is still only the third seed. Do not claim method-level stability until seed 4 is completed under the same frozen protocol.
