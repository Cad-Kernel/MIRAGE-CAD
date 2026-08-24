# MIRAGE-CAD Training Code

This folder contains the executable code for **MIRAGE-CAD**, an IR-anchored multimodal framework for editable CAD program generation on FllumaOne-100K.

The code supports two experiment scales:

- `smoke500`: a pipeline smoke test for data preparation, STEP extraction, alignment, latent-prior training, retrieval, generation, and evaluation.
- `50k`: the paper-scale experiment with 50,000 training samples, 5,000 validation samples, and 5,000 test samples.

## Method Summary

MIRAGE-CAD uses the Construction IR as the shared anchor for CAD construction semantics.

```text
text / image / point cloud / STEP-BRep query
  -> modality encoder
  -> shared Construction-IR latent space
  -> modality-specific IR latent prior
  -> Construction Soft Prefix Adapter
  -> LoRA-IR generated Construction IR plan
  -> LoRA-Code generated executable Flluma Python program
```

The baseline is called **Direct Retrieval RAG**. It retrieves examples directly from the query modality embedding and then runs the same LoRA program generator. It is not treated as a separate older version of the method.

## Code Layout

```text
miragecad/
  data.py              data loading, STEP tensorization, prompt construction
  models.py            multimodal alignment model and STEP/B-Rep encoder
  losses.py            contrastive alignment losses
  latent_prior.py      modality-to-IR latent prior (ResidualMLP + retrieval metrics)
  soft_prefix.py       SoftPrefixAdapter: z_ir_hat -> prefix tokens for LoRA-IR
  gen_prompts.py       build_ir_prompt and build_program_prompt with modality evidence
  point_sampling.py    deterministic/random/FPS point-cloud sampling

gen_scripts/
  train_soft_prefix_ir.py     Stage 3: train LoRA-IR adapter + soft-prefix jointly
  generate_predicted_ir.py    Stage 4b: cache predicted IR for train split
  run_miragecad.py            inference for pipelines A-E (all ablation modes)
  evaluate_ir_quality.py      IR cosine, op-set F1, and LCS metrics
  mix_ir_dataset.py           mix GT and predicted IR for Stage 4b training data
  scripts/                    gen pipeline shell wrappers (smoke500)

prepare_manifest.py    creates smoke500 and 50k JSONL splits
extract_step_features.py
train_alignment.py
build_index.py
train_latent_prior.py
generate_latent_prior.py
generate_programs.py
evaluate_latent_retrieval.py
evaluate_programs.py
retrieve_candidates.py
train_program_lora.py
scripts/               base pipeline shell wrappers
```

## STEP/B-Rep Branch

The STEP branch is real geometry-derived input, not copied metadata. STEP features are extracted from each `model.step` file using Flluma/OpenCASCADE before WSL training.

The loader converts each extracted STEP JSON into a fixed-size Global-Local-Relation B-Rep representation:

- a 50-dimensional global B-Rep descriptor;
- padded face-descriptor tensors;
- padded edge-descriptor tensors;
- a lightweight relation descriptor.

If the extractor output does not yet contain detailed face or edge descriptors, the loader uses zero-padded local tensors while still using the available kernel-derived global and relation statistics. This keeps old extracted files usable without changing the model interface.

## Point-Cloud Branch

FllumaOne point clouds contain 2,048 surface samples. MIRAGE-CAD trains with 1,024 sampled points by default:

- training: hybrid random/FPS sampling;
- validation and testing: deterministic FPS sampling.

The point-cloud prior uses normalized `x,y,z` coordinates only. Normals are deliberately excluded so the protocol remains comparable with datasets that do not provide normals.

## Paths

Windows source folder:

```powershell
C:\Workspace\Project\Paper\MIRAGE-V2\src
```

WSL training folder:

```bash
~/workspace/MIRAGE/src
```

Dataset:

```bash
/mnt/c/Workspace/Project/FllumaOne/FllumaOne-100K
```

Flluma CLI for STEP extraction:

```powershell
C:\Workspace\Project\Flluma\build\Desktop_Qt_6_8_3_MSVC2022_64bit-Release\bin\FllumaCLI.exe
```

## Sync Code to WSL

```powershell
Copy-Item -Recurse -Force `
  "C:\Workspace\Project\Paper\MIRAGE-V2\src\*" `
  "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\"
```

Then enter WSL:

```bash
wsl
conda activate ai_dev
cd ~/workspace/MIRAGE/src
```

## Smoke500 Pipeline

All commands below run inside WSL with `conda activate ai_dev` from `~/workspace/MIRAGE/src`.

### Stage 1 — Data Preparation and Alignment

1. Prepare the split.

```bash
bash scripts/prepare_500.sh
```

2. Extract real STEP/B-Rep descriptors from Windows PowerShell.

```powershell
powershell -ExecutionPolicy Bypass -File "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\scripts\extract_step_features_500.ps1"
```

3. Train IR-anchored multimodal alignment.

```bash
bash scripts/train_alignment_500.sh
```

4. Build the training IR retrieval index and the test IR index.

```bash
bash scripts/build_index_500.sh
bash scripts/build_test_index_500.sh
```

### Stage 2 — Latent Prior

5. Train MIRAGE-CAD latent priors (STEP and point-cloud modalities).

```bash
bash scripts/train_prior_step_500.sh
bash scripts/train_prior_point_500.sh
```

6. Evaluate prior retrieval.

```bash
bash scripts/eval_retrieval_prior_step_500.sh
bash scripts/eval_retrieval_prior_point_500.sh
```

### Stage 4 — LoRA-Code Generator (Base)

7. Train the LoRA CAD program generator (independent of Stages 2–3).

```bash
bash scripts/train_lora_program_500.sh
```

