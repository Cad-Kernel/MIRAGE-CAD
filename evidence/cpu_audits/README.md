# CPU audits and explanatory assets

`review01_dataset_v1` contains the 50,000-row token/label audit. Source-root-relative descriptor loading
gives A1E prompt median 137 with no truncation. B2P has 19 EOS-only rows, 6,096 partially supervised
body-truncated rows, and 644 rows with no target supervision: 6,740 rows (26.96%) lose body tokens.
The no-target subset is included in 6,740, not added again. The older 6,333/631 reconstruction is
reproduced by making descriptor paths unresolved. This does not restore historical runtime byte binding.

`review01_native_results_v1` preserves the raw native rows used for the four-seed result checks.
`result_arithmetic_v1` and `local_evidence_v1` retain scoped numerical/integrity diagnostics.
`parameter_visuals_v1` contains six recorded perturbations re-exported on CPU, including failures.
`external_baselines_v1` contains official-version/weight/metric metadata, not new baseline executions.
Full third-party paper/code responses remain upstream references rather than project-licensed files.

No model training, inference or new geometric rescoring is performed by the bundle verifier.
