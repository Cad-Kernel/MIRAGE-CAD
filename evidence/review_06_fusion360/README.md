# review 06 fusion360

400 matched IDs, three evaluated methods, a native/log-based failure taxonomy, and paired shape/original-coordinate galleries. 226 MIRAGE and 392 CAD-Recode CD-scoreable cases do not have identical IoU denominators. Specific shape defects require visual confirmation.

Historical records and raw rows are retained beneath this directory. Read `evidence/README.md` and
`docs/ANONYMIZATION.md` for source-hash/path conventions. Models and the complete corpus are catalogued, not embedded.

## Native outcome accounting (400 IDs per method)

| Outcome | MIRAGE generated plan | NN-IR | CAD-Recode |
|---|---:|---:|---:|
| CD scoreable | 226 | 392 | 392 |
| Syntax failure | 2 | 3 | 0 |
| Execution failure | 160 | 2 | 8 |
| STEP export failure | 5 | 0 | 0 |
| Kernel crash, stage unresolved | 1 | 0 | 0 |
| Empty prediction mesh | 5 | 3 | 0 |
| Remesh failure | 1 | 0 | 0 |

For MIRAGE, unexpected keyword arguments (75) and missing API attributes (45) account for
120/160 execution failures (75%). This is a log-based classification, not a visual diagnosis.
IoU is available for 212 MIRAGE, 389 NN-IR and 379 CAD-Recode cases; boolean failures stay null.
The recorded 200-pair MIRAGE/CAD-Recode IoU medians are 0.0604/0.9226. Two display conventions
(normalized shapes and original coordinates with declared unit transforms) must remain separate.
