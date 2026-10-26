> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Raw Evidence Preservation

The complete registered evidence for the 24 qualitative cases is retained for
later paper writing, revision, supplementary material and audit. If the editor
asks for fewer figures, reduce the manuscript or a separately versioned
submission subset. Do not delete or rewrite this complete research archive.

## Contents

- Byte-exact copies of all 55 full files already registered in
  `selection/source_audit_v1.json`: dataset JSONL, complete four-modality raw and
  repaired prediction/plan JSONL, gate/geometry rows and summaries, relevant
  source scripts/metadata, manuscript snapshot and current checkpoint observations.
- All 8 original asset roles for each of the 24 cases: reference STEP, original
  point NPZ, encoder image PNG, STEP descriptor, original IR/code, feature tree
  and metadata. Repeated reference objects are deduplicated by content hash.
- `archive_plan.json`: original paths, byte sizes, expected hashes and the
  mapping from each case/role to its archive object.
- `objects/`: actual copied bytes, named by SHA256 plus original extension.
- `index.html`: a local browser entry that links archive copies and existing
  case snapshots/renders inside Review/05. It does not require the WSL source
  tree or original corpus path to view these registered case assets.
- `archive_actuals.json` and `archive_manifest.json`: copy counts, actual bytes
  and an independently verifiable SHA256 inventory.

Existing selected records, derived renders, CSVs and previous seals are not
overwritten. Preserve the **whole `05_qualitative` folder**, because the archive
index also links case snapshots and renders in its sibling folders.

## Scope and Boundaries

This is a local copy of registered qualitative evidence, not a backup of all
100,000 CAD objects, every training checkpoint or the software environment.
Train/validation/test JSONL are kept in full, but assets for unselected samples
referenced inside those files are not all copied here. Keep the original full
corpus and experiment outputs in their existing locations as well.

Checkpoint files are preserved only as the already registered **current
observations**. Their presence does not resolve the missing historical training
seed/runtime checkpoint-byte binding. No new provenance attestation is invented.

This archive is on the same local machine. Hash verification is not an off-device
backup. Nothing is trained, predicted, re-evaluated, re-rendered or repaired during
archiving. Original source files are read only; archive copies are byte-exact.
