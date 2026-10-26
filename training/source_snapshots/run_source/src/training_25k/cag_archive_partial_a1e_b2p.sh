#!/bin/bash
# Archive existing A1E/B2P seed artefacts before a frozen CAG run.
#
# Dry-run by default. Use --apply to move files/directories into outputs/archive.
set -euo pipefail

cd ~/workspace/MIRAGE/src

SEED=${SEED:?set SEED, e.g. SEED=1}
MODALITY=${MODALITY:-step}
GEN=${GEN:-outputs/e1_observation_bypass}
APPLY=0
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    -h|--help)
      sed -n '2,18p' "$0"
      exit 0
      ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
ARCHIVE="outputs/archive/cag_a1e_b2p_seed${SEED}_${STAMP}"

targets=(
  "outputs/b1_1epoch_${MODALITY}_s${SEED}"
  "outputs/b2_pred_matched_${MODALITY}_s${SEED}"
  "outputs/b1_1epoch_${MODALITY}_s${SEED}.train.log"
  "outputs/b2_pred_matched_${MODALITY}_s${SEED}.train.log"
  "${GEN}/gen_code_${MODALITY}_A1E_s${SEED}.jsonl"
  "${GEN}/gen_code_${MODALITY}_B2P_s${SEED}.jsonl"
  "${GEN}/seed_${SEED}_actuals.json"
  "${GEN}/cag_seed_${SEED}_actuals.json"
  "${GEN}/cag_seed_${SEED}_preflight.json"
)

found=()
for t in "${targets[@]}"; do
  [ -e "$t" ] && found+=("$t")
done

if [ "${#found[@]}" -eq 0 ]; then
  echo "No seed $SEED A1E/B2P artefacts found."
  exit 0
fi

echo "Archive target: $ARCHIVE"
echo "Will move:"
for t in "${found[@]}"; do
  echo "  $t"
done

if [ "$APPLY" -eq 0 ]; then
  echo
  echo "dry run. Re-run with --apply to move these artefacts."
  exit 0
fi

mkdir -p "$ARCHIVE"
for t in "${found[@]}"; do
  mkdir -p "$ARCHIVE/$(dirname "$t")"
  mv "$t" "$ARCHIVE/$t"
done

cat > "$ARCHIVE/ARCHIVE_REASON.txt" <<EOF
Archived before CAG frozen A1E/B2P run.
seed=$SEED
modality=$MODALITY
timestamp_utc=$STAMP
reason=Existing artefacts would make the frozen runner refuse to start or risk mixing partial output with formal revision evidence.
EOF

echo "Archived ${#found[@]} artefact(s) to $ARCHIVE"
