> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Folder And Path Convention

## Identity And Layout

Use a stable lowercase case ID, for example the pattern `q-<corpus>-<modality>-<arm>-s<seed>-<sample_id>` (a pattern, not an enrolled case). Each method/seed output has its own case ID. `comparison_group_id` joins outputs of the same target and modality, especially Fusion 360 MIRAGE generated-plan, MIRAGE retrieval/NN, and CAD-Recode outputs. Do not merge different targets using visual similarity.

```text
05_qualitative/
  qualitative_case_registry.csv
  qualitative_case_registry.schema.json
  cases/<case_id>/
    case.json                    typed snapshot of this CSV row
    provenance.json              original paths, hashes, row locators, model/code provenance
    assets.json                  asset status and render/camera metadata
    input/                       exact text, input image/point cloud/STEP when packaged
    reference/model.step         optional preserved copy, linked to original SHA256
    plans/raw.txt                original generated plan, if available
    plans/canonicalized.txt      actual P1a plan used by decoder, if applicable
    code/prediction.py           full executed prediction, not an excerpt
    code/excerpt.txt             separately identified figure excerpt
    prediction/model.step        only when a real exported output exists
    renders/reference/view01.png
    renders/reference/view02.png
    renders/prediction/view01.png
    renders/prediction/view02.png
    logs/                        gate, geometry, raw traceback/failure, render errors
  selection/                     cohort IDs/hashes, rules, candidate/exclusion records
  figures/                       later figure layouts and captions with case IDs
```

Folders under `cases/` are created only when a real case is registered. The initial setup was header-only; the 2026-10-22 update registered24 actual candidates under policy03/result04. No placeholder IDs, metrics, fake success rows or fictitious existing paths are allowed. Keep assets unframed by publication layout until figure assembly; a failure need not have a predicted STEP/render.

## Source Paths And Portable Assets

1. Preserve actual absolute Windows, WSL or UNC source paths verbatim in the private registry/provenance. Record their path style and machine context. Do not assume a Windows file exists because a guessed WSL translation is plausible.
2. Package-relative paths use forward slashes relative to `05_qualitative/`, without `..`. Use these only for files actually created. Proposed future destinations belong in `assets.json` as `planned_path`, not in actual-path CSV cells.
3. Typical original roots are `__DEV_ROOT__\scratch\...` for Windows CAD evaluation, `__RUN_SOURCE_ROOT__/outputs/...` for training predictions, and `__RUN_SOURCE_ROOT__\...` for Windows access to WSL. These are roots, not proof of any particular case asset.
4. For each existing asset, save SHA256, byte count, verified-at UTC, path style and source role. Shared source files can be referenced rather than copied thousands of times.
5. A JSONL record locator must include file path/SHA256, one-based physical line, sample ID and modality/arm/seed where present. Preserve the actual field names (`prediction`, `predicted_ir`, etc.). Check the line's stable key before extraction. `prediction_record_locator_path` points to that locator file if no standalone plan/code exists yet.
6. Record both checkout path and commit plus dirty-file/script hashes. A commit alone does not identify uncommitted wrappers. Hash plan/code checkpoints and evaluator sources separately.

Suggested `provenance.json` content: schema version; case ID; source split and sample key; experiment/protocol hash; checkout commit and relevant dirty source hashes; startup/final checkpoint hashes; seed; repair and P1a policy; input/reference/plan/code/evaluator file records; JSONL locators; extraction commands and timestamps. Keep raw generated plan, P1a plan and Stage4b packed prefix distinct. A training-only packed prefix is not a test-time generated plan.

## Asset Status And Rendering

Each entry in `assets.json` records `asset_role`, `status`, `source_path`, `package_path`, `planned_path`, `sha256`, `missing_reason` and optional `view_id`/camera/render metadata. Use status `existing`, `planned`, `missing`, `not_applicable` or `failed`; a file is existing only after it has been verified. A zero-byte or failed-render file is not a completed render.

For view01/view02 record camera position/target/up, projection, normalization/scale, bounding box, renderer/version, material/background, mesh conversion settings and source STEP hash. Match target/prediction cameras and scale per target; do not independently resize an incorrect prediction to make it look accurate. `reference_render_path`/`predicted_render_path` are primary-view shortcuts; `assets.json` owns the complete two-or-more-view inventory. Keep original model/render and annotated publication panel separate.

For no-solid failures, prediction assets are `not_applicable` with the gate reason, not zero-valued geometry. For an expected but lost file, use `missing`; for a failed render, use `failed` and retain renderer logs. Geometry can be scoreable but visibly wrong; preserve that as a distinct failure class.

## Metric And Selection Rules

- Store individual-case metrics, not an arm-level median copied into each row. `f1_at_1_fraction` and `iou_fraction` are fractions, e.g. 0.0273 means 2.73%; CD needs its original units/scaling and evaluator definition. Preserve evaluator protocol/normalization/sampling and point-count details in `metric_protocol_path`.
- Missing metric cells are blank/null with `metric_status` and reason. An unscoreable individual CD/F@1 is not silently replaced by zero. Failure-as-zero unconditional aggregates belong to a separately labeled aggregate calculation and denominator, not this measured-case field.
- Selection cohort must state evaluation IDs, modality/condition/seed, scoreable denominator, metric sort direction, quantile rule, exclusions and tie-breaking. Success in executability and success in geometry are separate. A near-median choice must name the metric/cohort used; do not infer representative status from a pleasing render.
- Complexity/operation labels come from reference metadata with a source link, not guessed from the generated shape. Keep rare-operation/high-complexity sampling as tags even if the primary `case_type` is failure or near-median.
- For Fusion 360, use separate condition rows with a shared comparison group and target. Keep preprocessing, scoreability and CAD-Recode provenance explicit. Availability does not imply common training data or a causal architecture comparison.

## Public Release

The private registry preserves original machine paths for retrieval. A later public copy should use verified package-relative assets and a path mapping, strip usernames/private paths from the released copy, retain hashes and licenses, and leave the private original intact. This setup does not declare source data redistribution rights or publish anything.
