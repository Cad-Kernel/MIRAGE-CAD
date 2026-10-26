> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Candidate Selection And Path-Locking Results

Date: 2026-10-22.

```yaml
Selection: COMPLETE_DETERMINISTIC_RETROSPECTIVE_RULES
Registry: 24_RECORDS_63_COLUMNS
Main candidates: 8
Appendix candidates: 16
Unique target objects: 22
Current status of every case: candidate
Original input/reference source assets missing: 0
Path/locator/hash/typed CSV checks: PASS
Selection contract tests: 13_PASS
Schema negative mutation checks: 14_PASS
Review04 final evidence inventory: ALL17_FILES_UNCHANGED
Persistent generated STEP assets: NOT_CREATED
Matched-camera two-view renders: NOT_STARTED
Visual/semantic verification: PENDING
Historical training seed/checkpoint-byte binding: UNRESOLVED
Training/model/CAD execution by this task: NONE
```

## Source And Selection Scope

The primary gallery candidates use only the historical deployed B2 condition from `MIRAGE-V2/final/ComputersGraphics_version2/main.tex`, table `tab:generation`, on2500 fixed IID test objects per modality. This is not the new Review/04 ArmA/B experiment and not a selected replication seed. Exact gate counts match the paper after its one-decimal rounding. All10000 sample/modality source rows are retained; no metric-outlier or failed query was deleted from the selection cohort.

Program repair is TRUE: extrude-on-face followed by P0. P1a plan canonicalization is separately recorded. Raw plan, canonicalized plan, raw program, intermediate repaired program and actually evaluated program are separate immutable literal extractions. Do not relabel this condition no-repair or combine these cases with Review/01-04 outcomes in an unlabeled panel.

Rules were written before candidate IDs were emitted but after quantitative results were available: this is retrospective metric/complexity sampling, not preregistration or an unbiased sampling estimate. Empirical percentiles use the complete scoreable cohort of each modality, with midranks for ties. Central scoreable success, dominant native failure, CD-near-median,10th-percentile F@1 tail, least frequent reference operation and maximum-complexity cases are all included. No visual attractiveness criterion was used.

## Main Eight Candidates

Success means executable and scoreable here, not semantically correct or high-fidelity. F@1 is shown as percent; unscoreable individual metrics remain unavailable, not zero.

| Modality | Role | Sample ID | Reference tier | Ref feature count | CD | F@1 (%) | Actual gate outcome |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| text | representative_success | flluma_0095386 | L2 | 1 | 5.88250165978 | 15.0877326 | pass |
| text | hard_failure | flluma_0090079 | L4 | 6 | unavailable | unavailable | execution_failure |
| image | representative_success | flluma_0093014 | L3 | 6 | 31.5394982601 | 4.14981618 | pass |
| image | hard_failure | flluma_0090051 | L4 | 8 | unavailable | unavailable | execution_failure |
| point | representative_success | flluma_0091123 | L3 | 7 | 75.7342815284 | 3.66145833 | pass |
| point | hard_failure | flluma_0090719 | L3 | 6 | unavailable | unavailable | execution_failure |
| step | representative_success | flluma_0097267 | L3 | 4 | 2.47191086612 | 19.7260791 | pass |
| step | hard_failure | flluma_0090147 | L2 | 7 | unavailable | unavailable | execution_failure |

## Native Main-Failure Evidence

These are exact observed native error summaries, not fabricated stack traces. More specific API/topology interpretation must continue to cite the saved native row. Low F@1 alone is not labeled a proven missing hole or missing feature.

- text / `flluma_0090079`: `exec error: topology reference 'join_001:top_face:b9ce48e7f7b9' did not resolve any face`. Dominant first-failure stage has1027 cases; this exact message occurs100 times. Native messages: `cases/q-flone-text-b2legacy-flluma_0090079/logs/native_failure_messages.json`.
- image / `flluma_0090051`: `exec error: Part.loft() got an unexpected keyword argument 'profile'`. Dominant first-failure stage has913 cases; this exact message occurs71 times. Native messages: `cases/q-flone-image-b2legacy-flluma_0090051/logs/native_failure_messages.json`.
- point / `flluma_0090719`: `exec error: target must be a FeatureHandle`. Dominant first-failure stage has852 cases; this exact message occurs52 times. Native messages: `cases/q-flone-point-b2legacy-flluma_0090719/logs/native_failure_messages.json`.
- step / `flluma_0090147`: `exec error: extrude_on_face join/add requires height`. Dominant first-failure stage has614 cases; this exact message occurs50 times. Native messages: `cases/q-flone-step-b2legacy-flluma_0090147/logs/native_failure_messages.json`.

## All Twenty-Four Candidates

Each modality has6 records and covers all reference complexity tiers L1,L2,L3,L4. There were no category shortages or extra tier-fill rows. Repeated target IDs across modalities are separate pathway outputs, not extra independent objects.20 candidates are scoreable;4 are native execution failures.

