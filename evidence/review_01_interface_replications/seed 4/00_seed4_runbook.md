> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Seed 4 Runbook -- Frozen A1E/B2P Comparison

Date created: 2026-09-29

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

## Decision Log

2026-09-29:

- Seeds 1, 2, and 3 were already closed.
- Seed 4 was run as the final registered frozen replicate.
- No protocol changes were made after observing prior seed results.
- Seed 4 followed the same sequence:
  training -> prediction -> gate evaluation -> geometry scoring -> summary -> review record.

## Frozen Protocol

Seed 4 followed the registered four-seed protocol exactly:

- Modality: STEP
- A1E rows: 25,000
- B2P rows: 25,000
- Evaluation slice: same 500 STEP rows
- A1E updates: 3125
- B2P updates: 3125
- Epochs: 1
- Gradient accumulation: 8
- Checkpoint: final
- Decoding: same settings
- Repair: false
- No protocol change after seeing seeds 1, 2, or 3

## Step 1 -- Training + Prediction In WSL

User ran manually in WSL:

```bash
cd ~/workspace/MIRAGE/src
SEED=4 bash training_25k/cag_run_frozen_a1e_b2p_seed.sh
```

Observed outputs:

```text
outputs/b1_1epoch_step_s4/
outputs/b2_pred_matched_step_s4/
outputs/e1_observation_bypass/gen_code_step_A1E_s4.jsonl
outputs/e1_observation_bypass/gen_code_step_B2P_s4.jsonl
outputs/e1_observation_bypass/cag_seed_4_preflight.json
outputs/e1_observation_bypass/cag_seed_4_actuals.json
```

Observed on 2026-09-29:

```text
A1E final step: 3125
A1E eval_loss: 0.10364610701799393
B2P training report: present, seed 4, train_rows 25000
A1E predictions: 500
B2P predictions: 500
actuals validation:
  a_final_artifacts_present: true
  a_prediction_complete: true
  b_final_artifacts_present: true
  b_prediction_complete: true
actuals protocol:
  modality: step
  limit: 500
  epochs: 1
  expected_updates: 3125
  gradient_accumulation_steps: 8
  checkpoint_selection: final
  repair: false
```

## Step 2 -- Gate Evaluation In Windows PowerShell

Command:

```powershell
& "__DEV_ROOT__\src\scripts\run_e1_execution.ps1" `
  -Modalities step `
  -Conditions A1E_s4,B2P_s4
```

Observed outputs:

```text
__DEV_ROOT__\scratch\exec_e1_step_A1E_s4\execution_rows.jsonl
__DEV_ROOT__\scratch\exec_e1_step_B2P_s4\execution_rows.jsonl
```

Gate summary:

| Arm | n | Syntax OK | Build | STEP export |
|---|---:|---:|---:|---:|
| A1E_s4 | 500 | 96.8% | 81.4% | 80.6% |
| B2P_s4 | 500 | 96.4% | 90.0% | 89.2% |

Observed:

```text
A1E_s4 execution rows: 500
B2P_s4 execution rows: 500
A1E_s4 build/export: 81.4% / 80.6%
B2P_s4 build/export: 90.0% / 89.2%
kernel_crash_count: 0 for both arms
repair: false
```

## Step 3 -- Prepare Geometry Inputs In WSL

Command:

```bash
cd ~/workspace/MIRAGE/src
SEED=4 bash training_25k/cag_prepare_frozen_a1e_b2p_eval_seed.sh
```

Observed outputs:

```text
outputs/e1_observation_bypass/geom_input_step_A1E_s4.jsonl
outputs/e1_observation_bypass/geom_input_step_B2P_s4.jsonl
outputs/e1_observation_bypass/cag_seed_4_geometry_prep_manifest.json
```

Observed:

```text
step_A1E_s4: 500 rows -> geom_input_step_A1E_s4.jsonl
step_B2P_s4: 500 rows -> geom_input_step_B2P_s4.jsonl
wrote cag_seed_4_geometry_prep_manifest.json
```

## Step 4 -- Geometry Scoring In Windows PowerShell

Command:

```powershell
foreach ($A in @("step_A1E_s4", "step_B2P_s4")) {
  & "__DEV_ROOT__\src\scripts\evaluate_geometry_nbest.ps1" `
    -InputJsonl "__RUN_SOURCE_ROOT__\outputs\e1_observation_bypass\geom_input_$A.jsonl" `
    -OutputDir  "__DEV_ROOT__\scratch\geom_e1_$A"
}
```

Observed:

```text
geom_e1_step_A1E_s4 geometry rows: 500
geom_e1_step_B2P_s4 geometry rows: 500
```

## Step 5 -- Seed Summary

Command:

```powershell
python __DEV_ROOT__\src\training_25k\cag_summarize_a1e_b2p_seed_eval.py --seed 4
```

Summary:

| Arm | n | Build | STEP export | Scored | Median CD | Median F@1 | Unconditional mean F@1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| A1E_s4 | 500 | 81.4% | 80.6% | 402 / 500 | 2.392 | 20.23% | 16.30% |
| B2P_s4 | 500 | 90.0% | 89.2% | 445 / 500 | 2.159 | 20.31% | 18.72% |

Paired geometry:

| Joint n | A1E paired CD | B2P paired CD | A1E paired F@1 | B2P paired F@1 | A1E closer | Sign-test p |
|---:|---:|---:|---:|---:|---:|---:|
| 372 | 2.368 | 2.263 | 20.31% | 20.68% | 174 / 372 | 0.233 |

Summary JSON:

```text
__DEV_ROOT__\scratch\cag_seed_4_a1e_b2p_eval_summary.json
```

## Close Condition

Seed 4 is CLOSED. All close conditions are satisfied:

- `cag_seed_4_actuals.json` exists
- A1E predictions = 500
- B2P predictions = 500
- gate rows exist for both arms
- geometry rows exist for both arms
- both geometry row files have 500 rows
- `cag_seed_4_a1e_b2p_eval_summary.json` exists
- `01_seed4_closed_record.md` is written
