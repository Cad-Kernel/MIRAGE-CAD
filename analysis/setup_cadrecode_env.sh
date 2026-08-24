#!/bin/bash
# Build `cadrecode_env`, the isolated environment that carries TWO jobs, and freeze what it is.
#
#   bash src/scratch/setup_cadrecode_env.sh --print    # show the commands, change nothing
#   bash src/scratch/setup_cadrecode_env.sh            # create if absent, then manifest + smoke
#   bash src/scratch/setup_cadrecode_env.sh --recreate
#
# TWO JOBS, NOT ONE. That was an open question until the Flluma probe settled it:
#
#   cadrecode_env
#     |- CAD-Recode inference
#     '- STEP -> mesh tessellation, and execution of the CadQuery code CAD-Recode emits
#
# The second job landed here because Flluma cannot build a geometry kernel:
# is_kernel_available() answers True for both OPENCASCADE and MANIFOLD while
# GeometryKernelFactory.create() returns None for both, and every kernel-level function takes that
# object. So the canonical STEP-to-mesh operator is a NEW external protocol component living here,
# not the manuscript's existing evaluation operator, and the paper says so.
#
# ai_dev IS NEVER MODIFIED. Every published MIRAGE number came out of it, and this environment
# needs transformers 4.47.1 against its 5.5.1. The script refuses to target it.
#
# DELIBERATELY NOT INSTALLED:
#   open3d     the demo's renderer only, built from source with headless rendering in CAD-Recode's
#              Dockerfile. Nothing in the metric or the input pipeline touches it.
#   pytorch3d  farthest-point sampling for the model input only. Deferred until the input pipeline
#              is actually built, because it is a git-commit-pinned source install and FPS over 8192
#              points is thirty lines of numpy if it proves painful.
#   flash-attn the demo requests attn_implementation='flash_attention_2' when CUDA is present.
#              Flash attention is exact, not an approximation, so its absence changes throughput and
#              not outputs. Recorded in the manifest either way rather than assumed.
#
# VERSIONS COME FROM CAD-RECODE'S OWN DOCKERFILE, not from what pip resolves today. The point of
# this environment is to run THEIR checkpoint under THEIR stack. trimesh is pinned to 4.5.3, the
# same version external_eval uses, so the mesh stack matches across the two environments.
set -uo pipefail

ENV_NAME=${ENV_NAME:-cadrecode_env}
PY=${PY:-3.11}
MANIFEST_DIR=${MANIFEST_DIR:-/mnt/c/Workspace/Project/Paper/MIRAGE-V2/scratch/cadrecode_env}
PROBE=${PROBE:-/mnt/c/Workspace/Project/Paper/MIRAGE-V2/src/scratch/probe_cadrecode_mesh.py}

