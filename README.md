# MIRAGE-CAD: code and revision evidence

MIRAGE-CAD generates executable parametric CAD programs from **one active input modality per query**:
text, an image, a point cloud, or a STEP-derived global descriptor. It does not evaluate simultaneous
multimodal fusion. The reported STEP pathway effectively uses 50 global kernel statistics, not an
entity-level topology-aware B-Rep encoder.

This repository contains the historical submission code together with a separately organized revision
evidence bundle. Historical results and their unfavorable outcomes are retained. Asset preparation is
not semantic validation, and a completed training run is not evidence of a fully controlled comparison.

## Start here

| Location | Purpose |
|---|---|
| `evidence/README.md` | Experiment-by-experiment evidence guide and limitations |
| `training/README.md` | Original training entry points, two source snapshots, historical versions and run records |
| `docs/ANONYMIZATION.md` | Anonymous transformations, path tokens and original/distributed hash distinction |
| `docs/KNOWN_LIMITATIONS.md` | Scientific and reproduction limits that must accompany the results |
| `docs/ARTIFACT_SCOPE.md` | Included files and every explicitly catalogued omission |
| `tools/verify_revision_artifact.py` | CPU-only file/hash and raw-row checks, without models or CAD execution |
| `miragecad/`, `pipeline/`, `analysis/`, `external/`, `reports/` | Historical submission layout, preserved separately from revision snapshots |

```bash
python3 tools/verify_revision_artifact.py
```

This verifies the **distributed anonymous copies**, not the original private byte strings. It does not
load a language model, train, execute CAD, certify semantic correctness, or reproduce every published
experiment. Full reproduction additionally requires the dataset, model checkpoints and Flluma runtime.

## Revision experiments

| Package | Scope | Interpretation |
|---|---|---|
| Review 01 | Four A1E/B2P decoder/interface seeds with fixed upstream components | Observed coverage directions; initialization, checkpoint and truncation confounds remain. Not a strict matched textualization experiment. |
| Review 02 | Frozen construction-signature-disjoint STEP split plus train-only descriptor NN | In-corpus diagnostic; four held-out single-operation signatures, not broad compositional generalization. |
| Review 03 | Four independent full-stack B0/B2 STEP runs | Complete-condition replication; B2 has extra stages and unequal total compute/sequence length. |
| Review 04 | One paired-seed exposure-policy diagnostic across four modalities | Matched schedules and documented packing amendment; cumulative exposure also changes, so not order-only. |
| Review 05 | Four-pathway qualitative candidates and raw/render assets | Historical repaired deployed B2 condition, not the new no-program-repair replications. |
| Review 06 | Fusion 360 correspondence, failure taxonomy and side-by-side assets | External performance boundary; availability of CD and IoU is distinguished. |
| CPU audits | Dataset token/label audit, result checks, parameter illustrations, baseline metadata | Scoped checks with explicit unknowns, not a new model experiment. |

For full-stack B0/B2, mean Build is 51.38% +/- 5.74 pp versus 61.91% +/- 5.09 pp across four seeds.
This gain coexists with lower B2 syntax and worse conditional mean CD in every seed. Median/paired
geometry and unconditional F-score must not be substituted for unfavorable mean-CD tails.

## Reproduction and code versions

The original `pipeline/` layout remains a historical recipe. The revision training sources are under
`training/source_snapshots/`, with run-source and development-overlay versions kept separate.
The exact recovered Review 01 trainer is under `training/historical/review_01/`.
Do not replace a historical trainer by the current file and assume the checkpoint rule is identical.

Machine-specific prefixes and identified personal strings are replaced by documented neutral tokens.
The archived wrappers are not a turnkey installer: configure data/runtime paths and inspect historical
hash guards before training. No model weights or complete training corpus are added to Git.

## License and third-party material

Project-authored code remains under the existing [0BSD license](LICENSE). This does not relicense
the training corpus, Fusion-derived inputs, upstream code, model checkpoints or quoted external
materials. See `docs/THIRD_PARTY_AND_DATA.md`. Full upstream papers, model payloads, complete corpus
manifests and private editorial correspondence are not bundled as ordinary project source.
Their status, source identifiers and hashes are catalogued where relevant. This local integration
does not certify that all data/runtime redistribution requirements have been resolved.

The evidence bundle has not been pushed by the integration task. Figure adoption, semantic labels,
historical prediction-to-weight binding and a final anonymous-access/full-reproduction check remain
separate from the CPU checks recorded here.

## Local Git history and remote status

The local repository was rebuilt as one anonymous root commit containing the sanitized source and
revision evidence. Earlier commits, remote-tracking references and their object database are absent
from this repository. Historical scientific identifiers in the evidence are retained as provenance.

This local operation did not push or change the hosting service. An existing remote can still expose
the earlier history, and fetching it can reintroduce that history locally. Do not treat the old hosted
repository as anonymous until remote publication and logged-out access have been checked separately.
See `docs/GIT_HISTORY.md` and `evidence/git_history_anonymity_status.json`.
