# Release manifest

What this release contains, where each part came from, and what was deliberately left out. Kept so
the release can be regenerated and audited rather than trusted.

Assembled 2026-08-24 from the working repository, then trimmed twice. **439 files, 6.9 MB.**

## Source mapping

| Release folder | Source | Files |
|---|---|---|
| `miragecad/` | `src/miragecad/` | 8 |
| `tools/` | `src/*.py` (top level only) | 23 |
| `pipeline/stages/` | `src/training_25k/*` (top level only) | 66 |
| `pipeline/helpers/` | `src/training_25k/scripts/` | 20 |
| `pipeline/generation/` | `src/gen_scripts/` | 12 |
| `pipeline/retrieval/` | `src/scripts/` | 67 |
| `analysis/` | `src/scratch/*.py`, excluding `cadrecode_*` and `external_*`, plus three derivation scripts moved out of the manuscript-audit set | 81 |
| `external/` | `src/scratch/{cadrecode,external}_*` | 13 |
| `reports/execution/` | `scratch/exec_*/execution_summary.json`, renamed to the run directory | 121 |
| `reports/editability/` | `scratch/editability_*/` summary and rows | 8 |
| `reports/external/` | paired report, batch summary, environment manifests | 6 |
| `reports/geometry/` | the `geometry_nbest_rows.jsonl` files named in `figure-data.json`, plus the two family-held-out files | 6 |
| `reports/figure-data.json` | `figures/svg/figdata.json` — kept when the figure tooling was dropped, because it records where each drawn numeral came from | 1 |
| `reports/training/` | `scratch/*_results.json` | 1 |
| `docs/` | `E2_protocol_frozen.md` | 1 |

Filters applied to every copy: no `__pycache__`, no `.pyc`/`.pyo`/`.bak`, no `.safetensors`/`.bin`/
`.npy`/`.pk`, and nothing larger than 3 MB.

### Three files came from the WSL working tree

The Windows and WSL copies of `src/` had diverged. `e2_analysis.py`, `e2_latent_cosine.py` and
`training_25k/external_prep.py` existed only under WSL, and the first two are named by
`docs/E2_protocol_frozen.md` as the scripts that produce the plan-diagnostic results. They were
copied from there. Four remaining WSL-only files — `probe_flluma.py`, `probe_flluma2.py`,
`probe_torch.py`, `dryrun_alias.py` — are environment smoke tests and a dev helper of 300 to 400
bytes each, and are not included.

## Excluded, with reasons

| Excluded | Size | Reason |
|---|---|---|
| `scratch/cadrecode_runs/` | 24 MB | CAD-Recode's own generated code, STEP output and raw generations. Its code and checkpoint are CC BY-NC 4.0. Only our aggregate measurement (`batch_summary.txt`) is published, because that is ours. |
| `execution_rows.jsonl` across 121 runs | 18 MB | Per-row dumps. Their summaries are published and are what every reported number is read from. |
| `geometry_nbest_rows.jsonl`, 36 of 42 | ~16 MB | Only the files a reported figure or headline claim rests on are included. |
| Model checkpoints, LoRA adapters | ~74 MB each | Large binaries; belong in a release or model host. |
| FllumaOne-100K corpus | — | A separate dataset with its own citation. |
| `figures/` | — | Figure generators, specs, drawing kit and checker: artwork tooling. `figdata.json` was moved to `reports/figure-data.json`. |
| `verification/`, 15 scripts | — | Manuscript auditing: bibliography sync, table inventory, section audits, undefined-reference and submission-format checks. All of it reads a LaTeX source not published here, so a reviewer has no use for it and a reproducer cannot run it. Three scripts that do real derivation — the operation vocabulary, the STEP descriptor layout, the `Prog-Op-F1` convention — were moved into `analysis/` instead. |
| `tools/sync_to_wsl.sh` | — | Copies one workstation's Windows tree into its own WSL mount. |
| Four Chinese-language documents | ~93 KB | `ALL_EXPERIMENTS_INDEX.md` (7,914 CJK characters), `MIRAGE-CAD_debug_report.md` (6,021), `MIRAGE-CAD_v0.1_manifest.md` (2,175), and `MIRAGE-CAD_experiment_results.md` (52 CJK plus 24 cross-references to documents not in this release). Unreadable to most reviewers, and not self-contained here. |
| `MIRAGE-CAD_v1.0_25k_plan.md` | — | Opens with "Status: planned, not started. This is a plan document". |
| `MIRAGE-CAD_architecture.md` | — | A pre-implementation design document. Its closing sections are a roadmap whose Milestones 3 and 4 (50k and 80k experiments) were never run, alongside "Expected Contributions" and "Future Work". Publishing forward-looking plans beside a finished paper invites the wrong questions. |
| `PROVENANCE.md` | — | Written against the working-repository layout: 43 paths under `scratch/`, six under `review/`, and references to two removed documents. In this layout it would send a reader to files that do not exist. Its function is served by README's traceability table, which uses paths that do. |

## Verified before release

- **No CJK characters anywhere: 0 of 439 files.**
- No API keys, tokens, passwords or credentials anywhere in the tree.
- No CAD-Recode source, checkpoint, or generated output. Confirmed by searching for its output
  filenames (`prediction.step`, `extracted_code.py`, `raw_generation.txt`): zero hits.
- All 139 Python files parse cleanly.
- Every report file named in `README.md` exists.
- Both scripts named by `docs/E2_protocol_frozen.md` are present.
- `miragecad/` contains no absolute paths. `pipeline/` contains 87 files that do, which `README.md`
  states rather than hides.
- Remaining matches for planning vocabulary are false positives: `TODO` as a shell variable counting
  files to copy, `todo` as a Python list, "Phase" as a pipeline stage name, and "deferred" describing
  deferred evaluation.

## Still to be decided by the owner

- **Anonymity.** If the associated manuscript is under double-anonymised review, publishing under an
  identifiable account may break it. The `LICENSE` copyright line reads "MIRAGE-CAD authors" rather
  than naming anyone, and can be changed at camera-ready.
