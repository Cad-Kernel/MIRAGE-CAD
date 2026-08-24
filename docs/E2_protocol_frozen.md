# E2 — Is the explicit plan an informative diagnostic? Protocol, frozen before analysis

Frozen 2026-08-21, before any AUROC, correlation or interval in this experiment was computed.
Nothing below may be changed once the first outcome number exists; if something has to change, the
change is recorded as an amendment with its date and reason, and the superseded version stays.

## Research question

Does the explicit construction plan provide a useful intermediate diagnostic of downstream failure
and geometric fidelity, **beyond what is already available from the continuous latent**?

This is the one property the paper currently asserts about explicit text without quantifying it.
Section 7 lists four things the plan provides as an interface; three are exercised in Results, and
failure localisation is supported only by three case-style analyses. E2 either upgrades that to an
empirical claim or leaves it explicitly unquantified.

## No training

No model is trained, fine-tuned or re-selected. The arm is **B2-Pred on its 500-row STEP slice**,
already generated and already scored. One GPU pass is required, and it computes a diagnostic that
was never stored, not a new model.

## The arm, and why its diagnostics are shared

`B2P_metadata.json` records `conditioning_at_inference: predicted plans (same file the deployed arm
uses)`. The plan diagnostics are therefore properties of a plan file shared with the deployed arm,
while the outcomes are B2-Pred's own. That is the correct pairing for this question: it asks whether
a plan-level observable predicts *this arm's* downstream failure.

## Diagnostics

Four, and the first two must not be conflated — they were, in the manuscript, until this protocol
was written.

| symbol | definition | stored? |
|---|---|---|
| `lat_cos` | `cos(z_ir_hat, z_ir)`, the **prior's** predicted construction latent against the encoded reference plan. `z_ir_hat = prior(z_m)` where `z_m` is the encoded observation. | **no — one GPU pass** |
| `plan_cos` | `cos(E_ir(predicted_ir), E_ir(reference_ir))`, both through `normalize_ir_text`. This is what the manuscript calls *IR cosine*, and it is a similarity between two **plan texts**. | yes, `outputs/tab_ir_quality_step_C.json` |
| `op_set_f1` | `op_set_metrics(pred, ref)["f1"]` over `OP_*` tokens only | yes, same file |
| `op_seq_lcs` | LCS ratio over the `OP_*` token sequence | yes, same file |

`plan_cos` is a plan-level diagnostic, not a latent one. The distinction is the whole point of the
experiment: `lat_cos` is what an implementation without an explicit plan could compute, and every
other row needs the plan to exist.

Grammar validity is reported descriptively only. If fewer than 20 of the 500 plans are
grammar-invalid, no AUROC is computed for it, because an AUROC on a handful of positives is noise
with a decimal point.

## Outcomes

**Outcome 1 — validity-failure localisation.** For each diagnostic, over all 500 rows:

    AUROC(diagnostic, build_ok)
    AUROC(diagnostic, step_export_ok)

**Sign convention, frozen.** All four diagnostics are oriented so that *higher is better plan
agreement*, and both AUROCs predict **success**. An AUROC of 0.5 is no signal; above 0.5 means a
better-agreeing plan is more often followed by a successful build or export. Column headers say
`AUROC(success)` so no reader has to guess the direction.

**Outcome 2 — geometric fidelity.** Spearman `rho_s`, each on its own metric-scoreable subset,
with the subset size stated per cell:

    rho_s(diagnostic, cd)            on rows with a non-null cd
    rho_s(diagnostic, f_score_1pct)  on rows with a non-null f_score_1pct

**Expected directions, frozen.** Lower CD is better, so a *negative* rho indicates a useful
diagnostic. Higher F@1 is better, so a *positive* rho does. Tables mark the useful direction with
an arrow so a sign error cannot pass as a finding.

## Statistics

- **Paired bootstrap, B = 10,000, seed 20260821.** Resampling is over **samples**, not over
  diagnostics, so the pairing between a row's diagnostics and its outcome survives.
- The headline comparison is `ΔAUROC = AUROC(plan diagnostic) − AUROC(lat_cos)`, with a 95 %
  percentile interval, one row per plan diagnostic per outcome.
- Spearman intervals are percentile bootstrap on the same resampling scheme.
- **No classifier is trained.** No threshold is selected. No diagnostic is combined with another.
- Denominators are stated per cell and never pooled across outcomes.

