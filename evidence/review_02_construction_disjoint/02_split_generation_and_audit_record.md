> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Split Generation And Audit Record

Date: 2026-09-29

## Status

```yaml
Protocol: FROZEN
Split criterion: FROZEN
Sample IDs: FROZEN
Leakage audit: PASS
Dataset JSONL generation: COMPLETE
Training: NOT STARTED
Prediction: NOT STARTED
Gate evaluation: NOT STARTED
Geometry scoring: NOT STARTED
Package status: PHASE_1_CLOSED
```

No model training or prediction was run in this phase.

## Generator

Script:

```text
__DEV_ROOT__\src\training_25k\cag_build_construction_disjoint_split.py
```

Run command:

```bash
cd ~/workspace/MIRAGE/src
python3 __DEV_ROOT__/src/training_25k/cag_build_construction_disjoint_split.py \
  --src-root __RUN_SOURCE_ROOT__ \
  --out-dir data/construction_disjoint_step_v1 \
  --review-out-dir __EVIDENCE_SOURCE_ROOT__/02/split
```

Assignment policy:

```yaml
signature_version: op_graph_sig_v1
assignment_policy: hash_dp_group_disjoint_v1
assignment_seed: MIRAGE-CAD-CAG-construction-disjoint-2026-09-29
```

Note: an initial greedy assignment was rejected before sample-ID freeze because it underfilled the test set despite a 500-row group-disjoint subset being feasible. The final frozen assignment uses deterministic subset-sum DP over construction-signature groups. This correction happened before any training, prediction, gate evaluation, or geometry scoring.

## Output Locations

WSL data output:

```text
~/workspace/MIRAGE/src/data/construction_disjoint_step_v1/
```

Review evidence copy:

```text
__EVIDENCE_SOURCE_ROOT__\02\split\
```

Review evidence files:

```text
__EVIDENCE_SOURCE_ROOT__\02\split\train_ids.txt
__EVIDENCE_SOURCE_ROOT__\02\split\val_ids.txt
__EVIDENCE_SOURCE_ROOT__\02\split\test_ids.txt
__EVIDENCE_SOURCE_ROOT__\02\split\construction_split_manifest.csv
__EVIDENCE_SOURCE_ROOT__\02\split\nearest_train_construction_audit.csv
__EVIDENCE_SOURCE_ROOT__\02\split\split_manifest.json
__EVIDENCE_SOURCE_ROOT__\02\split\cag_construction_split_actuals.json
```

Large WSL-only evidence:

```text
~/workspace/MIRAGE/src/data/construction_disjoint_step_v1/signature_inventory.jsonl
~/workspace/MIRAGE/src/data/construction_disjoint_step_v1/train.jsonl
~/workspace/MIRAGE/src/data/construction_disjoint_step_v1/val.jsonl
~/workspace/MIRAGE/src/data/construction_disjoint_step_v1/test.jsonl
```

## Split Counts

| Split | Rows | Unique op_graph_sig_v1 signatures |
|---|---:|---:|
| Train | 25,000 | 33 |
| Val | 2,500 | 5 |
| Test | 500 | 4 |
| Unused | 2,000 | 6 |

Source inventory:

| Item | Count |
|---|---:|
| Source rows | 30,000 |
| Unique op_graph_sig_v1 signatures | 48 |

## Hard Leakage Audit

```yaml
train_val_signature_overlap: 0
train_test_signature_overlap: 0
val_test_signature_overlap: 0
status: PASS
```

Independent ID/JSONL check:

```yaml
train_ids_vs_train_jsonl: MATCH, 25000 unique IDs
val_ids_vs_val_jsonl: MATCH, 2500 unique IDs
test_ids_vs_test_jsonl: MATCH, 500 unique IDs
```

## Distribution Audit

Operation-count distribution:

| Split | Mean | SD | Min | Q25 | Median | Q75 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|
| Train | 5.576 | 2.367 | 1 | 4 | 6 | 7 | 11 |
| Val | 5.210 | 3.040 | 1 | 4 | 4 | 5 | 10 |
| Test | 1.000 | 0.000 | 1 | 1 | 1 | 1 | 1 |
| Unused | 5.766 | 2.742 | 1 | 2 | 7 | 8 | 8 |

