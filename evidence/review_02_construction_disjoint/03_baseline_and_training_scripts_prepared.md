> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Baseline And Training Scripts Prepared

Date: 2026-10-04

## Status

```yaml
NN baseline script: PREPARED
MIRAGE retraining script: PREPARED
Scripts synced to WSL: YES
Python compile check: PASS
Bash syntax check: PASS
CLI import/help check in ai_dev: PASS
NN baseline run: COMPLETE
NN baseline gate evaluation: COMPLETE
NN baseline geometry scoring: COMPLETE
MIRAGE retraining: COMPLETE
MIRAGE prediction: COMPLETE
MIRAGE gate evaluation: COMPLETE
MIRAGE geometry scoring: COMPLETE
```

## Scripts

Windows checkout:

```text
__DEV_ROOT__\src\training_25k\cag_gen_cd_step_nn_descriptor_baseline.py
__DEV_ROOT__\src\training_25k\cag_prepare_construction_disjoint_geometry.py
__DEV_ROOT__\src\training_25k\cag_run_construction_disjoint_nn_baseline.sh
__DEV_ROOT__\src\training_25k\cag_run_construction_disjoint_step_b2p_training.sh
```

WSL checkout:

```text
~/workspace/MIRAGE/src/training_25k/cag_gen_cd_step_nn_descriptor_baseline.py
~/workspace/MIRAGE/src/training_25k/cag_prepare_construction_disjoint_geometry.py
~/workspace/MIRAGE/src/training_25k/cag_run_construction_disjoint_nn_baseline.sh
~/workspace/MIRAGE/src/training_25k/cag_run_construction_disjoint_step_b2p_training.sh
```

## WSL Script Hashes

```text
bc4e12162c837fa5bccb8b446fb217b298337fc0ff6561cdc03882542553cc93  training_25k/cag_gen_cd_step_nn_descriptor_baseline.py
e1b4e6b996c4a05090a4cba84148d75c5390e84334b231fe2f73933b0b507015  training_25k/cag_prepare_construction_disjoint_geometry.py
92aa02e59ec85bf7d028ac0756a814dab021b94faac33540053eaae834e56222  training_25k/cag_run_construction_disjoint_nn_baseline.sh
7387a403b18204ed07cf688b56ad487b0741fa058dc4f7b2c85c47577c0962eb  training_25k/cag_run_construction_disjoint_step_b2p_training.sh
```

## Checks Run

Windows-side:

```text
python -m py_compile:
  cag_gen_cd_step_nn_descriptor_baseline.py
  cag_prepare_construction_disjoint_geometry.py
  cag_build_construction_disjoint_split.py
  PASS

bash -n via WSL over Windows path:
  cag_run_construction_disjoint_nn_baseline.sh
  cag_run_construction_disjoint_step_b2p_training.sh
  PASS
```

WSL-side:

```text
python3 -m py_compile:
  cag_gen_cd_step_nn_descriptor_baseline.py
  cag_prepare_construction_disjoint_geometry.py
  cag_build_construction_disjoint_split.py
  PASS

bash -n:
  cag_run_construction_disjoint_nn_baseline.sh
  cag_run_construction_disjoint_step_b2p_training.sh
  PASS

ai_dev CLI import/help:
  cag_gen_cd_step_nn_descriptor_baseline.py --help
  cag_prepare_construction_disjoint_geometry.py --help
  PASS
```

## Baseline Design

The baseline script is deliberately simple and GPU-free:

```yaml
arm: NN_DESC_TRAIN
retrieval_pool: construction-disjoint train split only
query_set: construction-disjoint test split
descriptor: global STEP descriptor from step_features JSON
distance: z-score normalized L2 by default
prediction: nearest train reference program
model_training: none
model_loading: none
```

It writes:

```text
~/workspace/MIRAGE/src/outputs/construction_disjoint_step_v1/nn_step_descriptor_train_only.jsonl
~/workspace/MIRAGE/src/outputs/construction_disjoint_step_v1/nn_step_descriptor_train_only_actuals.json
~/workspace/MIRAGE/src/outputs/construction_disjoint_step_v1/geom_input_step_NN_DESC_TRAIN.jsonl
~/workspace/MIRAGE/src/outputs/construction_disjoint_step_v1/geom_input_step_NN_DESC_TRAIN_manifest.json
```

After WSL baseline generation, gate and geometry must be run in Windows PowerShell with the commands printed by the wrapper.

## MIRAGE Retraining Guard

The MIRAGE retraining wrapper refuses to start unless:

- split actuals show sample IDs frozen and leakage audit PASS;
- train/val/test rows are 25,000 / 2,500 / 500;
- the NN descriptor baseline prediction file exists with 500 rows.

Override exists only for deliberate exceptions:

```bash
ALLOW_WITHOUT_BASELINE=1 bash training_25k/cag_run_construction_disjoint_step_b2p_training.sh
```

Do not use this override in the default plan.

## Run Order

```text
1. Run NN descriptor baseline wrapper.
2. Run Windows gate evaluation for NN_DESC_TRAIN.
3. Run Windows geometry scoring for NN_DESC_TRAIN.
4. Inspect baseline result.
5. Only then run MIRAGE construction-disjoint STEP retraining wrapper.
```
