> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# 14 -- Seed 4 Interruption Record

Date: 2026-10-14

## Status

```yaml
Experiment: Review/03 B0 vs B2 full-stack multi-seed replication
Seed: 4
Status: INTERRUPTED
Training: PARTIAL
Prediction: NOT_STARTED
Gate evaluation: NOT_STARTED
Geometry scoring: NOT_STARTED
Seed status: NOT_CLOSED
```

## What Completed

Observed files in `outputs/b0_b2_fullstack_s4`:

```yaml
preflight:
  status: COMPLETE
  path: outputs/b0_b2_fullstack_s4/cag_b0_b2_seed_4_preflight.json
  timestamp: 2026-10-13 18:58

B0 no-plan code:
  status: COMPLETE
  output: outputs/b0_b2_fullstack_s4/b0_lora_code_noplan_25k
  training_report: outputs/b0_b2_fullstack_s4/b0_lora_code_noplan_25k/training_report.json
  timestamp: 2026-10-13 22:54
  seed: 4
  train_rows: 25000
  val_rows: 2500
  max_length: 2048
```

## Where It Stopped

The run entered B2 alignment:

```yaml
B2 alignment:
  status: PARTIAL_INTERRUPTED
  output: outputs/b0_b2_fullstack_s4/align_25k
  present_files:
    - best.pt
  missing_required_files:
    - last.pt
    - training_report.json
  log: outputs/b0_b2_fullstack_s4/align_25k.train.log
```

The last visible alignment log is still in epoch 5:

```yaml
last_visible_phase: epoch 5/5
last_visible_step: approximately 396 / 3125
last_log_timestamp: 2026-10-14 02:44
```

No active `cag_run_b0_b2`, `train_alignment`, `train_latent_prior`, `train_soft_prefix`, `train_program_lora`, `gen_predicted_ir`, or `gen_code_from` process was observed when checked after restart. This is consistent with the machine or WSL session stopping overnight.

## Interpretation

Seed 4 did start. It completed B0 no-plan training and then was interrupted during B2 alignment. Because the alignment stage lacks `last.pt` and `training_report.json`, it must not be treated as complete.

The frozen runner refuses partial stage directories. Therefore, rerunning the same command without moving or removing the partial alignment directory will stop rather than silently reuse an incomplete alignment checkpoint.

## Safe Recovery

Use a non-destructive archive/rename for the interrupted alignment directory and log, then rerun the same seed command. B0 will be kept; B2 alignment will restart cleanly.

```bash
cd ~/workspace/MIRAGE/src

mv outputs/b0_b2_fullstack_s4/align_25k \
   outputs/b0_b2_fullstack_s4/align_25k_interrupted_20261014_0244

mv outputs/b0_b2_fullstack_s4/align_25k.train.log \
   outputs/b0_b2_fullstack_s4/align_25k_interrupted_20261014_0244.train.log

SEED=4 bash training_25k/cag_run_b0_b2_fullstack_seed.sh
```

After rerun, keep the same rule: do not run seed 5 or any new experiment; close seed 4 with prediction, gate evaluation, geometry scoring, and a seed review record first.
