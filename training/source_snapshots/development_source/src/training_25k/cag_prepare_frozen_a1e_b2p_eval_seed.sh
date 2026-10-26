#!/bin/bash
# Prepare seed-specific geometry inputs for the CAG frozen A1E/B2P comparison.
# Run in WSL after training + prediction + gate evaluation.

set -euo pipefail

source __USER_HOME__/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

SEED=${SEED:-1}
LIMIT=${LIMIT:-500}

python scratch/cag_prepare_a1e_b2p_seed_geometry.py \
  --seed "$SEED" \
  --expected-rows "$LIMIT"

cat <<EOF

=== NOW IN WINDOWS POWERSHELL ===

1) Gate / execution evaluation, if not already done:

  & "__DEV_ROOT__\\src\\scripts\\run_e1_execution.ps1" \`
    -Modalities step \`
    -Conditions A1E_s${SEED},B2P_s${SEED}

2) Geometry scoring:

  foreach (\$A in @("step_A1E_s${SEED}", "step_B2P_s${SEED}")) {
    & "__DEV_ROOT__\\src\\scripts\\evaluate_geometry_nbest.ps1" \`
      -InputJsonl "__RUN_SOURCE_ROOT__\\outputs\\e1_observation_bypass\\geom_input_\$A.jsonl" \`
      -OutputDir  "__DEV_ROOT__\\scratch\\geom_e1_\$A"
  }

3) Seed summary after geometry scoring:

  python __DEV_ROOT__\\src\\scratch\\cag_summarize_a1e_b2p_seed_eval.py --seed ${SEED}

EOF