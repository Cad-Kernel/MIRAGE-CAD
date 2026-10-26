> Historical source record, anonymized for review. Later audits may supersede interpretation; original values are retained.

# 16 -- Seed 4 Generation Record

Date: 2026-10-16

## Status

```yaml
Experiment: Review/03 B0 vs B2 full-stack multi-seed replication
Seed: 4
Training: COMPLETE
Prediction: COMPLETE
Geometry input prep: COMPLETE
Generation actuals JSON: COMPLETE
Gate evaluation: NOT_STARTED
Geometry scoring: NOT_STARTED
Seed status: GENERATION_COMPLETE_NEEDS_GATE_AND_GEOMETRY
Seeds 1 / 2 / 3: CLOSED
Four-seed aggregate: PENDING_SEED_4_EVALUATION
```

All four registered seeds have completed training and prediction. Seed 4 still needs gate evaluation, geometry scoring, and result registration before this experiment can close.

## Paths

```yaml
Windows source checkout: __DEV_ROOT__\src
WSL execution checkout: __RUN_SOURCE_ROOT__
Review package: __EVIDENCE_SOURCE_ROOT__\03
Seed outputs: __RUN_SOURCE_ROOT__/outputs/b0_b2_fullstack_s4
Seed training data: __RUN_SOURCE_ROOT__/data/b0_b2_fullstack_s4
Actuals JSON: __RUN_SOURCE_ROOT__/outputs/b0_b2_fullstack_s4/cag_b0_b2_seed_4_actuals.json
Actuals SHA256: 658924a2af68a79f09ee7ba19241a817f67c254c64ea376a74e61e279c88b1e9
Actuals created UTC: 2026-10-16T01:52:25.115482+00:00
Actuals created Europe/Paris: 2026-10-16T03:52:25.115482+02:00
```

Interrupted alignment artifacts remain archived under the seed base. The current completed alignment and all downstream components passed the generation audit.

## Inspection Results

The following checks were performed directly on the files:

- B0, alignment, all four priors, Stage 3/3b, and Stage 4/4b have completed training reports and required nonempty checkpoint files.
- All ten trainable stages report seed 4.
- Alignment and priors have `last.pt`; Stage 3/3b reports specify `checkpoint_rule=final`.
- Each prior report points to seed 4's alignment `last.pt`.
- Both prediction files, both plan files, and both geometry input files parse successfully as JSONL, contain 2500 unique IDs, and follow the exact frozen test order.
- All six output hashes match the generation actuals JSON.
- No seed-4 execution/geometry output directories were present in Windows scratch when inspected.

## Output Hashes

The prediction and geometry files below are under `__RUN_SOURCE_ROOT__/outputs/b0_b2_fullstack_s4/predictions/`. Each contains 2500 rows.

```yaml
gen_step_B0_s4.jsonl:
  sha256: f22c42cf81754a1eb0dce87a853f6bb038d74bd595131c6b1f43d0618fab9782
gen_step_B2_s4.jsonl:
  sha256: 24a0cd2c31b5a519f6fa229741b559c2d5d0be614e5e96f8a8c0a6143a24f325
geom_input_step_B0_s4.jsonl:
  sha256: a037788dd7e75fdc80d6c455dc5e5cc6652e92fd9a5e710d95468ed4491616cb
geom_input_step_B2_s4.jsonl:
  sha256: 12877e966e87ffcba18e9601f8caf078e13d0e83997a4867bc18241cc8aa5a8e
predicted_ir_test_step_raw_s4.jsonl:
  sha256: c0f6b87a570090a83e4c878d488c6add3564bf603af96095dcf5699bca6629c5
predicted_ir_test_step_p1a_s4.jsonl:
  sha256: d9fdac3f742697e7e3dc705431fc9c51bd723476ad5a33cdbfba4a72220b3f67
```

The seed-specific Stage 4b mix is `__RUN_SOURCE_ROOT__/data/b0_b2_fullstack_s4/train_stage4b_mix.jsonl`, with 3130 rows and SHA256 `d4fc448f347ced50ee621453adce9193a9bd45dc9810337f56b2d10fbb004892`.

## Training Reports

