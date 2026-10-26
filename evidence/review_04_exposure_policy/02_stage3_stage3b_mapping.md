> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Stage 3 / Stage 3b Exact Mapping

Audit date: 2026-10-16. No new training or inference was run.

Windows source: `__DEV_ROOT__\src`.

WSL training source: `__RUN_SOURCE_ROOT__`.

All relative paths below resolve under the WSL training source. The complete hash/metadata snapshot is `03_stage_mapping_actuals.json`.

## Reviewer Requirement

Reviewer 2 comment 3 asks for a clearer justification of STEP-first followed by four-modality continuation and discussion of whether balanced training from the outset could materially change behavior. It identifies a confound between architecture and the deployed curriculum. It does not specifically require a four-seed curriculum experiment.

Source: `__EVIDENCE_SOURCE_ROOT__\reviews.txt`.

## Historical Training Stages

| Stage | Entry Point | Training Examples | Validation Examples | Epochs | Accumulation | Recorded Final Updates | LR |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Stage 3 | training_25k/06_train_lora_ir.sh | 25000 STEP | 2500 STEP | 3 | 16 | 4689 | 2e-4 |
| Stage 3b | training_25k/06b_train_lora_ir_stage3b.sh | 8000 mixed | 800 mixed | 1 | 16 | 500 | 1e-5 |
| Stage 4 | training_25k/09_train_lora_code_stage4.sh | 25000 GT-plan code | 2500 | 1 | 8 | 3125 | 2e-4 |
| Stage 4b | training_25k/10_train_lora_code_stage4b.sh | 3147 mixed-plan code | 2500 | 3 | 8 | 1182 | 5e-5 |

All these stages use per-device batch size 1 on the single-device recipe. Stage 3/3b use prefix length 4, plan LoRA rank 8 / alpha 16, max_length 1536, and Qwen/Qwen2.5-Coder-1.5B. Code LoRA uses rank 16 / alpha 32.

Stage 3's custom `checkpoint-4689/trainer_state.json` records `{step: 4689, eval_loss: 0.12318836897611618}`. Stage 3b's checkpoint-500 records `{step: 500, eval_loss: 0.15475434064865112}`. These custom files are not full HF optimizer/RNG resume states. Stage 4/4b have standard trainer states confirming global_step/max_steps of 3125 and 1182.

Plan budget: **4689 + 500 = 5189 optimizer updates**. Assuming all source examples were retained, historical row presentations are 75000 + 8000 = 83000; partial accumulation groups make this different from 5189 * 16 = 83024. Do not equate optimizer updates, unique source rows, modality cases, example presentations, and token counts.

The historical Stage 3 root lacks `soft_prefix_training_report.json`. Its reported original configuration is supported by the wrapper, saved adapter config, and custom checkpoint step metadata, rather than a complete root training report.

## Actual Stage 3b Mixture

In `gen_scripts/train_soft_prefix_ir.py`:

1. Read `data/25k/train.jsonl` and keep `rows[:2000]`; read validation and keep `rows[:200]`.
2. Build one example per retained source sample for each supplied modality/prior.
3. Concatenate the modality blocks. The historical CLI order is STEP, point, text, image; the printed `modalities` report sorts labels, but that report order is not the concatenation order.
4. Trainer shuffles the concatenated training dataset.

The completed report has 8000 training and 800 validation examples, consistent with all 2000/200 source rows surviving for all four modalities. Therefore dataset-level proportions are 25% each. There is no dedicated sampler enforcing four examples of each modality in every accumulation group.

`build_examples` currently catches encoding errors and skips rows, and also skips empty targets. A new control must count and audit materialized cases before training; it cannot assume balanced counts remain true after skipped records.

Latents are precomputed before plan training. The fixed upstream checkpoints are not optimized by the plan trainer. For point training, sampled points also populate the prompt evidence block.

## Stage Boundary And Initialization

Stage 3b loads both Stage 3's LoRA and prefix through `--init-lora-ir-dir`, but creates a fresh Trainer/optimizer/scheduler. Thus the original curriculum also includes an optimizer-state reset, a new warmup/decay schedule, and LR reduction from 2e-4 to 1e-5.

To vary exposure policy cleanly, both new arms must make the same reset after 4689 updates and use the same 500-update second-phase schedule. Balanced-from-start should therefore mean balanced data in both phases, not removal of the optimizer/LR boundary.

A common seed alone is insufficient to prove identical fresh LoRA/prefix initialization: modality-specific preprocessing can consume RNG state before initialization. Save one common initial adapter/prefix pair and verify identical hashes when both arms start.

## Historical Arm A Reuse Audit

Current on-disk contents of `outputs/lora_ir_25k`:

```yaml
Root LoRA SHA256: 007cd8fb805453b98efe004935ea6a4617631e9bcd5be0ab1496ef1f5079c9a0
Checkpoint-4689 LoRA SHA256: 007cd8fb805453b98efe004935ea6a4617631e9bcd5be0ab1496ef1f5079c9a0
Root prefix SHA256: bbbce7031554067f21a01f0a3c610450dd3042bb51a73e0dee7ab84b1c9d2d83
Checkpoint-4500 prefix SHA256: bbbce7031554067f21a01f0a3c610450dd3042bb51a73e0dee7ab84b1c9d2d83
Checkpoint-4689 prefix SHA256: 84dbf85f45341bc82ef1cbfb97decf6648ff3e6f6c51517367ba3d0172a48e81
```

