#!/bin/bash
# Phase 2 / Stage 1: four-modality star-topology alignment training, with
# rare-op-boosted sampling enabled (--rare-op-boost 2.0 -- mild 2x oversample
# of rows containing OP_SWEEP_TUBE/OP_CIRCULAR_PATTERN/OP_SKETCH_ON_FACE/
# OP_FACE_EXTRUDE_ADD/OP_FACE_EXTRUDE_CUT/OP_PROFILE_CUT, per the v1.0 plan's
# decision to try mild rare-op-aware sampling before attempting hard-negative
# mining). This is the ONLY Stage 1 change from the 5K recipe -- do not also
# change epochs/batch/lr casually, so any rare-op improvement can be
# attributed to the sampler, not a confounded hyperparameter change.
#
# NOTE: there is no saved 5K-scale train_alignment_*.sh in this repo to copy
# (the 5K run that produced outputs/align_smoke5k_ep10 was done ad hoc and
# never captured in a script) -- this script is modeled on the 50K wrapper
# (scripts/train_alignment_50k.sh) instead, with epochs increased from 50K's
# 3 to 5 as a middle ground (revisit if Stage 1 diagnostics look undertrained).
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

python train_alignment.py \
  --train-jsonl data/25k/train.jsonl --val-jsonl data/25k/val.jsonl \
  --output-dir outputs/align_25k \
  --modalities text image point step ir --image-mode iso \
  --epochs 5 --batch-size 8 --grad-accum 4 \
  --max-text-length 128 --max-ir-length 256 --point-count 1024 \
  --rare-op-boost 2.0 \
  --bf16

echo "=== Checkpoint: outputs/align_25k/best.pt (+last.pt, training_report.json) ==="
