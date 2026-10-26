# review 04 exposure policy

One paired seed with 4,689+500 plan steps and 1,182 actual downstream steps per arm. Both arms share the optimizer-reset/LR boundary. The training-only target-preserving packing amendment is disclosed. This changes exposure as well as order.

Historical records and raw rows are retained beneath this directory. Read `evidence/README.md` and
`docs/ANONYMIZATION.md` for source-hash/path conventions. Models and the complete corpus are catalogued, not embedded.

## One-paired-seed outcomes

All rows use 2,500 cases; rates and F@1 are percentages. Non-scoreable F is zero only for the unconditional mean.

| Input | Arm | Syntax | Build | Export | Scoreable | Unconditional mean F@1 |
|---|---|---:|---:|---:|---:|---:|
| STEP | A | 97.28 | 60.96 | 60.08 | 58.52 | 10.795239 |
| STEP | B | 83.48 | 57.88 | 55.36 | 53.00 | 8.015022 |
| Point | A | 97.44 | 52.60 | 51.76 | 50.68 | 2.380663 |
| Point | B | 82.56 | 54.32 | 50.24 | 47.52 | 2.991428 |
| Text | A | 98.36 | 50.44 | 49.80 | 49.32 | 7.861099 |
| Text | B | 84.96 | 53.92 | 51.80 | 47.68 | 7.464002 |
| Image | A | 97.04 | 54.08 | 52.84 | 51.32 | 2.618009 |
| Image | B | 84.76 | 56.84 | 53.48 | 50.56 | 3.069695 |

A is STEP-first then balanced; B is balanced from start. Syntax and scoreability are lower for B
in all modalities. Point/Image paired geometry favors B, STEP favors A, and Text is mixed.
This single-seed diagnostic changes exposure as well as order and is not a uniform gain.
