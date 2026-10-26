# review 03 fullstack replications

Four full-stack B0/B2 seed pairs on 2,500 fixed STEP queries. Report seed mean/sample SD, paired and unconditional metrics, lower syntax and adverse mean-CD tails. Total training compute, code lengths and Stage4b filtered counts are not identical.

Historical records and raw rows are retained beneath this directory. Read `evidence/README.md` and
`docs/ANONYMIZATION.md` for source-hash/path conventions. Models and the complete corpus are catalogued, not embedded.

## Per-seed executable coverage

| Seed | B0 Build | B2 Build | B0 export | B2 export |
|---|---:|---:|---:|---:|
| 1 | 55.68% | 68.76% | 55.00% | 68.28% |
| 2 | 51.88% | 57.60% | 48.76% | 56.88% |
| 3 | 43.12% | 62.76% | 42.76% | 61.60% |
| 4 | 54.84% | 58.52% | 54.20% | 57.32% |

Mean Build is 51.38% +/- 5.74 pp versus 61.91% +/- 5.09 pp. Mean export is 50.18% +/- 5.67 pp
versus 61.02% +/- 5.29 pp. B2 paired medians and unconditional mean F@1 favor B2 in each seed,
but syntax is lower and full-scoreable-set mean CD is worse in all seeds. Source counts, total
computation and code lengths are not all matched. See the paired-case JSONLs and complete aggregate.
