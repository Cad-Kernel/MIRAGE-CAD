> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Qualitative Evidence Registry

Date: 2026-10-22.

Status: CANDIDATES_AND_EXISTING_PATHS_LOCKED. Registered records:24 (8 main,16 appendix;22 unique target objects). All records remain `candidate`, not verified/selected figures. Matched-camera gallery rendering and visual/semantic review have NOT started.

This package records evidence for the four input pathways and separately scoped external Fusion360 analysis. The current automatic selection is retrospective, deterministic metric/complexity sampling, not best-looking figure selection or a new performance experiment. It launches no training, model forward, CAD execution or rendering.

- `qualitative_case_registry.csv`:24 populated63-column candidate rows. One row represents one observed sample/modality/condition output; historical training seed is null when unattested. Different methods on the same target require separate rows linked by `comparison_group_id`.
- `qualitative_case_registry.schema.json`: typed case-record contract and CSV column order. Arrays use JSON inside CSV cells; booleans use `true`/`false`; blank cells mean null, never numeric zero. `notes` may be empty text. Every case must provide a selection reason and cohort source.
- `01_reviewer_requirements.md`: verified reviewer requests and evidence checklist.
- `02_folder_and_path_convention.md`: original-source references, portable package paths, two-view rendering, failure logs and Fusion 360 grouping.
- `03_candidate_selection_policy.md`: rules recorded before IDs were emitted, source-condition mapping, metrics/rank denominators, tie breaks, tier/rare-op sampling and source/provenance limitations. This is explicitly post-results qualitative selection, not preregistration.
- `04_candidate_selection_and_path_locking_results.md`: all24 candidate IDs/metrics/tiers, main8 failure messages, exact source/asset paths, validation results and the next rendering boundary.
- `selection/source_audit_v1.json`: all2500 IID test rows per modality match the historical paper Table7 gate rates; plans/code/geometry inputs and IDs agree. Exact observed source hashes, original native summaries, complexity/operation frequencies and checkout limitations retained.
- `selection/cohort_v1.jsonl`: all10000 sample/modality outcomes, including every failure/outlier, empirical scoreable-cohort ranks and selection eligibility; no query or metric-tail filtering.
- `selection/candidate_rows_v1.json`: immutable selected-candidate snapshot, full policy/reasons, before-edit CSV hash, per-slot choices and zero category shortages. This does not mark final figure selection.
- `selection/candidate_contract_tests_v2.json`:13 current rule/locator/rarity/tier/seed-provenance guard tests PASS. The v1 test snapshot is historical, prior to handling a non-Git source root.
- `selection/registry_validation_v1.json`: all24 CSV typed records match snapshots/schema contract, actual paths and literal extraction/JSONL locators;470 distinct source/extraction/closure records checked,14 malformed-schema mutation tests rejected, source IDs reselected deterministically. Covers every keyword used in this fixed schema; not a general Draft2020 validator claim.
- `selection/path_lock_manifest_v1.json`: timestamped candidate-package snapshot,24 stable IDs, hashes for every case file/registry/report/selection authority. Later visual decisions must create a new version rather than silently rewriting this snapshot; this is not a new scientific training protocol freeze.
- `cases/<case_id>/`: exact query text, raw/P1a plans, raw/intermediate/executed code, reference IR/code, native gate/geometry/error-message rows, excerpts, locators and source/asset manifests. Actual generated STEP/gallery-render cells are null; future paths exist only as planned assets.
- `support/build_registry.mjs` and `registry_population_v1.json`: existing artifact-tool builder extended to populate the original CSV without schema/column changes; typed worksheet and CSV roundtrip PASS. Initial header preserved in `selection/registry_header_before_v1.csv`; review preview is a registry screenshot, not CAD imagery.
- `support/select_gallery_candidates.py` and `validate_candidate_registry.py`: CPU-only source extraction/selection and final auditing. No generated program is imported or executed.

Use test or external-test cases for reconstruction claims. The 945 Stage4b train-role plans and tokenizer failures are training diagnostics, not held-out qualitative reconstruction evidence. Keep them in `train_diagnostic` if later registered.

Current cohort is the **historical deployed B2, repaired-code Table7 condition**, not Review/04 and not a best seed from the replication runs. `program_repair=true` (extrude-on-face then P0), with separate P1a plan canonicalization. Per modality the six candidates are representative executable/scoreable success, dominant native hard failure, CD-near-median, F@1 low-tail, rare reference operation and high complexity. Together they cover L1-L4 in each modality without extra tier-fill rows. Rarity is within the2500-part IID test cohort, not globally across the corpus. A representative executable success is not automatically a faithful semantic reconstruction.

Original models/images/checkpoints/results remain authoritative and unchanged. Literal text/plan/code/row fields were copied into real case folders with source hashes and physical line locators; no source was moved or repaired during extraction. All original input/reference source assets for these cases are present. Native evaluation's temporary predicted STEP/PLY outputs were deleted by the original scorer, so matched target/prediction views and persistent generated STEP exports remain future work.

Legacy provenance limitation: the WSL source/data root is an unversioned copy, not a Git repository. Its commit, historical training seed and runtime-bound checkpoint SHA are not invented. Current Windows repo/current-checkpoint observations are separately recorded, not substituted as historical run attestations. Resolve that provenance and perform visual/two-view review before promoting cases to `verified`/`selected`.

Review/01-04 remain CLOSED; this task verified all17 files in Review/04's final evidence inventory unchanged. Do not restart internal training or reevaluate these cases. Next prepare a separately authorized deterministic two-view export/render workflow with common target/prediction cameras/scale, preserving each failure as a failure. Fusion360 side-by-side analysis, semantic edits and external benchmark feasibility are not completed by this registry.
