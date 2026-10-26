> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Seed 3 Runbook -- Frozen A1E/B2P Comparison

Date created: 2026-09-27

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

2026-09-27 09:36 AM:

- Seed 2 is formally closed.
- Do not write method-level stability claims yet, because the registered protocol has four seeds.
- Next action is seed 3 training and prediction only.
- Do not start seed 4 until seed 3 is fully closed:
  training -> prediction -> gate evaluation -> geometry scoring -> summary -> review record.

## Current Two-Seed Trend

| Seed | Arm | Build | STEP export | Paired CD | Paired F@1 |
|---|---|---:|---:|---:|---:|
| 1 | A1E | 66.0% | 65.0% | 2.745 | 19.97% |
| 1 | B2P | 92.4% | 91.6% | 2.241 | 21.97% |
| 2 | A1E | 75.4% | 74.8% | 2.446 | 20.20% |
| 2 | B2P | 93.8% | 93.0% | 2.338 | 21.00% |

Working interpretation:

- B2P has much higher coverage in both frozen replicates so far.
- On the paired scoreable subset, B2P is better on CD and F@1 in both seed 1 and seed 2.
- A1E appears more seed-sensitive in Build/STEP export, but this remains an interim observation until seeds 3 and 4 are complete.

## Frozen Protocol

Seed 3 must follow the registered four-seed protocol exactly:

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
- No protocol change after seeing seed 1 or seed 2

## Step 1 -- Training + Prediction In WSL

User will run manually in WSL:

```bash
cd ~/workspace/MIRAGE/src
SEED=3 bash training_25k/cag_run_frozen_a1e_b2p_seed.sh
```

Expected outputs:

```text
outputs/b1_1epoch_step_s3/
outputs/b2_pred_matched_step_s3/
outputs/e1_observation_bypass/gen_code_step_A1E_s3.jsonl
outputs/e1_observation_bypass/gen_code_step_B2P_s3.jsonl
outputs/e1_observation_bypass/cag_seed_3_preflight.json
outputs/e1_observation_bypass/cag_seed_3_actuals.json
```

After completion, check:

```bash
cd ~/workspace/MIRAGE/src

ls -lh \
  outputs/b1_1epoch_step_s3/checkpoint-3125/trainer_state.json \
  outputs/b1_1epoch_step_s3/adapter_model.safetensors \
  outputs/b1_1epoch_step_s3/soft_prefix.pt \
  outputs/b2_pred_matched_step_s3/training_report.json \
  outputs/b2_pred_matched_step_s3/adapter_model.safetensors \
  outputs/e1_observation_bypass/gen_code_step_A1E_s3.jsonl \
  outputs/e1_observation_bypass/gen_code_step_B2P_s3.jsonl \
  outputs/e1_observation_bypass/cag_seed_3_preflight.json \
  outputs/e1_observation_bypass/cag_seed_3_actuals.json

wc -l outputs/e1_observation_bypass/gen_code_step_A1E_s3.jsonl
wc -l outputs/e1_observation_bypass/gen_code_step_B2P_s3.jsonl

cat outputs/b1_1epoch_step_s3/checkpoint-3125/trainer_state.json

python3 - <<'PY'
import json
p="outputs/e1_observation_bypass/cag_seed_3_actuals.json"
j=json.load(open(p))
print("validation:", json.dumps(j.get("validation"), indent=2, sort_keys=True))
print("protocol:", json.dumps(j.get("protocol"), indent=2, sort_keys=True))
print("A1E trainer_state:", json.dumps(j.get("arms",{}).get("A1E",{}).get("trainer_state"), indent=2, sort_keys=True))
print("B2P training_report:", json.dumps(j.get("arms",{}).get("B2P",{}).get("training_report"), indent=2, sort_keys=True))
PY
```

Expected success criteria:

- A1E prediction rows = 500
- B2P prediction rows = 500
- A1E trainer_state step = 3125
- actuals validation all true:
  - `a_final_artifacts_present: true`
  - `a_prediction_complete: true`
  - `b_final_artifacts_present: true`
  - `b_prediction_complete: true`
- protocol matches frozen settings:
  - `limit = 500`
  - `epochs = 1`
  - `expected_updates = 3125`
  - `gradient_accumulation_steps = 8`
  - `checkpoint_selection = final`
  - `repair = false`
  - `modality = step`

Only after this succeeds, update status to:

```yaml
Training: COMPLETE
Prediction: COMPLETE
Gate evaluation: PENDING
Geometry scoring: PENDING
Summary JSON: PENDING
Review record: PENDING
Seed status: OPEN
```

Observed on 2026-09-28:

