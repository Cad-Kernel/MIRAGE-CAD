> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Fusion 360 Existing-Evidence Audit

Date: 2026-10-22.

Current scope: **Step 1 only, inventory and sample-ID correspondence audit**.
Step 1 status: COMPLETE / independently verified PASS. Master: 400 rows, 67 CSV
columns. All three methods cover the same 400 IDs; CD/IoU availability differs.
No training, model forward, prediction regeneration, CAD code execution,
tessellation, geometry evaluation, rendering or case selection is authorized here.
Review/01-04 remain CLOSED and the preserved Review/05 package is not modified.

## Work Order

1. Inventory/correspondence audit: establish the original 400-case universe and
   order; join reference, MIRAGE autonomous point-generated-plan, training-index
   NN-IR-assisted pathway, CAD-Recode, metrics, execution/export evidence and
   existing assets by exact `sample_id`. Check duplicate/extra/missing IDs,
   physical row locators, order differences, files and hashes.
2. Failure taxonomy: later, only from verified native evidence and inspected
   outputs. Low IoU alone is not evidence of a missing hole or topology defect.
3. Case selection/rendering: later, record deterministic retrospective selection
   rules before choosing representative/near-median, low-tail, hard-failure and
   relative-success examples. Keep target/method cameras and scale matched.
4. Archive/paper registry: later, preserve raw assets and derive a separately
   versioned manuscript subset. Never reduce the research archive to meet page
   limits.

## Step 1 Deliverables

- `01_inventory_and_correspondence_audit.md`: observed correspondence, paths,
  missing/current assets, counts, integrity issues and remaining limitations.
- `fusion360_case_registry.csv`: one row per original test ID, in authoritative
  input order. A JSONL path is accompanied by a physical line locator; it is not
  represented as an individual prediction file.
- `audit/master_ids_v1.txt`, `audit/master_records_v1.json`: canonical identifiers
  and typed joined evidence. No method-specific success subset defines the master.
- `audit/source_files_v1.json`: existing/missing file inventory and SHA256.
- `audit/correspondence_v1.json`: ID-set/order/locator checks and current native
  evidence. Historical metric values are copied, not recomputed.
- `support/`: read-only collectors, contract tests and CSV authoring/verification.

`verified_failure_class`, `failure_evidence`, and `selection_bucket` are reserved
for later steps and remain blank in Step 1. Raw native statuses/errors are kept
separately so a blank taxonomy field does not hide known execution evidence.

CD and IoU have separate scoreability fields and paired denominators. A missing
or failed IoU is not zero. Historical export success, metric availability and
current artifact existence are separate facts. NN-IR uses retrieval assistance
and is not relabelled as the autonomous MIRAGE entry.

The old external manifest may predate final geometry production. Its placeholder
paths/statuses will not override terminal per-case run/score manifests. Any
differences are retained in the audit rather than silently corrected in sources.

The verified Step-1 outcome is documented in
`01_inventory_and_correspondence_audit.md`. Existing source files and all prior
Review/04-05 seals remain unchanged. The Step-1 CSV/master are separately sealed;
later taxonomy or selection must create a new version rather than overwrite them.

```yaml
Internal retraining: CLOSED
Review/05 candidate assets and raw preservation: COMPLETE
Step 1 correspondence audit: COMPLETE_PASS
Step 2 failure taxonomy: NOT_STARTED
Step 3 selection_and_CAD_rendering: NOT_STARTED
Step 4 raw_asset_archive_and_submission_subset: NOT_STARTED
Training: NO
Prediction regeneration: NO
```
