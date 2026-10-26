> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# 01 -- Frozen Protocol: B0 vs B2 Multi-Seed Replication

Date: 2026-10-05

## Purpose

Reviewer 2 objected that trained conditions were reported as single-seed runs and specifically asked that key comparisons, especially B1a vs B2-Pred and B0 vs B2, be repeated across multiple random seeds. The B1a/B2-Pred issue is handled in `Review/01`. This protocol freezes the B0 vs B2 replication before preparing scripts or inspecting any new results.

## Status

```yaml
Experiment: B0 vs B2 multi-seed replication
Reviewer target: R2 key comparison seed variance
Protocol: FROZEN_FULL_STACK
Training: NOT_STARTED
Prediction: NOT_STARTED
Gate evaluation: NOT_STARTED
Geometry scoring: NOT_STARTED
```

## Arms

The paper labels and local code mapping have been checked against the manuscript draft and the existing scripts:

```yaml
B0:
  paper label: Direct query -> code
  local role: trained no-plan baseline
  original script: training_25k/33_noplan_baseline.sh
  original checkpoint: outputs/lora_code_noplan_25k
  original raw prediction: outputs/noplan_baseline/gen_step_noplan.jsonl
  original repaired prediction: outputs/noplan_baseline/gen_step_noplan_repaired_p0.jsonl
  original gate output: __DEV_ROOT__\scratch\exec_noplan_step

B2:
  paper label: Generated plan -> code (MIRAGE-CAD)
  local role: deployed generated-plan pathway
  original plan checkpoint: outputs/lora_ir_25k_stage3b
  original code checkpoint: outputs/qwen25_coder_1_5b_program_25k_stage4b
  original raw prediction: outputs/qwen25_coder_1_5b_program_25k_stage4b/gen_test_step_stage3b.jsonl
  original repaired prediction: outputs/qwen25_coder_1_5b_program_25k_stage4b/gen_test_step_stage3b_repaired_p0.jsonl
  original repaired gate output: __DEV_ROOT__\scratch\exec_eval_25k_stage3b_step
  original no-repair gate output: __DEV_ROOT__\scratch\exec_norepair_25k_stage3b_step
```

B2-Pred is not the same arm as B2. B2-Pred is the exposure-matched predicted-plan diagnostic addressed in `Review/01`; B2 is the deployed generated-plan MIRAGE-CAD pathway from the main B0/B2 table.

## Frozen Controls

```yaml
Seeds:
  - 1
  - 2
  - 3
  - 4

Training source split: matched
Training row count: matched where the arm definition permits it
Validation source split: matched
Validation row count: matched
Sample-order policy: matched
Evaluation slice: fixed and identical across arms/seeds
Update budget: matched where the arm definition permits it
Seed: matched within each B0/B2 pair
Checkpoint-selection rule: final checkpoint, fixed before training
Decoding settings: fixed and matched
Program/code repair: false
B2 plan-stage canonicalization: P1a face/extrude alias canonicalization, logged separately
Evaluator:
  gate: __DEV_ROOT__\src\scripts\evaluate_execution.ps1
  geometry: __DEV_ROOT__\src\scripts\evaluate_geometry_nbest.ps1
```

Do not change the definitions of B0 and B2 merely to make their input forms superficially identical. The controlled factors are the source split, row count, sample-order policy, seed, evaluation slice, update/checkpoint rule, decoding, repair policy, and evaluators.

The replication scope is frozen as strict/full-stack B2:

```yaml
B0:
  scope: retrain all trainable components of the direct query -> code condition per seed
  components:
    - no-plan LoRA-Code

B2:
  scope: retrain all trainable components of the deployed generated-plan condition per seed
  components:
    - alignment model
    - STEP / point / text / image latent priors
    - Stage 3 LoRA-IR
    - Stage 3b LoRA-IR continuation
    - Stage 4 LoRA-Code
    - Stage 4b LoRA-Code continuation

Condition-level rule:
  all trainable components unique to each condition are retrained independently per seed
```

This measures deployed condition-level training-run variance, not only code-decoder variance.

Checkpoint selection is frozen as final. For alignment and latent priors, downstream stages use `last.pt`; for Stage 3/3b soft-prefix training, the wrapper passes `--checkpoint-rule final`. This intentionally differs from historical Stage 3/3b wrappers that restored the best eval checkpoint, because Review/03 was frozen before training with a final-checkpoint rule.

`Program/code repair: false` means no deterministic program repair is applied to B0 or B2 generated code before gate/geometry evaluation. B2 retains the deployed P1a plan-stage face/extrude alias canonicalization before code generation, and the P1a log is recorded separately for each seed.

## Metrics

Per seed and arm:

```yaml
Syntax
Execute
Build
Solid validity
STEP export
Scoreable
Conditional median CD
Conditional mean CD
Conditional median F@1
Conditional mean F@1
Unconditional mean F@1, failures as zero
Unconditional median F@1, failures as zero
Failure categories
```

Across seeds:

```yaml
Mean ± SD for coverage metrics
Mean ± SD for unconditional F@1
Per-seed deltas, B2 - B0
Paired geometry comparison where sample alignment permits
Direction consistency across seeds
```

## Interpretation Boundary

This experiment is meant to answer whether the B0 vs B2 comparison is stable across independent training seeds under controlled budgets and evaluation. It should not be used to claim broad external generalization or universal superiority of any representation.

Preferred claim form if results are consistent:

> Under matched training and evaluation settings, the B0 vs B2 comparison showed the same directional pattern across four independently trained seeds.

Preferred claim form if results are mixed:

> The B0 vs B2 comparison showed seed sensitivity; we therefore report seed-level variability rather than treating a single trained instance as method-level evidence.

## Run Policy

Run one seed at a time. For each seed:

```yaml
Training: COMPLETE
Prediction: COMPLETE
Gate evaluation: COMPLETE
Geometry scoring: COMPLETE
Seed review record: COMPLETE
```

Only after that seed is closed should the next seed begin.

## Immediate Next Step

Run seed 1 dry-run/preflight first:

```bash
cd ~/workspace/MIRAGE/src
DRY_RUN=1 SEED=1 bash training_25k/cag_run_b0_b2_fullstack_seed.sh
```

If dry-run passes, run seed 1:

```bash
cd ~/workspace/MIRAGE/src
SEED=1 bash training_25k/cag_run_b0_b2_fullstack_seed.sh
```

Do not start seed 2 until seed 1 has completed training, prediction, gate evaluation, geometry scoring, and seed registration.
