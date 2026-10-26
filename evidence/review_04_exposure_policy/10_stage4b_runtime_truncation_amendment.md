> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Stage 4b Target-Preserving Packing Amendment

Date: 2026-10-17

Current-state update2026-10-18: both A/B plan branches are complete and actual paired Stage4b preflight passes under this unchanged locked policy. See `13_plan_branches_and_paired_preflight_results.md`. Initial A-only/B-pending evidence below is historical, not the current readiness state. Stage4b training has not started and is not released by this amendment.

```yaml
Amendment ID: R04-S4B-PACK-01
Status: OPERATOR_CONFIRMED_POLICY_HASH_LOCKED_CPU_VALIDATED
Original scientific protocol: FROZEN_UNCHANGED
Original execution fingerprint: 905782583273b437e9e82d11882583d81167738baa4d988712c2263a2e643d73
New packing implementation: VERSIONED_STAGE4B_ONLY_OVERLAY
New-policy unit tests: 14_PASS
New-policy A and shared-validation actual-plan preflight: PASS
New-policy paired actual-plan preflight: PENDING_B_ACTUAL_PLANS
Training continuation: NOT_AUTHORIZED_BY_THIS_AMENDMENT
Arm A Phase 1 / Phase 2: COMPLETE_4689_AND_500_ACTUAL_STEPS
Arm A train-role plan generation: COMPLETE_945
Arm A Stage 4b: BLOCKED_BEFORE_TRAINING
Arm B: NOT_STARTED
```

## Purpose And Timing

This operator-confirmed amendment documents a Stage4b-only correction after Arm A plan generation exposed a zero-supervision guard failure. The operator confirmed applying the common rule to all construction-plan fields, predicted and GT, in training and validation, then requested the B-only wrapper. Its exact policy/tokenizer/prompt identity is now locked separately in `execution/stage4b_policy_lock_v1.json`, before B training/generation. Neither arm's Stage4b optimizer had started. This is a disclosed post-freeze amendment, not a rule claimed to have been predeclared before Arm A training or generation.

The scientific arms, seed, source splits, sample IDs, roles, example counts, update budgets, initialization, LR boundary and evaluators remain unchanged. Nevertheless, preserving complete targets instead of truncating the concatenated sequence changes the tokens visible to Stage 4b and the amount of supervised target text. It must be reported as a common downstream data-packing change, not described as having no effect on training data or token exposure.

This revision adds an isolated Stage4b packing module and CPU audit, but does not wire them into a training continuation entrypoint. The three original execution files, cached tensors, checkpoints and frozen preparation artifacts remain unchanged. No training is launched or resumed. Scope confirmation is not authorization to run the B branch or either Stage4b.

## Verified Incident And Completed Work

The original packer concatenates encoded prompt and encoded target, then takes the first 1536 tokens. Prompt labels are masked with `-100`. A long prompt can therefore consume the entire sequence and remove every reference-code training token.

Arm A reached final actual global steps 4689 and 500, with verified same-arm final LoRA/prefix completion artifacts. All 945 train-role plans were generated and saved. The guard failed during `dataset_check()` before the Stage 4b output directory or optimizer was created. Arm B's directory does not exist.

The first failing frozen role is case index 22, sample `flluma_0074580`: its full prompt contains 1689 tokens and its reference-code target including EOS contains 872 tokens. There are 19 zero-supervision rows, all predicted roles. Those 19 are retained in the original 945 predicted roles; no IDs are deleted, replaced or converted to GT roles.

Completed Arm A plan training and generated plans should be preserved, not restarted. Their reuse requires an explicit original-version provenance/continuation audit; it does not authorize editing their original fingerprints or completion metadata.

## Feasibility Audit: Why Predicted-Only Is Insufficient

Evidence files:

- `execution/stage4b_A_token_budget_actuals.json`
- `execution/stage4b_A_token_budget_rows.jsonl`: all 3150 actual train-role rows, including IDs and exact token counts.
- `execution/stage4b_validation_token_budget_actuals.json`
- `execution/stage4b_validation_token_budget_rows.jsonl`: all 2500 fixed GT-plan validation rows.
- `execution/audit_stage4b_token_budget.py`: CPU-only audit; original tokenization is not modified.

Counts use the existing frozen tokenizer and prompt builder: `prompt` with `add_special_tokens=True`, plus `reference_code + eos_token` with `add_special_tokens=False`. Targets are the existing cached reference-code strings, unchanged.

