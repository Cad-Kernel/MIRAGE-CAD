> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# 02 -- B0/B2 Label-to-Code Mapping

Date: 2026-10-05

## Status

```yaml
Paper labels mapped to local code: COMPLETE
Original output paths identified: COMPLETE
Original B0/B2 results checked: COMPLETE
Training wrapper: NOT_PREPARED
Training: NOT_STARTED
```

## Paper Mapping

The manuscript draft defines the B0/B2 comparison as:

```yaml
B0:
  configuration: Direct query -> code
  construction_conditioning: none
  explicit_plan: no
  training_control: Stage 4 pathway

B2:
  configuration: Generated plan -> code (MIRAGE-CAD)
  construction_conditioning: latent, then generated plan
  explicit_plan: yes, generated
  training_control: deployed Stage 4 + 4b
```

The same draft states that the results sections also use an execution-condition naming system:

```yaml
B2: C3 in the E1 / observation-bypass naming system
B2-Pred: exposure-matched predicted-plan diagnostic, not the same as B2
B1a: A1E in the E1 naming system
```

Therefore, `Review/03` should compare:

```yaml
B0: trained no-plan baseline
B2: deployed generated-plan MIRAGE-CAD pathway
```

It should not compare B0 against B2-Pred. B2-Pred has already been handled by the A1E/B2P four-seed package in `Review/01`.

## Original B0 Local Mapping

```yaml
script: training_25k/33_noplan_baseline.sh
script_sha256: 6ab1e4f2e771f2589043b220c9a0d4b883888fae63d299bf10f20b7accf89edd
checkpoint: outputs/lora_code_noplan_25k
training_report: outputs/lora_code_noplan_25k/training_report.json
raw_prediction: outputs/noplan_baseline/gen_step_noplan.jsonl
raw_prediction_rows: 2500
raw_prediction_sha256: 04c86a82936264ea1bd2a9df0273d6c210a8d70a943748a5fe67e0f94d1c4db3
repaired_prediction: outputs/noplan_baseline/gen_step_noplan_repaired_p0.jsonl
repaired_prediction_rows: 2500
repaired_prediction_sha256: 56db2bb99a1548bab39482d22280347e743d5436560c9e3fbae7e4e8cb322cdf
original_gate_output: __DEV_ROOT__\scratch\exec_noplan_step
original_repair_applied: true
```

Original B0 training report:

```yaml
model_name: Qwen/Qwen2.5-Coder-1.5B
target: program
train_rows: 25000
val_rows: 2500
max_length: 2048
output_dir: outputs/lora_code_noplan_25k
```

Original B0 gate result:

```yaml
rows: 2500
syntax_ok: 2440 / 2500 = 97.6%
build_ok: 886 / 2500 = 35.44%
step_export_ok: 864 / 2500 = 34.56%
```

## Original B2 Local Mapping

The B2 row in the manuscript is the deployed generated-plan pathway. The specific result matching the 70.0% Build / 66.2% STEP-export row uses Stage 3b plan generation plus the Stage 4b code decoder, with code repair applied.

```yaml
plan_checkpoint: outputs/lora_ir_25k_stage3b
code_checkpoint: outputs/qwen25_coder_1_5b_program_25k_stage4b
stage3b_script: training_25k/scripts/run_full_stage3b_pipeline.sh
stage3b_script_sha256: 6bbb2f5ab7f188594582d8a66ad7d918465052a016f693ba5c770db0c6c81c5c
stage4_script: training_25k/09_train_lora_code_stage4.sh
stage4_script_sha256: e2ba1f28b89b6d29aecabce198c0b53bca410ae768766b0354f88903a053d934
stage4b_script: training_25k/10_train_lora_code_stage4b.sh
stage4b_script_sha256: ebaa047c270ea805b91738c52ebcf76251d542c0d3710a2023727e6e5b846ff0
stage3b_train_script: training_25k/06b_train_lora_ir_stage3b.sh
stage3b_train_script_sha256: 72e6a9bbaa6f3e1677522d840614f26f0642fb6c5962bd9812d3cf9f69228761
raw_prediction: outputs/qwen25_coder_1_5b_program_25k_stage4b/gen_test_step_stage3b.jsonl
raw_prediction_rows: 2500
raw_prediction_sha256: 4b48a8706d0c5a82c387b24523c5e0bce5f56993733945735d751f3f18c1855d
repaired_prediction: outputs/qwen25_coder_1_5b_program_25k_stage4b/gen_test_step_stage3b_repaired_p0.jsonl
repaired_prediction_rows: 2500
repaired_prediction_sha256: 23e362bb8bff75fb6caaea0d1d44a7f6c1b636a85d092fe00ae28c29413ba72b
original_repaired_gate_output: __DEV_ROOT__\scratch\exec_eval_25k_stage3b_step
original_no_repair_gate_output: __DEV_ROOT__\scratch\exec_norepair_25k_stage3b_step
```

