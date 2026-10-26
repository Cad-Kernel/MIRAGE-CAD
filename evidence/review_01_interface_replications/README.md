# review 01 interface replications

Four decoder/interface seeds with nominally matched added updates, fixed upstream components and unresolved warm-start/checkpoint/truncation confounds. Read the later CPU audit. Do not claim strict causal textualization control or equivalence.

Historical records and raw rows are retained beneath this directory. Read `evidence/README.md` and
`docs/ANONYMIZATION.md` for source-hash/path conventions. Models and the complete corpus are catalogued, not embedded.

## Recorded four-seed coverage (observational comparison)

| Endpoint | A1E mean +/- sample SD | B2P mean +/- sample SD |
|---|---:|---:|
| Build | 73.80% +/- 6.41 pp | 90.65% +/- 3.24 pp |
| STEP export | 73.05% +/- 6.49 pp | 89.90% +/- 3.15 pp |
| Unconditional mean F@1 | 14.76% +/- 1.59 pp | 18.77% +/- 0.61 pp |

These are recorded outcomes, not an isolated causal effect of textualization. Upstream components
were fixed; initialization/history, best-versus-final rules, available mixed-step artifacts and the
source-reconstructed truncation asymmetry remain. Paired medians favor B2P in all four seeds, but
full-scoreable-set conditional median F@1 does not. Native rows and the later audit are in
`../cpu_audits/review01_native_results_v1` and `../cpu_audits/review01_dataset_v1`.
