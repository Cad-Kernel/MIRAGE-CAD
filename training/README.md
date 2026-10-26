# Training sources and run provenance

## Versions, not a replacement history

| Path | Meaning |
|---|---|
| `source_snapshots/run_source/src/` | Snapshot of the actual WSL run-source tree; paths/names neutralized only. |
| `source_snapshots/development_source/src/` | Separate development/overlay snapshot used by later wrappers. |
| `historical/review_01/` | Recovered exact historical trainer, four source actuals and lineage audit. |
| `run_records/` | Retained trainer states, training reports, run actuals and adapter configurations; no tensor payloads. |
| `source_versions.jsonl` | Original and distributed hashes for each source file. |
| `experiments.json` | Entry-point and evidence mapping for the four revision experiments. |

The original algorithm/control flow and numerical constants are checked by non-string Python AST
comparison where the original source parses. Paths and personal text differ, so distributed SHA256 is
not claimed identical to the original SHA256. Existing frozen manifests retain historical hash claims;
use the explicit source mapping rather than changing their expected values silently.

## Entry points (inspect the experiment mapping first)

```bash
# Source-root-relative commands from the corresponding historical/run snapshot:
SEED=1 bash training_25k/cag_run_frozen_a1e_b2p_seed.sh
bash training_25k/cag_run_construction_disjoint_nn_baseline.sh
bash training_25k/cag_run_construction_disjoint_step_b2p_training.sh
SEED=1 bash training_25k/cag_run_b0_b2_fullstack_seed.sh

# Review 04 uses the separately archived development overlay:
bash training_25k/cag_run_exposure_policy.sh preflight
```

These are documented historical entry points, **not commands run by this integration**. Training and
cache-generation stages require their original dataset/checkpoints/runtime and explicit configuration.
Seeds 1--4, one-seed closure policy, checkpoint rules, stage-specific budgets and repair/P1a differences
are documented with each experiment; do not infer equal total compute from equal seed labels.

Create a separate inspection/configuration workspace, leaving archived sources unchanged:

```bash
python3 tools/materialize_training_workspace.py \
  --snapshot run_source --destination /path/to/new-run-source
```

This substitutes neutral path tokens and copies source only. It does not start training, fix historical
hash guards, recreate missing data, or certify that legacy Windows/WSL wrappers are turnkey. Review
the expected source/layout and hash mapping before any new run. The repeated-seed evidence is already
recorded; no retraining is needed to verify that evidence.

## Scope of the key comparisons

Review 01 repeats code/interface training with fixed upstream components and unresolved confounds.
Review 03 retrains full conditions independently, but B2 has extra stages, code lengths differ, and
grammar filtering changes downstream counts. Review 04 is one paired exposure diagnostic with a
documented runtime packing correction, not a pure ordering or multi-seed study.

## Environment metadata

`environment/` contains the captured current training/CAD environment metadata where available.
These snapshots supplement the historical requirements and run records; they do not reconstruct an
unrecorded historical training environment or redistribute the native CAD runtime.