Original B2 training reports:

```yaml
Stage3b LoRA-IR:
  model_name: Qwen/Qwen2.5-Coder-1.5B
  modalities: [image, point, step, text]
  init_lora_ir_dir: outputs/lora_ir_25k
  train_rows: 8000
  val_rows: 800
  prefix_len: 4
  max_length: 1536
  output_dir: outputs/lora_ir_25k_stage3b

Stage4 code decoder:
  model_name: Qwen/Qwen2.5-Coder-1.5B
  target: program
  train_rows: 25000
  val_rows: 2500
  max_length: 1536
  output_dir: outputs/qwen25_coder_1_5b_program_25k

Stage4b code decoder:
  model_name: Qwen/Qwen2.5-Coder-1.5B
  target: program
  train_rows: 3147
  val_rows: 2500
  max_length: 1536
  output_dir: outputs/qwen25_coder_1_5b_program_25k_stage4b
```

Original B2 repaired gate result:

```yaml
rows: 2500
syntax_ok: 2363 / 2500 = 94.52%
build_ok: 1749 / 2500 = 69.96%
step_export_ok: 1654 / 2500 = 66.16%
```

Original B2 no-repair gate result:

```yaml
rows: 2500
syntax_ok: 2363 / 2500 = 94.52%
build_ok: 1742 / 2500 = 69.68%
step_export_ok: 1647 / 2500 = 65.88%
```

## Shared Data

```yaml
train_jsonl: data/25k/train.jsonl
train_rows: 25000
train_sha256: 991e0a6d811b5927d9316fed50c7cc09472719af1726b8c92017c3fbb86906ca

val_jsonl: data/25k/val.jsonl
val_rows: 2500
val_sha256: 4b76f8fec86f8fac7fbb9635542a924ccf3b91893115639d13ed79ada374a021

test_jsonl: data/25k/test.jsonl
test_rows: 2500
test_sha256: 248a032248d0d9e20b4474ee8adb705d74968a443b534cf51d96601eba0a019e

stage4b_mix_jsonl: data/25k/train_stage4b_mix.jsonl
stage4b_mix_rows: 3147
stage4b_mix_sha256: 50450a75e20bf056fbc3aaa1542c316ffefaa66f0d7c9182358a9bad1a459fe2
```

## Replication Boundary Requiring Validation

There is no label ambiguity left: B0 and B2 are mapped. The remaining decision is the scope of what gets retrained for each seed.

```yaml
Option A -- strict/full-stack B2:
  B0: retrain the no-plan direct query-to-code model per seed
  B2: retrain the generated-plan pathway per seed, including the plan-generation components and code decoder
  strength: strongest answer to Reviewer 2 because it measures full B2 training-run variation
  cost: highest

Option B -- decoder-level B2:
  B0: retrain the no-plan direct query-to-code model per seed
  B2: reuse fixed upstream predicted plans / plan checkpoint and retrain only the generated-plan code decoder per seed
  strength: weaker; measures code-decoder variation, not full B2 pathway variation
  cost: lower
```

Recommendation: use Option A if computationally feasible. If Option B is chosen, the response must explicitly say that the replication estimates the code-decoder component of B2 rather than the full generated-plan pathway.

## Protocol Consequence

The validated `Review/03` protocol requests `repair=false`. Therefore the new multi-seed replication should be described as a controlled no-repair seed replication. It should not be described as a literal rerun of the original repaired Table 2 numbers, although the original repaired and no-repair B2 results differ only slightly in Build/STEP export.