| Set / Role | Rows | Original Zero-Supervision Rows | Full Target Would Be Truncated | Empty-Plan Scaffold + Full Target Exceeds 1536 |
| --- | ---: | ---: | ---: | ---: |
| Arm A predicted role | 945 | 19 | 211 | 0 |
| Arm A GT role | 2205 | 0 | 413 | 0 |
| Arm A total | 3150 | 19 | 624 | 0 |
| Shared GT-plan validation | 2500 | 0 | 459 | 0 |

The 211 predicted-role cases include the 19 zero-supervision cases and 192 partially truncated targets. A further 413 GT-role targets were partially truncated under the original rule. The longest full training target is 1123 tokens including EOS; the longest validation target is 1118. The 19 overflowing prompts are 1615-1691 tokens before appending code.

**The initially suggested combination of full targets, unchanged GT prompts, predicted-plan-only truncation and a 1536 cap is infeasible for the 413 GT-role rows and 459 validation rows.** Retaining the original target clipping on those GT rows would violate a claim that all Stage 4b targets are preserved completely.

The operator has confirmed the both-role scope and the B-only continuation sequence. The exact packing identity is hash-locked with CPU implementation evidence; the scientific frozen package is not rewritten. Paired actual-plan acceptance still awaits B. Only the B-plan manual command is separately released in record12; Stage4b release remains suspended.

## Confirmed Scope

Policy name: `stage4b_preserve_full_code_truncate_construction_plan_v1`.

Apply the same plan-field truncation rule to **both predicted-role and GT-role construction-plan fields**, and to the fixed Stage 4b GT-plan validation inputs. Preserve the complete reference-code target in each case. A GT role still takes its plan from its fixed GT source, not from a generated plan; only the visible conditioning prefix may be shorter. Both original full plans and their provenance remain saved.

This is a Stage 4b-specific training/validation policy. It must not change Phase 1/2 plan supervision, the shared historical Stage 4 checkpoint, plan generation, P1a canonicalization, query evidence, inference decoding, or gate/geometry evaluation. In particular, evaluation-time generation must never use reference-code length to crop its input: the target-aware packing rule is supervised training/validation preprocessing only.

The superseded predicted-only proposal is retained above as incident history. It must not be used as an alternative mode of the implemented policy. Dropping rows, clipping targets, enlarging max_length and grammar filtering remain forbidden.

## Deterministic Packing Contract

1. Keep `max_length = 1536`. Freeze the exact tokenizer files, prompt-builder source and new policy implementation/version before either Stage 4b trains.
2. Select plan text strictly by the frozen role: predicted text is the existing same-arm final Phase 2 P1a plan, including an empty/invalid string; GT text is the cached reference plan. Never fall back from empty predicted text to GT.
3. Encode the entire unchanged cached reference code followed by one explicitly appended EOS, using the existing target encoding convention. Do not truncate, summarize, reformat or regenerate this target.
4. Protect all fixed prompt content: instructions, modality line, plan-field heading, separators, complete query-derived evidence and final code-output cue, including their special-token handling. Query evidence is not part of the disposable plan budget.
5. Render and encode the original full prompt first. If full prompt plus full target fits, return exactly that token sequence and labels. Do not alter a fitting plan or tokenize it through a different segment-joining convention.
6. If it does not fit, preserve a deterministic prefix of the selected construction-plan field and remove its tail. No head deletion, middle selection, arm-dependent thresholds, syntax-based selection, replacement plan, added END token or new repair is permitted. A zero-length visible plan is allowed if necessary and must be logged.
7. Re-render the whole prompt and count its actual encoded tokens for every final candidate. BPE token counts across insertion boundaries are not additive. The arithmetic budget below is an initial estimate, not a substitute for checking the final sequence.
8. Preserve an exact text prefix on valid character boundaries; decoding a partial byte-level token prefix must not introduce replacement characters or normalize/rewrite the original plan text. Freeze a deterministic candidate-reduction procedure; do not assume BPE prefix-token lengths are strictly monotone.
9. If even an empty plan plus protected scaffold plus full target does not fit, abort with sample ID, role, full token counts and artifact hashes. Do not drop or replace the row. This failure mode is not observed in the audited A/shared-validation cases, but must still be tested and enforced.
10. Label every prompt token `-100` and every complete target token, including the appended EOS, with its exact target token ID. Assert `input_ids <= 1536` and that the unmasked-label sequence equals the complete target-ID sequence, not merely that one target token remains.

Conceptual initial budget:

```text
available_plan_budget = 1536
                      - protected_scaffold_tokens
                      - complete_reference_code_and_EOS_tokens

visible_plan = a deterministic head-preserving prefix of the role-selected plan
final encoded prompt + complete target must be recounted exactly and fit
```