# Pinned to CAD-Recode's Dockerfile. cadquery-ocp is the OCCT binding and is now a protocol
# component, not an ordinary dependency: it executes CAD-Recode's generated code, converts STEP to
# mesh, and supplies the meshes IoU is computed on.
# FORCED DEVIATION FROM CAD-RECODE'S PIN, and the only one. Their Dockerfile pins torch 2.5.1
# +cu124, which raises "no kernel image is available for execution on the device" on this GPU:
# RTX 50-series is sm_120 and that build ships code up to sm_90. The capability smoke test below
# catches it by launching a real kernel, which is how it was found.
#
# 2.7.0+cu128 is the smallest step that works -- the first series with sm_120 code, on an index
# already proven on this machine since every MIRAGE training run used cu128. Everything else stays
# pinned to their Dockerfile.
#
# This is defensible only because the paper already declares this is NOT a reproduction: their
# benchmark split and evaluation code are unreleased, so Phase 2 is a sanity gate and the text is
# forbidden from claiming reproduction. The deviation is disclosed there.
#
# The CPU route keeps their pin exactly and is one command away, not a rewrite:
#   TORCH=2.5.1 TORCH_INDEX=https://download.pytorch.org/whl/cpu \
#     bash src/scratch/setup_cadrecode_env.sh --recreate
# It costs roughly an order of magnitude in wall clock and does not recover their environment
# either -- they ran on H100s, so neither this GPU nor this CPU is that.
TORCH=${TORCH:-2.7.0}
TORCH_INDEX=${TORCH_INDEX:-https://download.pytorch.org/whl/cu128}
TRANSFORMERS=4.47.1
TOKENIZERS=0.21.0
HUB=0.27.0
SAFETENSORS=0.4.5
CADQUERY_COMMIT=e99a15df3cf6a88b69101c405326305b5db8ed94
CADQUERY_OCP=7.7.2
TRIMESH=4.5.3
MANIFOLD3D=3.0.0
NUMPY=2.2.0
SCIPY=1.14.1
# cadquery's own dependencies. CAD-Recode's Dockerfile installs everything with --no-deps and so
# lists these individually; taking only the interesting-looking lines from it left `import
# cadquery` dying on multimethod.
CQ_DEPS="multimethod==1.12 casadi==3.6.7 ezdxf==1.3.5 nlopt==2.9.0 path==17.0.0 typish==1.9.3"

PRINT_ONLY=0
RECREATE=0
for a in "$@"; do
  case "$a" in
    --print) PRINT_ONLY=1 ;;
    --recreate) RECREATE=1 ;;
    -h|--help) sed -n '2,40p' "$0"; exit 0 ;;
    *) echo "unknown argument: $a" >&2; exit 2 ;;
  esac
done

CREATE="conda create -y -n $ENV_NAME python=$PY"
PIP_TORCH="conda run -n $ENV_NAME pip install torch==$TORCH --index-url $TORCH_INDEX"
PIP_REST="conda run -n $ENV_NAME pip install \
  transformers==$TRANSFORMERS tokenizers==$TOKENIZERS huggingface-hub==$HUB \
  safetensors==$SAFETENSORS numpy==$NUMPY scipy==$SCIPY \
  trimesh==$TRIMESH manifold3d==$MANIFOLD3D cadquery-ocp==$CADQUERY_OCP \
  $CQ_DEPS \
  git+https://github.com/CadQuery/cadquery.git@$CADQUERY_COMMIT"

if [ "$PRINT_ONLY" -eq 1 ]; then
  echo "$CREATE"; echo "$PIP_TORCH"; echo "$PIP_REST"; exit 0
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
  echo "=== creating $ENV_NAME (python $PY) ==="
  $CREATE || { echo "create failed" >&2; exit 1; }
fi

# The dependency install runs EVERY time, not only on creation. pip skips what is already
# satisfied, so this is cheap, and it repairs a half-built environment -- which is the state the
# first attempt left behind when cadquery's own dependencies turned out to be missing. Skipping it
# for an existing env means a partial install can never be completed by re-running the script.
echo "=== torch $TORCH from $TORCH_INDEX ==="
$PIP_TORCH || { echo "torch install failed" >&2; exit 1; }
echo "=== the rest, pinned to CAD-Recode's Dockerfile ==="
$PIP_REST || { echo "dependency install failed" >&2; exit 1; }

mkdir -p "$MANIFEST_DIR"

# ---------------------------------------------------------------------------
# Manifest, then CAPABILITY SMOKE TESTS. Versions are not enough: Flluma reported
# is_kernel_available() True for a kernel whose factory returns None, which is exactly the class of
# failure a version list cannot see. So every claimed capability is exercised by a call.
# ---------------------------------------------------------------------------
echo
echo "=== manifest ==="
# Written to a file and run as a file. `conda run ... python -` receives NO STDIN, so the earlier
# heredoc form produced a 0-byte manifest and empty smoke tests while the script reported success.
TMPPY=$(mktemp -d)
cat > "$TMPPY/manifest.py" <<'PY'
import platform, sys
print("python           ", sys.version.replace("\n", " "))
print("platform         ", platform.platform())
for mod in ("torch", "transformers", "tokenizers", "huggingface_hub", "safetensors",
            "numpy", "scipy", "trimesh", "manifold3d", "cadquery", "OCP"):
    try:
        m = __import__(mod)
        print(f"{mod:17s}", getattr(m, "__version__", "(no __version__)"))
    except Exception as e:
        print(f"{mod:17s} MISSING: {type(e).__name__}: {e}")