### Stage 3 — LoRA-IR Generator + Soft Prefix (MIRAGE-CAD)

8. Train the LoRA-IR generator and soft-prefix adapter jointly. Requires Stage 1 alignment and Stage 2 prior checkpoints.

```bash
bash gen_scripts/scripts/train_lora_ir_500.sh
```

Output: `outputs/lora_ir_500/`

### Stage 4b — Predicted IR Cache (MIRAGE-CAD)

9. Generate predicted Construction IR for the train split only. Do **not** run on val or test — this would leak training signal.

```bash
bash gen_scripts/scripts/generate_cache_ir_500.sh
```

Output: `outputs/predicted_ir_train_500.jsonl`

### Inference — Ablation Pipelines A–E

10. Run all five MIRAGE-CAD ablation pipelines on the step modality test set.

```bash
bash gen_scripts/scripts/run_gen_step_500.sh
```

Outputs in `outputs/gen_step_500/`:

| File | Pipeline | Description |
|---|---|---|
| `direct_rag.jsonl` | A | Direct Retrieval RAG (query embedding retrieval) |
| `prior_rag.jsonl` | B | Prior Retrieval RAG (prior latent retrieval) |
| `gen_ir.jsonl` | C | MIRAGE-CAD: soft-prefix IR generation, no retrieval |
| `gen_ir_retrieval.jsonl` | D | MIRAGE-CAD: soft-prefix IR generation + retrieval |
| `full.jsonl` | E | MIRAGE-CAD Full: N=5 candidates, execution-guided selection |

11. Evaluate IR generation quality for Pipeline C.

```bash
bash gen_scripts/scripts/evaluate_ir_500.sh
```

Output: `outputs/gen_step_500/ir_quality_500.json`

### Base Pipeline Evaluation (Direct RAG Baseline)

12. Run quick program generation and evaluation for baseline comparison.

```bash
bash scripts/generate_500_quick.sh
bash scripts/evaluate_500_quick.sh
bash scripts/generate_prior_step_500.sh
bash scripts/evaluate_prior_step_500.sh
bash scripts/generate_rerank_step_500.sh
bash scripts/evaluate_rerank_step_500.sh
```

Use `smoke500` only to confirm the pipeline runs end-to-end. Do not report it as the main result.

## 50k Paper-Scale Pipeline

1. Prepare the split.

```bash
bash scripts/prepare_50k.sh
```

The 50k split uses stratified L1-L4 sampling from the official train/validation/test splits:

| Split | Total | L1 | L2 | L3 | L4 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Train | 50,000 | 1,500 | 8,500 | 27,500 | 12,500 |
| Validation | 5,000 | 150 | 850 | 2,750 | 1,250 |
| Test | 5,000 | 150 | 850 | 2,750 | 1,250 |

2. Extract STEP/B-Rep descriptors from Windows PowerShell.

```powershell
powershell -ExecutionPolicy Bypass -File "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE\src\scripts\extract_step_features_50k.ps1"
```

3. Train alignment and build indices.

```bash
bash scripts/train_alignment_50k.sh
bash scripts/build_index_50k.sh
bash scripts/build_test_index_50k.sh
```

4. Train MIRAGE-CAD latent priors.

```bash
bash scripts/train_prior_step_50k.sh
bash scripts/train_prior_point_50k.sh
```

5. Train the LoRA CAD program generator.

```bash
bash scripts/train_lora_program_50k.sh
```

6. Evaluate latent-prior retrieval.

```bash
bash scripts/eval_retrieval_prior_step_50k.sh
bash scripts/eval_retrieval_prior_point_50k.sh
```

7. Run Direct Retrieval RAG baseline.

```bash
bash scripts/generate_50k.sh
bash scripts/evaluate_50k.sh
```

8. Run MIRAGE-CAD STEP prior and rerank variants.

```bash
bash scripts/generate_prior_step_50k.sh
bash scripts/evaluate_prior_step_50k.sh
bash scripts/generate_rerank_step_50k.sh
bash scripts/evaluate_rerank_step_50k.sh
```

For paper tables, report the full 5k test results, not quick debugging runs.

## Main Result Files

```text
outputs/align_smoke500/best.pt
outputs/align_smoke500/train_ir_index.npz
outputs/prior_step_smoke500/best.pt
outputs/lora_ir_500/                       (LoRA-IR adapter + soft_prefix.pt)
outputs/predicted_ir_train_500.jsonl       (Stage 4b cache)
outputs/gen_step_500/full.jsonl            (Pipeline E — main paper result)
outputs/gen_step_500/ir_quality_500.json   (IR evaluation)

outputs/align_50k/best.pt
outputs/align_50k/train_ir_index.npz
outputs/50k_test_ir_index.npz
outputs/prior_step_50k/best.pt
outputs/prior_point_50k/best.pt
outputs/predictions_50k.jsonl
outputs/predictions_prior_step_50k.jsonl
outputs/predictions_rerank_step_50k.jsonl
outputs/eval_50k/evaluation_summary.json
outputs/eval_retrieval_prior_step_50k.json
```

## Paper Naming

Use these names consistently (five ablation levels):

| Level | Name | Description |
|---|---|---|
| A | **Direct Retrieval RAG** | Query embedding retrieval → LoRA-Code |
| B | **Prior Retrieval RAG** | Prior latent retrieval → LoRA-Code |
| C | **MIRAGE-CAD (IR only)** | Soft-prefix IR generation, no retrieval → LoRA-Code |
| D | **MIRAGE-CAD (IR + RAG)** | Soft-prefix IR generation + prior retrieval → LoRA-Code |
| E | **MIRAGE-CAD Full** | Level D + N=5 candidates + execution-guided selection |

Do not use version labels for the method in the paper. Keep the baseline and proposed method names explicit.
