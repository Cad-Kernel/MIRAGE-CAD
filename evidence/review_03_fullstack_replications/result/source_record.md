> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Review/03 Result Package

Date: 2026-10-16. Status: CLOSED; seeds 1, 2, 3, 4 audited successfully.

## Files

- `01_four_seed_full_results.md`: complete readable results, including all errors and distributions.
- `cag_b0_b2_four_seed_eval_summary.json`: equal-weight seed aggregate, sample SD, deltas, and direction counts.
- `cag_b0_b2_seed_{1,2,3,4}_eval_summary.json`: complete per-seed metric/audit/provenance records, paired sample IDs, error counts, and outliers.
- `cag_b0_b2_seed_{1,2,3,4}_paired_cases.jsonl`: 2500 rows per seed preserving both arms' execution and geometry fields, scoreability, and unconditional F@1.
- `seed_{1,2,3,4}_full_results.md`: per-seed readable output generated from the same computation.

Raw prediction files, evaluator rows, and CLI logs remain in the source/scratch directories recorded in the JSON. No raw results were repaired, filtered from means, or overwritten by this analysis. CD > 1000 is an audit flag only.

## Code And Paths

```yaml
Windows source checkout: __DEV_ROOT__\src
WSL training checkout: __RUN_SOURCE_ROOT__
Result package: __EVIDENCE_SOURCE_ROOT__\03\result
Evaluator outputs: __DEV_ROOT__\scratch
Frozen runner: __DEV_ROOT__\src\training_25k\cag_run_b0_b2_fullstack_seed.sh
Analysis script: __DEV_ROOT__\src\training_25k\cag_summarize_b0_b2_fullstack_eval.py
```

The analysis script uses Python's standard library. It computes exact fair-binomial sign/McNemar tails with integer sums, checks unique IDs and ordering, compares source hashes across seeds, recomputes gate counts, and verifies that geometry candidates equal raw program predictions. Focused numeric checks cover exact tails, paired ties, quantiles, sample SD, and finite scoreability. An incomplete/misaligned dataset causes an exception rather than a closed summary.

Recompute in Windows PowerShell:

```powershell
python "__DEV_ROOT__\src\training_25k\cag_summarize_b0_b2_fullstack_eval.py" `
  --source-root "__RUN_SOURCE_ROOT__" `
  --scratch-root "__DEV_ROOT__\scratch" `
  --out-dir "__EVIDENCE_SOURCE_ROOT__\03\result"
```

Recomputation only reads trained/evaluated outputs and regenerates analysis files; it does not train, decode, or run CAD evaluation. Generated timestamps may differ. Source hashes and metric values should remain unchanged if the recorded inputs are unchanged.

## Metric Definitions

Scoreable requires syntax, execution, Build, solid validity, STEP export, and finite CD/F@1. Full-set conditional statistics use the arm's own scoreable subset. Paired statistics use the shared scoreable intersection. Unconditional F@1 assigns zero to every non-scoreable output.

CD is the mean of the two directional mean squared nearest-neighbour distances in the evaluator's native units. F@1 uses a distance threshold of 1% of the target bounding-box diagonal. Raw F@1 in JSON is 0-1; fields explicitly ending in `_pct` are 0-100.

The analysis script hash is stored in the aggregate JSON/full report. Frozen training script hashes are preserved in each seed's generation actuals. Evaluator-source hashes describe the source present at analysis time, not a historical native-binary build attestation.

## Public-Code Notes

This is an in-corpus STEP condition-level replication with four training seeds. B2 has additional stages and seed-dependent Stage 4b mix sizes; program repair is disabled but P1a plan canonicalization is retained. Do not label total training compute as identical or all repair as disabled.

Retain the recorded seed-4 alignment interruption/restart history. The frozen runner's original first-prior logging-directory issue is documented in `../15_seed4_component_progress.md`; reproducing its orchestration requires the `priors` log parent to exist before starting that stage. These analysis results do not modify the frozen runner or its recorded hash.
