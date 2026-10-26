> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# B-Only Plan-Branch Continuation

Date: 2026-10-17.

Observed update2026-10-18: the operator completed this command. Both B phases and945 plans verify; A remains unchanged; actual paired Stage4b preflight PASS. See record13 for current results. The NOT_STARTED-at-release statements below are preserved as history; **do not rerun B-only**.

This record covers only B Phase1 -> B Phase2 -> B train-role plan generation. It supersedes the old full-wrapper command for the current partially completed run. It is not a Stage4b or evaluation release. The assistant does not execute the training command.

## Implementation And Audit

Canonical code checkout: `__DEV_ROOT__\src\training_25k`.
Frozen data/import/output checkout: `__RUN_SOURCE_ROOT__`.

Code checkout base commit at audit: `052392b6c7dc0305d04033b1f56d19b12fffb0a2`. The checkout is dirty; these new execution files are uncommitted and identified by the recorded SHA256, not by that commit alone. The Python entrypoint SHA256 is `3d2a3e193dc0451d35a49ae9481d506bf7bb49d0f19f2d070501d5a0bb7293e9`; Bash wrapper SHA256 is `b194b9e244058e1b2100ddd74f81269d6f4d49d81dc2643a72da1ddcffae1294`.

- `cag_exposure_policy_b_only.py`: version `review04_b_plan_only_v2`, explicit B-only orchestration around unchanged original plan-phase functions.
- `cag_run_exposure_policy_b_only.sh`: default CPU preflight; training requires `run --confirm-training` supplied manually.
- `execution/test_b_only_continuation.py`: 24 CPU/stub contracts, no real model training or generation.
- `execution/b_only_contract_tests_v2.json`: current code/test-source hashes and PASS test evidence.
- `execution/b_only_preflight_v2.json`: final actual-input CPU dry-run (release requires PASS).
- Corresponding `.a_inventory.json`: protected A tree, byte hashes, sizes and modification timestamps.
- `execution/stage4b_policy_lock_v1.json`: immutable all-plan-field packing policy/tokenizer/prompt identity, locked before B generation. Its version is independent of the B-only entrypoint version.
- `execution/b_only_manual_release_v2.json`: generated after final dry-run/current-input revalidation; no training is started by registration.

Final v2 CPU dry-run: PASS. All36 recorded base/shared/initialization files and all83997 cache entries were reverified. A's69-file tree stayed unchanged. B Phase1:75024 rows /57798 unique inputs tokenized /4689 planned updates. B Phase2:8000 rows /8000 unique inputs /500 planned updates. Plan validation:800 rows. Both phases preserve the original first/last batch shapes and sampler hashes. B is still NOT_STARTED and both Stage4b directories are absent. Native B trained global steps remain unknown until the human executes the command.

The initial `b_only_contract_tests_v1.json`/`b_only_preflight_v1.json` are retained as history, not the release basis. Final v2 adds confinement of report writes to `Review/04/execution` and verification of the actual saved model-startup LoRA/prefix chain. No scientific manifest, exposure policy, budget, tokenizer behavior or original source file changes between these execution checks.

## Mandatory Startup Guards

- Original62-file seal, source/runtime versions and original three execution-file hashes/fingerprint match.
- Frozen manifests/IDs/roles and common A/B initialization hashes match, as do base-model and shared-checkpoint files. Only the frozen source/package roots are accepted.
- Cache completion/index match the original release; all83997 entries are byte/tensor verified during dry-run and again before manual training. No cache generation is called.
- A finals are actual4689/500 checkpoints; actual startup tensors match the common initialization then same-arm Phase1 final. All945 A plans retain their original IDs/order, final model/prefix and P1a provenance.
- A is accessed read-only by this orchestration. Its complete69-file snapshot is compared before/after dry-run and at every training/generation boundary, including on failure. No chmod/ownership/ACL changes are performed, and no OS-level write isolation is claimed.
- B output root must be absent or entirely empty. Any partial/completed B output blocks a fresh invocation. An exclusive `B_ONLY_STARTED.json` claim prevents a second invocation from silently resuming.
- Both Stage4b directories must remain absent. No CLI arm/stage selector, A-plan regeneration, test-code generation or Stage4b call is exposed.
- Report paths are confined to direct non-symlink JSON files in `Review/04/execution`; even custom report flags cannot write into A/B outputs.
- Phase boundary retains the original fresh optimizer/scheduler/RNG reset, LR vectors and sampler hashes. Actual model startup hashes and final steps are checked, not just directory names.

## Manual Training Command

Run only after the final v2 dry-run and manual release record are PASS/present. In WSL Ubuntu with `ai_dev` active:

```bash
cd ~/workspace/MIRAGE/src
bash __DEV_ROOT__/src/training_25k/cag_run_exposure_policy_b_only.sh run --confirm-training
```

This command rechecks inputs/cache and then starts B. Do not rerun the old full wrapper. No arguments defaults to CPU preflight, but the existing default preflight report is deliberately not overwritten; a repeat CPU audit needs a new JSON basename via `--report` inside `Review/04/execution`.

## Expected Outputs And Stop Point

| Stage | Rows | Required Actual Step / Output |
| --- | ---: | --- |
| B Phase1 | 75024 | `plan_phase1/trainer_state.json`:4689 |
| B Phase2 | 8000 | `plan_phase2/trainer_state.json`:500 |
| B train-role plan generation | 945 | `predictions/train_roles_plans.jsonl`, exact fixed IDs/order |

All outputs are under `__RUN_SOURCE_ROOT__/outputs/exposure_policy_s42/arm_B/`. Original per-phase completion/training reports preserve the original parent fingerprint. New `B_ONLY_STARTED.json`, boundary records and `B_ONLY_COMPLETE.json` carry the continuation/policy/preflight lineage separately; old completion metadata is never rewritten.

The generated-plan file is accompanied by `.complete.json` and `.p1a_log.json`. Empty/invalid plans remain present; they are not replaced with GT or filtered. There is no code generation in this command.

Successful terminal state:

```yaml
Arm A plan branch: COMPLETE_UNCHANGED
Arm B plan branch: COMPLETE_4689_AND_500_ACTUAL_STEPS_945_PLANS
Stage4b A: NOT_STARTED
Stage4b B: NOT_STARTED
Next: actual A/B paired Stage4b preflight
```

If training fails or the machine restarts, retain all files and send the traceback/status for inspection. The wrapper refuses nonempty B outputs; do not delete completion/STARTED files, force resume or rerun from scratch to bypass a guard. Any later recovery must explicitly validate completed stages and define a new narrowly scoped continuation.

After B completes, the same locked packing policy must pass actual A/B3150-row and shared2500-row validation audits, including identical target-ID/scaffold/evidence identities and zero lost code/EOS. Cropping counts may differ by predicted plan. Only a later separate release permits Stage4b A/B, each requiring actual1182 updates, then four-modality evaluation.
