> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Fusion 360 Case Selection and Rendering Protocol v1

Status: FROZEN before selecting case IDs or rendering this gallery.
Scope: retrospective qualitative sampling from the sealed 400-case inventory and
native-log taxonomy. This is not a preregistration, a new evaluation, or a new
estimate of aggregate performance. No training, prediction regeneration,
program execution, geometry repair, or metric recomputation is permitted.

## Preservation and Phase Boundary

Step 1 and Step 2 remain CLOSED, with their sealed bytes unchanged. All existing
files in `audit/source_files_v1.json` are copied byte-for-byte into a
content-addressed `raw_archive_v1/objects/` store. The original path, role,
existence status, byte count, and SHA256 are retained. Missing historical files
remain missing. This includes complete registered JSONL files, not just the
selected lines. It is not a backup of the entire training corpus, all model
weights, or all 1,725 official Fusion 360 test objects.

The full research archive is retained even if the editor requests fewer figures.
Later formatting or submission subsets must be separate versions. Raw STEP,
metrics, logs, plans, codes, mesh arrays, unlabelled views, transformations,
camera records, selected-case metadata, and selection ranks are not overwritten.

## Deterministic Selection

Six main-text candidates and twelve additional appendix candidates are selected.
Every panel contains Reference / CAD-Recode / MIRAGE generated-plan / NN
retrieval in this order. The historical evaluated, repaired external predictions
are used, not the later no-repair internal experiments.

Selection uses only the sealed numeric metrics and native-log taxonomy. It does
not read images, render geometry, or assign semantic shape defects. Measured zero
IoU participates as zero; unavailable IoU/CD is excluded from the relevant
numeric cohort, never imputed as zero.

Percentiles are midranks `(average zero-based rank + 0.5) / N`. Ties are sorted
by sample_id. All cohorts and ranks are computed before excluding previously
selected IDs. Slots are allocated in ascending eligible-cohort size, then the
slot order below, so a rare failure is not exhausted by a broad metric slot.
The first still-unused candidate in the fixed ranking is selected. Exhaustion
is a hard error, not permission for visual hand replacement. Every eligible
candidate and its priority is saved. Hash rankings use SHA256 of
`fusion360-gallery-v1|<slot>|<sample_id>`.

| Slot | Bucket and fixed eligible cohort | Priority within cohort |
| --- | --- | --- |
| M01 | Relative MIRAGE success: MIRAGE/CAD-Recode jointly IoU-scoreable, MIRAGE IoU > CAD-Recode IoU | nearest median positive IoU difference |
| M02 | Near-median: MIRAGE/CAD-Recode jointly IoU-scoreable | MIRAGE IoU percentile nearest 0.50; then MIRAGE CD percentile nearest 0.50 |
| M03 | Low-tail scoreable: same joint cohort | MIRAGE IoU percentile nearest 0.10; then MIRAGE CD percentile nearest 0.90 |
| M04 | MIRAGE execution failure with MISSING_API_ATTRIBUTE or UNEXPECTED_KEYWORD_ARGUMENT, CAD-Recode CD-scoreable | hash rank |
| M05 | CAD-Recode advantage: joint IoU cohort, CAD-Recode IoU > MIRAGE IoU | nearest median positive IoU difference |
| M06 | NN contrast: MIRAGE/NN jointly IoU-scoreable, nonzero absolute IoU difference | absolute-difference percentile nearest 0.75; direction not constrained |
| A01 | MIRAGE/CAD-Recode jointly IoU-scoreable | MIRAGE IoU percentile nearest 0.25 |
| A02 | same joint cohort | MIRAGE IoU percentile nearest 0.75 |
| A03 | same joint cohort | MIRAGE IoU percentile nearest 0.90 |
| A04 | all CAD-Recode IoU-scoreable | CAD-Recode IoU percentile nearest 0.50 |
| A05 | all CAD-Recode IoU-scoreable | CAD-Recode IoU percentile nearest 0.25 |
| A06 | CAD-Recode execution failure, MIRAGE CD-scoreable if any; otherwise all CAD-Recode execution failures | hash rank; any fallback explicitly recorded |
| A07 | MIRAGE EMPTY_PREDICTION_MESH | hash rank |
| A08 | MIRAGE REMESH_FAILURE | hash rank |
| A09 | MIRAGE STEP_EXPORT_FAILURE | hash rank |
| A10 | MIRAGE CD-scoreable with IOU_BOOLEAN_FAILURE | hash rank |
| A11 | NN EMPTY_PREDICTION_MESH | hash rank |
| A12 | MIRAGE KERNEL_CRASH_STAGE_UNRESOLVED | hash rank |

