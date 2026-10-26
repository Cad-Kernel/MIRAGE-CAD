> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Candidate Selection And Path-Locking Policy

Date: 2026-10-22. Version: `qual_gallery_candidate_v1`.

This is retrospective, metric-guided qualitative sampling after the quantitative results are known. It is not a preregistered experiment, an unbiased performance estimate, or an optimization of the model. Rules below are recorded before candidate IDs are emitted. No training, model forward, generated-code execution, rendering or evaluator rerun is authorized by this step.

## Primary Source

Use only the historical deployed B2 pathway reported in `MIRAGE-V2/final/ComputersGraphics_version2/main.tex`, table `tab:generation`, on all2500 IID test IDs per modality. Do not substitute Review/01-04 runs, choose a best seed, combine checkpoints, use train-role predictions, or mix Fusion360 into this cohort.

Exact source pattern, relative to WSL `__RUN_SOURCE_ROOT__`:

- Test IDs/inputs: `data/25k/test.jsonl`; assert disjointness from `train.jsonl` and `val.jsonl`.
- Raw/used plans: `outputs/lora_ir_25k_stage3b/predicted_ir_test_<modality>{,_p1a}.jsonl`.
- Raw/intermediate/executed code: `outputs/qwen25_coder_1_5b_program_25k_stage4b/gen_test_<modality>_stage3b{,_repaired,_repaired_p0}.jsonl`.
- Geometry input: `outputs/stage3b_geometry/geom_input_<modality>_stage3b.jsonl`.
- Standalone gate: Windows `MIRAGE-V2/scratch/exec_eval_25k_stage3b_<modality>`.
- Geometry: Windows `MIRAGE-V2/scratch/geom_stage3b_<modality>_stage3b/geometry_nbest_rows.jsonl`.

This historical condition has **program repair=true** (extrude-on-face then P0), separately from P1a plan canonicalization. The source wrapper and geometry run metadata must agree. Native gate counts must round to the paper's reported Syntax/Build/export percentages: Text98.3/57.2/53.1, Image94.3/57.8/52.3, Point89.5/55.4/52.6, STEP94.5/70.0/66.2. Counts/order/associations are checked directly, not just inferred from matching filenames.

Current files can identify exact historical generated plans/code and their recorded outcomes, but current checkpoint bytes and default CLI seed alone are not proof of the historical training-run seed/checkpoint bytes. If runtime binding is not present in legacy metadata, leave registry training seed/checkpoint SHA null, record the known model directory and current observed hashes separately, and flag the unresolved historical provenance. Such cases remain candidates, not verified/selected. Do not retroactively invent a frozen historical run seal.

The WSL source/data root is not assumed to be a Git checkout. Record its actual Git availability and preserve a null commit when it is an unversioned copy. Observe the canonical Windows repository separately; never label that repository's commit as the commit of a different copied tree.

## Cohort And Metrics

- One row per test sample/modality/condition. Retain every test row in the source cohort audit, including failures and metric outliers.
- Scoreable means reference present, all five geometry-run gates passed, finite CD/F@1. Individual unscoreable CD/F@1 remain null, not zero.
- Compute empirical percentile ranks on each modality's complete scoreable cohort. Ties receive the mean0-based rank divided by(n-1); a singleton receives0.5.
- Sort directions: higher F@1 is better, lower CD is better. No clipping or outlier exclusion. Quantiles used for selection are ranks, not a numerical fidelity threshold.
- Candidate selection requires standalone/geometry gate flags to agree, a present target and exactly one geometry candidate. All disagreements/missing records remain in the cohort audit with explicit reasons; no silent relabeling.
- Operations/family come from the reference IR, not the generated model. `operation_count` counts reference `F ... OP_*` feature records, including OP_SKETCH. This is not necessarily the same operation-count definition as the construction-disjoint signature protocol. Complexity uses provided test metadata/lookup, never a visual guess.

## Deterministic Selection

Process modalities in order Text, Image, Point, STEP. Within each modality select distinct source IDs, in the order below. Reuse across modalities is allowed and explicitly identified; it never creates extra independent test parts. Final ties use lexicographic sample ID.

1. Main `representative_success`: among scoreable eligible cases, closest F@1 percentile to0.50, then closest CD percentile to0.50. This means executable/scoreable success, **not semantic or high-fidelity reconstruction**.
2. Main `hard_failure`: among eligible cases failing a standalone gate, choose the most frequent first-failure stage, then its most frequent exact native error string. Choose the case closest to the reference-operation-count median within that error group, then sample ID. Do not call a low-F@1 case a proven missing-hole/topology failure without visual evidence.
3. Appendix `near_median`: closest CD percentile to0.50, then closest F@1 percentile to0.50, excluding already chosen IDs.
4. Appendix `low_tail`: closest F@1 percentile to0.10, then closest CD percentile to0.90, excluding already chosen IDs. This is not the single worst case.
5. Appendix `rare_operation`: prioritize the least frequent reference OP_* by number of test objects containing that operation, then scoreable cases closest to median F@1, then sample ID. Rarity is explicitly **within this2500-object IID test cohort**, not global corpus rarity. Keep the actual rare-operation name and frequency.
6. Appendix `high_complexity`: highest documented complexity tier, then largest reference-feature operation count, then scoreable/median-F@1 preference and sample ID. A failure remains a failure if the selected high-complexity case is not scoreable.
7. If any documented complexity tier is still absent, add one appendix tier-coverage candidate per missing tier, choosing a scoreable case nearest that tier's median F@1 where available. Otherwise use the dominant-failure selection within that tier. Use `near_median` or `hard_failure` plus an explicit tier-coverage tag.

The initial target is8 main candidates plus16 appendix candidates; tier-coverage supplements may increase this count. If a category has no eligible unused case, save a shortage entry rather than quietly changing its definition. Candidates are not visually selected figures. Keep the full cohort, selection order/reasons, rank denominators, exclusions and source hashes for later review.

## Paths And Asset Status

Extract exact raw/used plans, raw/intermediate/executed code, exact text query, raw gate/geometry rows, original native error messages and JSONL record locators into each real case folder. Hash original file bytes and extracted literal UTF8 field bytes; do not repair, reformat or execute code while packaging. A code excerpt is separately labeled and never replaces the full program.

Register an actual source image, point NPZ,50-statistic STEP descriptor JSON, reference STEP or original reference render only after checking existence/nonzero bytes. Preserve source path style plus physical JSONL line and stable key. The exact query text is the dataset `text` field, not a rewritten caption. Point NPZ is the source cloud; historical normalized/FPS tensors were not necessarily retained. STEP input is the global-descriptor JSON, not a topology-aware graph input.

Predicted STEP and matched-camera gallery views are **not** inferred from `step_export_ok=true`: the original scorer deletes temporary candidate.step/PLY. Leave actual-path registry cells null unless a real persistent asset is found. Use `assets.json` planned/missing/not_applicable/failed states for future assets. Failed programs must never receive a reference or retrieval solid as their predicted output. Original reference images do not satisfy the pending matched-camera two-view target/prediction requirement by themselves.

## Exit State

`Candidate selection: COMPLETE` and `Path locking: COMPLETE` may be recorded after schema/row/source/hash checks pass. `Gallery: NOT_RENDERED`, `Visual verification: PENDING`, `Registry status: candidate` remain explicit. Fusion360, edit audit and external benchmark feasibility remain separately scoped work. Existing quantitative evidence packages and their weights/results are read-only.
