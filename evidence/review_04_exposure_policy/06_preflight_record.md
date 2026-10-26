> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Review/04 Preparation And Freeze Record

Date: 2026-10-16

```yaml
Scientific design: VALID
Protocol: FROZEN
Freeze scope: design + source/case/role manifests + initialization + shared input hashes
Preparation preflight: PASS
Regression tests: 7 / 7 PASS
Training entrypoint/wrapper: NOT_PREPARED
Latent/point cache: NOT_BUILT
Training release: NOT_READY
Training: NOT_STARTED
Prediction: NOT_STARTED
Evaluation: NOT_STARTED
```

This record closes the requested preparation stage only. There are no new model results or curriculum conclusions. No `Trainer.train`, model forward/backward, optimizer update, GPU training, automatic resume or historical-checkpoint replacement was executed. A cached base was loaded on CPU to create and reload untrained common initialization artifacts; this is initialization, not training.

## Paths

Evidence package: `__EVIDENCE_SOURCE_ROOT__\04`.

Inspected training checkout: `__RUN_SOURCE_ROOT__` (`__RUN_SOURCE_ROOT__`). Windows source mirror: `__DEV_ROOT__\src`.

No training-source files were edited in this preparation stage. Preparation scripts/artifacts are in the evidence package. Future isolated run paths are reserved under `outputs/exposure_policy_s42/arm_A` and `arm_B`; the preflight verified that all six plan-phase/code-adaptation output paths are absent. Existing historical and Review/01-03 outputs were not reused as new run outputs or overwritten.

## Six Checks

| Check | Result | Evidence |
| --- | --- | --- |
| Manifests, exact counts, paired source order | PASS | JSONL files and hashes in `04_preflight_actuals.json` |
| Source inputs/targets | PASS | 30000 rows, five file-content SHA256 values per row, no skips |
| Shared checkpoints | PASS | Alignment, four priors, Stage 4 identical to the mapping snapshot |
| Actual installed Trainer budget/sampler | PASS | CPU budget planning + complete real DataLoader accumulation-group traversal |
| Saved common initialization | PASS | A/B per-file hashes identical, LoRA reload and prefix tensor equality verified |
| Execution specification/source/output isolation | PASS | Fixed settings, unchanged mapped source hashes, separate absent run paths |

Source IDs: train 25000, val 2500, test 2500; all three pairwise ID intersections are zero. Frozen source JSON SHA256 values match the earlier mapping snapshot. Each row's reference IR/code and STEP feature JSON is read; point NPZ shape/finite coordinates and image integrity are checked on CPU. All 150000 referenced resource file contents are individually hashed. The resource inventory SHA256 is `32514481a43218cb79c93930b670d4ddf25716c99541da89337989317cb7990d`.

This resource audit does not claim to have executed the frozen query encoders or built a latent cache. A later shared inference-only materializer must fail on any encoding error/nonfinite vector, retain exact IDs/modalities and never change these manifests to bypass a failure.

## Exact Exposure

| Phase/Arm | Cases | STEP | Point | Text | Image | Planned Updates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Phase 1 A | 75024 | 75024 | 0 | 0 | 0 | 4689 |
| Phase 1 B | 75024 | 18756 | 18756 | 18756 | 18756 | 4689 |
| Phase 2, each arm | 8000 | 2000 | 2000 | 2000 | 2000 | 500 |
| Total A | 83024 | 77024 | 2000 | 2000 | 2000 | 5189 |
| Total B | 83024 | 20756 | 20756 | 20756 | 20756 | 5189 |

Phase 1 A/B use the identical source-ID sequence and actual seedable sampler index order. Each train ID appears three times, with 24 preselected IDs appearing a fourth time. Phase 2 is the same first 2000 train IDs expanded in STEP/point/text/image order, with one shared manifest. Validation is 200 fixed IDs x four modalities = 800 cases in both phases/arms, without model selection. Evaluation is the original 2500 ordered test IDs x four modalities = 10000 cases per arm.

## Optimizer Budget

Runtime: torch `2.10.0+cu128`, transformers `5.5.0`, accelerate `1.13.0`, PEFT `0.19.1`. The Trainer source SHA256 and epoch sampler-index hashes are in actuals. No library upgrade was made.

| Stage | DataLoader Batches/Epoch | Accumulation | Epochs | Traversed Groups | Presentations | LR | Warmup |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Plan Phase 1 | 75024 | 16 | 1 | 4689 | 75024 | 2e-4 | 141 |
| Plan Phase 2 | 8000 | 16 | 1 | 500 | 8000 | 1e-5 | 15 |
| Stage 4b | 3150 | 8 | 3 | 1182 | 9450 | 5e-5 | 36 |

The probe constructs the installed Trainer on CPU using a tiny model whose forward raises if called. It asks Trainer for its planned maximum steps and traverses every real DataLoader batch using Trainer's `get_batch_samples`. Both agree with these budgets. The selected optimizer is checked as fused AdamW, but no optimizer step is executed. Paired-arm fresh-loader index order is reproducible.

Stage 4b has 393 full groups of eight plus one partial group of six per epoch: 394 x 3 = 1182 groups. This verifies that the installed Trainer's current accumulation/drop-last rules produce the intended schedule, not just a paper calculation. It is **not** an observed trained `global_step`; actual trained values are null in preflight actuals. The future entrypoint must assert final actual global steps 4689, 500 and 1182 before registering any run complete.

