> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# CPU Export and Two-View Rendering Results

Date: 2026-10-22. Rendering assets: `rendering/cpu_v1/`.

## Completed Work

The locked 24-case qualitative candidate set has been exported and rendered on
CPU. No training, model forward pass, new plan/code prediction, extra program
repair, or historical metric recomputation was performed.

| Item | Actual result |
| --- | ---: |
| Locked cases | 24 (8 main candidates, 16 appendix candidates) |
| Original reference objects | 22 unique targets across 24 modality-case records |
| Newly retained prediction STEP files | 20/20 historically scoreable cases |
| Historical hard failures | 4, preserved without retry or shape substitution |
| Render meshes | 44 (24 reference-case meshes + 20 prediction meshes) |
| Primary two-view PNGs | 88 (48 reference + 40 prediction) |
| Supplemental common-frame PNGs | 12, for 3 out-of-target-frame cases |
| Total CAD view PNGs | 100, each 640 x 640 RGB |
| Case comparison panels | 24, each 1340 x 1490 |
| Candidate contact sheets | 5 (main 8 + one sheet per modality) |
| Actual render-path CSV | 24 rows, 23 columns |
| Blank CAD renders | 0 |
| Shared camera/scale checks | PASS |
| Camera and CPU raster unit tests | 5/5 PASS |
| Original candidate-package files | 385/385 hash-verified unchanged |

This is a completed asset-generation stage, not final manuscript figure selection.
All records remain **candidate**. Fusion 360/CAD-Recode and semantic-edit figures
are outside this rendering run.

## Where to Look

Start with
[the local gallery](__EVIDENCE_SOURCE_ROOT__/05_qualitative/rendering/cpu_v1/index.html).
It links every case to its two-view comparison, full generated plan, literal code
excerpt, exact original input asset, original reference, historical gate/geometry
rows, new prediction STEP where one exists, and failure evidence where it does not.

The two registries are intentionally separate:

- `qualitative_case_registry.csv`: original locked selection/provenance record,
  unchanged. Its null historical STEP/render fields are not retroactively rewritten.
- `rendering/cpu_v1/render_asset_registry.csv`: actual **newly generated** STEP,
  PNG, case-page, plan/code and failure-log paths, joined by `case_id`. Four failed
  cases have blank prediction paths, not substituted geometry or zeros.
- `rendering/cpu_v1/render_assets.json`: corresponding typed records and contact
  sheet paths. CSV and JSON were independently round-trip checked.

Per-case layout:

```text
rendering/cpu_v1/cases/<case_id>/
  prediction.step                 # only the 20 historical scoreable cases
  native_export.json              # current CPU re-export provenance
  native_cli.log
  reference_mesh.npz
  reference_mesh.json
  prediction_mesh.npz             # only historical scoreable cases
  prediction_mesh.json
  reference_iso_pos.png
  reference_iso_neg.png
  prediction_iso_pos.png          # only historical scoreable cases
  prediction_iso_neg.png
  *_shared_union.png              # supplementary views for 3 cases only
  render_manifest.json            # camera, scale, pixels, hashes
  panel.png
  index.html
```

Original case files remain under `cases/<case_id>/`, separately from these assets.
Reference STEP/input images/point files remain at their original registered paths.
They were not overwritten or silently copied under new scientific identities.

## Condition and Provenance

These figures correspond to the **historical deployed repaired B2 condition**
from the original four-modality comparison, as declared in the locked selection
policy. They do **not** mix Review/01 A1E/B2P, Review/02 construction-disjoint,
Review/03 B0/B2 seeds, or Review/04 exposure-policy arms.

The executed source is each case's byte-hash-verified `code/prediction.py`, already
containing the historically evaluated repair stages. No additional repair was
applied. Raw code, intermediate repaired code, raw plan and P1a plan remain
separately preserved in the original case folder.

The original evaluator deleted its temporary STEP files. Therefore these new
STEP files are explicitly **current native CPU re-exports of locked historical
code**, not recovered old files. Successful re-export does not establish byte
identity with deleted files or resolve the historical training seed/runtime
checkpoint-byte binding gap. Existing missing provenance remains missing.

