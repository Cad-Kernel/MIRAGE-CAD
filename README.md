# MIRAGE-CAD

Code, pipeline scripts, analysis scripts and run reports for **MIRAGE-CAD**, a multimodal system
that generates executable parametric CAD programs by routing every input modality through a shared
*construction representation* and an explicit *construction plan*.

From text, a rendered image, a point cloud, or STEP/B-Rep geometry, the system predicts a
construction latent, decodes it into a readable construction plan, and generates Python CAD code
that an OpenCASCADE kernel executes and exports as STEP.

This repository is organised so that **every reported number can be traced to the file that produced
it**. See [Tracing a reported number to its report](#tracing-a-reported-number-to-its-report).

**Licence: [0BSD](LICENSE)** — use it for anything, with no conditions and no attribution required.
One caveat applies to the external comparison; see [Licence](#licence).

---

## Repository layout

| Folder | Files | Contents |
|---|---|---|
| `miragecad/` | 8 | The library: modality encoders, latent priors, the soft-prefix adapter, losses, data and prompt construction. |
| `tools/` | 23 | Command-line tools: retrieval index building, execution evaluation through the five gates, geometry scoring, program scoring, the parameter-perturbation probe. |
| `pipeline/stages/` | 66 | The numbered end-to-end recipe, `01_prepare_data` onward. This is the order in which the system was trained and evaluated. |
| `pipeline/helpers/` | 20 | Supporting scripts called by the stages: dataset mixing, diagnostics, ablation drivers. |
| `pipeline/generation/` | 12 | Plan and program generation, soft-prefix training, IR quality evaluation. |
| `pipeline/retrieval/` | 67 | Retrieval index construction and the retrieval-baseline evaluations. |
| `analysis/` | 81 | One script per reported analysis — interventions, budget sensitivity, anchor separation, failure taxonomy, coverage/fidelity accounting, editability aggregation, the plan-diagnostic study, and the derivations of the operation vocabulary and the STEP descriptor layout. |
| `external/` | 13 | The CAD-Recode comparison: input pipeline, runner, common evaluator, paired analysis. See [External comparison](#external-comparison-cad-recode). |
| `reports/` | 143 | Run outputs. See [Reports](#reports). |
| `docs/` | 1 | `E2_protocol_frozen.md`: the plan-diagnostic protocol, frozen before any of its outcome numbers were computed, including what it may and may not conclude. |

## Reports

`reports/` is the evidence layer. It holds the outputs the reported tables and figures are read
from, not the raw model outputs.

| Path | Contents |
|---|---|
| `reports/execution/` | 121 gate-rate summaries, one per evaluated arm. Each records the row count, and the pass counts and rates for the five gates: syntax, execution, build, kernel validity, STEP export. |
| `reports/editability/` | Parameter-perturbation results: per-perturbation outcomes and the aggregate, for the generated arm and the two retrieval arms. |
| `reports/external/` | The CAD-Recode comparison: the paired coverage/fidelity report, the batch summary, and the environment manifests for the isolated evaluation environment. |
| `reports/geometry/` | Per-part geometry rows for the comparisons the reported figures rest on. |
| `reports/figure-data.json` | Every numeral drawn in the diagnostic and coverage/fidelity figures, with the run file each came from. It names its own twelve inputs, all of which are under `reports/`. |

## Tracing a reported number to its report

| Reported quantity | Report |
|---|---|
| Four-modality results (syntax, Prog-Op-F1, build, STEP export) | `reports/execution/exec_eval_25k_stage3b_{text,image,point,step}.json` |
| Direct-latent and exposure-matched arms | `reports/execution/exec_e1_step_{A1E,B2P,A1,C3}.json` |
| Observation-channel and prefix interventions | `reports/execution/exec_e1_step_{C3,C2,S3,S2}.json`, `exec_e1_text_{C3,C2}.json` |
| Worth of the deterministic repair rules | `exec_eval_25k_stage3b_*` against `exec_norepair_25k_stage3b_*` |
| Coverage against fidelity, family-held-out split | `reports/geometry/geom_comp_step_{ours,nnir}.jsonl` |
| External positioning against CAD-Recode | `reports/external/external_paired_report.txt`, `batch_summary.txt` |
| Parametric behaviour | `reports/editability/editability_25k_step_c/` |
| Plan-diagnostic study | `reports/figure-data.json`, produced by `analysis/e2_analysis.py` and `analysis/e2_latent_cosine.py` under the protocol in `docs/E2_protocol_frozen.md` |

Arm identifiers differ between the two naming systems used during the work: the direct-latent arm
at 3,000 updates is `A1E`, the same arm at 9,000 updates is `A1`, the exposure-matched plan arm is
`B2P`, and the deployed arm is `C3`. Intervention cells are `C3`/`C2` for observation present and
suppressed, and `S3`/`S2` for the same two with a shuffled construction prefix.

## Reproducing

```bash
pip install -r requirements.txt
```

Then work through `pipeline/stages/` in numeric order. The stages assume a corpus laid out as
FllumaOne-100K and a single CUDA device; the language-model stages load Qwen2.5-Coder-1.5B in 4-bit
NF4 with double quantisation and train LoRA adapters on top.

**The pipeline scripts contain machine-specific absolute paths.** They were written to run on one
workstation, and 87 of the 165 files under `pipeline/` carry a hard-coded Windows or WSL path. They
are published as the record of what was actually run, not as a turnkey installer; expect to edit
paths before running any of them. The library under `miragecad/` is free of absolute paths.

Some scripts carry header comments referring to internal design notes that are not part of this
release. Those references are commentary; nothing depends on them.

## External comparison (CAD-Recode)

The comparison against CAD-Recode is a **system-level positioning experiment**, not a reproduction
of that method's published benchmark.

**CAD-Recode's code and checkpoint are CC BY-NC 4.0 and are not redistributed here.** The runner in
`external/` loads the released implementation from an upstream checkout at run time and hashes the
extracted source, so an upstream change is detected rather than silently absorbed. Nothing of that
project's code, checkpoint, or generated output is included in this repository. To repeat the
comparison you need your own checkout and checkpoint from the upstream release.

Both systems were scored through one common evaluator, applied identically: a frozen tessellation
operator, both shapes normalised into the unit cube, Chamfer distance as defined in CAD-Recode's
released demo, and volumetric IoU by mesh boolean. Coverage and conditional fidelity are reported
separately and are never combined into one score, because they answer different questions and on
this data they point in opposite directions.

## Licence

Everything in this repository is released under **0BSD** (see [LICENSE](LICENSE)): you may use,
copy, modify and distribute it for any purpose, commercial or not, with no conditions attached and
no requirement to credit anyone.

**That covers this repository's own contents only.** It cannot and does not grant rights to third
parties' work:

- **CAD-Recode** is CC BY-NC 4.0. None of it is included here, but running anything in `external/`
  requires obtaining it yourself, and its non-commercial term governs your use of it.
- **Qwen2.5-Coder-1.5B**, the base model the language-model stages fine-tune, carries its own
  upstream licence.
- **FllumaOne-100K**, the training corpus, is a separate dataset with its own citation and terms.

## What is not in this repository

| Not included | Why |
|---|---|
| Model checkpoints and LoRA adapters | Large binaries; they belong in a release or model host rather than a source tree. |
| The FllumaOne-100K corpus | A separate dataset with its own citation. |
| CAD-Recode code, checkpoint, or generated outputs | CC BY-NC 4.0; loaded from upstream at run time and not redistributed. |
| Per-row execution dumps | 18 MB across 121 runs. Their summaries are in `reports/execution/` and are what the reported numbers are read from. |
| Generated program dumps | Large, and regenerable from `pipeline/generation/`. |
| The manuscript, and the scripts that audit it | Bibliography checks, table inventories and section audits operate on a LaTeX source that is not published here, so they could not run. |
| Figure generators | Artwork tooling. The data behind the figures is kept, as `reports/figure-data.json`. |
| Internal planning and status documents | Roadmaps, milestone lists and progress notes: project management, not reproduction material. |

## Known limitations of this implementation

These are implementation faults rather than limitations of the approach, and they bound how some
results should be read.

- **The point-cloud encoder is scale-blind by construction.** Its input is divided by the maximum
  radius, so absolute size is removed before the network sees it.
- **The STEP branch's local streams carried no information on this corpus.** The face, edge and
  relation streams receive no per-entity records, so the reported STEP results effectively depend on
  the 50-dimensional global descriptor alone, whose layout `analysis/appendix_step_layout.py`
  reconstructs from the source. No claim about learned B-Rep encoding is supported.
- **`Prog-Op-F1` extracts identifiers wherever they occur**, not only at call sites, so its absolute
  level is not operation accuracy. Its orderings are unaffected;
  `analysis/trace_progopf1.py` quantifies the effect.
- **Every training result is a single run.** Seeds are fixed but no result carries a seed-variance
  estimate, which bounds how finely two configurations can be distinguished.
- **The code-decoder stages train on STEP-conditioned rows** and their adapters are reused across
  modalities, which is a confound in any cross-modality comparison.
