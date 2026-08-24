import json, sys
from pathlib import Path
import torch
sys.path.insert(0, '.')
from miragecad.data import read_jsonl, read_text
from miragecad.gen_prompts import build_program_prompt
from gen_scripts.run_miragecad import load_lm, load_tokenizer, generate_text

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
lora_code = load_lm('Qwen/Qwen2.5-Coder-1.5B', Path('outputs/qwen25_coder_1_5b_program_5k'), torch.bfloat16, device)
lora_code_tok = load_tokenizer(Path('outputs/qwen25_coder_1_5b_program_5k'))

# predicted_ir + reference_ir already generated in Stage 3 (align_smoke5k_ep10 +
# prior_step_5k + lora_ir_5k), reused here to avoid rerunning LoRA-IR.
stage3_rows = read_jsonl(Path('outputs/lora_ir_5k/gen_test100.jsonl'))
test_rows = {r['sample_id']: r for r in read_jsonl(Path('data/smoke5k/test.jsonl'))[:100]}

out_path = Path('outputs/qwen25_coder_1_5b_program_5k/gen_test100_from_predicted_ir.jsonl')
with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
    for i, s3 in enumerate(stage3_rows):
        sid = s3['sample_id']
        row = test_rows.get(sid)
        if row is None:
            continue
        predicted_ir = s3['predicted_ir']
        prompt = build_program_prompt(row, 'step', predicted_ir)
        prediction = generate_text(lora_code, lora_code_tok, prompt, 1536, 1536, 0.0, 1.0, device)
        out = {
            'sample_id': sid,
            'target': 'program',
            'predicted_ir': predicted_ir,
            'reference_ir': s3.get('reference_ir', ''),
            'prediction': prediction,
            'reference': read_text(row.get('program_path', '')),
        }
        f.write(json.dumps(out, ensure_ascii=False) + '\n')
        if (i + 1) % 10 == 0:
            print(f'{i+1}/{len(stage3_rows)} done', flush=True)
print('Wrote', out_path)
