> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# 15 -- Seed 4 Component Progress Record

Date: 2026-10-14

This record supersedes the current-state interpretation in `14_seed4_interruption_record.md`. That file remains a historical record of the interrupted alignment attempt.

## Current Status

```yaml
Seed: 4
B0 no-plan training: COMPLETE
B2 alignment clean rerun: COMPLETE
B2 STEP latent prior: COMPLETE
B2 point/text/image priors: NOT_STARTED_OR_NOT_PRESENT
B2 Stage 3/3b/4/4b: NOT_STARTED_OR_NOT_PRESENT
Prediction: NOT_STARTED
Gate evaluation: NOT_STARTED
Geometry scoring: NOT_STARTED
Seed status: NOT_CLOSED
Active training or generation processes at inspection: NONE_FOUND
```

## Paths And Provenance

```yaml
Windows source checkout: __DEV_ROOT__\src
WSL execution checkout: __RUN_SOURCE_ROOT__
Seed base: __RUN_SOURCE_ROOT__/outputs/b0_b2_fullstack_s4
Interrupted alignment archive: __RUN_SOURCE_ROOT__/outputs/b0_b2_fullstack_s4/align_25k_interrupted_20261014_0244
```

The current alignment directory now contains `best.pt`, `last.pt`, and `training_report.json`. The STEP prior likewise contains both checkpoints and its completed eight-epoch report. Downstream stages use `last.pt` under the frozen final-checkpoint rule.

```yaml
B0 training report SHA256: ad37e74c3a3fa930e11e78275d350c8ee89fa03772551ce34a13fd4cf0281a42
Alignment training report SHA256: 3861980b0f875a99070f1544cc72e3109ea549ec0fb19198ffed1aca2d475e2e
STEP prior training report SHA256: 339ae0f6c9f4333e32ed6869c00158f751dcd75244bd3e19508c4970c6b29786
STEP prior last.pt SHA256: 11c2461770ef81fc10f1511659cfa44692891ff25502162e3b08f6218a843743
Frozen runner SHA256: e32ba4bdf5afff97107c966750a3a61f55426e8f54eb6a8db05f0c847c62dc55
```

## STEP Prior Result

Report: `__RUN_SOURCE_ROOT__/outputs/b0_b2_fullstack_s4/priors/prior_step_25k/training_report.json`.

The report records seed 4, eight epochs, batch size 48, learning rate 0.0001, and alignment input `outputs/b0_b2_fullstack_s4/align_25k/last.pt`.

| Epoch | Validation Loss |
| --- | ---: |
| 1 | 0.41706770264877463 |
| 2 | 0.3458759680671512 |
| 3 | 0.3255304046115785 |
| 4 | 0.3040223462542273 |
| 5 | 0.2897938033038715 |
| 6 | 0.27760213915750664 |
| 7 | 0.2745034095813643 |
| 8 | 0.26699652825042886 |

```yaml
Final epoch: 8
Final step: 4168
loss: 0.26699652825042886
l2: 0.00020894442656393744
cosine_loss: 0.053489723787555156
nce: 0.2132978590709412
direct_median_rank: 1.0
direct_mrr: 0.8560183947941042
direct_r@1: 0.7417453032619549
direct_r@5: 0.9956761036279067
direct_r@10: 1.0
pred_median_rank: 1.0
pred_mrr: 0.9698965054637981
pred_r@1: 0.9414308352290459
pred_r@5: 1.0
pred_r@10: 1.0
```

Validation loss decreases throughout the run. Final R@1 is 94.14%, versus 74.17% for direct embeddings. These are validation batch-level retrieval metrics computed within each batch and averaged across batches; they are not full-corpus retrieval accuracy or CAD Build coverage. The highest R@1 occurs at epoch 7 (94.22%); the frozen rule still selects epoch 8, which has the lowest validation loss. No end-to-end B0/B2 performance conclusion is available yet.

## Wrapper Exit Diagnosis

The frozen wrapper starts `tee -a "$PRIOR.train.log"` before creating the parent `priors` directory. The Python trainer creates that directory as part of its output setup. If `tee` starts first, it cannot open its log path. With `set -o pipefail`, the wrapper then exits after the Python trainer completes. This explains a reproducible exit mechanism consistent with all four seeds stopping after the first STEP prior; no retained stderr proves the exact exit cause for this invocation.

The current `priors` parent directory already exists. The STEP prior's completed files pass the wrapper's keep checks, so the same seed-4 command can continue with the point prior. No checkpoint removal or renaming is required at this point. The frozen runner source and training settings were not modified during this inspection.

## Continue Command

Run manually in WSL:

```bash
cd ~/workspace/MIRAGE/src
SEED=4 bash training_25k/cag_run_b0_b2_fullstack_seed.sh
```

Keep completed B0, alignment, and STEP prior outputs. Continue point/text/image priors, Stage 3/3b/4/4b, and prediction. Gate and geometry follow after `GENERATION_COMPLETE_NEEDS_GATE_AND_GEOMETRY` is emitted.