## Interpretation, frozen before the numbers exist

All four readings below are safe to write; which one applies is decided by the intervals, not by
preference.

1. **Plan diagnostics clearly higher** (ΔAUROC intervals excluding zero, positive): the explicit
   plan provides a more informative observable diagnostic of downstream validity failure than
   latent similarity alone.
2. **Comparable** (intervals containing zero): plan and latent carry similar predictive signal,
   while the plan exposes named operations and ordering in an inspectable representation.
3. **Latent higher**: textualisation did not improve predictive diagnostic strength over latent
   cosine, although the plan still provides operation-level observability and intervention points.
   This is a real possible outcome and it does not retract anything the paper claims.
4. **Geometry correlations weak throughout**: agreement with one canonical reference history is
   weakly coupled to geometric fidelity, consistent with construction non-identifiability
   (§7.3).

## The caveat that must travel with every E2 number

`op_set_f1`, `op_seq_lcs` and `plan_cos` are measured against the **dataset's reference
construction**, which is one construction consistent with the target, not the only one. A low score
therefore does not mean wrong geometry or a bad CAD model — the posterior over histories given a
solid is not concentrated, which is §7.3's argument and not a caveat invented for this experiment.

E2 asks whether **reference-plan agreement helps predict a downstream outcome**. It does not ask,
and cannot answer, whether plan agreement equals geometric correctness. Any sentence in the paper
that uses an E2 number must respect that distinction.

## What E2 cannot conclude

- Nothing about a decoder trained without a plan: no such model is trained here.
- Nothing causal. These are observational associations on one arm, one seed, 500 rows.
- Nothing about a human reading the plan. Inspectability remains asserted, not measured.

## Amendments

**2026-08-21, data source corrected before any outcome was accepted.** The protocol named
`outputs/tab_ir_quality_step_C.json` as the source of `plan_cos`, `op_set_f1` and `op_seq_lcs`.
That file is a **different 500-row draw** from the test split: it shares only 82 sample ids with
the B2-Pred slice. The first analysis run joined to those 82 rows and reported them; that output is
void and is not an E2 result.

The correct source is `outputs/ablation_prefix/score_step_prior.json`, verified three ways: its 500
ids overlap the E1 arm 500/500, its `predicted_ir` is byte-identical to B2-Pred's for all 500 rows,
and its summary reproduces the manuscript's own figures (`ir_cosine_mean` 0.8859 → 0.886,
`op_set_f1_mean` 0.8801 → 88.0). The manuscript was never affected: its 0.886 and 0.047 already
come from this file, on the same rows as every other number in that table.

The analysis script now **refuses** a partial join instead of noting it and continuing.

**2026-08-21, `lat_cos` computation corrected, twice, before any outcome was accepted.** Two
independent faults, both caught by the sanity check against the prior's own training-time cosine
rather than by inspection:

1. The reference target was `normalize_ir_text(reference_ir)`. The prior is trained against
   `read_text(ir_path)`, the raw IR file text (`train_latent_prior.py:68`); the normalisation
   belongs to the plan-text metric only.
2. `load_step_brep_tensors` was called without `strict=True`. Its default returns **all-zero**
   descriptors when the JSON cannot be read, and `data/25k/step_features_test.jsonl` stores
   Windows paths that WSL cannot open, so all 500 rows received an identical zero descriptor. Use
   `data/25k/test.jsonl`, whose paths are relative and readable.

Either fault alone produced a mean `lat_cos` near 0.01 against a training-time value of ~0.955 —
a noise baseline that would have made every plan diagnostic look strong for a reason unrelated to
the plan. After both corrections the mean is 0.9562, off by 0.001. No result computed on a
pre-correction baseline is admissible.

## Execution order

1. `src/scratch/e2_latent_cosine.py` — GPU, WSL, `ai_dev`. Computes `lat_cos` per `sample_id` for
   the 500 STEP rows and writes `scratch/e2_latent_cosine.jsonl`. Read-only with respect to every
   checkpoint.
2. `src/scratch/e2_analysis.py` — CPU. Joins the four diagnostics to B2-Pred's outcomes, computes
   both outcomes with the intervals above, and writes the table.

Step 2 refuses to run if step 1's output is missing, rather than silently dropping `lat_cos` and
answering a different question.
