> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Step 2 Log-Based Failure Taxonomy

Date: 2026-10-22. Version: native-log-taxonomy-v1.

This is a **retrospective descriptive classification** of existing results, not a
preregistered hypothesis test or a new model/evaluation protocol. Existing log
vocabulary was inspected before this rule set was written. The rules below are
recorded before applying the classifier to all 1,200 method/sample records.

## Scope and Input

Use the sealed Step-1 universe of 400 original test IDs and its exact source
locators. Process all three methods for every ID, in original master order.
MIRAGE means autonomous point-generated-plan; NN means training-index NN-IR
assisted; CADR means CAD-Recode. No subset is selected or removed.

No training, new model prediction, code repair, CAD execution, STEP export,
tessellation, metric recomputation, CAD rendering or qualitative case selection.
Previously sealed files are not edited, including the Step-1 README and CSV.

## Two Independent Outcome Axes

Every method/sample receives one `primary_outcome`:

1. Explicit native kernel crash, whose exact execution/build location is not
   inferred from incomplete gate flags.
2. First observed failing program gate: syntax, execution, build, solid validity,
   STEP export. For MIRAGE/NN use recorded native gate flags. CAD-Recode is not
   claimed to have run Flluma's five gates; use its own extraction/execution result.
3. After export: reported empty prediction mesh, remesh failure, GT verification
   failure, resource/evaluator failure, other native unscoreability, or CD failure.
4. `CD_SCOREABLE` only if the native record has finite `cd_x1000` and CD status ok.
   This is not semantic success, high fidelity, or proof that IoU is available.

`verified_failure_class` equals a non-scoreable primary outcome, or null for a
CD-scoreable record. IoU is recorded separately as `iou_outcome` and
`iou_failure_class`: available (including measured zero), boolean failure,
other IoU/GT eligibility failure, or not available after an earlier primary failure.
A failed boolean is an evaluator event, not measured zero overlap.

These axes must not be added as if they were disjoint failure populations.

## Reason Subtypes

Apply deterministic, ordered message patterns to the reported failure message,
not to CD/IoU values. Preserve every original message and the matching rule:

- Missing API attribute/method, including owner and symbol when explicitly named.
- Unexpected keyword, missing required argument, or positional-argument arity.
- Explicit sequence/value contract, duplicate parameter declaration, undefined
  name, unsupported operand types, unresolved topology reference, or handle type.
- Syntax diagnostics and native access violations.
- STEP export's explicit OCCT-build error, without moving it to an earlier gate.
- Empty tessellation only when reported; zero triangles/zero faces only when
  the corresponding native diagnostic actually records that count.
- CAD-Recode line-edge or three-point-arc construction only when both its
  exception and native traceback name that operation. No collinearity or other
  geometric root cause is inferred.
- A safe `*_UNSPECIFIED` subtype for a reported error that does not establish
  a more specific cause. Do not force quoted words such as `'width'` into KeyError
  without an exception type or traceback that establishes it.

One subtype per primary outcome supports disjoint descriptive counts. It is a
diagnostic label, not proof of a causal training/architecture explanation.

## Geometry Quality Boundary

Retain existing CD and IoU literally. Do not introduce a new low-IoU acceptance
threshold or claim missing holes, wrong feature order, disconnected parts or
wrong topology from metrics alone. `geometry_review_status` remains
`NOT_VISUALLY_REVIEWED`; semantic failure labels and selection buckets stay null.
Scoreable-but-poor geometry requires a separately defined metric stratum and/or
visual inspection in Step 3. Step 2 closes only the native/log taxonomy.

## Outputs and Preservation

- `taxonomy/failure_taxonomy_v1.json`: all 1,200 classified records and per-method
  counts, with literal native evidence and rule IDs.
- `fusion360_failure_taxonomy_v1.csv`: long table keyed by `(sample_id, method)`.
- `fusion360_case_registry_step2_v1.csv`: original 400-row/67-column Step-1
  values unchanged, plus method-prefixed taxonomy fields. Original unprefixed
  reserved fields remain blank to avoid ambiguity about which method they mean.
- `taxonomy/evidence_v1/<method>/<sample_id>.json`: per-record evidence, pointers
  into sealed Step-1 records, original physical line/hash locators, and hashes
  for native source manifests/logs used in classification.
- `03_failure_taxonomy_results.md`: full outcome/subtype counts, limits and
  reviewer-facing interpretation.
- A new Step-2 validation report and seal. Later semantic review/selection must
  create another version, not silently replace these original log labels.

Classification uses sealed source snapshots and rechecks the current native
manifest/gate/log files it reads against Step-1 source hashes. It does not create
the Step-4 raw-asset archive or assert missing historical model provenance.