Both arms must instantiate a fresh optimizer/scheduler at the 4689-update boundary and transfer only same-arm final LoRA/prefix weights. LR vectors are fixed and hashed in `manifests/lr_vectors.json`; a single uninterrupted B scheduler is forbidden.

## Fixed Stage 4b Roles

3150 distinct train IDs: 945 predicted-plan roles and 2205 GT roles, exactly 30/70. Roles are selected by a separate seeded train-pool permutation before any plan output exists. The same IDs, roles and row order apply to A and B, with separate same-arm plan text and adapters.

Invalid/empty predicted plans stay in their frozen roles, with valid reference code targets. No arm-dependent grammar filtering, resampling or deletion is allowed. P1a plan canonicalization stays enabled and separately logged; program/code repair remains false. Stage 4b starts from the same shared historical GT-plan Stage 4 checkpoint in both arms, not the old Stage 4b decoder.

## Initialization And Hashes

Base: `Qwen/Qwen2.5-Coder-1.5B`, pinned revision `df3ce67c0e24480f20468b6ef2894622d69eb73b`, existing local cache only. All cached base files are hashed.

Fresh untrained LoRA/prefix were created on CPU after resetting RNG to 42 and saved once, then copied to A/B. Their complete files, including tokenizer artifacts, have identical A/B SHA256 values. LoRA B tensors are initially zero, LoRA A is nonzero/finite, the saved adapter reloads as trainable, and prefix tensors are identical.

| Component | Shared A/B SHA256 |
| --- | --- |
| Initial LoRA adapter | `54586081a12f2f5c88ae9577045a5130368102992e047cc536450e3dd302a078` |
| Initial prefix | `91c3cee8d61d408d42bfec3725d335b94e29a93d0be0e2252b6cbc9e24f3ebe1` |

This matches the new branches to each other; it does not claim historical or quantized-initialization bitwise reproduction. Existing upstream best checkpoints are constants shared by both arms. Final selection applies to all newly trained pieces. Full paths/hashes are in actuals; do not substitute upstream `last.pt` in only one arm.

## Immutable Manifest Index

| File | Rows | SHA256 |
| --- | ---: | --- |
| `phase1_A.jsonl` | 75024 | `f5896b3e055e72bf17548525563c54152b6dafb2ecd5763da743226842bf9ba7` |
| `phase1_B.jsonl` | 75024 | `0cef5ee7dc56a0cb9a781155f8c90ed1e559b351fd4482d2da0aea6b137ce005` |
| `phase2_shared.jsonl` | 8000 | `832b1a42c5cb9b3916bd6388b32b98ed7ab64edb6db7a7eb915238e3719589e9` |
| `stage4b_roles.jsonl` | 3150 | `0dbdfb9a02e89195a37804529cc4670cf665f21b7f5cf5da08f069b87e172b67` |
| `validation_shared.jsonl` | 800 | `9bc61b951ccca84504074165c6ad557c265509bb5d53e0173804b7c88bd26755` |
| `evaluation_shared.jsonl` | 10000 | `da83c46de184a1fff8b30222d23ec7e637ff5c0e7526ff7f1c39ff77a3f6f1d0` |

Train/val/test ID lists, exact LR vectors, complete resource inventory and source-code inventory are also included. The generator refuses to overwrite different existing frozen content. Seven tests cover determinism/counts, duplicate IDs, cross-split leakage, arm-order mutation, role mutation and overwrite refusal.

## Interpretation Boundaries

- Name this a **training exposure-policy diagnostic**, not a pure curriculum/order-only ablation: cumulative modality exposure changes intentionally.
- Describe 83024 presentations as a matched re-run with explicit step-budget normalization, not exact historical reproduction. Matched case counts do not imply matched token counts or GPU time.
- One paired seed does not establish exposure-policy robustness, equivalence, or absence of a material effect from a small observed difference.
- Existing `hybrid` point sampling with even seed 42 realizes FPS; do not claim a realized 50/50 random/FPS mix. Both arms share the same realized samples.
- Point-plan evidence remains `off`; program repair is false but P1a plan canonicalization is true.
- No new internal training arm, seed replication or external training was added.

## Next Gate

Design and input artifacts are now frozen. Next implement and audit a manifest-aware training entrypoint/wrapper and one shared frozen query cache. Record script/command hashes, exact case-to-cache mapping, at-least-one-supervised-token checks, refusal of nonempty output directories/silent resume, correct current-arm initialization transfers and final actual-step assertions. Only then release commands for the user to run manually.

Do not run the historical Stage 3/3b shell scripts as this experiment: their Cartesian-product dataset construction cannot realize the new per-case B manifest and can silently skip failed examples. No training command is provided in this preparation-only record.

## Reproduce Preparation Only

Read-only verification in WSL `ai_dev` from the evidence package, not a training launcher:

```bash
cd __EVIDENCE_SOURCE_ROOT__/04
python -m unittest -v test_prepare_exposure_policy.py
python seal_preparation.py --verify
```

Add `--verify-resources` to the seal verification command for a fresh read-only rehash of all 150000 external resource files; the default fast verification checks sealed package artifacts and directly referenced checkpoint/base/source files, including the resource inventory itself. Neither mode changes files or runs training.

Initial preparation was executed with `python prepare_exposure_policy.py --source-root __RUN_SOURCE_ROOT__`. Re-running that generator in the original package updates its timestamped preflight report, so do not use it for read-only verification of a sealed package. Preserve the original report and seal for archival comparison; any later full generation rerun belongs in a separately named audit package.
