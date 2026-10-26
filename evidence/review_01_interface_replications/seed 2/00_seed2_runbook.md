> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Seed 2 Runbook -- Frozen A1E/B2P Comparison

Date created: 2026-09-26

## Status

```yaml
Training: COMPLETE
Prediction: COMPLETE
Gate evaluation: COMPLETE
Geometry scoring: COMPLETE
Seed status: CLOSED
```

## Frozen Protocol

Seed 2 must follow the registered four-seed protocol exactly:

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
- No protocol change after seeing seed 1

## Step 1 -- Training + Prediction In WSL

Run in WSL:

```bash
cd ~/workspace/MIRAGE/src
SEED=2 bash training_25k/cag_run_frozen_a1e_b2p_seed.sh
```

Expected outputs:

```text
outputs/b1_1epoch_step_s2/
outputs/b2_pred_matched_step_s2/
outputs/e1_observation_bypass/gen_code_step_A1E_s2.jsonl
outputs/e1_observation_bypass/gen_code_step_B2P_s2.jsonl
outputs/e1_observation_bypass/cag_seed_2_preflight.json
outputs/e1_observation_bypass/cag_seed_2_actuals.json
```

After completion, check:

```bash
cat outputs/b1_1epoch_step_s2/checkpoint-3125/trainer_state.json
wc -l outputs/e1_observation_bypass/gen_code_step_A1E_s2.jsonl
wc -l outputs/e1_observation_bypass/gen_code_step_B2P_s2.jsonl
ls -l outputs/e1_observation_bypass/cag_seed_2_actuals.json
```

Expected:

```text
A1E final step: 3125
B2P final step: 3125
A1E predictions: 500
B2P predictions: 500
actuals json: present
```

Observed on 2026-09-27:

```text
A1E final step: 3125
B2P training report: present, seed 2, train_rows 25000
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

Run after Step 1 is complete:

```powershell
& "__DEV_ROOT__\src\scripts\run_e1_execution.ps1" `
  -Modalities step `
  -Conditions A1E_s2,B2P_s2
```

Expected outputs:

```text
__DEV_ROOT__\scratch\exec_e1_step_A1E_s2\execution_rows.jsonl
__DEV_ROOT__\scratch\exec_e1_step_B2P_s2\execution_rows.jsonl
```

Record gate summary here after running:

| Arm | n | Syntax OK | Build | STEP export |
|---|---:|---:|---:|---:|
| A1E_s2 | 500 | 95.0% | 75.4% | 74.8% |
| B2P_s2 | 500 | 96.0% | 93.8% | 93.0% |

## Step 3 -- Prepare Geometry Inputs In WSL

Run in WSL:

```bash
cd ~/workspace/MIRAGE/src
SEED=2 bash training_25k/cag_prepare_frozen_a1e_b2p_eval_seed.sh
```

If that file is not in `training_25k`, use the synced location that exists:

```bash
SEED=2 bash scratch/cag_prepare_frozen_a1e_b2p_eval_seed.sh
```

Expected outputs:

```text
outputs/e1_observation_bypass/geom_input_step_A1E_s2.jsonl
outputs/e1_observation_bypass/geom_input_step_B2P_s2.jsonl
outputs/e1_observation_bypass/cag_seed_2_geometry_prep_manifest.json
```

## Step 4 -- Geometry Scoring In Windows PowerShell

Run:

```powershell
foreach ($A in @("step_A1E_s2", "step_B2P_s2")) {
  & "__DEV_ROOT__\src\scripts\evaluate_geometry_nbest.ps1" `
    -InputJsonl "__RUN_SOURCE_ROOT__\outputs\e1_observation_bypass\geom_input_$A.jsonl" `
    -OutputDir  "__DEV_ROOT__\scratch\geom_e1_$A"
}
```

Then verify:

```powershell
(Get-Content "__DEV_ROOT__\scratch\geom_e1_step_A1E_s2\geometry_nbest_rows.jsonl").Count
(Get-Content "__DEV_ROOT__\scratch\geom_e1_step_B2P_s2\geometry_nbest_rows.jsonl").Count
```

Expected:

```text
500
500
```

Observed on 2026-09-27:

```text
__DEV_ROOT__\scratch\geom_e1_step_A1E_s2\geometry_nbest_rows.jsonl: 500
__DEV_ROOT__\scratch\geom_e1_step_B2P_s2\geometry_nbest_rows.jsonl: 500
```

## Step 5 -- Seed Summary

Run whichever path exists for the summary script:

```powershell
python __DEV_ROOT__\src\scratch\cag_summarize_a1e_b2p_seed_eval.py --seed 2
```

or:

```powershell
python __DEV_ROOT__\src\training_25k\cag_summarize_a1e_b2p_seed_eval.py --seed 2
```

Expected output:

```text
__DEV_ROOT__\scratch\cag_seed_2_a1e_b2p_eval_summary.json
```

Record final seed 2 summary here:

| Arm | n | Build | STEP export | Scored | Median CD | Median F@1 | Unconditional mean F@1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| A1E_s2 | 500 | 75.4% | 74.8% | 370 / 500 | 2.436 | 20.17% | 15.23% |
| B2P_s2 | 500 | 93.8% | 93.0% | 462 / 500 | 2.281 | 19.90% | 19.10% |

Paired geometry:

| Joint n | A1E paired CD | B2P paired CD | A1E paired F@1 | B2P paired F@1 | A1E closer | Sign-test p |
|---:|---:|---:|---:|---:|---:|---:|
| 351 | 2.446 | 2.338 | 20.20% | 21.00% | 142 / 351 | 0.0004117 |

## Close Condition

Only mark seed 2 CLOSED when all are true:

- `cag_seed_2_actuals.json` exists
- A1E predictions = 500
- B2P predictions = 500
- gate rows exist for both arms
- geometry rows exist for both arms
- both geometry rows files have 500 rows
- `cag_seed_2_a1e_b2p_eval_summary.json` exists

Then update status:

```yaml
Training: COMPLETE
Prediction: COMPLETE
Gate evaluation: COMPLETE
Geometry scoring: COMPLETE
Seed status: CLOSED
```
