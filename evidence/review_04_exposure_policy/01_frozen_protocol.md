> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# Review/04 Training Exposure-Policy Diagnostic

Date: 2026-10-16

```yaml
Status: FROZEN
Freeze scope: SCIENTIFIC_DESIGN_AND_INPUT_ARTIFACTS
Mapping: COMPLETE
Seed: 42
Paired seeds: 1
Training: NOT_STARTED
Manifests: FROZEN
CPU preparation preflight: PASS
Training release: NOT_READY
Training wrapper: NOT_PREPARED
```

The protocol's design/input freeze and release of a training command are separate gates. Preparation fixes manifests, budgets, initialization, shared inputs and execution settings without calling training. A later manifest-aware entrypoint/wrapper audit is required before releasing a training command. Neither a protocol freeze nor a preparation PASS authorizes training.

## Question And Arms

Question: does balanced modality exposure from the beginning materially change the final modality trade-off compared with STEP-first exposure followed by balanced continuation, under matched optimization schedules and fixed upstream components?

Arm A: STEP-only plan training, then balanced four-modality continuation.

Arm B: balanced four-modality plan training in both phases, with no STEP-only warm-up. Preserve the same optimizer reset and LR boundary as A.

This is a single-seed exposure-policy diagnostic. It does not estimate curriculum seed variance, isolate pure ordering at fixed modality totals, or establish that all architecture effects have been separated from training.

## Plan Budget

| Phase | Arm A | Arm B | Updates Per Arm | Full-Batch Example Presentations | LR |
| --- | --- | --- | ---: | ---: | ---: |
| 1 | STEP only | Balanced from the start | 4689 | 75024 | 2e-4 |
| 2 | Balanced continuation | Balanced continuation | 500 | 8000 | 1e-5 |
| Total | | | 5189 | 83024 | |

Each full update uses one device, batch size 1, and accumulation 16. The manifests materialize exactly 75024 first-phase cases and 8000 second-phase cases, avoiding arm-dependent partial accumulation groups. Historical epoch-based A processed approximately 83000 examples; the extra 24 examples here are an explicit budget normalization for both new arms, not a claim that the new A is byte-for-byte historical A. Reviewer-facing wording: "a matched re-run of the historical exposure policy with explicit step-budget normalization."

Build a common first-phase source-ID sequence from seeded permutations of the same 25000-row training pool: three complete passes plus 24 cases. Use identical source IDs/counts/order-policy in A and B. A assigns STEP to every case. B assigns exactly 18756 cases to each modality through a separately seeded shuffled label sequence. Balanced means equal dataset-level counts; do not infer equal counts in every optimizer update.

The authoritative bytes are in `manifests/phase1_A.jsonl` and `phase1_B.jsonl`. Preparation uses separate named seed-42 RNG streams for source order, modality labels, and Stage 4b roles. The first 24 IDs of a fourth seeded permutation receive a fourth presentation; the other 24976 IDs receive three. Each phase trains for one epoch over its fully materialized cases with the installed seedable random sampler. This also differs from three historical source-dataset epochs: no claim of exact historical sample ordering is made. Actual paired-arm sampler reproducibility is checked on CPU.

Phase 2 uses the first 2000 train IDs expanded to all four modalities, exactly as the original Stage 3b source/ratio rule: 2000 cases per modality. Materialized case order and training sampler must be identical across arms for this phase.

Across the entire schedule, A has 77024 STEP presentations and 2000 for each other modality; B has 20756 for each modality. These different marginal counts are part of the exposure policy. Total case presentations match, but token counts and actual compute may differ and must be logged.

## Initialization And Optimization Controls

- Save one fresh seed-42 LoRA/prefix initialization and load the identical files into both first-phase arms. Hash both components. Do not rely only on setting the same seed before different preprocessing work.
- Use Qwen/Qwen2.5-Coder-1.5B, plan LoRA rank 8 / alpha 16 / dropout 0.05, prefix length 4, max_length 1536, NF4 double quantization, and BF16 in both arms.
- Share the frozen alignment and four modality priors listed in `02_stage3_stage3b_mapping.md`. Hash them before training and use the same cached latents/point samples for a given sample/modality in both arms.
- Use `adamw_torch_fused`, linear LR scheduler, warmup_ratio 0.03, weight_decay 0, max_grad_norm 1, Adam betas 0.9/0.999 and epsilon 1e-8 in each corresponding phase. Set seed/data_seed to 42. Warmup steps are 141, 15 and 36 for Phase 1, Phase 2 and Stage 4b respectively.
- Reset optimizer state, scheduler, and phase seed at the same 4689-update boundary in both arms. Transfer both final LoRA and final prefix into phase 2.
- Use final checkpoint selection for all newly trained components. Validation is logged but never selects between arms/checkpoints or changes a schedule.
- Materialization must abort on missing features, encoding failures, empty reference targets, ID mismatch, or row-count imbalance. No arm-specific silent dropping.
- Keep the frozen source train/val/test split; no retrieval, no test data in adaptation, no model-output-dependent changes to source IDs.

Pin base revision `df3ce67c0e24480f20468b6ef2894622d69eb73b`; use the cached base without downloads. `04_preflight_actuals.json` records base/cache/shared-checkpoint hashes, actual installed Trainer details, sampler index hashes and initialization hashes. `05_execution_spec.json` fixes the remaining settings and isolated future output directories. Final wrapper/command hashes cannot yet be recorded because no training wrapper has been prepared.

