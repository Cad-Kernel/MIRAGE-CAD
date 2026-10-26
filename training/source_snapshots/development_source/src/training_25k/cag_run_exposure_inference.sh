#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_ROOT="${MIRAGE_SOURCE_ROOT:-$HOME/workspace/MIRAGE/src}"
PACKAGE_ROOT="${REVIEW04_PACKAGE_ROOT:-__EVIDENCE_SOURCE_ROOT__/04}"
if (( $# == 0 )); then set -- preflight; fi
case "$1" in
  preflight) export CUDA_VISIBLE_DEVICES="" ;;
  run) ;;
  *) printf '%s\n' 'Only CPU preflight or explicit single-arm inference is supported; no training.' >&2; exit 2 ;;
esac
cd -- "$SOURCE_ROOT"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
exec python -u "$HERE/cag_exposure_inference.py" "$@" \
  --source-root "$SOURCE_ROOT" --package-root "$PACKAGE_ROOT"