```text
A1E final step: 3125
B2P training report: present, seed 3, train_rows 25000
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

Run after Step 1 is verified:

```powershell
& "__DEV_ROOT__\src\scripts\run_e1_execution.ps1" `
  -Modalities step `
  -Conditions A1E_s3,B2P_s3
```

Expected outputs:

```text
__DEV_ROOT__\scratch\exec_e1_step_A1E_s3\execution_rows.jsonl
__DEV_ROOT__\scratch\exec_e1_step_B2P_s3\execution_rows.jsonl
```

Record gate summary here after running:

| Arm | n | Syntax OK | Build | STEP export |
|---|---:|---:|---:|---:|
| A1E_s3 | 500 | 93.8% | 72.4% | 71.8% |
| B2P_s3 | 500 | 95.2% | 86.4% | 85.8% |

Observed on 2026-09-28:

```text
A1E_s3 execution rows: 500
B2P_s3 execution rows: 500
A1E_s3 build/export: 72.4% / 71.8%
B2P_s3 build/export: 86.4% / 85.8%
kernel_crash_count: 0 for both arms
repair: false
```

## Step 3 -- Prepare Geometry Inputs In WSL

Run in WSL:

```bash
cd ~/workspace/MIRAGE/src
SEED=3 bash training_25k/cag_prepare_frozen_a1e_b2p_eval_seed.sh
```

Expected outputs:

```text
outputs/e1_observation_bypass/geom_input_step_A1E_s3.jsonl
outputs/e1_observation_bypass/geom_input_step_B2P_s3.jsonl
outputs/e1_observation_bypass/cag_seed_3_geometry_prep_manifest.json
```

Observed on 2026-09-28:

```text
step_A1E_s3: 500 rows -> geom_input_step_A1E_s3.jsonl
step_B2P_s3: 500 rows -> geom_input_step_B2P_s3.jsonl
wrote cag_seed_3_geometry_prep_manifest.json
```

## Step 4 -- Geometry Scoring In Windows PowerShell

Run:

```powershell
foreach ($A in @("step_A1E_s3", "step_B2P_s3")) {
  & "__DEV_ROOT__\src\scripts\evaluate_geometry_nbest.ps1" `
    -InputJsonl "__RUN_SOURCE_ROOT__\outputs\e1_observation_bypass\geom_input_$A.jsonl" `
    -OutputDir  "__DEV_ROOT__\scratch\geom_e1_$A"
}
```

Then verify:

```powershell
(Get-Content "__DEV_ROOT__\scratch\geom_e1_step_A1E_s3\geometry_nbest_rows.jsonl").Count
(Get-Content "__DEV_ROOT__\scratch\geom_e1_step_B2P_s3\geometry_nbest_rows.jsonl").Count
```

Expected:

```text
500
500
```

Observed on 2026-09-28:

```text
geom_e1_step_A1E_s3 geometry rows: 500
geom_e1_step_B2P_s3 geometry rows: 500
```

## Step 5 -- Seed Summary

Run:

```powershell
python __DEV_ROOT__\src\training_25k\cag_summarize_a1e_b2p_seed_eval.py --seed 3
```

Expected output:

```text
__DEV_ROOT__\scratch\cag_seed_3_a1e_b2p_eval_summary.json
```

Record final seed 3 summary here:

| Arm | n | Build | STEP export | Scored | Median CD | Median F@1 | Unconditional mean F@1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| A1E_s3 | 500 | 72.4% | 71.8% | 352 / 500 | 2.445 | 21.12% | 14.95% |
| B2P_s3 | 500 | 86.4% | 85.8% | 427 / 500 | 2.305 | 20.41% | 17.93% |

Paired geometry:

| Joint n | A1E paired CD | B2P paired CD | A1E paired F@1 | B2P paired F@1 | A1E closer | Sign-test p |
|---:|---:|---:|---:|---:|---:|---:|
| 328 | 2.403 | 2.312 | 21.24% | 21.61% | 145 / 328 | 0.04089 |

Summary JSON:

```text
__DEV_ROOT__\scratch\cag_seed_3_a1e_b2p_eval_summary.json
```

## Close Condition

Only mark seed 3 CLOSED when all are true:

- `cag_seed_3_actuals.json` exists
- A1E predictions = 500
- B2P predictions = 500
- gate rows exist for both arms
- geometry rows exist for both arms
- both geometry rows files have 500 rows
- `cag_seed_3_a1e_b2p_eval_summary.json` exists
- `01_seed3_closed_record.md` is written

Then update status:

```yaml
Training: COMPLETE
Prediction: COMPLETE
Gate evaluation: COMPLETE
Geometry scoring: COMPLETE
Summary JSON: COMPLETE
Review record: COMPLETE
Seed status: CLOSED
```
