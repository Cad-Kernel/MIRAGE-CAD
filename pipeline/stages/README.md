# MIRAGE-CAD v1.0 — 25K Training Runbook

Full rationale/decision-gates: `docs/MIRAGE-CAD_v1.0_25k_plan.md` (read that
first if anything here seems unmotivated). This file is the **execution
order** — what to run, in what order, and **where every result lands**, so a
new session (or you, after a reboot) can find everything without re-deriving
it.

**Environment convention** (matches every other script in this repo):
- All `.sh` scripts run in **WSL**, conda env `ai_dev`, from
  `~/workspace/MIRAGE/src` (the scripts `cd` there themselves).
- All `.ps1` scripts run in **Windows PowerShell** (WSL cannot `import
  flluma`) — these call `FllumaCLI.exe` for real CAD-kernel execution.
- Edit Python/shell source on the **Windows side**
  (`C:\Workspace\Project\Paper\MIRAGE-V2\src`) first, then `cp` to WSL
  (`~/workspace/MIRAGE/src`) before running — this whole `training_25k/`
  folder needs to be copied to WSL once before step 1 (see below).

## One-time setup: copy this folder (and the modified train_alignment.py) to WSL

```bash
# from Windows PowerShell or the Bash tool, NOT WSL:
wsl -e bash -lc "cp -r /mnt/c/Workspace/Project/Paper/MIRAGE-V2/src/training_25k ~/workspace/MIRAGE/src/ && cp /mnt/c/Workspace/Project/Paper/MIRAGE-V2/src/train_alignment.py ~/workspace/MIRAGE/src/train_alignment.py && chmod +x ~/workspace/MIRAGE/src/training_25k/*.sh"
```
(`train_alignment.py` was modified in place to add the `--rare-op-boost`
sampler, §2.1 of the plan doc — this is the only pre-existing file this plan
changes; everything else is new, added-only.)

## Step-by-step order

Run in this exact order. Each row: script -> what it does -> **where results land** -> approx. environment.

| # | Script | Does | **Results land at** | Env |
|---|---|---|---|---|
| 1 | `01_prepare_data.sh` | Build 25K/2.5K/2.5K manifest split | `data/25k/{train,val,test}.jsonl`, `data/25k/manifest.json` | WSL |
| 2 | `02_extract_step_features.ps1 -Split train` (then `-Split val`, then `-Split test`) | STEP/B-Rep feature extraction via FllumaCLI, one call per split | `data/25k/step_features/` (flat, shared across splits — **do not** look for a per-split subfolder), `data/25k/step_features_{split}.jsonl`, `data/25k/step_features_{split}_summary.json` | Windows PowerShell |
| 3 | `03_train_alignment.sh` | Stage 1: 4-modality alignment, `--rare-op-boost 2.0` | `outputs/align_25k/{best.pt,last.pt,training_report.json}` | WSL |
| 4 | `04_build_retrieval_indices.sh` | Train + test IR retrieval indices | `outputs/align_25k/{train,test}_ir_index.npz` (+ `.json` sidecars) | WSL |
| 5 | `05_train_prior_step.sh`, `05_train_prior_point.sh`, `05_train_prior_text.sh`, `05_train_prior_image.sh` (run all four, any order, independent) | Stage 2: per-modality latent priors | `outputs/prior_{step,point,text,image}_25k/{best.pt,last.pt,training_report.json}` | WSL |
| **A** | `18_audit_rareop_decision_gate.sh` — **run once now, BEFORE Stage 3/4, using a quick predicted_ir pass** (see note below) | **Decision gate**: has rare-op collapse improved? | `outputs/rareop_audit_25k/{step,point,text,image}.json` | WSL |
| 6 | `06_train_lora_ir.sh` | Stage 3: LoRA-IR (soft-prefix), STEP-only training, reused for all 4 modalities at inference | `outputs/lora_ir_25k/` (adapter + `soft_prefix.pt` + tokenizer + `soft_prefix_training_report.json`) | WSL |
| 7 | `07_gen_predicted_ir_train_subset.sh` | Generate predicted_ir on 1000 train rows, for the Stage 4b mix | `outputs/lora_ir_25k/predicted_ir_train_subset.jsonl` | WSL |
| 8 | `08_build_stage4b_mix.sh` | Filter to grammar-valid rows, build 70/30 mix | `data/25k/train_stage4b_mix.jsonl` | WSL |
| 9 | `09_train_lora_code_stage4.sh` | Stage 4: LoRA-Code on ground-truth IR only | `outputs/qwen25_coder_1_5b_program_25k/` | WSL |
| 10 | `10_train_lora_code_stage4b.sh` | Stage 4b: continue-train on the 70/30 mix | `outputs/qwen25_coder_1_5b_program_25k_stage4b/` — **this is the recommended checkpoint for everything downstream** | WSL |
| 11 | `11_gen_test_predicted_ir_{step,point,text,image}.sh` (all four) | Stage 3 formal eval: predicted_ir for the full 2.5K test set | `outputs/lora_ir_25k/predicted_ir_test_{step,point,text,image}.jsonl` | WSL |
| 12 | `12_repair_p1a_all.sh` | P1a repair (face-extrude alias), applied to predicted_ir, all 4 modalities | `outputs/lora_ir_25k/predicted_ir_test_{step,point,text,image}_p1a.jsonl` (+ `repair_face_extrude_alias_log_{modality}.json`) | WSL |
| 13 | `13_gen_test_code_{step,point,text,image}.sh` (all four) | Stage 4b formal eval: generate program.py from repaired predicted_ir | `outputs/qwen25_coder_1_5b_program_25k_stage4b/gen_test_{step,point,text,image}.jsonl` | WSL |
| 14 | `14_repair_code_all.sh` | extrude_on_face repair, then P0 (profile_cut offset) repair, applied to generated code, all 4 modalities | `outputs/qwen25_coder_1_5b_program_25k_stage4b/gen_test_{modality}_repaired.jsonl` (intermediate) and `..._repaired_p0.jsonl` (**final, use this one downstream**) | WSL |
| 15 | `15_evaluate_execution_all.ps1` | Real FllumaCLI build/validate/STEP-export, all 4 modalities | `scratch/exec_eval_25k_{step,point,text,image}/{execution_rows.jsonl,execution_summary.json}` (Windows paths) | Windows PowerShell |
| 16 | `16_evaluate_retrieval_all.sh` | Table 1: retrieval R@k/MRR, all 4 modalities | `outputs/eval_retrieval_prior_{step,point,text,image}_25k.json` | WSL |
| 17 | `17_evaluate_ir_quality_all.sh` | Table 2: IR Cosine/Op-Set F1/Op-Seq LCS, all 4 modalities | `outputs/lora_ir_25k/ir_quality_{step,point,text,image}_25k.json` | WSL |
| 18 | `18_audit_rareop_decision_gate.sh` — **run again now, with the full test-set predicted_ir from step 11/12** (the run in step "A" above was a quick pre-check; this is the real one) | Rare-op collapse audit, final | `outputs/rareop_audit_25k/{step,point,text,image}.json` (overwrites the quick pre-check) | WSL |
| 19 | `19_evaluate_programs_all.sh` | Table 3 (text-level half): syntax/Op-F1/LCS/source-sim, no kernel execution | `outputs/qwen25_coder_1_5b_program_25k_stage4b/eval_{step,point,text,image}_25k/{evaluation_rows.jsonl,evaluation_summary.json}` | WSL |