The empty-plan audit established the lower endpoint. The new implementation has since packed all 3150 actual A rows and all 2500 shared-validation rows successfully, using exact full-prompt re-encoding rather than additive budget estimates.

Implemented candidate rule: encode the plan without special tokens and retain its character offsets. Start with `k = min(plan_token_count, 1536 - empty_prompt_tokens - full_target_tokens)`. The candidate is the literal text prefix ending at offset `k-1` (or empty at k=0). Re-render and encode the complete prompt. Decrease k one at a time until the sequence fits. No binary search, decode/re-encode rewriting, grammar repair or claim of a globally maximal retained prefix is involved. Fitting original prompts bypass this shortening path entirely.

## Implementation And CPU Acceptance Evidence

Canonical source root: `__DEV_ROOT__\src\training_25k`.

- `cag_stage4b_packing_v1.py`: dedicated `tokenize_stage4b_preserve_target` and fixed-role `Stage4bPackedDataset`. Policy SHA256: `611a21ef38c3086bdfa05d57d77726b0ea115d570f2750d7e274903d085d5b8c`.
- `cag_preflight_stage4b_packing.py`: original-parent/seal/cache/final-checkpoint/prediction-provenance checks, full actual-row packing, first/last/cropped-role collated batch checks, and real installed Trainer sampler/budget traversal. No training CLI exists in this script.
- `execution/test_stage4b_packing_v1.py` and `execution/stage4b_packing_v1_tests.json`: 14 passing CPU contracts, including the real frozen fast tokenizer and Unicode offsets.
- `execution/stage4b_packing_v1_preflight/preflight_actuals.json`: immutable hashed source/tokenizer/prompt identity and current preflight summary. Amendment fingerprint: `efc5ea52d9ab2b9b3aa46661a0a4f46805e09c0b466b9162f3962d9dee335fd1`.
- Same directory `A_rows.jsonl` and `validation_rows.jsonl`: every source ID/role, full-target-ID hash, protected-scaffold/evidence hashes, exact retained plan prefix and all token counts. These are audit prefixes, not replacement generated plans.

| Actual Set | Rows Retained | Predicted Cropped | GT Cropped | Zero Supervision | Scaffold + Target Overflow | Packing Failures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A training | 3150 (945 predicted + 2205 GT) | 211 | 413 | 0 | 0 | 0 |
| Shared validation | 2500 GT | 0 | 459 | 0 | 0 | 0 |
| B training | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING |

A maximum original/retained plan lengths are 1536/948 tokens; shared validation 947/638. Both maximum packed sequence lengths are 1536. No plan was emptied by budget in these actual sets. A has 1,898,764 full supervised tokens per pass (5,696,292 over three planned epochs); shared validation has 1,528,910 per pass. These describe tokenization, not completed Stage4b training.

Installed CPU DataLoader traversal remains 3150 rows x 3 epochs -> **1182 planned updates**, comprising 1179 groups of eight and three groups of six. Native Stage4b actual global_step remains unavailable because neither arm has trained Stage4b. The preflight status is `PASS_A_AND_VALIDATION_B_PENDING`, not paired PASS.

The original 62-file preparation seal was reverified PASS. The original execution regression suite was rerun: 15 PASS (`execution/test_result_20261017T114847694493Z.json`). Original execution hashes/fingerprint and completed A artifacts still pass. Cache index/identity coverage was checked globally; metadata/tensor bytes were reverified for every train/validation entry consumed here, not claimed to be a fresh full 83997-entry tensor scan.

## Required Logs And Paired Checks

For each train/validation row record: arm, case index, source ID, role, source-plan and reference-code hashes, original/retained plan token and character counts, original/final prompt counts, full target-ID count/hash, final sequence length, original/final supervised-token counts, truncation/emptied-by-budget flags, protected-scaffold/evidence hashes, policy/code/tokenizer versions and the reason for any failure.

Keep original model-plan grammar status separate from the visible packed-prefix grammar status. Cropping a GT or predicted plan can remove its END marker; this is not permission to grammar-filter, repair or relabel that row.

The implemented policy retains all3150 A rows and crops211 predicted plus413 GT plans; shared validation retains all2500 rows and crops459 plans. These actual counts match the earlier full-length overflow audit. B's predicted-plan crop count remains unknown. Its413 GT-role crop identities and the shared validation packing must match A because those inputs are identical.

