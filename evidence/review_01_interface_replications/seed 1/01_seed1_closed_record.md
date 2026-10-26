> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Seed 1 Closed Record -- Frozen A1E/B2P Comparison

Date: 2026-09-26

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

## Seed 1 Result

| Arm | n | Build | STEP export | Scored | Median CD | Median F@1 | Unconditional mean F@1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| A1E_s1 | 500 | 66.0% | 65.0% | 323 / 500 | 2.745 | 19.87% | 12.54% |
| B2P_s1 | 500 | 92.4% | 91.6% | 456 / 500 | 2.176 | 20.63% | 19.33% |

Paired geometry:

| Joint n | A1E paired CD | B2P paired CD | A1E paired F@1 | B2P paired F@1 | A1E closer | Sign-test p |
|---:|---:|---:|---:|---:|---:|---:|
| 301 | 2.745 | 2.241 | 19.97% | 21.97% | 105 / 301 | 1.732e-07 |

## Provenance Files

Training and prediction:

```text
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/cag_seed_1_preflight.json
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/cag_seed_1_actuals.json
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/gen_code_step_A1E_s1.jsonl
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/gen_code_step_B2P_s1.jsonl
```

Geometry and summary:

```text
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/geom_input_step_A1E_s1.jsonl
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/geom_input_step_B2P_s1.jsonl
~/workspace/MIRAGE/src/outputs/e1_observation_bypass/cag_seed_1_geometry_prep_manifest.json
__DEV_ROOT__\scratch\exec_e1_step_A1E_s1\execution_rows.jsonl
__DEV_ROOT__\scratch\exec_e1_step_B2P_s1\execution_rows.jsonl
__DEV_ROOT__\scratch\geom_e1_step_A1E_s1\geometry_nbest_rows.jsonl
__DEV_ROOT__\scratch\geom_e1_step_B2P_s1\geometry_nbest_rows.jsonl
__DEV_ROOT__\scratch\cag_seed_1_a1e_b2p_eval_summary.json
```

## Conclusion

Seed 1 supports B2P on both coverage and geometry:

- B2P builds and exports many more programs than A1E.
- B2P produces many more scorable outputs.
- B2P has better unconditional mean F@1.
- On the jointly scoreable subset, B2P also has better median CD and median F@1.

Reviewer-facing wording for this seed:

> In the first frozen replicate, the textual-plan interface did not show a fidelity penalty relative to the continuous interface. Instead, B2P achieved higher Build/STEP coverage and better paired geometry. This directly addresses the update/checkpoint mismatch concern for this seed.

Important limitation:

> This is still one seed. It must not be promoted to a method-level stability claim until seeds 2, 3, and 4 are completed under the same frozen protocol.
