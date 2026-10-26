> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# 03 -- B0 vs B2 Multi-Seed Replication

This folder records the completed four-seed full-stack B0 vs B2 replication requested by Reviewer 2. Start with `18_four_seed_closed_summary.md` for interpretation and `result/01_four_seed_full_results.md` for all results.

## Current Status

```yaml
Protocol: FROZEN_FULL_STACK
Seed plan: FROZEN
Label-to-code mapping: COMPLETE
B2 replication scope: FROZEN_STRICT_FULL_STACK
Training scripts: PREPARED_AND_DRY_RUN_PASS
Training: ALL_4_SEEDS_COMPLETE
Prediction: ALL_4_SEEDS_COMPLETE
Gate evaluation: ALL_4_SEEDS_COMPLETE
Geometry scoring: ALL_4_SEEDS_COMPLETE
Generation actuals JSON: ALL_4_SEEDS_COMPLETE
Evaluation summary JSON: ALL_4_SEEDS_COMPLETE
Four-seed aggregate: COMPLETE
Review record: ALL_4_SEEDS_COMPLETE
Seed 1 status: CLOSED
Seed 2 status: CLOSED
Seed 3 status: CLOSED
Seed 4 status: CLOSED
Package status: CLOSED
Reviewer-2 B0/B2 seed-variance request: ADDRESSED_FOR_INTERNAL_STEP_COMPARISON
```

## Reviewer Mapping

Reviewer 2 requested repeated training seeds for the key comparisons, specifically naming B1a vs B2-Pred and B0 vs B2. The B1a/B2-Pred side is addressed by `Review/01`; this completed package addresses the B0/B2 training-seed request. Interpret it as a replication of full trained conditions, with their different stage/compute budgets.

## Files

- `01_frozen_protocol.md`  
  Frozen experimental plan, controls, metrics, and cautionary wording.

- `02_label_to_code_mapping.md`  
  Mapping from paper labels B0/B2 to local scripts, checkpoints, output paths, original results, and the remaining full-stack-vs-decoder-only scope decision.

- `03_script_preparation_record.md`  
  Frozen wrapper, helper scripts, dry-run command, seed-1 command, output paths, and evaluator commands.

- `04_seed1_component_progress.md`  
  Partial seed-1 component record through B0 no-plan, B2 alignment, and B2 STEP latent prior.

- `05_seed1_generation_record.md`  
  Seed-1 training/prediction completion record, output hashes, actuals summary, and gate/geometry commands.

- `06_seed1_gate_partial_geometry_record.md`  
  Seed-1 gate results, B0 geometry result, and missing B2 geometry command.

- `07_seed1_closed_record.md`  
  Complete seed-1 gate, geometry, paired comparison, interpretation, and next command.

- `08_seed2_component_progress.md`  
  Partial seed-2 component record through B0 no-plan, B2 alignment, and B2 STEP latent prior.

- `09_seed2_generation_record.md`  
  Seed-2 training/prediction completion record, output hashes, actuals summary, and gate/geometry commands.

- `10_seed2_closed_record.md`  
  Complete seed-2 gate, geometry, paired comparison, interpretation, and next command.

- `11_seed3_component_progress.md`  
  Partial seed-3 component record through B0 no-plan, B2 alignment, and B2 STEP latent prior.

- `12_seed3_generation_record.md`  
  Seed-3 training/prediction completion record, output hashes, actuals summary, and gate/geometry commands.

- `13_seed3_closed_record.md`  
  Complete seed-3 gate, geometry, paired comparison, interpretation, and next command.

- `14_seed4_interruption_record.md`  
  Seed-4 interruption audit: B0 complete, B2 alignment partial, safe recovery command.

- `15_seed4_component_progress.md`  
  Updated seed-4 state after clean alignment rerun and STEP prior completion, metrics, hashes, and continuation command.

- `16_seed4_generation_record.md`  
  Seed-4 training/prediction completion, checkpoint and sample-ID audit, hashes, P1a actuals, and gate/geometry commands.

- `17_seed4_closed_record.md`  
  Final seed-4 coverage, geometry, paired analysis, sampling failures, and closure.

- `18_four_seed_closed_summary.md`  
  Four-seed interpretation, means and sample SD, direction consistency, caveats, and reviewer-facing wording.

- `result/`  
  Complete reproducible results: per-seed and aggregate JSON, 10000 seed-query paired-case rows, full reports, and reproduction instructions.

## Run Order

```text
1. Inspect existing B0/B2 scripts and outputs. [COMPLETE]
2. Validate full-stack vs decoder-only B2 replication scope. [COMPLETE: strict/full-stack B2]
3. Write and check exact-match multi-seed wrapper. [COMPLETE]
4. Freeze actual command, seed list, output paths, and hash checks. [COMPLETE]
5. Run seed 1 only. [COMPLETE]
6. Gate + geometry for seed 1. [COMPLETE]
7. Register seed 1. [COMPLETE]
8. Close seed 2, then seed 3. [COMPLETE]
9. Complete seed 4 training + prediction. [COMPLETE]
10. Gate + geometry and result registration for seed 4. [COMPLETE]
11. Aggregate mean ± SD and paired comparisons across seeds 1-4. [COMPLETE]
```

Do not jump to later seeds before each previous seed has completed training, prediction, gate evaluation, geometry scoring, and review registration.

All four registered seeds are now closed. No seed 5 is planned. B2 improves Build, export, unconditional mean F@1, and paired median CD/F@1 in all four seeds; syntax and raw mean CD favor B0. Both the gains and failure tails are preserved in the result package.