Fairness requires identical rules and paired role/target/evidence identities, not equal numbers of cropped generated plans. Full target hashes and total supervised target-token presentations must be identical across A/B for matching frozen code targets. Conditioning-plan prefixes and their retained lengths may differ.

## Frozen Invariants

- Seed 42; original source split, IDs, case order policy and all immutable manifests.
- Phase 1/2 processing, 75024/8000 cases, 4689/500 updates, LR 2e-4 -> 1e-5 boundary and optimizer/scheduler/RNG resets.
- Shared alignment, priors, query cache, initial plan LoRA/prefix and historical GT-plan Stage 4 initialization.
- Stage 4b 945 predicted + 2205 GT roles, same 3150 IDs/order, three epochs, accumulation 8, LR 5e-5, 1182 planned updates, 9450 presentations, final checkpoint selection.
- All actual-step, sample-order, LR, finite-weight and nonempty-reference checks; no row dropping or implicit resume.
- Same four-modality ordered evaluation sets and decoding; P1a plan canonicalization retained, program repair false, existing gate/geometry evaluators unchanged.

Row counts and update budgets remain fixed; sequence composition, target-label counts and realized compute are not claimed identical to the failed original packing. Validation losses under old/new packing are not directly comparable; the new common validation policy must be reported separately from historical losses.

## Versioning And Continuation Plan

The original 62-file seal, `01_frozen_protocol.md`, `05_execution_spec.json`, completed A checkpoints, saved predictions and cache must remain byte-for-byte intact. Cross-reference this draft from the live README/amendment index rather than editing a sealed original protocol merely to insert a link. An approved amendment would be an explicit overlay, not a replacement history.

The original cache and completed checkpoints bind a global fingerprint that includes the original execution files. Editing those files in place could invalidate reusable upstream/cache provenance even when their content is scientifically unchanged. A future implementation must use an audited versioned Stage 4b policy/continuation layer and explicit original-parent/amendment lineage. Do not rewrite old fingerprints, fabricate new completion markers, or remove hash/output guards to force acceptance.

Proposed order, after scope approval and implementation tests:

1. Verify and retain A Phase 1/2 finals and all 945 plans; confirm both Stage 4b outputs remain absent.
2. Freeze the common downstream policy/code before seeing B generated plans. Do not tune it using downstream gate/geometry results.
3. Release a narrowly scoped, explicit continuation entrypoint for B Phase 1 -> B Phase 2 -> B 945 train-role plans only. Use unchanged plan training/tokenization, initial B files and shared cache; new optimizer/scheduler/seed rules remain unchanged. This step is proposed, not authorized here.
4. Run the amended actual-plan preflight on both 3150-row Stage 4b datasets and the shared 2500-row validation dataset. Save per-row logs and hashes and require complete targets, zero failed/zero-supervision rows and matching paired invariants.
5. Only after both pass, release A Stage 4b then B Stage 4b manual training commands, each starting fresh from the shared Stage 4 checkpoint and each asserting actual `global_step == 1182`.
6. Generate the frozen four-modality evaluation predictions, run gate/geometry and register results. No method-level conclusion follows from packing feasibility alone.

Do not rerun the original full wrapper: its existing-output guard correctly rejects a partially completed run. No automatic crash resume, deletion or retraining of completed A plan branches is part of this draft.

## Approval Boundary And Next Action

Scope approval is recorded from the operator's instructions: **both GT and predicted roles plus Stage4b validation**, complete code targets and the1536 cap. The exact implementation/tokenizer/prompt identity is now locked in `execution/stage4b_policy_lock_v1.json`, with A/validation CPU acceptance evidence. B and the paired actual-plan preflight are not complete.

The B-plan-only continuation layer is now implemented and audited separately in `12_b_only_continuation_release.md`:24 passing CPU contracts, final real dry-run PASS, original-parent/amendment lineage and protected A output checks. Only the B-plan manual command is released there; neither B training nor generation was executed by the assistant. After the human produces B's actual945 plans, rerun this same packing preflight into a new audit directory. Only paired PASS can precede a separate Stage4b release. Do not rerun the original full wrapper.

Read-only CPU audit command (from WSL ai_dev, choose a new output directory on each run):

```bash
CUDA_VISIBLE_DEVICES="" python __DEV_ROOT__/src/training_25k/cag_preflight_stage4b_packing.py \
  --output __EVIDENCE_SOURCE_ROOT__/04/execution/stage4b_packing_v1_preflight_after_B
```

If invoked before B exists, it intentionally reports A/validation PASS with B pending; this is not training permission. Existing audit directories are refused rather than overwritten.
