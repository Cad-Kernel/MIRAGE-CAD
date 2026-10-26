import json, sys
from pathlib import Path
import torch
sys.path.insert(0, '.')
from miragecad.data import read_jsonl, read_text
from miragecad.gen_prompts import build_program_prompt
from gen_scripts.run_miragecad import load_lm, load_tokenizer, generate_text

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
lora_code = load_lm('Qwen/Qwen2.5-Coder-1.5B', Path('outputs/qwen25_coder_1_5b_program_5k_stage4b'), torch.bfloat16, device)
lora_code_tok = load_tokenizer(Path('outputs/qwen25_coder_1_5b_program_5k_stage4b'))

test_rows = read_jsonl(Path('data/smoke5k/test.jsonl'))[:100]
stage3_rows = {r['sample_id']: r for r in read_jsonl(Path('outputs/lora_ir_5k/gen_test100_mnt1536.jsonl'))}

# A: ground-truth IR condition
out_gt = Path('outputs/qwen25_coder_1_5b_program_5k_stage4b/gen_test100_from_gt_ir.jsonl')
with open(out_gt, 'w', encoding='utf-8', newline='\n') as f:
    for i, row in enumerate(test_rows):
        gt_ir = read_text(row['ir_path'])
        prompt = build_program_prompt(row, 'step', gt_ir)
        prediction = generate_text(lora_code, lora_code_tok, prompt, 1536, 1536, 0.0, 1.0, device)
        f.write(json.dumps({'sample_id': row['sample_id'], 'target': 'program', 'prediction': prediction, 'reference': read_text(row.get('program_path', ''))}, ensure_ascii=False) + '\n')
        if (i + 1) % 20 == 0:
            print(f'GT-IR {i+1}/100 done', flush=True)
print('Wrote', out_gt)

# B: predicted_ir condition (reuse Stage 3 predicted_ir with max_new_tokens=1536 fix)
out_pred = Path('outputs/qwen25_coder_1_5b_program_5k_stage4b/gen_test100_from_predicted_ir.jsonl')
with open(out_pred, 'w', encoding='utf-8', newline='\n') as f:
    for i, row in enumerate(test_rows):
        s3 = stage3_rows[row['sample_id']]
        predicted_ir = s3['predicted_ir']
        prompt = build_program_prompt(row, 'step', predicted_ir)
        prediction = generate_text(lora_code, lora_code_tok, prompt, 1536, 1536, 0.0, 1.0, device)
        f.write(json.dumps({'sample_id': row['sample_id'], 'target': 'program', 'predicted_ir': predicted_ir, 'prediction': prediction, 'reference': read_text(row.get('program_path', ''))}, ensure_ascii=False) + '\n')
        if (i + 1) % 20 == 0:
            print(f'predicted_ir {i+1}/100 done', flush=True)
print('Wrote', out_pred)
