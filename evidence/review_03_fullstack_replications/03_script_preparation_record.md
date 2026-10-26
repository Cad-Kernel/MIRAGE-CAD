> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# 03 -- Script Preparation Record: B0 vs B2 Full-Stack Seeds

Date: 2026-10-05

## Frozen Decision

```yaml
Experiment: B0 vs B2 full-stack multi-seed replication
B2 scope: strict/full-stack
Seeds: [1, 2, 3, 4]
Modality: STEP
Evaluation rows: 2500
Checkpoint rule: final
Program/code repair: false
B2 plan-stage canonicalization: P1a face/extrude alias canonicalization, logged separately
Training: NOT_STARTED
```

The replication is full-stack at the condition level: all trainable components unique to each condition are retrained independently per seed.

## Prepared Scripts

```yaml
runner:
  path: __DEV_ROOT__\src\training_25k\cag_run_b0_b2_fullstack_seed.sh
  sha256: e32ba4bdf5afff97107c966750a3a61f55426e8f54eb6a8db05f0c847c62dc55

actuals/provenance:
  path: __DEV_ROOT__\src\training_25k\cag_b0_b2_fullstack_actuals.py
  sha256: fb89241688fd1df5441eeacd2fa8c2cbdc74facdebcdb8c2c48494ca319f2b85

geometry prep:
  path: __DEV_ROOT__\src\training_25k\cag_prepare_b0_b2_seed_geometry.py
  sha256: 73a2865dec970940138309bfd8465de2c8bec84b5aaf708ead74395858991bab

soft-prefix trainer:
  path: __DEV_ROOT__\src\gen_scripts\train_soft_prefix_ir.py
  sha256: 20eea7454bed71fd405294f9e375fa7240f2e160a7a8c60b296c63dc28c473ac
  change: adds explicit --checkpoint-rule {best,final}; default remains best, Review/03 wrapper passes final
```

## Static Checks

```yaml
python_compile:
  status: PASS
  command: python -m py_compile train_soft_prefix_ir.py cag_b0_b2_fullstack_actuals.py cag_prepare_b0_b2_seed_geometry.py

bash_syntax:
  status: PASS
  command: wsl bash -n __DEV_ROOT__/src/training_25k/cag_run_b0_b2_fullstack_seed.sh

seed1_dry_run:
  status: PASS
  timestamp_utc: 2026-10-05T18:34:53
  command: DRY_RUN=1 SEED=1 bash training_25k/cag_run_b0_b2_fullstack_seed.sh
  guard_checked_scripts: 12
  data_hashes_match_frozen_25k: true
  seed_scoped_output_paths: true
  training_started: false
```

## Output Layout

For seed `s`:

```text
outputs/b0_b2_fullstack_s{s}/
  b0_lora_code_noplan_25k/
  align_25k/
  priors/
    prior_step_25k/
    prior_point_25k/
    prior_text_25k/
    prior_image_25k/
  lora_ir_25k/
  lora_ir_25k_stage3b/
  qwen25_coder_1_5b_program_25k/
  qwen25_coder_1_5b_program_25k_stage4b/
  predictions/
  cag_b0_b2_seed_{s}_preflight.json
  cag_b0_b2_seed_{s}_actuals.json

data/b0_b2_fullstack_s{s}/
  train_stage4b_mix.jsonl
```

The runner refuses seed values outside `{1,2,3,4}`, refuses seed `42`, validates the frozen 25K data hashes, and refuses partial stage directories or partial prediction files.

## Dry-Run Command

Run this first. It performs freshness guard checks, frozen data hash checks, seed/path checks, writes a preflight JSON, and exits before any training starts.

```bash
cd ~/workspace/MIRAGE/src
DRY_RUN=1 SEED=1 bash training_25k/cag_run_b0_b2_fullstack_seed.sh
```

Expected dry-run status:

```yaml
guard: PASS
data hashes: PASS
seed-scoped output paths: PASS
training started: false
```

## Seed 1 Training Command

Only run this after dry-run passes:

```bash
cd ~/workspace/MIRAGE/src
SEED=1 bash training_25k/cag_run_b0_b2_fullstack_seed.sh
```

Do not start seed 2 until seed 1 has completed:

```yaml
Training: COMPLETE
Prediction: COMPLETE
Gate evaluation: COMPLETE
Geometry scoring: COMPLETE
Seed review record: COMPLETE
```

## Gate + Geometry Commands After Seed 1 Generation

The runner prints these commands at completion. They are recorded here for convenience:

```powershell
$Root = "__RUN_SOURCE_ROOT__"

& "__DEV_ROOT__\src\scripts\evaluate_execution.ps1" `
  -InputJsonl "$Root\outputs\b0_b2_fullstack_s1\predictions\gen_step_B0_s1.jsonl" `
  -OutputDir "__DEV_ROOT__\scratch\exec_b0b2_step_B0_s1" `
  -CodeField prediction

& "__DEV_ROOT__\src\scripts\evaluate_execution.ps1" `
  -InputJsonl "$Root\outputs\b0_b2_fullstack_s1\predictions\gen_step_B2_s1.jsonl" `
  -OutputDir "__DEV_ROOT__\scratch\exec_b0b2_step_B2_s1" `
  -CodeField prediction

& "__DEV_ROOT__\src\scripts\evaluate_geometry_nbest.ps1" `
  -InputJsonl "$Root\outputs\b0_b2_fullstack_s1\predictions\geom_input_step_B0_s1.jsonl" `
  -OutputDir "__DEV_ROOT__\scratch\geom_b0b2_step_B0_s1"

& "__DEV_ROOT__\src\scripts\evaluate_geometry_nbest.ps1" `
  -InputJsonl "$Root\outputs\b0_b2_fullstack_s1\predictions\geom_input_step_B2_s1.jsonl" `
  -OutputDir "__DEV_ROOT__\scratch\geom_b0b2_step_B2_s1"
```

## Interpretation Boundary

This package will answer Reviewer 2's request for multiple random seeds on the B0 vs B2 key comparison. It should be reported as condition-level training-run variance under the deployed B2 pathway, not as a claim about external generalization.
