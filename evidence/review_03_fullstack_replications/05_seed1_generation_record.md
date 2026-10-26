> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# 05 -- Seed 1 Generation Record

Date: 2026-10-08

## Status

```yaml
Experiment: Review/03 B0 vs B2 full-stack multi-seed replication
Seed: 1
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
  outputs/b0_b2_fullstack_s1

Seed data:
  data/b0_b2_fullstack_s1

Seed predictions:
  outputs/b0_b2_fullstack_s1/predictions
```

## Protocol Snapshot

```yaml
B0 scope: full retrain of direct query -> code no-plan condition
B2 scope: full retrain of deployed generated-plan pathway components
B2 plan-stage canonicalization: P1a face/extrude alias canonicalization before code generation
Checkpoint selection: final
Evaluation slice: data/25k/test.jsonl, first 2500 STEP rows
Program/code repair: false
Run policy: one seed fully closed before the next
```

## Actuals JSON

```yaml
path: outputs/b0_b2_fullstack_s1/cag_b0_b2_seed_1_actuals.json
created_utc: 2026-10-08T00:57:27.580814+00:00
status: GENERATION_COMPLETE_NEEDS_GATE_AND_GEOMETRY
```

Frozen data hashes recorded in the actuals:

```yaml
train_jsonl:
  path: data/25k/train.jsonl
  rows: 25000
  sha256: 991e0a6d811b5927d9316fed50c7cc09472719af1726b8c92017c3fbb86906ca

val_jsonl:
  path: data/25k/val.jsonl
  rows: 2500
  sha256: 4b76f8fec86f8fac7fbb9635542a924ccf3b91893115639d13ed79ada374a021

test_jsonl:
  path: data/25k/test.jsonl
  rows: 2500
  sha256: 248a032248d0d9e20b4474ee8adb705d74968a443b534cf51d96601eba0a019e
```

## Completed Outputs

```yaml
B0 prediction:
  path: outputs/b0_b2_fullstack_s1/predictions/gen_step_B0_s1.jsonl
  rows: 2500
  sha256: 513d069742ae7758861d173de74e5a99046e934828760828bcf160aa3e89f132

B2 prediction:
  path: outputs/b0_b2_fullstack_s1/predictions/gen_step_B2_s1.jsonl
  rows: 2500
  sha256: 4c0c070a6a82e927011332aa4dd412da9e2aa7c486729f0fb07fdda7b0b3e034

B2 raw predicted IR:
  path: outputs/b0_b2_fullstack_s1/predictions/predicted_ir_test_step_raw_s1.jsonl
  rows: 2500
  sha256: 1e3f6c6641053a9a0eccc9131c120ef6ec5c434bf501c89002a73792a14fd314

B2 P1a predicted IR:
  path: outputs/b0_b2_fullstack_s1/predictions/predicted_ir_test_step_p1a_s1.jsonl
  rows: 2500
  sha256: 1cf84358583b3d40dfee6febf35bf003c79b0b747b3fac0255413139ff8c4faf

B0 geometry input:
  path: outputs/b0_b2_fullstack_s1/predictions/geom_input_step_B0_s1.jsonl
  rows: 2500
  sha256: 1fdb5f7944a2d5ed8b4ebf13dc09d1134251a5392f417f1be29069ab9c0c2b49

B2 geometry input:
  path: outputs/b0_b2_fullstack_s1/predictions/geom_input_step_B2_s1.jsonl
  rows: 2500
  sha256: b56c88b213bcc7de8c9e1a27117fa3040378182269786ad7034e6bf685fb60a8

Stage4b mix:
  path: data/b0_b2_fullstack_s1/train_stage4b_mix.jsonl
  rows: 2987
  sha256: d36e149e2c9a25edc53706801cfaebd5ad545c2106a8bfd4927a082982102938
```

## Training Component Summary

```yaml
B0 no-plan code:
  seed: 1
  train_rows: 25000
  val_rows: 2500
  max_length: 2048
  output_dir: outputs/b0_b2_fullstack_s1/b0_lora_code_noplan_25k

B2 Stage 3 LoRA-IR:
  seed: 1
  modalities: [step]
  train_rows: 25000
  val_rows: 2500
  checkpoint_rule: final
  output_dir: outputs/b0_b2_fullstack_s1/lora_ir_25k
  normal_loss: 0.13016091337352992
  zero_loss: 0.17053889555633067

B2 Stage 3b LoRA-IR:
  seed: 1
  modalities: [image, point, step, text]
  train_rows: 8000
  val_rows: 800
  checkpoint_rule: final
  output_dir: outputs/b0_b2_fullstack_s1/lora_ir_25k_stage3b
  normal_loss: 0.16000322344247253
  zero_loss: 0.19258627672679723

B2 Stage 4 code:
  seed: 1
  train_rows: 25000
  val_rows: 2500
  max_length: 1536
  output_dir: outputs/b0_b2_fullstack_s1/qwen25_coder_1_5b_program_25k

B2 Stage 4b code:
  seed: 1
  train_rows: 2987
  val_rows: 2500
  max_length: 1536
  output_dir: outputs/b0_b2_fullstack_s1/qwen25_coder_1_5b_program_25k_stage4b
```

## Analysis

Seed 1 has successfully reached the point where the controlled B0/B2 comparison can be evaluated. The important checks are clean: both B0 and B2 produced exactly 2500 STEP predictions on the same frozen test slice, both geometry input files have exactly 2500 rows, and the actuals file records the frozen data hashes and script hashes.

At this stage, the result is a pipeline-completion result, not a performance result. We should not interpret B0 vs B2 until the gate and geometry runs finish. The next evidence needed is:

```yaml
Gate:
  syntax
  execute
  build
  solid validity
  STEP export

Geometry:
  scoreable count
  conditional CD / F@1
  unconditional F@1
  paired B0 vs B2 geometry where jointly scoreable
```

## Next Commands

Run these in Windows PowerShell:

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

Do not start seed 2 before seed 1 gate and geometry are complete and registered.
