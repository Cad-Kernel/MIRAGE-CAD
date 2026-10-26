> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# 12 -- Seed 3 Generation Record

Date: 2026-10-13

## Status

```yaml
Experiment: Review/03 B0 vs B2 full-stack multi-seed replication
Seed: 3
Training: COMPLETE
Prediction: COMPLETE
Geometry input prep: COMPLETE
Gate evaluation: NOT_STARTED
Geometry scoring: NOT_STARTED
Seed status: GENERATION_COMPLETE_NEEDS_GATE_AND_GEOMETRY
```

This is not yet a closed seed. It has completed training and prediction, but the reviewer-facing result still requires gate evaluation and geometry scoring.

## Checkout / Output Paths

```yaml
Windows source checkout:
  __DEV_ROOT__\src

WSL execution checkout:
  __RUN_SOURCE_ROOT__

Review package:
  __EVIDENCE_SOURCE_ROOT__\03

Seed base:
  outputs/b0_b2_fullstack_s3

Seed data:
  data/b0_b2_fullstack_s3

Seed predictions:
  outputs/b0_b2_fullstack_s3/predictions
```

## Actuals JSON

```yaml
path: outputs/b0_b2_fullstack_s3/cag_b0_b2_seed_3_actuals.json
created_utc: 2026-10-13T00:02:52.817153+00:00
status: GENERATION_COMPLETE_NEEDS_GATE_AND_GEOMETRY
```

## Completed Outputs

```yaml
B0 prediction:
  path: outputs/b0_b2_fullstack_s3/predictions/gen_step_B0_s3.jsonl
  rows: 2500
  sha256: 0a9c6d70a396a04605100f3dd2bf5094bd8020317af5e7a33b935ed3e834bcdb

B2 prediction:
  path: outputs/b0_b2_fullstack_s3/predictions/gen_step_B2_s3.jsonl
  rows: 2500
  sha256: d50a9ff77e489ee7497b32e34385bf8f0d3e97bfe7afcc728ca3890d919434ad

B2 raw predicted IR:
  path: outputs/b0_b2_fullstack_s3/predictions/predicted_ir_test_step_raw_s3.jsonl
  rows: 2500
  sha256: a71f414c7a08987a223b78dcd5cc559fca1a0507cfeadf857bd9ec1f4813be62

B2 P1a predicted IR:
  path: outputs/b0_b2_fullstack_s3/predictions/predicted_ir_test_step_p1a_s3.jsonl
  rows: 2500
  sha256: 41813de694e213764f30b640587cb1b6982cae7cf67535821384a494838a39bb

B0 geometry input:
  path: outputs/b0_b2_fullstack_s3/predictions/geom_input_step_B0_s3.jsonl
  rows: 2500
  sha256: fb802cdb9d9d8e04d3c669faff5e8e390f893edec56c3c84fe289d789a31c911

B2 geometry input:
  path: outputs/b0_b2_fullstack_s3/predictions/geom_input_step_B2_s3.jsonl
  rows: 2500
  sha256: b95c79b831a9cae42aa5c821d1b704c3144867a00d120bfed84f5ca05154b93a

Stage4b mix:
  path: data/b0_b2_fullstack_s3/train_stage4b_mix.jsonl
  rows: 2997
  sha256: b97bfc8508f1af428346068e525b8ef0656a6a5b3b5864a5ee19e1c9bcea2f7e
```

## Training Component Summary

```yaml
B0 no-plan code:
  seed: 3
  train_rows: 25000
  val_rows: 2500
  max_length: 2048
  output_dir: outputs/b0_b2_fullstack_s3/b0_lora_code_noplan_25k

B2 Stage 3 LoRA-IR:
  seed: 3
  modalities: [step]
  train_rows: 25000
  val_rows: 2500
  checkpoint_rule: final
  output_dir: outputs/b0_b2_fullstack_s3/lora_ir_25k
  normal_loss: 0.11959809663891792
  zero_loss: 0.15309255580306053

B2 Stage 3b LoRA-IR:
  seed: 3
  modalities: [image, point, step, text]
  train_rows: 8000
  val_rows: 800
  checkpoint_rule: final
  output_dir: outputs/b0_b2_fullstack_s3/lora_ir_25k_stage3b
  normal_loss: 0.1518122836248949
  zero_loss: 0.1831063968129456

B2 Stage 4 code:
  seed: 3
  train_rows: 25000
  val_rows: 2500
  max_length: 1536
  output_dir: outputs/b0_b2_fullstack_s3/qwen25_coder_1_5b_program_25k

B2 Stage 4b code:
  seed: 3
  train_rows: 2997
  val_rows: 2500
  max_length: 1536
  output_dir: outputs/b0_b2_fullstack_s3/qwen25_coder_1_5b_program_25k_stage4b
```

## Analysis

Seed 3 has successfully reached the evaluation stage. Both B0 and B2 produced exactly 2500 STEP predictions on the same frozen test slice, and both geometry input files have exactly 2500 rows. The actuals file records the frozen data hashes, script hashes, prediction hashes, and stage summaries.

At this point, no B0/B2 performance conclusion should be drawn yet. The next required evidence is gate evaluation and geometry scoring.

## Next Commands

Run these in Windows PowerShell:

```powershell
$Root = "__RUN_SOURCE_ROOT__"

& "__DEV_ROOT__\src\scripts\evaluate_execution.ps1" `
  -InputJsonl "$Root\outputs\b0_b2_fullstack_s3\predictions\gen_step_B0_s3.jsonl" `
  -OutputDir "__DEV_ROOT__\scratch\exec_b0b2_step_B0_s3" `
  -CodeField prediction

& "__DEV_ROOT__\src\scripts\evaluate_execution.ps1" `
  -InputJsonl "$Root\outputs\b0_b2_fullstack_s3\predictions\gen_step_B2_s3.jsonl" `
  -OutputDir "__DEV_ROOT__\scratch\exec_b0b2_step_B2_s3" `
  -CodeField prediction

& "__DEV_ROOT__\src\scripts\evaluate_geometry_nbest.ps1" `
  -InputJsonl "$Root\outputs\b0_b2_fullstack_s3\predictions\geom_input_step_B0_s3.jsonl" `
  -OutputDir "__DEV_ROOT__\scratch\geom_b0b2_step_B0_s3"

& "__DEV_ROOT__\src\scripts\evaluate_geometry_nbest.ps1" `
  -InputJsonl "$Root\outputs\b0_b2_fullstack_s3\predictions\geom_input_step_B2_s3.jsonl" `
  -OutputDir "__DEV_ROOT__\scratch\geom_b0b2_step_B2_s3"
```

Do not start seed 4 before seed 3 gate and geometry are complete and registered.