### Note on the two Gate-A audit runs (steps "A" and 18)

`18_audit_rareop_decision_gate.sh` needs a predicted_ir file with `reference_ir`
populated for the STEP-side grouping. You technically don't have one until
step 11-12. Two options:
- **Cheap early check** (recommended): after step 5 (priors done), run
  `07_gen_predicted_ir_train_subset.sh`'s script manually against a small
  slice of `test.jsonl` instead of `train.jsonl` (just to get *some*
  predicted_ir + reference_ir pairs quickly) purely for the STEP-side audit
  input — this lets you check the collapse gate **before** committing to the
  multi-day Stage 3/4 training run. This is what row "A" in the table above
  refers to; it is not a separate script, just an earlier, smaller invocation
  of the same generation script pointed at a `--limit 50 --input-jsonl
  data/25k/test.jsonl` slice.
- **Or**: skip the early check and only run the audit once, after step 12,
  accepting that a Stage-1-only problem won't be caught until Stage 3/4 have
  already been trained (more expensive to discover late, but simpler if
  you'd rather not hand-craft the early-check invocation).

Either way, **do not skip the audit entirely** — it is the pre-registered
Gate A from the plan doc, and its outcome determines whether you should trust
the 25K numbers or stop and revisit Stage 1 first.

## Post-review additions (added 2026-08-04, run after the 19 steps above)

These come out of the submission review. Steps 20 and 21 are runnable now; 22 is a
protocol that needs external data first.

| # | Script | Does | **Results land at** | Env |
|---|---|---|---|---|
| 20 | `20_rerun_geometry_nbest_random100.sh` | Re-runs best-of-N geometry on a **seeded random** 100-sample subset with sampling parameters passed explicitly and recorded. Fixes review item **B5** — every existing 100-sample table used the *first* hundred rows, which run ~10 pp optimistic against the full 2,500. Both modalities share one sample set, so point-vs-STEP becomes comparable for the first time. Prints the PowerShell follow-up. | `outputs/geometry_nbest_random100/` (+ `run_metadata.json`), then `scratch/{exec,geometry}_nbest_random100_{step,point}/` | WSL, then Windows |
| 21 | `21_editability_probe.sh` | **B7**, the highest-value remaining experiment. Perturbs each declared parameter by ±10 %/±25 %, re-executes, and classifies the outcome into *rebuilt and moved* / *rebuilt with no geometry change* / *broke*. Also reports parametric coverage. Probes variant C **and** NN-IR A/B on the same parts — the one dimension where C has a structural reason to win. | `outputs/editability_25k/`, then `scratch/editability_25k_step_{c,direct,prior}/` | WSL, then Windows |
| 22 | `22_cross_dataset_protocol.md` | **C-EXT1** cross-dataset + external comparison. Protocol only — three decisions and two adapters are needed before it can run. Read it before starting; it lists the traps in the order they bite. | — | — |

Supporting files added at the same time:

```
training_25k/scripts/make_random_subset.py   seeded random JSONL subset, with an
                                             .ids.txt sidecar so the SAME parts can
                                             be reused across modalities/variants
src/editability_probe.py                     B7 core; runs under FllumaCLI
src/scripts/editability_probe.ps1            Windows wrapper for the above
src/scratch/aggregate_editability.py         B7 -> paper table
src/classify_execution_failures.py           regenerates the failure taxonomy
                                             (Table 11) from execution_rows.jsonl;
                                             previously applied by hand
```

**Note on the two 100-sample conventions.** Everything numbered 1-19 used
`--limit 100` = first hundred rows. Steps 20-21 use a seeded random subset instead.
Numbers from the two are not interchangeable, and step 20's output supersedes
`outputs/geometry_nbest_25k_stage3b/` rather than extending it.

## Optional, lower priority (do after the above, if desired)

- **Table 4 (N-best geometry)**: reuse the *existing* project scripts
  (`scratch/gen_nbest_candidates.py`, `scratch/repair_nbest_candidates.py`,
  `src/evaluate_geometry_nbest.py`, `src/scratch/aggregate_geometry_nbest.py`
  — no new scripts needed, they already take explicit checkpoint/index paths
  as CLI args) on a **100-200 sample subset** of `data/25k/test.jsonl`, STEP
  and point-cloud only. See `docs/MIRAGE-CAD_v1.0_25k_plan.md` §5 for why not
  the full 2.5K test set.
- **A/B NN-IR baseline at 25K scale**: low priority per the plan doc — the 5K
  finding (NN-IR saturates ~89-90% regardless of scale) is unlikely to change.

## If the computer shuts down mid-run

Every script writes its checkpoint/output to the path in the table above and
nowhere else — there is no hidden intermediate state. To resume:
1. Check which `outputs/`/`data/25k/` paths already exist (`ls -la
   ~/workspace/MIRAGE/src/outputs/` on WSL) to see which numbered steps
   completed.
2. STEP feature extraction (step 2) is explicitly resumable (`--resume` always
   passed) — just rerun the same `.ps1` call for whichever split was
   interrupted.
3. Every other step either finished (checkpoint/JSONL file exists and is
   non-empty) or didn't (rerun it from scratch — none of the training scripts
   have partial-checkpoint resume built in, matching every other script in
   this project).
