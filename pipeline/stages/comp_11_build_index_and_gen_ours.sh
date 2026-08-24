#!/bin/bash
# Compositional-split evaluation, part 1: build the retrieval index from the
# NEW reduced training set (data/25k_comp/train.jsonl -- 24,577 rows, the 4
# held-out families excluded), then generate the "Ours" (Stage3b-comp
# generated-IR) pipeline results on the full 2,923-sample comp_test.jsonl,
# for all 4 modalities: predicted_ir -> P1a repair -> code-gen -> code repair
# -> IR quality eval. Mirrors training_25k/scripts/run_full_stage3b_pipeline.sh,
# with all checkpoints/data swapped to the _comp variants.
#
# The retrieval index built here is ALSO the one the NN-IR baseline script
# (comp_13_gen_nnir_baseline.sh) needs -- built once here, reused there.
set -euo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

IR_S3B=outputs/lora_ir_25k_comp_stage3b
S4B_DIR=outputs/qwen25_coder_1_5b_program_25k_comp_stage4b
TEST_JSONL=data/25k_comp/comp_test.jsonl

if [ -f outputs/align_25k_comp/train_ir_index.npz ]; then
  echo "[$(date)] Retrieval index already built -- skipping."
else
  echo "=== Building retrieval index from data/25k_comp/train.jsonl ==="
  python build_index.py \
    --checkpoint outputs/align_25k_comp/best.pt --jsonl data/25k_comp/train.jsonl \
    --output outputs/align_25k_comp/train_ir_index.npz --index-modality ir \
    --batch-size 32 --point-count 1024
  echo "=== Wrote outputs/align_25k_comp/train_ir_index.npz ==="
fi

for m in step point text image; do
  case $m in
    step)  PRIOR=outputs/prior_step_25k_comp/best.pt ;;
    point) PRIOR=outputs/prior_point_25k_comp/best.pt ;;
    text)  PRIOR=outputs/prior_text_25k_comp/best.pt ;;
    image) PRIOR=outputs/prior_image_25k_comp/best.pt ;;
  esac

  if [ -f "$S4B_DIR/eval_${m}_comp/evaluation_summary.json" ]; then
    echo "[$(date)] [$m] Ours pipeline already complete -- skipping."
    continue
  fi

  if [ -f "$IR_S3B/predicted_ir_test_${m}.jsonl" ]; then
    echo "[$(date)] [$m] predicted_ir already generated -- skipping generation."
  else
    echo "=== [$m] predicted_ir, full comp_test (2,923 rows), lora_ir_25k_comp_stage3b ==="
    python training_25k/scripts/gen_predicted_ir.py \
      --modality $m \
      --alignment-checkpoint outputs/align_25k_comp/best.pt \
      --prior-checkpoint "$PRIOR" \
      --lora-ir-dir "$IR_S3B" \
      --input-jsonl "$TEST_JSONL" \
      --output-jsonl "$IR_S3B/predicted_ir_test_${m}.jsonl" \
      --max-length 1536 --max-new-tokens 1536 --batch-size 16
  fi

  echo "=== [$m] P1a repair ==="
  python scratch/repair_face_extrude_alias.py \
    --input "$IR_S3B/predicted_ir_test_${m}.jsonl" \
    --output "$IR_S3B/predicted_ir_test_${m}_p1a.jsonl" \
    --log "$IR_S3B/repair_face_extrude_alias_log_${m}.json" \
    --apply

  echo "=== [$m] code-gen with qwen25_coder_1_5b_program_25k_comp_stage4b ==="
  python training_25k/scripts/gen_code_from_predicted_ir.py \
    --modality $m --lora-code-dir "$S4B_DIR" \
    --ir-jsonl "$IR_S3B/predicted_ir_test_${m}_p1a.jsonl" \
    --input-jsonl "$TEST_JSONL" \
    --output-jsonl "$S4B_DIR/gen_test_${m}_comp.jsonl" \
    --max-length 1536 --max-new-tokens 1536 --batch-size 16

  echo "=== [$m] code repair (extrude_on_face then P0) ==="
  MID="$S4B_DIR/gen_test_${m}_comp_repaired.jsonl"
  OUT="$S4B_DIR/gen_test_${m}_comp_repaired_p0.jsonl"
  python3 scratch/repair_extrude_on_face.py "$S4B_DIR/gen_test_${m}_comp.jsonl" "$MID"
  python3 scratch/repair_profile_cut_offset.py "$MID" "$OUT"

  echo "=== [$m] IR quality (cosine/op-F1/op-LCS vs reference) ==="
  python -m gen_scripts.evaluate_ir_quality \
    --predicted-jsonl "$IR_S3B/predicted_ir_test_${m}_p1a.jsonl" \
    --alignment-checkpoint outputs/align_25k_comp/best.pt \
    --output-json "$IR_S3B/ir_quality_${m}_comp.json"

  echo "=== [$m] program-level text metrics (no execution) ==="
  python evaluate_programs.py \
    --predictions "$OUT" \
    --output-dir "$S4B_DIR/eval_${m}_comp"

  echo "[$(date)] [$m] Ours pipeline done."
done

echo "[$(date)] comp_11 (index + Ours pipeline) COMPLETE."