try:
    import torch
    print("torch.cuda        ", torch.version.cuda)
    print("cuda available    ", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("device            ", torch.cuda.get_device_name(0))
except Exception as e:
    print("torch cuda probe   FAILED:", e)
for opt in ("flash_attn", "pytorch3d", "open3d"):
    try:
        m = __import__(opt)
        print(f"{opt:17s}", getattr(m, "__version__", "present"), "(optional)")
    except Exception:
        print(f"{opt:17s} absent (deliberate)")
print("MANIFEST_SENTINEL_OK")
PY
conda run -n "$ENV_NAME" python "$TMPPY/manifest.py" > "$MANIFEST_DIR/manifest.txt" 2>&1
if ! grep -q MANIFEST_SENTINEL_OK "$MANIFEST_DIR/manifest.txt"; then
  echo "FAIL the manifest step produced no sentinel. It ran but wrote nothing usable," >&2
  echo "     which is how a no-op passes for a pass. See $MANIFEST_DIR/manifest.txt" >&2
  exit 1
fi
cat "$MANIFEST_DIR/manifest.txt"
conda run -n "$ENV_NAME" pip freeze > "$MANIFEST_DIR/pip_freeze.txt" 2>&1
command -v nvidia-smi >/dev/null && nvidia-smi > "$MANIFEST_DIR/nvidia_smi.txt" 2>&1
{
  echo "env_name=$ENV_NAME"
  echo "created_by=src/scratch/setup_cadrecode_env.sh"
  echo "jobs=CAD-Recode inference; STEP->mesh tessellation; CadQuery execution"
  echo "protocol_component=cadquery-ocp $CADQUERY_OCP, cadquery @$CADQUERY_COMMIT"
  echo "why_here=Flluma's GeometryKernelFactory.create returns None for both kernel types"
  echo "not_installed=open3d (renderer only), pytorch3d (input FPS, deferred), flash-attn (exact, throughput only)"
  echo "trimesh_matches_external_eval=$TRIMESH"
  echo "torch=$TORCH from $TORCH_INDEX"
  echo "torch_deviation=CAD-Recode pins 2.5.1+cu124, which has no sm_120 code and cannot run on"
  echo "torch_deviation=this GPU. Disclosed; permissible because the paper does not claim to"
  echo "torch_deviation=reproduce their benchmark, their split and evaluator being unreleased."
} > "$MANIFEST_DIR/env_manifest.txt"
echo "  manifest -> $MANIFEST_DIR"

echo
echo "=== capability smoke tests: every claim exercised by a call ==="
cat > "$TMPPY/smoke.py" <<'PY'
import sys
fails = 0


def check(label, fn):
    global fails
    try:
        detail = fn()
        print(f"  [PASS] {label}: {detail}")
    except Exception as e:
        fails += 1
        print(f"  [FAIL] {label}: {type(e).__name__}: {e}")


def t_torch():
    import torch
    x = torch.ones(3)
    return f"cpu tensor sum {float(x.sum())}"


def t_cuda_kernel():
    """Actually run a kernel on the device. is_available() is not a capability.

    The first version of this test checked a CPU tensor and torch.cuda.is_available(), and passed
    on a GPU that cannot execute a single kernel: torch 2.5.1+cu124 has no sm_120 code, and this
    card is sm_120, so is_available() answers True while every launch fails. That is the same shape
    as a geometry kernel reporting itself available and then refusing to construct, and this test
    exists because the earlier one did not catch it.
    """
    import torch
    if "+cpu" in torch.__version__:
        return f"skipped: {torch.__version__} is a CPU build, chosen deliberately"
    if not torch.cuda.is_available():
        raise RuntimeError("torch.cuda.is_available() is False")
    cap = torch.cuda.get_device_capability(0)
    a = torch.ones(64, 64, device="cuda")
    b = (a @ a).sum().item()          # forces a real kernel launch and a sync
    torch.cuda.synchronize()
    if b != 64 * 64 * 64:
        raise RuntimeError(f"matmul on device gave {b}, expected {64**3}")
    return f"sm_{cap[0]}{cap[1]}, 64x64 matmul on device = {b}"


def t_transformers():
    from transformers import AutoTokenizer  # noqa: F401
    import transformers
    return f"AutoTokenizer importable, {transformers.__version__}"


def t_cadquery():
    import cadquery as cq
    box = cq.Workplane("XY").box(2, 1, 0.5)
    return f"built a box, {len(box.vals())} solid(s)"


def t_tessellate():
    import cadquery as cq
    shape = cq.Workplane("XY").box(2, 1, 0.5).val()
    v, f = shape.tessellate(0.05, 0.3)
    return f"tessellate(0.05, 0.3) -> {len(v)} vertices, {len(f)} triangles"


def t_step_roundtrip():
    import os, tempfile
    import cadquery as cq
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "b.step")
        cq.exporters.export(cq.Workplane("XY").box(2, 1, 0.5), p)
        back = cq.importers.importStep(p)
        v, f = back.val().tessellate(0.05, 0.3)
        return f"STEP write+read+tessellate -> {len(v)} vertices, {len(f)} triangles"


