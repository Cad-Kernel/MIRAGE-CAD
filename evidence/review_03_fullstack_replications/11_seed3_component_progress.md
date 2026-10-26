> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# 11 -- Seed 3 Component Progress Record

Date: 2026-10-11

## Status

```yaml
Experiment: Review/03 B0 vs B2 full-stack multi-seed replication
Seed: 3
Status: PARTIAL_PROGRESS
Training: IN_PROGRESS
Prediction: NOT_STARTED
Gate evaluation: NOT_STARTED
Geometry scoring: NOT_STARTED
Seed status: NOT_CLOSED
```

Observed completed components in `outputs/b0_b2_fullstack_s3`:

```yaml
B0 no-plan code model:
  status: COMPLETE
  output: outputs/b0_b2_fullstack_s3/b0_lora_code_noplan_25k
  training_report: outputs/b0_b2_fullstack_s3/b0_lora_code_noplan_25k/training_report.json
  report_sha256: c190056625c58331b43ce2bd0e0bbaeb23cf95ba97aa24f16db36c4cd3626737

B2 alignment:
  status: COMPLETE
  output: outputs/b0_b2_fullstack_s3/align_25k
  training_report: outputs/b0_b2_fullstack_s3/align_25k/training_report.json
  report_sha256: 4e4b6d5f7cec4a1c36db5077201ef816edb190f6e2fda1c2833300ed887c082e

B2 STEP latent prior:
  status: COMPLETE
  output: outputs/b0_b2_fullstack_s3/priors/prior_step_25k
  training_report: outputs/b0_b2_fullstack_s3/priors/prior_step_25k/training_report.json
  report_sha256: 7831844dbf81e33e44800fd747e397685e0d03edecc4ac857260bb6402a72e40
  best_pt_sha256: 39ccbca85c3f4818ea711e364e0dbf9afa92611fe35fcfc2d07e4ee411d5b48c
  last_pt_sha256: 4b3403eff2618ef31a2ae69e4681dfee696bb134cdcc363b86b008fe85a9c4b9
```

Not yet observed in checkout:

```yaml
B2 point prior: NOT_STARTED_OR_NOT_PRESENT
B2 text prior: NOT_STARTED_OR_NOT_PRESENT
B2 image prior: NOT_STARTED_OR_NOT_PRESENT
B2 Stage 3 LoRA-IR: NOT_STARTED_OR_NOT_PRESENT
B2 Stage 4b train-subset predicted IR: NOT_STARTED_OR_NOT_PRESENT
B2 Stage 4b mix: NOT_STARTED_OR_NOT_PRESENT
B2 Stage 3b LoRA-IR: NOT_STARTED_OR_NOT_PRESENT
B2 Stage 4 code decoder: NOT_STARTED_OR_NOT_PRESENT
B2 Stage 4b code decoder: NOT_STARTED_OR_NOT_PRESENT
B0/B2 predictions: NOT_STARTED_OR_NOT_PRESENT
```

## STEP Prior Result

The completed component is the B2 STEP latent prior trained with:

```yaml
alignment_checkpoint: outputs/b0_b2_fullstack_s3/align_25k/last.pt
train_jsonl: data/25k/train.jsonl
val_jsonl: data/25k/val.jsonl
output_dir: outputs/b0_b2_fullstack_s3/priors/prior_step_25k
modality: step
epochs: 8
batch_size: 48
learning_rate: 0.0001
temperature: 0.07
lambda_l2: 1.0
lambda_cos: 1.0
lambda_nce: 1.0
seed: 3
```

Final epoch metrics:

```yaml
epoch: 8
step: 4168
loss: 0.30045414730063025
l2: 0.00019075085693434372
cosine: 0.04883216855660925
nce: 0.25143122977801197

direct_median_rank: 1.0
direct_mrr: 0.8195372966100585
direct_r@1: 0.6863207704616043
direct_r@5: 0.990959125869679
direct_r@10: 0.9996069186138656

pred_median_rank: 1.0
pred_mrr: 0.9660312061039906
pred_r@1: 0.9339622821447984
pred_r@5: 1.0
pred_r@10: 1.0
```

Validation loss by epoch:

```yaml
epoch_1_loss: 0.4348918854627969
epoch_2_loss: 0.37315678160707905
epoch_3_loss: 0.34774526180523746
epoch_4_loss: 0.3274212171727756
epoch_5_loss: 0.3212372728816743
epoch_6_loss: 0.3145981220141897
epoch_7_loss: 0.3017681803343431
epoch_8_loss: 0.30045414730063025
```

## Analysis

This STEP-prior component is healthy. The validation loss decreases monotonically across all eight epochs, and the final epoch is the best observed validation loss under the frozen final-checkpoint rule. The learned prior substantially improves retrieval over the direct STEP embedding: R@1 rises from `68.63%` direct to `93.40%` predicted, and MRR rises from `0.8195` to `0.9660`.

This is a strong upstream component result for seed 3, but it is not an end-to-end B0/B2 result. The reviewer-facing seed-3 comparison still requires the remaining B2 components, predictions, gate evaluation, and geometry scoring.

## Continue Command

To continue seed 3 from the current partial state, rerun the same frozen command:

```bash
cd ~/workspace/MIRAGE/src
SEED=3 bash training_25k/cag_run_b0_b2_fullstack_seed.sh
```

The runner should keep completed stages and continue absent stages. If it encounters an incomplete stage directory or partial prediction file, it should stop rather than silently resume.
