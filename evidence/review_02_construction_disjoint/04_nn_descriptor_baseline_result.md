> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# 04 -- Train-Only STEP Descriptor NN Baseline Result

## Status

```yaml
Baseline arm: NN_DESC_TRAIN
Baseline generation: COMPLETE
Gate evaluation: COMPLETE
Geometry scoring: COMPLETE
MIRAGE training: NOT_STARTED
Record status: CLOSED
```

This record covers the train-only nearest-neighbour STEP descriptor baseline for the construction-signature-disjoint in-corpus stress test. The split was not changed after seeing this result.

## Protocol

- Split: `construction_disjoint_step_v1`
- Test rows: 500
- Train rows available to retrieval: 25,000
- Retrieval distance: z-score L2 over STEP descriptors
- Retrieval access: train split only
- Prediction: retrieved train reference program copied as the candidate program
- Evaluation: same Windows execution gate and geometry scorer used for the MIRAGE revision experiments

## Construction Similarity Audit

The baseline actuals confirm that the nearest train item never shares the frozen construction signature or exact operation sequence with the test item.

```yaml
exact_signature_matches: 0 / 500
exact_operation_sequence_matches: 0 / 500
operation_set_f1:
  min: 0.0
  q25: 0.0
  median: 0.0
  q75: 0.0
  max: 0.0
operation_sequence_lcs:
  min: 0.0
  q25: 0.0
  median: 0.0
  q75: 0.0
  max: 0.0
```

Descriptor NN distance:

```yaml
n: 500
min: 1.290563702583313
q25: 2.6223772764205933
median: 11.069742202758789
q75: 17.927095413208008
max: 34.63768005371094
mean: 11.596178603887559
sd: 8.019266639896875
```

## Gate Evaluation

Gate result:

```yaml
rows: 500
syntax_ok: 500 / 500 = 100.0%
exec_ok: 500 / 500 = 100.0%
build_ok: 500 / 500 = 100.0%
solid_valid: 500 / 500 = 100.0%
step_export_ok: 500 / 500 = 100.0%
kernel_crash_count: 0
runtime_seconds: 12.271
```

Interpretation caution: 100% gate success is expected for this baseline because it returns executable train-set reference programs. This should not be interpreted as successful reconstruction of the target test geometry.

## Geometry Scoring

Geometry rows:

```yaml
rows: 500
has_target: 500
scoreable: 500
unscoreable: 0
gate_ok_candidates_in_geometry_rows: 500
```

Chamfer distance:

```yaml
n: 500
min: 0.25851162520680004
q25: 2.466451241836522
median: 6.492554284974444
mean: 8.897258017047982
q75: 11.799371613294163
max: 85.39378852401902
sd_population: 10.074825159405368
```

F@1%:

```yaml
n: 500
min: 0.0
q25: 0.0033482142857142855
median: 0.011637369791666666
mean: 0.018381052387406425
q75: 0.022938829787234043
max: 0.1394025895979021
sd_population: 0.02309634684612727
unconditional_mean_failure_as_zero: 0.01838105238740643
unconditional_median_failure_as_zero: 0.011637369791666666
```

BBox error:

```yaml
n: 500
min: 0.4966652393737003
q25: 3.126162031817942
median: 4.487397180630646
mean: 5.2230712203377125
q75: 6.586754404609276
max: 19.94000013618636
sd_population: 3.255086918990004
```

## Interpretation

This is a useful simple baseline for Reviewer 1's STEP/retrieval concern. It shows that a train-only global STEP descriptor nearest neighbour remains fully executable, but it does not recover the held-out target geometry well under the construction-signature-disjoint split.

The key reviewer-facing statement is:

> We added a train-only nearest-neighbour descriptor baseline for the construction-signature-disjoint STEP stress test. Although the retrieved train programs were all executable and STEP-exportable, the nearest neighbours shared no frozen operation-graph signatures or exact operation sequences with the test items, and geometry agreement was low (median F@1% = 1.16%, median CD = 6.49). This indicates that the held-out test items are not solved by retrieving an executable train construction under the frozen descriptor baseline.

Keep the split caveat attached to this result: the test split contains only four held-out operation-count-1 signatures, so this is a strict diagnostic stress test rather than a balanced benchmark of general compositional generalization.

## Evidence Files

All paths below are stored under `__EVIDENCE_SOURCE_ROOT__\02\baseline`.

```yaml
nn_step_descriptor_train_only.jsonl:
  sha256: ce74acf1d51392853d00a78db5a8bbbe11a6803c589607f009d762642dcbe667
nn_step_descriptor_train_only_actuals.json:
  sha256: 1e56136817189ca6ba206ecfa8b52fa45852e4274164b6f9a009cfe0b97e9dcc
geom_input_step_NN_DESC_TRAIN.jsonl:
  sha256: 1aeee7227ff8d749fbcdda6a04f4bf92014d8ea0823a1438c198a37bf237587e
geom_input_step_NN_DESC_TRAIN_manifest.json:
  sha256: 64ed73e2ed436883712d50c4da79071ecd157fcd856502985487f4b478f1394b
execution_summary_NN_DESC_TRAIN.json:
  sha256: b000a4b53e86a5009957c8e88c2bcb1977adc2f33830aeb88ccbd95df546c0a4
execution_rows_NN_DESC_TRAIN.jsonl:
  sha256: 2c339dec120ea696ea8beb0bbd411e99d4567d167ccc532fc5fe607a23a82a36
geometry_nbest_rows_NN_DESC_TRAIN.jsonl:
  sha256: f0aa7adfb9e34e8a119df3bd0a6cfdab3523247048c41c35cf7eebc3c8bc5e26
nn_baseline_summary_NN_DESC_TRAIN.json:
  sha256: 52af5558fe6adee68bff9053b1942d6e7ab5e600ad950a186f2cd94831671e2c
```
