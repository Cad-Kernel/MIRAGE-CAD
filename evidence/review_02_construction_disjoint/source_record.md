> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# 02 -- Construction-Disjoint Stress Test

This folder records the next major revision evidence package after the A1E/B2P frozen multi-seed replication.

## Purpose

Reviewer 1 raised that the original IID and family-held-out results may still contain construction-level redundancy, because nearest retrieved training plans can share essentially identical operation sets with test parts. This package freezes a construction-disjoint stress-test protocol before generating a new split, training models, or evaluating results.

## Current Status

```yaml
Protocol: FROZEN
Split criterion: FROZEN
Split audit: COMPLETE
Split IDs frozen: COMPLETE
Leakage audit: PASS
Dataset JSONL generation: COMPLETE
NN descriptor baseline generation: COMPLETE
NN descriptor baseline gate evaluation: COMPLETE
NN descriptor baseline geometry scoring: COMPLETE
MIRAGE B2P training: COMPLETE
MIRAGE B2P prediction: COMPLETE
MIRAGE B2P gate evaluation: COMPLETE
MIRAGE B2P geometry scoring: COMPLETE
Summary JSON: COMPLETE
Review record: COMPLETE
Package status: CD_STEP_STRESS_TEST_CLOSED
Reviewer-1 construction-disjoint requirement: SUBSTANTIALLY_ADDRESSED
Broad external generalization: STILL_OPEN
```

## Files

- `01_frozen_protocol.md`  
  Frozen construction-disjoint STEP stress-test protocol.

- `02_split_generation_and_audit_record.md`  
  Phase 1 split generation, leakage audit, nearest-train construction similarity audit, and frozen hashes.

- `03_baseline_and_training_scripts_prepared.md`  
  Prepared NN baseline and MIRAGE retraining scripts, WSL sync status, and syntax/import checks.

- `04_nn_descriptor_baseline_result.md`  
  Train-only STEP descriptor nearest-neighbour baseline generation, gate, geometry, hashes, and interpretation.

- `05_mirage_b2p_cd_result.md`  
  MIRAGE B2P construction-disjoint STEP training, prediction, gate, geometry, NN-baseline comparison, failure summary, hashes, and reviewer-facing interpretation.

- `split/`  
  Frozen IDs, split manifest, actuals, manifest CSV, and nearest-train construction audit.

- `baseline/`  
  Frozen NN descriptor baseline outputs, gate rows, geometry rows, summary JSON, and hashes.

- `mirage_b2p_cd/`  
  Frozen MIRAGE B2P predictions, geometry input, gate rows, geometry rows, training reports, summary JSON, and hashes.

## Decision

Primary scope is STEP-only. The goal is not to rerun the whole four-modality system first; it is to create a clean, feasible in-corpus diagnostic for construction-overlap leakage and reviewer-facing wording. Multi-modality expansion can be considered only after this package closes.

Phase 1 result:

```yaml
train_rows: 25000
val_rows: 2500
test_rows: 500
train_unique_signatures: 33
val_unique_signatures: 5
test_unique_signatures: 4
signature_overlap: 0
nearest_train_exact_signature_matches: 0
nearest_train_exact_operation_sequence_matches: 0
nearest_train_operation_set_f1_median: 0.0
```

Important caveat:

> This split is a very strict construction-signature / held-out-operation stress test. The test set is not complexity-balanced: all test samples have operation count 1. Use it to address construction-overlap leakage, not as a replacement for the original IID/family-held-out main benchmark.

Next run order:

```text
1. Train-only STEP descriptor NN baseline. [COMPLETE]
2. Gate + geometry for the baseline. [COMPLETE]
3. Inspect baseline result. [COMPLETE]
4. MIRAGE construction-disjoint STEP retraining. [COMPLETE]
5. MIRAGE gate + geometry. [COMPLETE]
```

NN baseline result:

```yaml
exact_signature_matches: 0 / 500
exact_operation_sequence_matches: 0 / 500
operation_set_f1_median: 0.0
operation_sequence_lcs_median: 0.0
build_ok: 500 / 500
step_export_ok: 500 / 500
scoreable: 500 / 500
median_cd: 6.492554284974444
median_f_at_1pct: 0.011637369791666666
mean_f_at_1pct: 0.018381052387406425
```

MIRAGE B2P construction-disjoint result:

```yaml
syntax_ok: 500 / 500
build_ok: 410 / 500
step_export_ok: 410 / 500
scoreable: 410 / 500
median_cd: 4.409928410527609
median_f_at_1pct: 0.027308872767857144
unconditional_mean_f_at_1pct: 0.025601028230479814

vs_NN_descriptor_baseline:
  median_cd_delta_B2P_minus_NN: -2.082625874446835
  median_f_at_1pct_delta_B2P_minus_NN: 0.01567150297619048
  unconditional_mean_f_at_1pct_delta_B2P_minus_NN: 0.007219975843073385
  paired_cd_wins_B2P_lower: 242 / 410
  paired_f_wins_B2P_higher: 270 / 407_non_ties
```
