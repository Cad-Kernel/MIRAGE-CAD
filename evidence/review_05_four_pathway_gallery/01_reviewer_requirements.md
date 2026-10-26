> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Reviewer Requirements And Evidence Checklist

Verified against `__EVIDENCE_SOURCE_ROOT__\reviews.txt` and `lettre.txt` on 2026-10-17. Reviewer numbers below follow the document headings, not file order.

| Source | Requirement | Registry / Asset Evidence |
| --- | --- | --- |
| Reviewer 1, comment 4, reviews.txt line 118 | Four modalities; successful and failed programs; generated plan; concise feature-tree or code excerpt; at least two rendered views; median and distribution tails | `modality`, `case_type`, `selection_cohort_path`, quantile/metric fields; full plan/code source plus excerpt; reference/prediction view records in `assets.json` |
| Reviewer 1, comment 4, line 118 | Parameter perturbations before/after; identify unreachable numeric arguments | Optional `parameter_edit` cases; paired comparison ID; exact edits, before/after geometry and unreachable arguments in provenance/notes. Not completed by a reconstruction gallery alone |
| Reviewer 4, reviews.txt line 27 | Exact text inputs, references, plans and executed outputs; complexity-tier sampling, rare operations, explicit failures; Fusion 360 side-by-side with CAD-Recode | Exact-text source asset; complexity and operation metadata; selection rationale; same-target comparison groups |
| Reviewer 4, reviews.txt line 29 | Analyze badly reconstructed shapes/features even when measurable; distinguish training/preprocessing differences | `scoreable_geometrically_wrong` and feature-specific notes; same metric protocol or explicit noncomparability; model/processing provenance |
| Editor, lettre.txt lines 45-47 | Representative successes/failures across all four pathways, including Fusion 360 analysis; distinguish executability from reconstruction | Separate Build/export/scoreability flags and geometry values; no success label inferred solely from execution |

The schema/path convention below is our implementation choice, not a verbatim reviewer instruction. Two rendered views should share documented target/prediction cameras and normalization. For hard failures with no output solid, preserve the reference views and actual failure log/code; explicitly label prediction geometry unavailable. Never render a reference or retrieval substitute as the failed model output.

## Before Marking A Case Selected

- [ ] Exact sample/modality/arm/seed, data split, checkpoint and repair/canonicalization policy are known.
- [ ] Prediction source is identified by JSONL hash, one-based line and stable record key, not only a guessed filename.
- [ ] All original input/reference/plan/code/evaluation/log paths are registered, with missing and not-applicable assets distinguished.
- [ ] Selection cohort, complexity tier, metric quantile and reason are documented. Preserve the candidate/exclusion log; do not show only favorable cases.
- [ ] Build/export/scoreability is verified independently of geometry quality. Measured F@1/IoU use fractions in [0,1]; CD scale and threshold/normalization/sampling definitions are linked.
- [ ] At least two target views and, when geometry exists, the matching two prediction views are rendered with recorded cameras. Display metrics are traced to the unchanged evaluator, not recomputed from figure screenshots.
- [ ] Full generated plan and full code remain accessible; excerpts are separately marked as excerpts.
- [ ] Failure cause is backed by logs or explicitly marked as a visual hypothesis, not inferred solely from low F@1.
- [ ] Fusion 360 comparisons refer to the same target and documented point preprocessing. Preserve both coverage and geometry failures, including measurable-but-wrong outputs. Missing CAD-Recode results remain missing.
- [ ] No training/validation case is presented as unseen test reconstruction. Packaging for public release separately checks licensing and removes private machine-specific paths from the public copy.