| Modality | Role | Sample ID | Tier | Ref feature count | CD | F@1 (%) | Empirical F@1 percentile | Ref template family |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| text | representative_success | flluma_0095386 | L2 | 1 | 5.88250165978 | 15.0877326 | 0.4996139 | ribbed_support_plate |
| text | hard_failure | flluma_0090079 | L4 | 6 | unavailable | unavailable | unavailable | revolved_hub_mount |
| text | near_median | flluma_0096516 | L2 | 7 | 5.37998697195 | 6.72554348 | 0.237837838 | face_recursive_mount |
| text | low_tail | flluma_0097413 | L3 | 6 | 51.9202421028 | 3.36843297 | 0.100772201 | heat_sink_base |
| text | rare_operation | flluma_0091927 | L1 | 1 | 0.154190905725 | 23.0452198 | 0.784555985 | sphere_stock |
| text | high_complexity | flluma_0090820 | L4 | 8 | 1.51278904372 | 15.1341986 | 0.5003861 | swept_pipe_bracket |
| image | representative_success | flluma_0093014 | L3 | 6 | 31.5394982601 | 4.14981618 | 0.5 | linear_ribbed_heat_sink_mount |
| image | hard_failure | flluma_0090051 | L4 | 8 | unavailable | unavailable | unavailable | lofted_transition_bracket |
| image | near_median | flluma_0093772 | L3 | 4 | 45.3460520418 | 8.54518581 | 0.748953975 | crescent_lug_profile |
| image | low_tail | flluma_0096266 | L2 | 4 | 311.36513173 | 0.09765625 | 0.10334728 | pocketed_service_plate |
| image | rare_operation | flluma_0091927 | L1 | 1 | 0.237362594408 | 0 | 0.0493723849 | sphere_stock |
| image | high_complexity | flluma_0094417 | L4 | 8 | 4.83655964172 | 4.24748563 | 0.507112971 | swept_pipe_bracket |
| point | representative_success | flluma_0091123 | L3 | 7 | 75.7342815284 | 3.66145833 | 0.5 | pipe_clamp |
| point | hard_failure | flluma_0090719 | L3 | 6 | unavailable | unavailable | unavailable | linear_ribbed_heat_sink_mount |
| point | near_median | flluma_0091975 | L2 | 3 | 45.8066469668 | 6.22558594 | 0.680956307 | control_plate |
| point | low_tail | flluma_0090825 | L3 | 7 | 911.579979565 | 0.390625 | 0.0981038747 | pipe_clamp |
| point | rare_operation | flluma_0091927 | L1 | 1 | 24.8295995483 | 0 | 0.0333882935 | sphere_stock |
| point | high_complexity | flluma_0098388 | L4 | 8 | 4.62764939995 | 3.70065789 | 0.502885408 | lofted_transition_bracket |
| step | representative_success | flluma_0097267 | L3 | 4 | 2.47191086612 | 19.7260791 | 0.499692686 | trapezoid_profile_foot |
| step | hard_failure | flluma_0090147 | L2 | 7 | unavailable | unavailable | unavailable | face_feature_service_cover |
| step | near_median | flluma_0096700 | L3 | 4 | 2.71689943869 | 20.6486407 | 0.535648433 | rounded_slot_profile_plate |
| step | low_tail | flluma_0094365 | L3 | 6 | 7.30242012684 | 4.58776596 | 0.0995697603 | linear_ribbed_heat_sink_mount |
| step | rare_operation | flluma_0095267 | L1 | 1 | 0.175197497157 | 25.8785377 | 0.703441918 | sphere_stock |
| step | high_complexity | flluma_0096596 | L4 | 8 | 0.485081832303 | 19.2258883 | 0.480639213 | swept_pipe_bracket |

Reference feature counts include OP_SKETCH and count `F ... OP_*` reference records. Do not substitute these counts for the different construction-signature operation-count definition in Review/02. Complexity is supplied metadata, not estimated from rendered complexity.

Rare operation in all four modality selections is OP_SPHERE, present in3 of the2500 test objects. Text/Image/Point use `flluma_0091927`; STEP uses `flluma_0095267` under the fixed tie/median preference. This is rarity within the current test cohort, not a claim of global corpus rarity.

## Exact Source And Extraction Paths

Private evidence root: `__EVIDENCE_SOURCE_ROOT__\05_qualitative`.

Original source/data root: WSL `__RUN_SOURCE_ROOT__`. Canonical Windows implementation repo: `__DEV_ROOT__`. The WSL root is not a Git repo. The currently observed Windows commit is recorded separately; it is not the historical commit of the WSL copy.