Complexity distribution:

| Split | L1 | L2 | L3 | L4 |
|---|---:|---:|---:|---:|
| Train | 187 | 3,879 | 13,689 | 7,245 |
| Val | 145 | 275 | 2,080 | 0 |
| Test | 417 | 0 | 83 | 0 |
| Unused | 151 | 946 | 648 | 255 |

Test template families:

| Template family | Rows |
|---|---:|
| COVER_PLATE_SHELL | 129 |
| ELLIPSOID_STOCK | 139 |
| INTERSECTION_OFFSET_STOCK | 83 |
| TORUS_STOCK | 149 |

Important interpretation:

> The strict op_graph_sig_v1 split is very clean but also very hard and distribution-shifted. The 500-row test set contains four held-out one-operation signatures, and its operation tokens do not overlap with the train signatures under the operation-set audit. This is best described as a construction-signature or held-out-operation stress test, not as a balanced complexity-disjoint benchmark.

## Nearest-Train Construction Similarity Audit

Computed for each test sample against train signatures only.

| Metric | Value |
|---|---:|
| Test rows | 500 |
| Exact signature matches | 0 |
| Exact operation-sequence matches | 0 |
| Operation-set F1 min/q25/median/q75/max | 0 / 0 / 0 / 0 / 0 |
| Operation-sequence LCS min/q25/median/q75/max | 0 / 0 / 0 / 0 / 0 |

This directly addresses the Reviewer 1 concern that family-held-out test parts could still have nearest training plans with operation-set F1 near 1.0. Under this split, exact construction-signature overlap is removed, and the train-nearest construction similarity audit is zero by both operation-set F1 and operation-sequence LCS.

## Hashes

Source data:

| Source | SHA256 |
|---|---|
| `data/25k/train.jsonl` | `991e0a6d811b5927d9316fed50c7cc09472719af1726b8c92017c3fbb86906ca` |
| `data/25k/val.jsonl` | `4b76f8fec86f8fac7fbb9635542a924ccf3b91893115639d13ed79ada374a021` |
| `data/25k/test.jsonl` | `248a032248d0d9e20b4474ee8adb705d74968a443b534cf51d96601eba0a019e` |

Frozen outputs:

| Output | SHA256 |
|---|---|
| `train_ids.txt` | `21e3f0e7bdcf8db1ef490d8eb31b6f98462cb7f1adb717ed1c42c41df6affb4e` |
| `val_ids.txt` | `1fa4cfd533c8c006a3ae54668aa899ee75d0cdfc05decaa8a535cb3029c7d03b` |
| `test_ids.txt` | `a2091abf33ef6d034024b6fa44a40b24ca29051cd1328606c344702ea264ec08` |
| `train.jsonl` | `5952447edcacf3de5bc26b8647e59566544526a29dacdda7eb60beab14a09a1b` |
| `val.jsonl` | `b30ec6cd734cf714bdd416029fd7dc7752fbb927641f4509f502d3b019142f05` |
| `test.jsonl` | `3c42ee760354323fa3ab503bb5af576b7a56d82e2e2d26367ffacc71935fbd55` |
| `construction_split_manifest.csv` | `fa03e2567f73b59c2cac24418b404cd4d2ba2cd55854b33dceb3071af817584a` |
| `signature_inventory.jsonl` | `e5f3ddc077e37aedd1c14f67f319b882b8d8eb7a6b633effeb1f3a84f0f05828` |
| `nearest_train_construction_audit.csv` | `2f7f244e96163cd16614f12a61b07a68e363b208bb5749890126e32070bfe598` |
| `split_manifest.json` | `002c88144c957436666a74ff505fb71e6ac30fb59b61f12e1ef22ea2202c4e31` |
| split generator script | `5aee985dd30eeefab15016813227173356b0f7c49fb0c4b46b65c374235a2550` |

## Next Step

Phase 1 is closed. The next allowed step is Phase 3 baseline-first execution, or Phase 2 data plumbing checks if the training scripts require path adaptation. Do not start MIRAGE training until the train-only NN construction retrieval baseline has been run or explicitly deferred.
