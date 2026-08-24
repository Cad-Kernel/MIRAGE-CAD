#!/bin/bash
# Build and enter `external_eval`, the environment that scores the external comparison.
#
#   bash src/scratch/external_eval_env.sh            # create if absent, then self-test
#   bash src/scratch/external_eval_env.sh --recreate # tear down and rebuild from scratch
#   bash src/scratch/external_eval_env.sh --print    # just print the commands, change nothing
#
# WHY A SEPARATE ENVIRONMENT, AND WHY THIS ONE IS THE SMALL ONE. Three environments are involved
# in the CAD-Recode comparison and conflating any two of them breaks something:
#
#   ai_dev         MIRAGE. transformers 5.5.1, torch 2.10.0+cu128. NEVER MODIFIED. Every
#                  published MIRAGE number was produced here, so installing anything for the
#                  external comparison into it would put that reproducibility at risk for no
#                  reason.
#   cadrecode_env  CAD-Recode inference and CadQuery execution. transformers 4.47.1,
#                  torch 2.5.1+cu124, per its Dockerfile. Its CADRecode class subclasses Qwen2
#                  internals, so it will not run under transformers 5.x. NOT built by this
#                  script -- it needs a GPU stack and is a separate step.
#   external_eval  THIS ONE. Scores both arms. numpy, scipy, trimesh, manifold3d. No torch, no
#                  CUDA, no model. Scoring is the one part both arms must share, so it lives
#                  apart from either arm's inference environment and can be audited on its own.
#
# THE KEY DISTINCTION THAT KEEPS THIS ENVIRONMENT SMALL: inference-preprocessing dependencies are
# NOT metric dependencies. pytorch3d appears in CAD-Recode's Dockerfile only for farthest-point
# sampling of the model input, and open3d only for the demo's renderer -- built from source with
# headless rendering, which is expensive and has nothing to do with the metric. Neither belongs
# here. The metric needs mesh sampling and a boolean engine, and that is all.
#
# VERSIONS ARE PINNED TO CAD-RECODE'S OWN. trimesh 4.5.3 and manifold3d 3.0.0 are the versions in
# its Dockerfile. The point of this environment is to compute ITS metric, so it uses ITS mesh
# stack rather than whatever is current.
set -uo pipefail

ENV_NAME=${ENV_NAME:-external_eval}
PY=${PY:-3.12}
EVAL_SCRIPT=${EVAL_SCRIPT:-/mnt/c/Workspace/Project/Paper/MIRAGE-V2/src/scratch/external_geometry_eval.py}

# Pinned to CAD-Recode's Dockerfile.
TRIMESH=4.5.3
MANIFOLD3D=3.0.0

CREATE_CMD="conda create -y -n $ENV_NAME python=$PY numpy scipy"
PIP_CMD="conda run -n $ENV_NAME pip install trimesh==$TRIMESH manifold3d==$MANIFOLD3D"
TEST_CMD="conda run -n $ENV_NAME python $EVAL_SCRIPT"

RECREATE=0
PRINT_ONLY=0
for a in "$@"; do
  case "$a" in
    --recreate) RECREATE=1 ;;
    --print) PRINT_ONLY=1 ;;
    -h|--help) sed -n '2,40p' "$0"; exit 0 ;;
    *) echo "unknown argument: $a" >&2; exit 2 ;;
  esac
done

if [ "$PRINT_ONLY" -eq 1 ]; then
  echo "$CREATE_CMD"
  echo "$PIP_CMD"
  echo "$TEST_CMD"
  exit 0
fi

if [ "$ENV_NAME" = "ai_dev" ]; then
  echo "Refusing: ai_dev is the MIRAGE environment and is never modified." >&2
  exit 1
fi

command -v conda >/dev/null || { echo "conda not on PATH." >&2; exit 1; }

if [ "$RECREATE" -eq 1 ]; then
  echo "=== removing $ENV_NAME ==="
  conda env remove -y -n "$ENV_NAME" || true
fi

if conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  echo "=== $ENV_NAME exists, skipping creation ==="
else
  echo "=== creating $ENV_NAME (python $PY, numpy, scipy) ==="
  $CREATE_CMD || { echo "create failed" >&2; exit 1; }
  echo "=== installing trimesh==$TRIMESH manifold3d==$MANIFOLD3D (CAD-Recode's pins) ==="
  $PIP_CMD || { echo "pip install failed" >&2; exit 1; }
fi

# ---------------------------------------------------------------------------
# Record what was actually built. A pinned command is a statement of intent; the manifest is
# what happened, and it is what a later reader needs to know whether a number is comparable.
# ---------------------------------------------------------------------------
MANIFEST_DIR=${MANIFEST_DIR:-/mnt/c/Workspace/Project/Paper/MIRAGE-V2/scratch/external_eval_manifest}
mkdir -p "$MANIFEST_DIR"
conda run -n "$ENV_NAME" python -c "import sys; print(sys.version)" > "$MANIFEST_DIR/python_version.txt" 2>&1
conda run -n "$ENV_NAME" pip freeze > "$MANIFEST_DIR/pip_freeze.txt" 2>&1
{
  echo "env_name=$ENV_NAME"
  echo "created_by=src/scratch/external_eval_env.sh"
  echo "trimesh_pin=$TRIMESH"
  echo "manifold3d_pin=$MANIFOLD3D"
  echo "purpose=score the CAD-Recode external comparison; scores BOTH arms"
  echo "note=no torch, no CUDA, no model. pytorch3d and open3d deliberately absent:"
  echo "note=pytorch3d is inference-preprocessing only (FPS), open3d is the demo renderer only."
} > "$MANIFEST_DIR/env_manifest.txt"
echo "  manifest -> $MANIFEST_DIR"

echo
echo "=== self-test ==="
echo "  $TEST_CMD"
$TEST_CMD
rc=$?

echo
if [ "$rc" -ne 0 ]; then
  echo "Self-tests did not all pass. Nothing external should be scored until they do."
  echo "In particular, the translation-only and scale-only checks are what verify that this"
  echo "metric discards absolute position and scale -- the basis for reporting that MIRAGE's"
  echo "scale-blind point pathway is not directly penalised by it."
else
  echo "Environment ready and the metric is verified. Next: the sample manifest, pairing the"
  echo "same external Fusion360 sample_ids across both arms, before any side-by-side number."
fi
exit $rc
