#!/bin/bash
# Compositional-split pipeline, Stage 2 through Stage 4b, chained into one
# script so it can be launched once and left running unattended (e.g.
# overnight, or while away from the machine). Run this AFTER
# comp_03_train_alignment.sh (Stage 1) has finished -- Stage 2's priors
# require outputs/align_25k_comp/best.pt to already exist.
#
# Stages, in order:
#   1. comp_05_train_priors.sh          -- Stage 2: 4 modality priors
#   2. comp_06_train_lora_ir.sh         -- Stage 3 (STEP-only) + Stage 3b (mixed)
#   3. comp_07_08_stage4b_prep.sh       -- generate predicted_ir subset + build 70/30 mix
#   4. comp_09_10_train_lora_code.sh    -- Stage 4 (GT IR) + Stage 4b (mixed)
#
# CRASH RECOVERY: after a power loss / reboot, just re-run this exact same
# command. Every stage's completion is checked via its own
# *_training_report.json marker file (written only after that stage's
# training genuinely finishes) -- an already-completed stage is skipped, not
# rerun. IMPORTANT CAVEAT: none of the four underlying trainers
# (train_alignment.py, train_latent_prior.py, gen_scripts.train_soft_prefix_ir,
# train_program_lora.py used only for Stage 4/4b has real --resume-from-checkpoint
# support) can resume MID-stage -- if the crash happens 80% through, say,
# Stage 3's ~3-epoch run, that whole stage restarts from epoch 0, not from
# 80%. This script only guarantees you never silently re-run or silently skip
# a WHOLE stage; it does not recover partial progress within one.
#
# All output is tee'd to logs/comp_stages2to4b.log (appended, not
# overwritten) so the log survives a reboot even if the terminal itself did
# not -- read that file after a restart to see exactly what happened last.
set -euo pipefail
cd ~/workspace/MIRAGE/src
mkdir -p logs
exec > >(tee -a logs/comp_stages2to4b.log) 2>&1

if [ ! -f outputs/align_25k_comp/best.pt ]; then
  echo "ERROR: outputs/align_25k_comp/best.pt not found -- Stage 1 (comp_03_train_alignment.sh) must finish first." >&2
  exit 1
fi

echo "=============================================="
echo "[$(date)] Resuming/starting pipeline run"
echo "=============================================="

# --- Stage 2: 4 modality priors ---
if [ -f outputs/prior_step_25k_comp/training_report.json ] && \
   [ -f outputs/prior_point_25k_comp/training_report.json ] && \
   [ -f outputs/prior_text_25k_comp/training_report.json ] && \
   [ -f outputs/prior_image_25k_comp/training_report.json ]; then
  echo "[$(date)] Stage 2 (4 priors) already complete -- skipping."
else
  echo "=============================================="
  echo "[$(date)] Starting Stage 2: 4 modality priors"
  echo "=============================================="
  bash training_25k/comp_05_train_priors.sh
fi

# --- Stage 3 + 3b: LoRA-IR ---
if [ -f outputs/lora_ir_25k_comp_stage3b/soft_prefix_training_report.json ]; then
  echo "[$(date)] Stage 3+3b (LoRA-IR) already complete -- skipping."
else
  echo "=============================================="
  echo "[$(date)] Starting Stage 3 + 3b: LoRA-IR"
  echo "=============================================="
  bash training_25k/comp_06_train_lora_ir.sh
fi

# --- Stage 4b prep: predicted_ir subset + 70/30 mix ---
if [ -f data/25k_comp/train_stage4b_mix.jsonl ]; then
  echo "[$(date)] Stage 4b prep already complete -- skipping."
else
  echo "=============================================="
  echo "[$(date)] Starting Stage 4b prep: predicted_ir subset + 70/30 mix"
  echo "=============================================="
  bash training_25k/comp_07_08_stage4b_prep.sh
fi

# --- Stage 4 + 4b: LoRA-Code ---
if [ -f outputs/qwen25_coder_1_5b_program_25k_comp_stage4b/training_report.json ]; then
  echo "[$(date)] Stage 4+4b (LoRA-Code) already complete -- skipping."
else
  echo "=============================================="
  echo "[$(date)] Starting Stage 4 + 4b: LoRA-Code"
  echo "=============================================="
  bash training_25k/comp_09_10_train_lora_code.sh
fi

echo "=============================================="
echo "[$(date)] ALL STAGES COMPLETE."
echo "Final checkpoint: outputs/qwen25_coder_1_5b_program_25k_comp_stage4b/"
echo "=============================================="
