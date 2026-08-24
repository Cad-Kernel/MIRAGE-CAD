#!/bin/bash
# Compositional-split pipeline / Stage 1: four-modality star-topology
# alignment, retrained from scratch on data/25k_comp (4 template families --
# cross_tab_profile_mount, stepped_profile_mount, face_recursive_mount,
# sweep_tube -- held out entirely into data/25k_comp/comp_test.jsonl; every
# operation type those families use still has at least one other carrier
# family in data/25k_comp/train.jsonl, verified by audit before this split
# was built). Identical hyperparameters to 03_train_alignment.sh (the
# original 25K recipe) -- only the data/output paths differ, so any
# difference in downstream compositional-generalization results is
# attributable to the held-out split, not a confounded hyperparameter change.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

python train_alignment.py \
  --train-jsonl data/25k_comp/train.jsonl --val-jsonl data/25k_comp/val.jsonl \
  --output-dir outputs/align_25k_comp \
  --modalities text image point step ir --image-mode iso \
  --epochs 5 --batch-size 8 --grad-accum 4 \
  --max-text-length 128 --max-ir-length 256 --point-count 1024 \
  --rare-op-boost 2.0 \
  --bf16

echo "=== Checkpoint: outputs/align_25k_comp/best.pt (+last.pt, training_report.json) ==="
