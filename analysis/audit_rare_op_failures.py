"""Rare-op failure audit: for the 87 samples using a rare operation
(OP_SWEEP_TUBE / OP_SKETCH_ON_FACE / OP_FACE_EXTRUDE_ADD / OP_FACE_EXTRUDE_CUT /
OP_CIRCULAR_PATTERN / OP_PROFILE_CUT), determine per-sample:
  - which rare op(s) it references
  - whether predicted_ir is grammar-valid
  - whether predicted_ir actually contains the expected rare op token
    (distinguishes Stage 3 IR-generation failure from Stage 4 code-translation failure)
  - execution result + error message

Writes a summary CSV-like table + a markdown file with 5 detailed examples per
operation (reference_ir / predicted_ir / generated program / error / reference program).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")
from miragecad.data import read_jsonl, read_text
from miragecad.gen_prompts import OP_TOKEN_PATTERN, validate_ir_grammar

RARE_OPS = ["OP_SWEEP_TUBE", "OP_SKETCH_ON_FACE", "OP_FACE_EXTRUDE_ADD", "OP_FACE_EXTRUDE_CUT", "OP_CIRCULAR_PATTERN", "OP_PROFILE_CUT"]

test_rows = {r["sample_id"]: r for r in read_jsonl(Path("data/smoke5k/test.jsonl"))}
pred_ir = {r["sample_id"]: r for r in [json.loads(l) for l in open("outputs/lora_ir_5k/predicted_ir_test500_full.jsonl")]}
gen_code = {r["sample_id"]: r for r in [json.loads(l) for l in open("outputs/qwen25_coder_1_5b_program_5k_stage4b/gen_test500_from_predicted_ir_repaired.jsonl")]}
exec_rows = {r["sample_id"]: r for r in [json.loads(l) for l in open("/mnt/c/Workspace/Project/Paper/MIRAGE-V2/scratch/exec_eval_stage4b_test500/execution_rows.jsonl")]}

rows_out = []
for sid, r in pred_ir.items():
    ref_ir = r.get("reference_ir", "")
    if not ref_ir:
        continue
    ref_ops = set(OP_TOKEN_PATTERN.findall(ref_ir))
    matched_rare = [op for op in RARE_OPS if op in ref_ops]
    if not matched_rare:
        continue
    predicted_ir = r["predicted_ir"]
    pred_ops = set(OP_TOKEN_PATTERN.findall(predicted_ir))
    ir_valid = validate_ir_grammar(predicted_ir)["valid"]
    has_expected_op = any(op in pred_ops for op in matched_rare)
    ex = exec_rows.get(sid, {})
    exec_ok = ex.get("exec_ok", None)
    error = ex.get("error", "")

    if exec_ok:
        stage = "OK"
    elif not has_expected_op:
        stage = "Stage3 (predicted_ir missing/lost the rare op)"
    elif not ir_valid:
        stage = "Stage3 (IR grammar invalid)"
    else:
        stage = "Stage4 (IR ok, code translation failed)"

    rows_out.append({
        "sample_id": sid,
        "rare_ops": ",".join(matched_rare),
        "ir_valid": ir_valid,
        "has_expected_op": has_expected_op,
        "exec_ok": exec_ok,
        "failure_stage": stage,
        "error": error,
    })

# Print summary table
print(f"{'sample_id':<18}{'rare_ops':<45}{'ir_valid':<9}{'has_op':<7}{'exec_ok':<8}{'stage'}")
for row in rows_out:
    print(f"{row['sample_id']:<18}{row['rare_ops']:<45}{str(row['ir_valid']):<9}{str(row['has_expected_op']):<7}{str(row['exec_ok']):<8}{row['failure_stage']}")

from collections import Counter
stage_counter = Counter(r["failure_stage"] for r in rows_out)
print()
print("failure_stage breakdown:", dict(stage_counter))

with open("outputs/qwen25_coder_1_5b_program_5k_stage4b/rare_op_audit_summary.json", "w", encoding="utf-8") as f:
    json.dump(rows_out, f, indent=2, ensure_ascii=False)

# Write detailed markdown with 5 examples per op
with open("outputs/qwen25_coder_1_5b_program_5k_stage4b/rare_op_audit_details.md", "w", encoding="utf-8") as f:
    f.write("# Rare-op failure audit\n\n")
    f.write(f"stage breakdown: {dict(stage_counter)}\n\n")
    for op in RARE_OPS:
        f.write(f"# {op}\n\n")
        examples = [r for r in rows_out if op in r["rare_ops"].split(",") and not r["exec_ok"]][:5]
        for r in examples:
            sid = r["sample_id"]
            f.write(f"## sample_id={sid}  (stage={r['failure_stage']})\n\n")
            f.write(f"error: `{r['error']}`\n\n")
            f.write("### reference_ir\n```text\n" + pred_ir[sid]["reference_ir"] + "\n```\n\n")
            f.write("### predicted_ir\n```text\n" + pred_ir[sid]["predicted_ir"] + "\n```\n\n")
            gc = gen_code.get(sid, {})
            f.write("### generated program (prediction)\n```python\n" + gc.get("prediction", "")[:2000] + "\n```\n\n")
            f.write("### reference program\n```python\n" + gc.get("reference", "")[:1500] + "\n```\n\n")
            f.write("---\n\n")

print("wrote outputs/qwen25_coder_1_5b_program_5k_stage4b/rare_op_audit_summary.json")
print("wrote outputs/qwen25_coder_1_5b_program_5k_stage4b/rare_op_audit_details.md")