Native executable used:

```text
__FLLUMA_ROOT__\build\Desktop_Qt_6_8_3_MSVC2022_64bit-Release\bin\FllumaCLI.exe
```

Native embedded Python: 3.11.11. Existing WSL tessellation environment:

```text
__USER_HOME__/miniforge3/envs/cadrecode_env/bin/python
CadQuery 2.5.0.dev0; NumPy 2.2.0
```

The native STEP-to-CustomNode mesh-import probe was unavailable and is retained
under `rendering/cpu_v1/probes/`. Both references and predictions therefore use
the same existing `probe_cadrecode_mesh.py::tessellate_step` function. Render-only
linear deflection is 0.03 mm and angular deflection 0.3 rad. Exact coincident
vertices are welded for edge rendering; no shape repair, smoothing, registration,
point normalization, translation or independent rescaling is performed.

These visualization tessellation settings do not replace any frozen metric
protocol. CD/F@1 values displayed in the gallery are unchanged historical values,
not measurements made from the new visualization meshes.

## Camera and Clipping

Both views are orthographic: azimuth 45 and 225 degrees, each at elevation
35.264389682754654 degrees. Primary frames are derived from the **reference**
bounding-box center and projected extent, with 82% image fit. Prediction uses
the exact same camera and pixels-per-mm within each comparison.

Three cases extend outside the target-derived frame:

| Modality | Sample | Treatment |
| --- | --- | --- |
| Text | flluma_0097413 | Original clipped views retained; additional common union-frame pair |
| Image | flluma_0093014 | Original clipped views retained; additional common union-frame pair |
| Point | flluma_0090825 | Original clipped views retained; additional common union-frame pair |

There are six affected primary prediction views. In supplementary views both
reference and prediction use the same expanded frame. Prediction is never
independently fitted to make its size or placement appear correct. All remaining
primary views, and every supplementary view, are within frame.

Small predictions intentionally remain small. In particular, near-zero overlap
or size-collapse examples must not be enlarged independently for presentation.

## Qualitative Reading

The main success candidates were selected around the **complete-cohort F@1
median among executable/scoreable cases**, not as visually excellent semantic
reconstructions. Rendering now makes that distinction inspectable:

- Some executable outputs omit or alter major target structures. For example,
  the image candidate `flluma_0093014` has a target fin array but a much simpler
  generated plate-like output. This is a visible geometric mismatch, not a new
  claim about the exact failed operation or its cause.
- The low-tail and rare-operation candidates include severe size or structure
  differences. They remain in the package according to the locked selection
  policy; they were not replaced after seeing the images.
- The four hard failures have two reference views and original native errors,
  but no predicted solid. Error categories remain grounded in existing logs:
  unresolved topology, unsupported loft argument, wrong handle type, and missing
  extrusion height.
- STEP median candidates are not evidence that every modality has equivalent
  semantic accuracy. These are individual figures, not a new statistical test.

The five contact sheets and supplementary union-frame predictions were visually
reviewed for nonblank geometry, framing and label placement. This is asset QA,
not a blinded semantic-quality study. Final figure selection, captions and
reviewer-facing wording still require manuscript-level review.

## Audit and Preservation

`cpu_render_actuals.json` records execution counts, pixel checks and camera checks.
`render_registry_csv_validation.json` records the literal CSV round trip.
`render_inventory_v1.json` seals new render assets, supporting scripts and this
record with SHA256. It is separate from the original candidate seal.

The source scripts are under `05_qualitative/render_support/`. The initial
tessellation run encountered a missing output directory for a historical failure
reference; a directory-creation fix allowed verified continuation. Local HTML
links were adapted for Windows/WSL paths. Neither fix changed candidates, code,
render tolerances, cameras, metrics or experimental definitions. Failed probes
and current successful export logs are retained.

The assets are preserved locally in Review/05. Hash manifests support integrity
checking but are not a separate-machine backup. No experiment in Review/01-04
was reopened and no training weight was modified.
