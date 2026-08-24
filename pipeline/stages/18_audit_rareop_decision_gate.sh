#!/bin/bash
# Phase 7 decision gate: has rare-op-boosted Stage 1 sampling (03_train_alignment.sh's
# --rare-op-boost 2.0) actually reduced the OP_SWEEP_TUBE/OP_CIRCULAR_PATTERN
# latent collapse found at 5K scale? Run this AFTER steps 03-05 (alignment +
# priors) and step 11/12 (need a P1a-repaired predicted_ir file with
# reference_ir, for the STEP-side grouping).
#
# 5K baseline numbers to compare against (docs/MIRAGE-CAD_experiment_results.md SS4.5):
#   STEP:  z_m cos sweep=0.900 circular=0.802 | z_hat cos sweep=0.876 circular=0.940 | contrast ~0.01/0.00
#   Point: z_m cos sweep=0.848 circular=0.938 | z_hat cos sweep=0.864 circular=0.961 | contrast ~0.10/0.01
#   Text:  z_m cos sweep=0.660 circular=0.569 | z_hat cos sweep=0.829 circular=0.902 | contrast ~0.09/0.02
#   Image: z_m cos sweep=0.730 circular=0.854 | z_hat cos sweep=0.865 circular=0.949 | contrast ~0.13/0.00
#
# DECISION GATE (per the v1.0 plan): if 25K's op-group cosines are still in
# the same 0.7-1.0 range (not clearly, substantially lower than the 5K
# numbers above, and not approaching the contrast group's ~0.0-0.13), rare-op
# collapse persists -- STOP and revisit the Stage 1 objective (hard-negative
# mining is the next thing to try, NOT simply raising --rare-op-boost further
# or adding more epochs) rather than proceeding to treat the 25K numbers as a
# fixed result.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

mkdir -p outputs/rareop_audit_25k

echo "=== STEP ==="
python training_25k/scripts/audit_rareop_collapse_step.py \
  --alignment-checkpoint outputs/align_25k/best.pt \
  --prior-checkpoint outputs/prior_step_25k/best.pt \
  --test-jsonl data/25k/test.jsonl \
  --predicted-ir-jsonl outputs/lora_ir_25k/predicted_ir_test_step_p1a.jsonl \
  --output-json outputs/rareop_audit_25k/step.json

for m in point text image; do
  echo "=== $m ==="
  python scratch/audit_rareop_collapse_crossmodal.py \
    --modality $m \
    --alignment-checkpoint outputs/align_25k/best.pt \
    --prior-checkpoint outputs/prior_${m}_25k/best.pt \
    --input-jsonl data/25k/test.jsonl \
    | tee outputs/rareop_audit_25k/${m}.json
done

echo "=== Wrote outputs/rareop_audit_25k/{step,point,text,image}.json -- compare against the 5K numbers in this script's header comment ==="
