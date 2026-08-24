"""Regenerate program.py only for the samples whose predicted_ir was actually
changed by scratch/repair_face_extrude_alias.py (27/500) -- generation is
deterministic (temperature=0.0), so the other 473 samples are identical to
the existing baseline and are reused as-is instead of re-running the LM.
"""
import json, sys
from pathlib import Path
import torch
sys.path.insert(0, '.')
from miragecad.data import read_jsonl, read_text
from miragecad.gen_prompts import build_program_prompt
from gen_scripts.run_miragecad import load_lm, load_tokenizer, generate_text

log = json.load(open('outputs/lora_ir_5k/repair_face_extrude_alias_log.json'))
touched = set(log['touched_samples'])
print(f'{len(touched)} samples touched by P1a alias repair -- only these will be regenerated')

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
lora_code = load_lm('Qwen/Qwen2.5-Coder-1.5B', Path('outputs/qwen25_coder_1_5b_program_5k_stage4b'), torch.bfloat16, device)
lora_code_tok = load_tokenizer(Path('outputs/qwen25_coder_1_5b_program_5k_stage4b'))

test_rows = {r['sample_id']: r for r in read_jsonl(Path('data/smoke5k/test.jsonl'))}
predicted_rows = {r['sample_id']: r for r in read_jsonl(Path('outputs/lora_ir_5k/predicted_ir_test500_full_p1a.jsonl'))}
baseline_rows = {r['sample_id']: r for r in read_jsonl(Path('outputs/qwen25_coder_1_5b_program_5k_stage4b/gen_test500_from_predicted_ir.jsonl'))}

out_path = Path('outputs/qwen25_coder_1_5b_program_5k_stage4b/gen_test500_from_predicted_ir_p1a.jsonl')
n_regen = 0
with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
    for sid, base_row in baseline_rows.items():
        if sid not in touched:
            f.write(json.dumps(base_row, ensure_ascii=False) + '\n')
            continue
        pr = predicted_rows[sid]
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
        n_regen += 1
        print(f'regenerated {n_regen}/{len(touched)} ({sid})', flush=True)
print('Wrote', out_path, '-- regenerated', n_regen, 'reused', len(baseline_rows) - n_regen)
