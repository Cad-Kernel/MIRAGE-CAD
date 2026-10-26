> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# 08 -- Seed 2 Component Progress Record

Date: 2026-10-09

## Status

```yaml
Experiment: Review/03 B0 vs B2 full-stack multi-seed replication
Seed: 2
Status: PARTIAL_PROGRESS
Training: IN_PROGRESS
Prediction: NOT_STARTED
Gate evaluation: NOT_STARTED
Geometry scoring: NOT_STARTED
Seed status: NOT_CLOSED
```

Observed completed components in `outputs/b0_b2_fullstack_s2`:

```yaml
B0 no-plan code model:
  status: COMPLETE
  output: outputs/b0_b2_fullstack_s2/b0_lora_code_noplan_25k
  training_report: outputs/b0_b2_fullstack_s2/b0_lora_code_noplan_25k/training_report.json
  report_sha256: 6733bed0df600f645d98c1ea72b37d0ee617bcfa5d2936aa54304f747acdd684

B2 alignment:
  status: COMPLETE
  output: outputs/b0_b2_fullstack_s2/align_25k
  training_report: outputs/b0_b2_fullstack_s2/align_25k/training_report.json
  report_sha256: e2e28acff91c4d9c7ef23b4526981435ca14217d30f837c7b47e681ad6781fff

B2 STEP latent prior:
  status: COMPLETE
  output: outputs/b0_b2_fullstack_s2/priors/prior_step_25k
  training_report: outputs/b0_b2_fullstack_s2/priors/prior_step_25k/training_report.json
  report_sha256: c4a5c9721f6353b6bfce0f61eac25dac5d04a3a9a4bde352bf62750b8f0f85d8
  best_pt_sha256: b86f66b8ccb6126397a0a529054ef13135ef0dc3dd20073a863222e490d0bae5
  last_pt_sha256: 5946e4802eace0ed954d0bad9f5aca98c93c4fe19eb9457dce53696ace0b4cbf
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
alignment_checkpoint: outputs/b0_b2_fullstack_s2/align_25k/last.pt
train_jsonl: data/25k/train.jsonl
val_jsonl: data/25k/val.jsonl
output_dir: outputs/b0_b2_fullstack_s2/priors/prior_step_25k
modality: step
epochs: 8
batch_size: 48
learning_rate: 0.0001
temperature: 0.07
lambda_l2: 1.0
lambda_cos: 1.0
lambda_nce: 1.0
seed: 2
```

Final epoch metrics:

```yaml
epoch: 8
step: 4168
loss: 0.2922369292322195
l2: 0.00019958589356700135
cosine: 0.05109394074610944
nce: 0.24094340255382946

direct_median_rank: 1.0
direct_mrr: 0.8391636171430912
direct_r@1: 0.7232704601197872
direct_r@5: 0.9917452875173317
direct_r@10: 1.0

pred_median_rank: 1.0
pred_mrr: 0.9662605051724416
pred_r@1: 0.9343553669047806
pred_r@5: 1.0
pred_r@10: 1.0
```

Validation loss by epoch:

```yaml
epoch_1_loss: 0.44312407104474194
epoch_2_loss: 0.36750608710747845
epoch_3_loss: 0.3441845922256416
epoch_4_loss: 0.3281425492099996
epoch_5_loss: 0.31735086637847826
epoch_6_loss: 0.3070859214607275
epoch_7_loss: 0.30220288431869363
epoch_8_loss: 0.2922369292322195
```

## Analysis

This STEP-prior component is healthy. The validation loss decreases monotonically across all eight epochs, and the final epoch is the best observed validation loss under the frozen final-checkpoint rule. The learned prior substantially improves retrieval over the direct STEP embedding: R@1 rises from `72.33%` direct to `93.44%` predicted, and MRR rises from `0.8392` to `0.9663`.

This is a strong upstream component result for seed 2, but it is not an end-to-end B0/B2 result. It only verifies that the seed-2 STEP prior is learning the intended map into IR latent space. The reviewer-facing seed-2 comparison still requires the remaining B2 components, predictions, gate evaluation, and geometry scoring.

## Continue Command

To continue seed 2 from the current partial state, rerun the same frozen command:

```bash
cd ~/workspace/MIRAGE/src
SEED=2 bash training_25k/cag_run_b0_b2_fullstack_seed.sh
```

The runner should keep completed stages and continue absent stages. If it encounters an incomplete stage directory or partial prediction file, it should stop rather than silently resume.