The two saved initializations live in `artifacts/initialization/arm_A` and `arm_B`. They are newly initialized on CPU using a cached BF16 base and standard PEFT initialization after an explicit seed reset, then copied byte-for-byte. Training will load these saved tensors into both NF4 bases. This is not a claim to reproduce the historical random initialization, or to reproduce initialization performed directly on a quantized base bit-for-bit.

Training uses the existing hybrid point sampler with seed 42 and validation/test uses FPS. The current hybrid implementation selects FPS for even seeds, so the realized training sampling here is FPS. Both arms share each cached sample/vector; do not describe this run as a realized 50/50 random/FPS mixture. Source images, point arrays, STEP features and targets are read/validated and individually hashed in `resource_inventory.jsonl`; frozen query latent encoding is a later inference-only preparation step, not yet performed.

Use the same 800 validation cases (first 200 validation IDs x four modalities) in both plan phases and both arms. Validation never selects a checkpoint, schedule, or arm. This common validation manifest is another explicit matched re-run choice, not the original Stage 3 validation recipe.

## Downstream Code Decoder

Share the fixed historical seed-42 Stage 4 GT-plan code checkpoint `outputs/qwen25_coder_1_5b_program_25k`.

Train one Stage 4b continuation per arm from this identical checkpoint. Use final A/B plan models to generate raw train-only STEP plans on a frozen source-ID manifest. This differs from the historical Stage 4b mix that used predecessor Stage 3 plans.

Role manifest: 945 predicted-plan IDs + 2205 separate GT-plan IDs = 3150 rows, exact 30/70 ratio. A separate seeded permutation of the full train pool selects the first 945 IDs as predicted roles and the next 2205 as GT roles, in fixed manifest order. Source IDs/roles are hashed before either plan model is trained. Retain invalid/empty predicted plans as inputs with valid reference code targets and log them; do not grammar-filter different rows in the two arms. P1a canonicalization preserves every role, including an unchanged empty result, and logs its outcome.

Both adapters: same role/ID/order manifest, seed/data_seed 42, Stage 4 initialization, three epochs, accumulation 8, LR 5e-5, max_length 1536, and final selection. Expected current-recipe budget is 1182 updates and 9450 row presentations per arm; verify these counts against the installed Trainer before freezing the wrapper.

CPU verification uses the installed Trainer's budget planner and traverses real DataLoader batches with `get_batch_samples`, never `train()`, model forward/backward or optimizer steps. For Stage 4b, each epoch contains 393 full accumulation groups of eight and one group of six: 394 x 3 = 1182 groups, 9450 presentations. This is pre-training budget verification, not an observed final `global_step`. The real training entrypoint must additionally assert `global_step == 1182` after training. The analogous final assertions are 4689 and 500 for the plan phases.

No Stage 4 or upstream retraining is required. Both plan branches and both Stage 4b adapters are newly trained because the original Arm A does not meet the strict common-initialization/final-checkpoint audit.

## Evaluation

Use the existing `data/25k/test.jsonl` in its existing order: 2500 source cases for each of text, image, point, and STEP. Both arms see the same cases; do not draw a new slice.

Fix greedy N=1 generation, num_beams 1, do_sample false, max_length 1536 and max_new_tokens 1536, and decoding batch size 8. Preserve query evidence in the code prompt. Keep point-plan evidence mode identical to the historical default (`off`) for both arms. Freeze point sampling seed 42.

Program/code repair: false. P1a plan-stage canonicalization: true in both arms, separately logged. Never describe this as all repair disabled.

Use the existing Windows gate and geometry evaluators. Primary endpoints: per-modality Build and STEP export. Also report syntax, execution, solid validity, scoreable count, conditional CD/F@1, unconditional F@1, paired geometry, raw means, failure categories, and outliers. No exclusions or post-hoc margin tuning.

Report a 4 x 2 modality/arm table for each principal endpoint, with differences in percentage points. Any across-modality average is descriptive and is not an estimate of seed variability. Small within-query p-values do not provide curriculum-training variance from one paired seed.

## Design/Input Freeze Gate

Before marking this design and its inputs FROZEN:

1. Materialize immutable source/case/role manifests and record hashes; verify no train/val/test leakage.
2. Record shared checkpoint/base-model hashes and identical common initialization hashes.
3. Count exact per-arm/per-phase modality exposures, effective batches, optimizer steps, partial batches, and planned code-adaptation rows.
4. Verify identical LR vectors and optimizer resets across arms. A single uninterrupted B scheduler is not accepted.
5. Confirm every source feature/target is present, readable and valid; hash actual file contents, not only JSON paths. No skipped records.
6. Reserve distinct, currently absent training output paths; freeze refusal of partial outputs/silent resume in the execution spec. Record preparation/dependency code hashes.
7. Run CPU-only preparation preflight with no gradient training; only after all checks pass mark the design/input protocol FROZEN.

## Training Release Gate

After the design/input freeze, prepare a new manifest-aware entrypoint and wrapper. Do not pass the new manifests directly to the historical Cartesian-product trainer: it cannot realize Phase 1 B's per-case modality assignment and its historical builder can silently skip cases.

Before a manual training command is released, audit that entrypoint/wrapper, record its command/code hashes, verify all manifest/hash/isolated-directory guards, and materialize one shared immutable latent/point cache with no skipped/failed/nonfinite encodings. Tokenization must retain at least one supervised target token per case; otherwise abort without changing the manifests. Reset training RNG after materialization/model loading, verify planned steps again, and require final actual-step assertions. The training wrapper remains NOT_PREPARED at the end of this preparation-only task.

No training is authorized to start merely because this protocol, a PASS preparation report, or the mapping snapshot exists.
