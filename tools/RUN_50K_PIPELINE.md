# MIRAGE-CAD 50k Pipeline

Run these commands after the `smoke500` pipeline is complete and stable.

```bash
cd ~/workspace/MIRAGE-V2/src
conda activate ai_dev
```

The 50k experiment uses 50,000 training samples, 5,000 validation samples, and 5,000 test samples.

## 1. Prepare Data

```bash
bash scripts/prepare_50k.sh
```

## 2. Extract STEP/B-Rep Descriptors

Run from Windows PowerShell, not WSL:

```powershell
powershell -ExecutionPolicy Bypass -File "\\wsl.localhost\Ubuntu\home\jizong\workspace\MIRAGE-V2\src\scripts\extract_step_features_50k.ps1"
```

## 3. Train Alignment and Build Indices

```bash
bash scripts/train_alignment_50k.sh
bash scripts/build_index_50k.sh
bash scripts/build_test_index_50k.sh
```

## 4. Train Program Generator

```bash
bash scripts/train_lora_program_50k.sh
```

## 5. Train MIRAGE-CAD Latent Priors

```bash
bash scripts/train_prior_step_50k.sh
bash scripts/train_prior_point_50k.sh
```

## 6. Evaluate Latent-Prior Retrieval

```bash
bash scripts/eval_retrieval_prior_step_50k.sh
bash scripts/eval_retrieval_prior_point_50k.sh
```

## 7. Direct Retrieval RAG Baseline

```bash
bash scripts/generate_50k.sh
bash scripts/evaluate_50k.sh
```

## 8. MIRAGE-CAD STEP Prior and Rerank Variants

```bash
bash scripts/generate_prior_step_50k.sh
bash scripts/evaluate_prior_step_50k.sh
bash scripts/generate_rerank_step_50k.sh
bash scripts/evaluate_rerank_step_50k.sh
```

Use the full 5k test summaries for paper tables.

