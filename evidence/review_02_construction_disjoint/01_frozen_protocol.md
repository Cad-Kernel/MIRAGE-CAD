> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Frozen Protocol -- Construction-Disjoint STEP Stress Test

Date frozen: 2026-09-29

## Core Question

The reviewer concern is that the existing IID and family-held-out results may still be supported by construction-level redundancy. In particular, template-family removal does not necessarily remove operation-sequence or construction-graph overlap.

This experiment asks:

> How does the STEP pathway behave when test queries are drawn from construction signatures that are excluded from the training split?

The goal is a stress test for construction-space generalization, not a new A1E/B2P interface comparison.

## Primary Scope

```yaml
primary_scope:
  modality: step
  corpus: FllumaOne procedural corpus rows already used by MIRAGE-CAD
  input_frame: rows available through data/25k/{train,val,test}.jsonl as the starting inventory
  output_package: Review/02 construction-disjoint evidence package
  primary_model: MIRAGE STEP textual-plan pathway
  primary_baseline: train-only nearest-neighbor construction retrieval baseline
  repair: false
  evaluator_reuse: existing gate and geometry evaluators
```

Rationale for STEP-only primary scope:

- It directly addresses the reviewer concern about construction redundancy and STEP/generalization wording.
- STEP is the most controlled single-modality setting already used in the A1E/B2P evidence package.
- It avoids turning the next step into a full four-modality retraining campaign before the split criterion is validated.

Non-primary optional follow-up:

- text/image/point construction-disjoint runs may be added later, but only after the STEP package closes or if explicitly needed for reviewer wording.

## Construction Signature

The split unit is a normalized construction signature computed from each row's reference `training_ir.txt`.

Primary signature version: `op_graph_sig_v1`.

Rules:

1. Read the IR text from `ir_path`.
2. Ignore non-construction identifiers and numeric values:
   - `PART`
   - `SEED`
   - parameter numeric values
   - sample IDs
3. Parse feature lines beginning with `F`.
4. For each feature line, extract:
   - operation token, e.g. `OP_PLATE`, `OP_HOLE_PATTERN`;
   - feature index in the IR order;
   - dependency references after `DEP`, if present;
   - target presence/type coarsely, e.g. no target, face target, body target, multi-target;
   - role token after `ROLE`, if present.
5. Normalize dependencies to prior feature indices rather than feature names.
6. Build the signature as the ordered list of normalized feature records.

Example schematic form:

```text
[(OP_SKETCH, role=profile_definition, deps=[]),
 (OP_EXTRUDE, role=secondary_feature, deps=[0], target=feature),
 (OP_HOLE_PATTERN, role=functional_feature, deps=[1], target=face),
 ...]
```

Template family must not be used as the primary split key. It may be reported as an audit field only.

## Split Rule

The split is group-disjoint by `op_graph_sig_v1`.

```yaml
split_rule:
  train_signatures ∩ val_signatures: empty
  train_signatures ∩ test_signatures: empty
  val_signatures ∩ test_signatures: empty
  row_assignment_unit: construction signature group
```

The script must produce:

```text
data/construction_disjoint_step_v1/train.jsonl
data/construction_disjoint_step_v1/val.jsonl
data/construction_disjoint_step_v1/test.jsonl
data/construction_disjoint_step_v1/split_manifest.json
data/construction_disjoint_step_v1/signature_inventory.jsonl
```

The split IDs are not considered frozen until `split_manifest.json` is written and copied into this review package.

## Split Size Targets

Primary target:

| Split | Target rows | Rule |
|---|---:|---|
| train | 25,000 | from train signatures only |
| val | 2,500 | from val signatures only |
| test | 500 | from test signatures only |

If the exact row counts cannot be achieved without breaking signature disjointness, use the largest feasible counts and record the shortfall before any training begins.

Test selection policy:

- deterministic;
- one row per held-out signature where feasible, to maximize construction diversity;
- stratify by operation count and existing complexity label where feasible;
- no filtering based on model outputs, gate results, or geometry results;
- no manual cherry-picking.

## Split Audit Required Before Training

Before any model training, the split script must report:

- total source rows;
- number of unique `op_graph_sig_v1` signatures;
- row counts per split;
- signature counts per split;
- proof that train/val/test signature intersections are empty;
- operation-token distribution per split;
- operation-count distribution per split;
- complexity-label distribution per split;
- template/family distribution per split if available;
- nearest-train operation-set F1 for each test row;
- nearest-train exact signature collision rate, which must be 0.0;
- nearest-train exact operation-sequence collision rate as an additional stricter or looser audit, depending on implementation.

Acceptance criteria:

```yaml
required:
  train_test_signature_overlap: 0
  train_val_signature_overlap: 0
  val_test_signature_overlap: 0
  test_rows: >= 500 unless infeasible and documented before training
  train_rows: >= 20000 unless infeasible and documented before training
  split_manifest_written_before_training: true
```

If these criteria fail, do not train. Revise only the split construction script or declare the stress test infeasible.

## Arms

Primary generated arm:

```yaml
MIRAGE_STEP_B2P_CD:
  description: STEP textual-plan pathway trained on construction-disjoint train split
  train_rows: split train rows, target 25000
  val_rows: split val rows, target 2500
  checkpoint_selection: final
  decoding: same deterministic decoding policy as the A1E/B2P frozen package
  repair: false
```

Primary baseline:

```yaml
NN_IR_TRAIN_ONLY_CD:
  description: nearest-neighbor construction retrieval baseline using only construction-disjoint train rows
  retrieval_index: built from train split only
  retrieval_allowed_to_see_val_or_test: false
  output: retrieved train reference program or plan/code path, according to existing NN-IR baseline implementation
```

Optional diagnostic arms, not primary:

- existing IID-trained STEP model evaluated on the construction-disjoint test slice;
- A1E continuous arm on the same split;
- no-plan baseline on the same split.

Optional arms must not delay the primary generated arm and NN baseline unless explicitly promoted before any results are generated.

## Retrieval Policy

Primary MIRAGE generated arm:

```yaml
retrieval_in_generation: disabled unless the existing STEP pathway requires it
if_required:
  retrieval_index_scope: train split only
  val_or_test_rows_in_index: forbidden
```

Baseline retrieval:

```yaml
retrieval_index_scope: train split only
top_k: freeze to existing NN-IR baseline default unless changed before any result
leakage_check: required
```

Any retrieval result must report nearest-train construction similarity so the paper can separate true generalization from near-neighbor behavior.

## Training And Checkpoint Policy

Primary training policy:

- final checkpoint only;
- no checkpoint selection by test performance;
- no repair;
- no post-hoc decoding changes after seeing construction-disjoint outputs;
- random seed fixed and recorded before training.

Initial seed policy:

```yaml
primary_seed: 1
additional_seeds: not planned until primary stress result is inspected for feasibility
```

Reason: this package is a stress-test/generalization diagnostic, not another replicated interface comparison. If it becomes a headline quantitative claim, additional seeds can be registered as a separate follow-up before running them.

## Evaluation Metrics

Gate metrics:

- syntax OK;
- execution OK;
- build OK;
- solid valid;
- STEP export OK;
- kernel crash count;
- scoreable output count.

Geometry metrics:

- median CD on scoreable outputs;
- median F@1 on scoreable outputs;
- unconditional mean F@1 over all 500 rows;
- unconditional median F@1 over all 500 rows.

Construction diagnostics:

- predicted/reference operation-set precision, recall, F1;
- operation-sequence LCS ratio;
- nearest-train operation-set F1;
- nearest-train operation-sequence LCS;
- exact signature overlap audit.

Reporting must keep these separate:

- executable coverage;
- conditional geometry on scored outputs;
- unconditional geometry over all attempted rows;
- construction-plan similarity;
- retrieval/nearest-neighbor similarity.

## Result Tables To Produce

Primary table:

| Arm | n | Syntax | Build | STEP export | Scored | Median CD | Median F@1 | Unconditional mean F@1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|

Construction-disjoint audit table:

| Split | Rows | Signatures | Mean op count | Median op count | Complexity mix | Notes |
|---|---:|---:|---:|---:|---|---|

Nearest-neighbor audit table:

| Test n | Exact signature overlap | Median nearest op-set F1 | Median nearest op-seq LCS | Same template/family rate |
|---:|---:|---:|---:|---:|

Failure taxonomy table:

| Arm | Syntax fail | Exec fail | Build fail | STEP export fail | Geometry score fail | Common failure notes |
|---|---:|---:|---:|---:|---:|---|

## Reviewer-Facing Interpretation Rules

If performance drops under construction-disjoint testing:

> This indicates that the original IID/family-held-out results partly benefit from construction-space redundancy. The revised paper should narrow the generalization claim accordingly and present the construction-disjoint result as a stress test.

If performance remains strong:

> This provides stronger evidence that the STEP pathway generalizes beyond exact construction signatures, while still remaining an in-corpus procedural stress test rather than an external benchmark.

Always preserve these cautions:

- This is not external real-world generalization.
- This is not simultaneous multimodal fusion.
- This does not make the STEP encoder topology-aware; the reported STEP pathway still uses global kernel descriptors unless the architecture changes.
- This does not establish human editability or semantic edit correctness.

## Close Conditions

This package can be marked CLOSED only when all are true:

- frozen split manifest exists;
- train/val/test signature-disjoint audit passes;
- primary generated arm training and prediction are complete;
- NN baseline output is complete;
- gate evaluation is complete;
- geometry scoring is complete;
- construction diagnostics are complete;
- summary JSON is written;
- reviewer-facing interpretation record is written;
- no unresolved protocol deviations remain.

## Forbidden Changes After Split Freeze

After `split_manifest.json` is copied into this review package:

- do not change split criterion;
- do not move signatures between train/val/test;
- do not change test row selection;
- do not alter decoding based on early outputs;
- do not add retrieval access to val/test rows;
- do not report only favorable subsets.

Any unavoidable deviation must be recorded before using the result in the paper.
