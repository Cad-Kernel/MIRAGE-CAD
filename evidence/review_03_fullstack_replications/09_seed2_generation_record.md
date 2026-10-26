> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# 09 -- Seed 2 Generation Record

Date: 2026-10-11

## Status

```yaml
Experiment: Review/03 B0 vs B2 full-stack multi-seed replication
Seed: 2
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
  outputs/b0_b2_fullstack_s2

Seed data:
  data/b0_b2_fullstack_s2

Seed predictions:
  outputs/b0_b2_fullstack_s2/predictions
```

## Actuals JSON

```yaml
path: outputs/b0_b2_fullstack_s2/cag_b0_b2_seed_2_actuals.json
created_utc: 2026-10-11T02:55:26.534053+00:00
status: GENERATION_COMPLETE_NEEDS_GATE_AND_GEOMETRY
```

## Completed Outputs

```yaml
B0 prediction:
  path: outputs/b0_b2_fullstack_s2/predictions/gen_step_B0_s2.jsonl
  rows: 2500
  sha256: 8ad1a5d5f88f911b2728c51399080ff2de06cc35555e4b8c09ba6e50cd72a52d

B2 prediction:
  path: outputs/b0_b2_fullstack_s2/predictions/gen_step_B2_s2.jsonl
  rows: 2500
  sha256: a18fd8f25344ba649aa4bc1fcd3e579d786ef6b97f58846c0e8ae84d9aa9b354

B2 raw predicted IR:
  path: outputs/b0_b2_fullstack_s2/predictions/predicted_ir_test_step_raw_s2.jsonl
  rows: 2500
  sha256: 82f14433336aa5f2b1f6a32ece647b3aad09ce831defb3a027cd479f10f3796e

B2 P1a predicted IR:
  path: outputs/b0_b2_fullstack_s2/predictions/predicted_ir_test_step_p1a_s2.jsonl
  rows: 2500
  sha256: 7d8b302e76baa20825748d78f8160075b778e1e2831b869d52eba386a5545625

B0 geometry input:
  path: outputs/b0_b2_fullstack_s2/predictions/geom_input_step_B0_s2.jsonl
  rows: 2500
  sha256: 1cd13a44a46a6436a231b8f0131182a9f82ced64213bb609c8885219f4c754d0

B2 geometry input:
  path: outputs/b0_b2_fullstack_s2/predictions/geom_input_step_B2_s2.jsonl
  rows: 2500
  sha256: 7b48b716ac7e88b3f3c524997d1df546937edc1e40545a1e5384dd507f70e114

Stage4b mix:
  path: data/b0_b2_fullstack_s2/train_stage4b_mix.jsonl
  rows: 3103
  sha256: bd98739deb1419a9db38a239dc93de592b5e127fd63e2ed3b9de6d6b11e5351c
```

## Training Component Summary

```yaml
B0 no-plan code:
  seed: 2
  train_rows: 25000
  val_rows: 2500
  max_length: 2048
  output_dir: outputs/b0_b2_fullstack_s2/b0_lora_code_noplan_25k

B2 Stage 3 LoRA-IR:
  seed: 2
  modalities: [step]
  train_rows: 25000
  val_rows: 2500
  checkpoint_rule: final
  output_dir: outputs/b0_b2_fullstack_s2/lora_ir_25k
  normal_loss: 0.12681951635479927
  zero_loss: 0.1514305301308632

B2 Stage 3b LoRA-IR:
  seed: 2
  modalities: [image, point, step, text]
  train_rows: 8000
  val_rows: 800
  checkpoint_rule: final
  output_dir: outputs/b0_b2_fullstack_s2/lora_ir_25k_stage3b
  normal_loss: 0.15793860465753823
  zero_loss: 0.18006616216618568

B2 Stage 4 code:
  seed: 2
  train_rows: 25000
  val_rows: 2500
  max_length: 1536
  output_dir: outputs/b0_b2_fullstack_s2/qwen25_coder_1_5b_program_25k

B2 Stage 4b code:
  seed: 2
  train_rows: 3103
  val_rows: 2500
  max_length: 1536
  output_dir: outputs/b0_b2_fullstack_s2/qwen25_coder_1_5b_program_25k_stage4b
```

## Analysis

Seed 2 has successfully reached the evaluation stage. Both B0 and B2 produced exactly 2500 STEP predictions on the same frozen test slice, and both geometry input files have exactly 2500 rows. The actuals file records the frozen data hashes, script hashes, prediction hashes, and stage summaries.

At this point, no B0/B2 performance conclusion should be drawn yet. The next required evidence is gate evaluation and geometry scoring.

## Next Commands

Run these in Windows PowerShell:

```powershell
$Root = "__RUN_SOURCE_ROOT__"

& "__DEV_ROOT__\src\scripts\evaluate_execution.ps1" `
  -InputJsonl "$Root\outputs\b0_b2_fullstack_s2\predictions\gen_step_B0_s2.jsonl" `
  -OutputDir "__DEV_ROOT__\scratch\exec_b0b2_step_B0_s2" `
  -CodeField prediction

& "__DEV_ROOT__\src\scripts\evaluate_execution.ps1" `
  -InputJsonl "$Root\outputs\b0_b2_fullstack_s2\predictions\gen_step_B2_s2.jsonl" `
  -OutputDir "__DEV_ROOT__\scratch\exec_b0b2_step_B2_s2" `
  -CodeField prediction

& "__DEV_ROOT__\src\scripts\evaluate_geometry_nbest.ps1" `
  -InputJsonl "$Root\outputs\b0_b2_fullstack_s2\predictions\geom_input_step_B0_s2.jsonl" `
  -OutputDir "__DEV_ROOT__\scratch\geom_b0b2_step_B0_s2"

& "__DEV_ROOT__\src\scripts\evaluate_geometry_nbest.ps1" `
  -InputJsonl "$Root\outputs\b0_b2_fullstack_s2\predictions\geom_input_step_B2_s2.jsonl" `
  -OutputDir "__DEV_ROOT__\scratch\geom_b0b2_step_B2_s2"
```

Do not start seed 3 before seed 2 gate and geometry are complete and registered.