def t_trimesh_boolean():
    import trimesh
    a = trimesh.creation.box((1, 1, 1))
    b = a.copy(); b.apply_translation((0.5, 0, 0))
    inter = a.intersection(b)
    return f"boolean intersection volume {inter.volume:.4f} (expect 0.5)"


for label, fn in (("torch cpu", t_torch), ("CUDA kernel actually launches", t_cuda_kernel),
                  ("transformers", t_transformers),
                  ("cadquery build", t_cadquery), ("OCP tessellate", t_tessellate),
                  ("STEP round trip", t_step_roundtrip),
                  ("trimesh boolean backend", t_trimesh_boolean)):
    check(label, fn)

print()
if fails:
    print(f"{fails} capability check(s) failed. Do not download a checkpoint until they pass:")
    print("a version number is not a capability, which is the lesson from a kernel that")
    print("reported itself available and then would not construct.")
    sys.exit(1)
print("all capabilities exercised, not merely present.")
print("SMOKE_SENTINEL_OK")
PY
SMOKE_LOG="$MANIFEST_DIR/smoke_tests.txt"
conda run -n "$ENV_NAME" python "$TMPPY/smoke.py" 2>&1 | tee "$SMOKE_LOG"
rc=${PIPESTATUS[0]}
rm -rf "$TMPPY"
# A missing sentinel means the block did not run to completion, which is NOT a pass. The earlier
# version of this script could not tell those apart and said "next steps" after doing nothing.
if ! grep -q SMOKE_SENTINEL_OK "$SMOKE_LOG"; then
  echo "FAIL the smoke tests did not reach their sentinel. Treating as failure, not success." >&2
  rc=1
fi

echo
if [ "$rc" -ne 0 ]; then
  echo "Environment incomplete. Nothing further until the smoke tests pass."
  exit $rc
fi
echo "=== next, still no checkpoint and no GPU model ==="
echo "  conda run -n $ENV_NAME python $PROBE"
echo "  That freezes the mesh protocol and checks tessellation determinism, which both the"
echo "  IoU metric and CAD-Recode's own input pipeline depend on."