CPU tensor comparison confirms all six root-prefix tensors equal checkpoint-4500; all six differ from checkpoint-4689. The root LoRA file is byte-identical to checkpoint-4689. Therefore the current root is not a uniform final-step adapter/prefix pair.

Stage 3b's current root matches its checkpoint-500 LoRA and prefix, but its recorded initialization path is the historical Stage 3 root. Its report omits explicit seed and checkpoint-rule fields. The inspection does not establish when the Stage 3 root combination arose or exactly what files Stage 3b saw at its historical training time.

**Decision: do not reuse the original Stage 3/3b root as the strict new Arm A.** Keep it as historical context and retrain both new plan arms from a common saved initialization. This observation concerns the historical unsuffixed directories; it does not alter the separately trained and audited Review/03 seed-specific checkpoints.

## Reusable Shared Components

The following original checkpoints exist and can be fixed constants for both new arms:

```text
outputs/align_25k/best.pt
outputs/prior_step_25k/best.pt
outputs/prior_point_25k/best.pt
outputs/prior_text_25k/best.pt
outputs/prior_image_25k/best.pt
outputs/qwen25_coder_1_5b_program_25k
```

Upstream reports record seed 42. Prior reports identify `outputs/align_25k/best.pt` as their alignment input. The common Stage 4 code decoder records seed 42 in `training_args.bin`, has final trainer_state global_step 3125, and does not use best-model-at-end selection. Current file hashes are included in the machine snapshot.

Shared upstream checkpoints can be historical best checkpoints because they are fixed constants, not selected separately by arm. The final-checkpoint rule applies to newly trained plan components and Stage 4b adaptations. Do not silently substitute last.pt for one arm's shared best.pt.

## Historical Stage 4b Mixture

`training_25k/07_gen_predicted_ir_train_subset.sh` generates raw STEP predicted plans from the first 1000 training rows using the Stage 3 model, not Stage 3b. `build_stage4b_mix.py` then:

- Filters predicted rows by grammar validity.
- Keeps 944 valid predicted plans in the historical dataset.
- Samples 2203 GT-plan rows excluding those predicted IDs.
- Shuffles 3147 rows using seed 42, approximating a 30% predicted / 70% GT ratio.

The historical Stage 3b evaluation reused the same old Stage 4b decoder; it did not regenerate that decoder's training mix after Stage 3b.

For the new control, each final plan arm should produce its own train-only predicted plans and its own Stage 4b adapter, both initialized from the same Stage 4 checkpoint. Do not reuse the historical grammar-filtering builder unchanged: each arm would retain different IDs/counts and could receive a different optimizer budget.

The draft proposes a fixed role manifest of 945 predicted-plan IDs + 2205 GT-plan IDs = 3150 rows. Both arms keep those roles/IDs even when a predicted plan is invalid or empty, while logging those failures. This preserves an exact 30/70 ratio and supports 1182 updates under the current three-epoch, accumulation-8 recipe. This is a proposed controlled adaptation, not the historical 3147-row dataset.

## Historical Four-Modality Evaluation Files

All four modalities use the same 2500 IDs/order from `data/25k/test.jsonl`.

| Modality | Raw Stage 3b Plan | Raw Program |
| --- | --- | --- |
| STEP | outputs/lora_ir_25k_stage3b/predicted_ir_test_step.jsonl | outputs/qwen25_coder_1_5b_program_25k_stage4b/gen_test_step_stage3b.jsonl |
| Point | outputs/lora_ir_25k_stage3b/predicted_ir_test_point.jsonl | outputs/qwen25_coder_1_5b_program_25k_stage4b/gen_test_point_stage3b.jsonl |
| Text | outputs/lora_ir_25k_stage3b/predicted_ir_test_text.jsonl | outputs/qwen25_coder_1_5b_program_25k_stage4b/gen_test_text_stage3b.jsonl |
| Image | outputs/lora_ir_25k_stage3b/predicted_ir_test_image.jsonl | outputs/qwen25_coder_1_5b_program_25k_stage4b/gen_test_image_stage3b.jsonl |

All eight files were checked for 2500 rows and exact test-ID order. The old formal code files with `_repaired_p0` suffix also exist and are recorded separately in the snapshot. They cannot substitute for fresh no-code-repair outputs of the new control.

The original pipeline applies P1a plan canonicalization before code decoding, then two program repair passes. New control settings must name the plan and program policies separately. The draft retains P1a in both arms and disables program repair.

The historical point plan generator defaults to `--point-evidence off`, while point training includes an evidence block. Keep this setting identical across both new arms and disclose it; do not fold an evidence-channel fix into the curriculum comparison.

## Scientific Scope

Balanced-from-start changes cumulative modality exposure as well as when exposure occurs. With STEP-first, most of the budget is STEP; with 25% from the start, each modality gets a larger non-STEP exposure share. Equal updates and equal total presentations do not make the marginal modality counts equal.

Name the experiment a **training exposure-policy diagnostic**. A pure order-only control would need to permute an identical sample/modality multiset, whose heavily STEP-weighted marginal distribution would no longer be balanced 25/25/25/25. No third arm is proposed here.
