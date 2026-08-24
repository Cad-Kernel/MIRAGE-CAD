#!/bin/bash
# Compositional-split evaluation, part 2: NN-IR baseline (Direct + Prior
# retrieval) on the full 2,923-sample comp_test.jsonl, using the retrieval
# index built in comp_11 (from the reduced 24,577-row comp train set -- the
# 4 held-out families are NOT in this index, so retrieval genuinely cannot
# return an exact template match for comp_test queries). Same Stage4b-comp
# LoRA-Code checkpoint as the "Ours" pipeline, so LoRA-Code is held constant
# and only the IR source (retrieved vs generated) differs.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

S4B_DIR=outputs/qwen25_coder_1_5b_program_25k_comp_stage4b
WORK=outputs/nnir_baseline_comp
TEST_JSONL=data/25k_comp/comp_test.jsonl

mkdir -p "$WORK"

if [ ! -f outputs/align_25k_comp/train_ir_index.npz ]; then
  echo "ERROR: outputs/align_25k_comp/train_ir_index.npz not found -- run comp_11_build_index_and_gen_ours.sh first." >&2
  exit 1
fi

for m in step point text image; do
  case $m in
    step)  PRIOR=outputs/prior_step_25k_comp/best.pt ;;
    point) PRIOR=outputs/prior_point_25k_comp/best.pt ;;
    text)  PRIOR=outputs/prior_text_25k_comp/best.pt ;;
    image) PRIOR=outputs/prior_image_25k_comp/best.pt ;;
  esac

  for mode in direct prior; do
    if [ -f "$WORK/${mode}_${m}_repaired_p0.jsonl" ]; then
      echo "[$(date)] [$m / $mode-NN-IR] already complete -- skipping."
      continue
    fi

    echo "=== [$m / $mode-NN-IR] ==="
    python scratch/gen_nn_ir_baseline.py \
      --modality $m --retrieval-mode $mode \
      --alignment-checkpoint outputs/align_25k_comp/best.pt \
      --prior-checkpoint "$PRIOR" \
      --retrieval-index outputs/align_25k_comp/train_ir_index.npz \
      --lora-code-dir "$S4B_DIR" \
      --input-jsonl "$TEST_JSONL" \
      --output-jsonl "$WORK/${mode}_${m}.jsonl" \
      --limit 3000 \
      --max-length 1536 --max-new-tokens 1536 --batch-size 16

    echo "=== [$m / $mode-NN-IR] code repair (extrude_on_face then P0) ==="
    MID="$WORK/${mode}_${m}_repaired.jsonl"
    OUT="$WORK/${mode}_${m}_repaired_p0.jsonl"
    python3 scratch/repair_extrude_on_face.py "$WORK/${mode}_${m}.jsonl" "$MID"
    python3 scratch/repair_profile_cut_offset.py "$MID" "$OUT"
  done
done

echo "[$(date)] comp_13 (NN-IR baseline) COMPLETE."
