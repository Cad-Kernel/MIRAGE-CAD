> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# 04 -- Seed 1 Component Progress Record

Date: 2026-10-06

## Checkout / Execution Paths

```yaml
Windows source checkout:
  __DEV_ROOT__\src

WSL execution checkout:
  __RUN_SOURCE_ROOT__

WSL short form:
  ~/workspace/MIRAGE/src

Review package:
  __EVIDENCE_SOURCE_ROOT__\03
```

These paths should be preserved in the public-code/reproducibility notes because the long-running training is executed from the WSL checkout while source edits and review records are maintained in the Windows checkout.

## Current Seed 1 Status

```yaml
Experiment: Review/03 B0 vs B2 full-stack multi-seed replication
Seed: 1
Status: PARTIAL_PROGRESS
Training: IN_PROGRESS
Prediction: NOT_STARTED
Gate evaluation: NOT_STARTED
Geometry scoring: NOT_STARTED
Seed status: NOT_CLOSED
```

Observed completed components in `outputs/b0_b2_fullstack_s1`:

```yaml
B0 no-plan code model:
  status: COMPLETE
  output: outputs/b0_b2_fullstack_s1/b0_lora_code_noplan_25k
  training_report: outputs/b0_b2_fullstack_s1/b0_lora_code_noplan_25k/training_report.json
  report_sha256: 60658c913257194c3a636fcff364354e96d89af39a65ad775310631899464f5c

B2 alignment:
  status: COMPLETE
  output: outputs/b0_b2_fullstack_s1/align_25k
  training_report: outputs/b0_b2_fullstack_s1/align_25k/training_report.json
  report_sha256: 2417dcb250c8ff2973d007dcbf4fb729f668655ef9128805176fa33f17134e36

B2 STEP latent prior:
  status: COMPLETE
  output: outputs/b0_b2_fullstack_s1/priors/prior_step_25k
  training_report: outputs/b0_b2_fullstack_s1/priors/prior_step_25k/training_report.json
  report_sha256: 993129e1eeeaaeb39077a5604b092a5550992ed0db10b332a7141f929c862cfe
  best_pt_sha256: 5cbb74ed7c4baa6d80f826e4f5943f8cb5829e05b1a93e8ca48cb7a2569efb14
  last_pt_sha256: 5836b11fdce7260dcce7cadf06a1ae5b1e79319c5ecfe86a9a15605d8a76bbbd
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
alignment_checkpoint: outputs/b0_b2_fullstack_s1/align_25k/last.pt
train_jsonl: data/25k/train.jsonl
val_jsonl: data/25k/val.jsonl
output_dir: outputs/b0_b2_fullstack_s1/priors/prior_step_25k
modality: step
epochs: 8
batch_size: 48
learning_rate: 0.0001
temperature: 0.07
lambda_l2: 1.0
lambda_cos: 1.0
lambda_nce: 1.0
seed: 1
```

Final epoch metrics:

```yaml
epoch: 8
step: 4168
loss: 0.28589463044168817
l2: 0.0002030523533423273
cosine: 0.05198135332397695
nce: 0.23371022599002453

direct_median_rank: 1.0
direct_mrr: 0.8696971749359707
direct_r@1: 0.7645440416515998
direct_r@5: 0.9968553489109255
direct_r@10: 1.0

pred_median_rank: 1.0
pred_mrr: 0.9654743435247889
pred_r@1: 0.9327830402356274
pred_r@5: 1.0
pred_r@10: 1.0
```

Best observed validation loss occurred at the final epoch:

```yaml
epoch_1_loss: 0.42980040216221
epoch_2_loss: 0.36392760290852133
epoch_3_loss: 0.3337087165915741
epoch_4_loss: 0.3170356510101624
epoch_5_loss: 0.30576055173603994
epoch_6_loss: 0.2958812225820883
epoch_7_loss: 0.29239017909990167
epoch_8_loss: 0.28589463044168817
```

## Analysis

This STEP-prior component looks healthy. The validation loss decreases monotonically across all eight epochs, so the final-checkpoint rule is not in tension with validation behavior for this component. The learned prior improves retrieval over the direct STEP embedding: R@1 rises from `0.7645` direct to `0.9328` predicted, and MRR rises from `0.8697` to `0.9655`, while R@5/R@10 are saturated at `1.0`.

This is a good upstream result for B2 seed 1, but it is not yet an end-to-end B0 vs B2 result. It only shows that the seed-1 STEP latent prior maps STEP observations into the IR latent space effectively. The reviewer-facing comparison cannot be interpreted until the remaining B2 components, predictions, gate evaluation, and geometry scoring are complete.

## Continue Command

To continue seed 1 from the current partial state, rerun the same frozen command:

```bash
cd ~/workspace/MIRAGE/src
SEED=1 bash training_25k/cag_run_b0_b2_fullstack_seed.sh
```

The runner is designed to keep completed stages and continue absent stages. If it encounters an incomplete stage directory or partial prediction file, it should stop rather than silently resume.
