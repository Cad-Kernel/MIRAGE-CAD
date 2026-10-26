#!/bin/bash
# Phase 3a: construction-disjoint STEP train-only descriptor NN baseline.
# This does not train or load a neural model. It retrieves the nearest TRAIN row
# by global STEP descriptor and emits that train row's reference program.
set -euo pipefail
source __USER_HOME__/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

source training_25k/_guard_fresh.sh \
  training_25k/cag_gen_cd_step_nn_descriptor_baseline.py \
  training_25k/cag_prepare_construction_disjoint_geometry.py

DATA=${DATA:-data/construction_disjoint_step_v1}
WORK=${WORK:-outputs/construction_disjoint_step_v1}
ARM=${ARM:-NN_DESC_TRAIN}
PRED="$WORK/nn_step_descriptor_train_only.jsonl"
ACTUALS="$WORK/nn_step_descriptor_train_only_actuals.json"
GEOM="$WORK/geom_input_step_${ARM}.jsonl"
GEOM_MANIFEST="$WORK/geom_input_step_${ARM}_manifest.json"

python - <<'PY'
import json, pathlib, sys
base = pathlib.Path("data/construction_disjoint_step_v1")
required = [
    base / "train.jsonl",
    base / "val.jsonl",
    base / "test.jsonl",
    base / "construction_split_manifest.csv",
    base / "cag_construction_split_actuals.json",
]
ok = True
for p in required:
    exists = p.exists()
    print(f"{'ok  ' if exists else 'FAIL'} {p}")
    ok &= exists
actuals = json.loads((base / "cag_construction_split_actuals.json").read_text())
print("split freeze_status:", actuals.get("freeze_status"))
print("overlap_audit:", actuals.get("overlap_audit"))
ok &= actuals.get("freeze_status", {}).get("sample_ids") == "FROZEN"
ok &= actuals.get("overlap_audit", {}).get("status") == "PASS"
sys.exit(0 if ok else 1)
PY

mkdir -p "$WORK"

if [ -f "$PRED" ] && [ "$(wc -l < "$PRED")" -eq 500 ]; then
  echo "=== keep complete NN descriptor baseline: $PRED ==="
else
  echo "=== generating train-only STEP descriptor NN baseline ==="
  python training_25k/cag_gen_cd_step_nn_descriptor_baseline.py \
    --train-jsonl "$DATA/train.jsonl" \
    --test-jsonl "$DATA/test.jsonl" \
    --manifest-csv "$DATA/construction_split_manifest.csv" \
    --split-actuals "$DATA/cag_construction_split_actuals.json" \
    --output-jsonl "$PRED" \
    --actuals-json "$ACTUALS"
fi

echo "=== preparing geometry input for $ARM ==="
python training_25k/cag_prepare_construction_disjoint_geometry.py \
  --predictions "$PRED" \
  --test-jsonl "$DATA/test.jsonl" \
  --output-jsonl "$GEOM" \
  --manifest-json "$GEOM_MANIFEST" \
  --arm "$ARM" \
  --expected-rows 500

echo
echo "=== BASELINE GENERATION COMPLETE; NOW RUN GATE + GEOMETRY IN WINDOWS POWERSHELL ==="
cat <<'EOF'
$Root = "__RUN_SOURCE_ROOT__"

& "__DEV_ROOT__\src\scripts\evaluate_execution.ps1" `
  -InputJsonl "$Root\outputs\construction_disjoint_step_v1\nn_step_descriptor_train_only.jsonl" `
  -OutputDir "__DEV_ROOT__\scratch\exec_cd_step_NN_DESC_TRAIN" `
  -CodeField prediction

& "__DEV_ROOT__\src\scripts\evaluate_geometry_nbest.ps1" `
  -InputJsonl "$Root\outputs\construction_disjoint_step_v1\geom_input_step_NN_DESC_TRAIN.jsonl" `
  -OutputDir "__DEV_ROOT__\scratch\geom_cd_step_NN_DESC_TRAIN"
EOF