Paths below are relative to the absolute seed-output directory given above.

| Component | Output Directory | Train Rows | Validation Rows | Notes |
| --- | --- | ---: | ---: | --- |
| B0 no-plan code | b0_lora_code_noplan_25k | 25000 | 2500 | max_length 2048 |
| B2 Stage 3 plan decoder | lora_ir_25k | 25000 | 2500 | STEP, final checkpoint, max_length 1536 |
| B2 Stage 3b plan decoder | lora_ir_25k_stage3b | 8000 | 800 | Four modalities, current-seed Stage 3 initialization, final checkpoint |
| B2 Stage 4 code decoder | qwen25_coder_1_5b_program_25k | 25000 | 2500 | max_length 1536 |
| B2 Stage 4b code decoder | qwen25_coder_1_5b_program_25k_stage4b | 3130 | 2500 | Current-seed Stage 4 continuation |

Stage 3 final normal loss is `0.11131587580293417`, versus zero-prefix loss `0.1315694533035159`. Stage 3b final normal loss is `0.14433008149266244`, versus zero-prefix loss `0.15999471195507795`. These losses are computed on different validation mixtures, so their absolute values should not be used to infer an improvement or regression from Stage 3 to Stage 3b. The shuffled-loss check is vacuous with evaluation batch size 1, as the reports explicitly note.

Stage 4b mixes have seed-dependent sizes because grammar-valid predicted plans are filtered before mixing: 2987, 3103, 2997, and 3130 rows for seeds 1-4. Record actual counts/updates in the final package; do not describe B0/B2 total training computation or all continuation row counts as identical.

## Repair Policy

Program/code repair remains disabled. B2 retains the frozen deployed P1a plan canonicalization; its log is `__RUN_SOURCE_ROOT__/outputs/b0_b2_fullstack_s4/predictions/repair_face_extrude_alias_log_step_s4.json`.

```yaml
P1a ADD remaps: 15
P1a CUT remaps: 24
P1a gated_out: 333
P1a conflict_skip: 1
P1a ambiguous_skip: 0
P1a distinct touched samples: 26
```

Report the policy as code repair disabled with P1a plan canonicalization retained. An unqualified statement that every repair step is disabled would be inaccurate.

## Interpretation And Next Step

Training and generation completed successfully, with sample alignment and output hashes verified. Executable coverage and geometric quality remain unevaluated for seed 4. Training losses alone do not establish whether B2 beats B0.

Run these four commands sequentially in Windows PowerShell:

```powershell
$Root = "__RUN_SOURCE_ROOT__"

& "__DEV_ROOT__\src\scripts\evaluate_execution.ps1" `
  -InputJsonl "$Root\outputs\b0_b2_fullstack_s4\predictions\gen_step_B0_s4.jsonl" `
  -OutputDir "__DEV_ROOT__\scratch\exec_b0b2_step_B0_s4" `
  -CodeField prediction

& "__DEV_ROOT__\src\scripts\evaluate_execution.ps1" `
  -InputJsonl "$Root\outputs\b0_b2_fullstack_s4\predictions\gen_step_B2_s4.jsonl" `
  -OutputDir "__DEV_ROOT__\scratch\exec_b0b2_step_B2_s4" `
  -CodeField prediction

& "__DEV_ROOT__\src\scripts\evaluate_geometry_nbest.ps1" `
  -InputJsonl "$Root\outputs\b0_b2_fullstack_s4\predictions\geom_input_step_B0_s4.jsonl" `
  -OutputDir "__DEV_ROOT__\scratch\geom_b0b2_step_B0_s4"

& "__DEV_ROOT__\src\scripts\evaluate_geometry_nbest.ps1" `
  -InputJsonl "$Root\outputs\b0_b2_fullstack_s4\predictions\geom_input_step_B2_s4.jsonl" `
  -OutputDir "__DEV_ROOT__\scratch\geom_b0b2_step_B2_s4"
```

After all four finish, close seed 4 and aggregate seeds 1-4. The wrapper's printed "before running seed 5" text is a generic footer error, not an experimental instruction. The frozen seed plan ends at seed 4; no seed 5 is registered or authorized here. The frozen wrapper was not changed during this inspection.