4. If resuming in a new Claude Code session: point it at this README and
   `docs/MIRAGE-CAD_v1.0_25k_plan.md`, and tell it which numbered step you
   were on — it can `ls`/`wc -l` the expected output paths above to verify
   what's actually done rather than trusting a stale memory of progress.

## Files in this folder

```
README.md                                  <- this file
01_prepare_data.sh
02_extract_step_features.ps1
03_train_alignment.sh
04_build_retrieval_indices.sh
05_train_prior_{step,point,text,image}.sh
06_train_lora_ir.sh
07_gen_predicted_ir_train_subset.sh
08_build_stage4b_mix.sh
09_train_lora_code_stage4.sh
10_train_lora_code_stage4b.sh
11_gen_test_predicted_ir_{step,point,text,image}.sh
12_repair_p1a_all.sh
13_gen_test_code_{step,point,text,image}.sh
14_repair_code_all.sh
15_evaluate_execution_all.ps1
16_evaluate_retrieval_all.sh
17_evaluate_ir_quality_all.sh
18_audit_rareop_decision_gate.sh
19_evaluate_programs_all.sh
scripts/
  gen_predicted_ir.py             <- generalized (text/image/point/step) predicted_ir generator
  gen_code_from_predicted_ir.py   <- generalized (text/image/point/step) code generator
  build_stage4b_mix.py            <- CLI-parameterized Stage 4b mix builder
  audit_rareop_collapse_step.py   <- CLI-parameterized STEP-side rare-op collapse audit
```

`training_25k/scripts/*.py` are new, CLI-parameterized generalizations of
existing 5K-scale one-off scripts that had every path hardcoded (see
`docs/MIRAGE-CAD_v1.0_25k_plan.md` and the code-review notes inline in each
file for exactly what changed and why). The numbered `.sh`/`.ps1` files are
new wrappers; no existing 5K/50K scripts were modified except
`train_alignment.py` (additive `--rare-op-boost` flag, default off).
