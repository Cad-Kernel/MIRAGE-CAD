import json, sys
from pathlib import Path
import torch
sys.path.insert(0, '.')
from miragecad.data import read_jsonl, read_text
from miragecad.gen_prompts import build_program_prompt
from gen_scripts.run_miragecad import load_lm, load_tokenizer, generate_text

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
lora_code = load_lm('Qwen/Qwen2.5-Coder-1.5B', Path('outputs/qwen25_coder_1_5b_program_5k_stage4c'), torch.bfloat16, device)
lora_code_tok = load_tokenizer(Path('outputs/qwen25_coder_1_5b_program_5k_stage4c'))

test_rows = {r['sample_id']: r for r in read_jsonl(Path('data/smoke5k/test.jsonl'))}
predicted_rows = read_jsonl(Path('outputs/lora_ir_5k/predicted_ir_test500_full_p1a.jsonl'))

out_path = Path('outputs/qwen25_coder_1_5b_program_5k_stage4c/gen_test500_from_predicted_ir_p1a.jsonl')
with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
    for i, pr in enumerate(predicted_rows):
        sid = pr['sample_id']
        row = test_rows[sid]
        predicted_ir = pr['predicted_ir']
        prompt = build_program_prompt(row, 'step', predicted_ir)
        prediction = generate_text(lora_code, lora_code_tok, prompt, 1536, 1536, 0.0, 1.0, device)
        f.write(json.dumps({
            'sample_id': sid,
            'target': 'program',
            'predicted_ir': predicted_ir,
            'prediction': prediction,
            'reference': read_text(row.get('program_path', '')),
        }, ensure_ascii=False) + '\n')
        if (i + 1) % 25 == 0:
            print(f'{i+1}/{len(predicted_rows)} done', flush=True)
print('Wrote', out_path)
