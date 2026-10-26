# review 02 construction disjoint

A deterministic in-corpus construction-signature-disjoint STEP diagnostic. Exact signature/sequence overlaps are removed; only four single-operation test signatures are held out. Train-only descriptor retrieval is a baseline, not proof of broad generalization.

Historical records and raw rows are retained beneath this directory. Read `evidence/README.md` and
`docs/ANONYMIZATION.md` for source-hash/path conventions. Models and the complete corpus are catalogued, not embedded.

## Main recorded outcomes

| Endpoint | Train-only descriptor NN | MIRAGE textual plan |
|---|---:|---:|
| Build / STEP export | 500/500 | 410/500 |
| Scoreable | 500/500 | 410/500 |
| Conditional median CD | 6.492554 | 4.409928 |
| Conditional median F@1 | 1.163737% | 2.730887% |
| Unconditional mean F@1 | 1.838105% | 2.560103% |

Conditional medians use each method's own scoreable set. On 410 jointly scoreable cases, MIRAGE
has lower CD in 242 and higher F@1 in 270 of 407 non-tied cases. The absolute fidelity is low.
This is a four-held-out-single-operation-signature diagnostic, not a matching IID coverage-drop study.