For quantile priorities, absolute percentile distance is minimized, not the raw
metric. Final ties use sample_id. Selection buckets are display strata, not new
failure diagnoses or representative population weights. Main and appendix
candidates can later be omitted for page limits, but the full locked set stays.

## Two Coordinate Series

The user approved retaining both series before rendering.

1. **Metric-space shape comparison.** Each shape is independently centered at
   its mesh bbox midpoint, scaled by its own largest bbox extent, and shifted
   by +0.5, matching the existing external evaluator's coordinate policy.
   No rotation, ICP, or manual alignment is applied. All four methods use the
   same fixed unit-cube framing, not separate visual auto-fit. Caption this as
   shape-normalized: global scale and translation errors are deliberately
   removed. Render tessellation is not the exact mesh used for historical
   scoring, and no new metric is computed.
2. **Reference-world coordinate diagnostic.** Reference STEP, MIRAGE, and NN
   retain their native coordinates. CAD-Recode DSL coordinates receive only
   the declared inverse input/DSL convention:
   `x_world = x_DSL * (reference_largest_extent / 200) + reference_bbox_midpoint`.
   This is not an independent best fit of the prediction. A shared union bbox
   of the renderable four methods determines one frame per case and view.
   This diagnostic has no score and does not establish that method outputs
   were originally trained with identical unit conventions. Tiny or displaced
   shapes remain tiny or displaced; no method-specific zoom is allowed.

Both forward and inverse 4x4 transformations, original bboxes, method-specific
render eligibility, shared frame, and projected size are retained. Frames are
computed only from renderable geometry. Reference-world geometry must not be
interpreted as a new physical-accuracy benchmark.

## Render Contract

- CPU-only import and tessellation of existing STEP. Do not reexecute programs.
- CadQuery/OCP already installed in `cadrecode_env`; no package installation.
- Deflection: `1e-4 * shape largest bbox extent`; angular tolerance 0.3 radians.
  This is visualization-only tessellation, not the frozen metric mesh.
- Preserve native vertices and triangle indices in NPZ. Do not smooth, fill,
  repair, simplify, or rotate geometry. Exact-coincident vertex welding for
  visible-edge extraction is allowed and documented, not topology repair.
- 640 x 640 unlabelled PNGs; orthographic projection (FOV not applicable).
- Views: isometric azimuth 45 degrees/elevation 35.264389682754654 degrees;
  front azimuth 270 degrees/elevation 0 degrees. 82% frame occupancy.
- Background RGB (248,249,251), body (176,190,205), feature edges (72,79,89).
  One fixed world-space directional light and shading algorithm for all methods.
- Camera basis, pose, projected center, span, size, lighting, and background
  must be identical across methods within a case/view/coordinate series.
- Mesh import/tessellation exceptions are recorded without replacing case IDs
  or retuning tolerance. Historical execution/export failures receive text
  placeholders, not fabricated surfaces. Historical empty-mesh/remesh failures
  remain unscoreable placeholders even if a different rendering tolerance might
  produce triangles. Their original STEP files remain archived.
- CD-scoreable shapes whose IoU boolean evaluation failed may be rendered as
  real geometry with an explicit IoU-unavailable label. Missing IoU is not zero.
- Preserve unlabelled views and metadata separately from labelled panels, HTML,
  and contact sheets so later typography/layout changes need no re-render.

## Visual Review and Completion

Render first, then review both views before any semantic annotation. Labels
such as missing hole, wrong extrusion, or oversimplified body require a
view-specific observation; metrics alone are insufficient. Ambiguous features
remain unconfirmed. Separate geometric observations from native API failures.
The 120/160 API/schema-pattern execution errors are observed log categories,
not proof of a causal mechanism or of whether generation versus API version
compatibility caused them.

Validation must check exact source/archive hashes, prior seals, eighteen unique
IDs, deterministic selection rerun, shared camera/scale contracts, reversible
transforms, finite/nonblank geometry renderings or explicit subpixel warnings,
unaltered historical metrics, missing-vs-zero semantics, two views, and local
links. Step 3 is not fully CLOSED until visual semantic review is documented.
Reviewer-facing external-generalization claims remain limited; no broad
generalization or accurate reconstruction claim follows from this gallery.
