import json, sys
from pathlib import Path
import torch
sys.path.insert(0, '.')
from transformers import AutoTokenizer
from miragecad.data import read_jsonl, read_text
from miragecad.gen_prompts import build_program_prompt
from gen_scripts.run_miragecad import load_lm, load_tokenizer, generate_text

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
lora_code = load_lm('Qwen/Qwen2.5-Coder-1.5B', Path('outputs/qwen25_coder_1_5b_program_5k'), torch.bfloat16, device)
lora_code_tok = load_tokenizer(Path('outputs/qwen25_coder_1_5b_program_5k'))

rows = read_jsonl(Path('data/smoke5k/test.jsonl'))[:100]
out_path = Path('outputs/qwen25_coder_1_5b_program_5k/gen_test100_from_gt_ir_mnt1536.jsonl')
with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
    for i, row in enumerate(rows):
        gt_ir = read_text(row['ir_path'])
        prompt = build_program_prompt(row, 'step', gt_ir)
        prediction = generate_text(lora_code, lora_code_tok, prompt, 1536, 1536, 0.0, 1.0, device)
        out = {
            'sample_id': row.get('sample_id', ''),
            'target': 'program',
            'prediction': prediction,
            'reference': read_text(row.get('program_path', '')),
        }
        f.write(json.dumps(out, ensure_ascii=False) + '\n')
        if (i+1) % 10 == 0:
            print(f'{i+1}/100 done', flush=True)
print('Wrote', out_path)
