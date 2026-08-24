#!/bin/bash
# One-off benchmark: find the best --batch-size for gen_code_from_predicted_ir.py
# (and by extension gen_predicted_ir.py / gen_nn_ir_baseline.py, which share the
# same generate()/generate_text_batch() machinery) on THIS machine's GPU.
# Fixed 32-sample subset, tries batch sizes 1/2/4/8/16/32, stops early if a
# batch size OOMs (larger ones would too). Reports samples/sec per batch size.
set -uo pipefail
source /home/jizong/miniforge3/etc/profile.d/conda.sh
conda activate ai_dev
cd ~/workspace/MIRAGE/src

IR_JSONL=/tmp/smoke_comp/pred_ir_step32.jsonl
LORA_CODE=outputs/qwen25_coder_1_5b_program_25k_comp_stage4b
INPUT_JSONL=data/25k_comp/comp_test.jsonl

for bs in 1 2 4 8 16 32; do
  echo "=== batch-size=$bs ==="
  START=$(date +%s)
  python training_25k/scripts/gen_code_from_predicted_ir.py \
    --modality step --lora-code-dir "$LORA_CODE" \
    --ir-jsonl "$IR_JSONL" \
    --input-jsonl "$INPUT_JSONL" \
    --output-jsonl "/tmp/smoke_comp/bench_bs${bs}.jsonl" \
    --max-length 1536 --max-new-tokens 1536 --batch-size "$bs" \
    > "/tmp/smoke_comp/bench_bs${bs}.log" 2>&1
  RC=$?
  END=$(date +%s)
  ELAPSED=$((END - START))
  if [ $RC -ne 0 ]; then
    echo "batch-size=$bs FAILED (rc=$RC) after ${ELAPSED}s -- likely OOM, see /tmp/smoke_comp/bench_bs${bs}.log"
    tail -n 15 "/tmp/smoke_comp/bench_bs${bs}.log"
    echo "Stopping benchmark (larger batch sizes would fail too)."
    break
  fi
  N=$(wc -l < "/tmp/smoke_comp/bench_bs${bs}.jsonl")
  RATE=$(python3 -c "print(f'{$N/$ELAPSED:.3f}')" 2>/dev/null || echo "?")
  echo "batch-size=$bs: ${ELAPSED}s for $N rows -> ${RATE} rows/sec"
done

echo "=== BENCHMARK COMPLETE ==="