| Role | Actual original path pattern |
| --- | --- |
| Test inputs/IDs | `__RUN_SOURCE_ROOT__/data/25k/test.jsonl` |
| Raw / P1a plans | `__RUN_SOURCE_ROOT__/outputs/lora_ir_25k_stage3b/predicted_ir_test_<modality>{,_p1a}.jsonl` |
| Raw / intermediate / evaluated code | `__RUN_SOURCE_ROOT__/outputs/qwen25_coder_1_5b_program_25k_stage4b/gen_test_<modality>_stage3b{,_repaired,_repaired_p0}.jsonl` |
| Native geometry input | `__RUN_SOURCE_ROOT__/outputs/stage3b_geometry/geom_input_<modality>_stage3b.jsonl` |
| Native gate | `__DEV_ROOT__\scratch\exec_eval_25k_stage3b_<modality>\execution_rows.jsonl` |
| Native geometry | `__DEV_ROOT__\scratch\geom_stage3b_<modality>_stage3b\geometry_nbest_rows.jsonl` |

Each record has a real `cases/q-flone-<modality>-b2legacy-<sample_id>/` folder containing:

- `case.json`, `provenance.json`, `assets.json`, `prediction_locator.json`.
- `input/exact_text.txt`: unchanged full dataset text field, not a rewritten caption.
- `plans/raw.txt`, `plans/canonicalized.txt`: literal generated/used plans.
- `code/raw_prediction.py`, `code/extrude_repaired.py`, `code/prediction.py`: all three code stages; no program executed while extracting.
- `code/excerpt.txt`: explicitly marked first40-line excerpt, not a replacement for full code.
- `reference/training_ir.txt`, `reference/program.py`: source-record reference text; original STEP/image/NPZ/descriptor/tree/metadata paths and hashes are in provenance/assets.
- `logs/gate_row.json`, `logs/geometry_row.json`, and native failure-message JSON only for actual failures.

## What Is Not Yet An Asset

Native evaluators exported candidate.step and sampled PLY in temporary directories and deleted them. STEP-export success does not mean a persistent predicted STEP file exists. Every candidate's actual predicted STEP/render registry cells are null. Future destinations appear only as `planned_path` in assets.json; hard failures have `not_applicable` prediction geometry, never a reference/retrieval substitute.

Original iso PNGs are verified reference/input images. They do not satisfy the outstanding two-view, shared-camera target/prediction gallery requirement. Source NPZ paths are known; exact historical normalized/FPS tensors are not newly regenerated or asserted identical. STEP input points to the50-global-statistic JSON descriptor, not a richer face-edge graph.

## Validation And Remaining Provenance

CSV63-column order/types match the24 case snapshots; artifact-tool typed worksheet and CSV reimport checks pass. The final CPU validator checked470 distinct source/extraction/closure records, all physical JSONL line hashes/stable keys, exact literal field extraction, native metrics, actual path existence and the complete case inventory. No original input/reference source assets are missing.

All selection choices reproduce from the saved10000-row cohort.13 selection tests PASS;14 intentionally malformed schema mutations were rejected. The fixed contract checker covers every validation keyword used in this schema; it is not represented as an independently certified general Draft2020 validator. Quantitative Review/04's17 final evidence artifacts remain byte-identical.

Legacy reports did not attest a historical training seed or bind checkpoint bytes at generation time. Registry `seed` and `checkpoint_sha256` are deliberately null. Current adapter/prefix hashes and source scripts were observed and saved but are not retroactive run attestations. Thus path/extraction validation can pass while registry status remains `candidate`; do not silently promote the cases to `verified`/`selected`.

## Query Entry Points

- `qualitative_case_registry.csv`: all63 fields for24 outputs, private absolute source paths plus real package-relative extracts.
- `selection/cohort_v1.jsonl`: complete10000-row source cohort, all metrics/failures/ranks/complexity/operations.
- `selection/candidate_rows_v1.json`: IDs, exact rules/order, reasons, selection details and immutable typed snapshots.
- `selection/source_audit_v1.json`: source hashes, full native gate summaries, operation/tier distributions and current checkout/checkpoint observations.
- `selection/registry_validation_v1.json`: final PASS, case-file hash inventory and all remaining boundaries.

## Next Boundary

1. Review the main8 target/input/plan/code candidates without relabeling executable success as faithful reconstruction. Record any exclusion/replacement reason; do not alter the source cohort or quantitative results.
2. Prepare a separate deterministic native export/render script for persistent STEP and two or more common target/prediction camera views. No independent prediction rescaling. Do not execute it without the operator's next run authorization.
3. Preserve failures as failures with reference views, raw code/plan and actual native error panel. Do not invent a predicted shape.
4. After visual/two-view and historical-provenance review, explicitly promote or exclude cases and assemble figures/captions. Fusion360/CAD-Recode gallery stays a separate cohort; parameter edits and external benchmark feasibility are not completed here.

No new internal training, model generation, native evaluation or CAD rendering was run. Review/05 gallery is not CLOSED; only candidate selection and existing-path locking are complete.
