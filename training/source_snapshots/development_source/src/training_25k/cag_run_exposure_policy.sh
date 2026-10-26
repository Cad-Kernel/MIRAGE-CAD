#!/usr/bin/env bash
set -euo pipefail

# No arguments means CPU-only preflight, never training.
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_ROOT="${MIRAGE_SOURCE_ROOT:-$HOME/workspace/MIRAGE/src}"
PACKAGE_ROOT="${REVIEW04_PACKAGE_ROOT:-__EVIDENCE_SOURCE_ROOT__/04}"
cd -- "$SOURCE_ROOT"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
if (( $# == 0 )); then
  set -- preflight
fi
python -u "$HERE/cag_exposure_policy.py" "$@" \
  --source-root "$SOURCE_ROOT" --package-root "$PACKAGE_ROOT"
