"""Stage 3 rare-op generation audit for OP_SWEEP_TUBE / OP_CIRCULAR_PATTERN.

Cheap, text-only diagnostics (no model loading) to characterize exactly HOW
Stage 3 (LoRA-IR) fails on these two operations, before deciding whether a
Stage3-mini targeted fine-tune is worth trying. Answers:
  - Is the target op missing entirely, or substituted with a wrong/
    hallucinated op name?
  - Is CAT (category) already wrong from the very first line (suggests the
    soft-prefix condition itself carries no distinguishing signal -- a
    latent-collapse fingerprint, matching the swept_pipe_bracket finding in
    docs/MIRAGE-CAD_debug_report.md 8.1)?
  - Is the PART id hallucinated, and if so, is the SAME hallucinated id
    reused verbatim across multiple different real samples (a template-
    collapse fingerprint)?
  - Is the predicted_ir grammar-valid / does it end with END, or is it
    truncated/malformed?
  - How concentrated is this by category?
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, '.')
from miragecad.data import read_jsonl
from miragecad.gen_prompts import OP_TOKEN_PATTERN, validate_ir_grammar

TARGET_OPS = ['OP_SWEEP_TUBE', 'OP_CIRCULAR_PATTERN']

def get_cat(ir_text):
    m = re.search(r'\bCAT\s+(\S+)', ir_text)
    return m.group(1) if m else None

def get_part_id(ir_text):
    m = re.match(r'^PART\s+(\S+)', ir_text.strip())
    return m.group(1) if m else None

rows = list(read_jsonl(Path('outputs/lora_ir_5k/predicted_ir_test500_full_p1a.jsonl')))

results = []
for r in rows:
    ref_ir = r.get('reference_ir', '')
    if not ref_ir:
        continue
    ref_ops = set(OP_TOKEN_PATTERN.findall(ref_ir.upper()))
    matched = [op for op in TARGET_OPS if op in ref_ops]
    if not matched:
        continue
    pred_ir = r['predicted_ir']
    pred_ops = set(OP_TOKEN_PATTERN.findall(pred_ir.upper()))
    ref_cat = get_cat(ref_ir)
    pred_cat = get_cat(pred_ir)
    ref_part_id = get_part_id(ref_ir)
    pred_part_id = get_part_id(pred_ir)
    grammar = validate_ir_grammar(pred_ir)
    ends_with_end = pred_ir.strip().endswith('END')

    has_target_op = any(op in pred_ops for op in matched)
    # 'wrong op substituted' heuristic: predicted has an op containing a
    # substring of the target op's family name but isn't the exact token
    # (e.g. OP_SWEEP_PIPE_BRACKET instead of OP_SWEEP_TUBE)
    substituted = []
    for op in matched:
        family = op.split('_')[1]  # 'SWEEP' or 'CIRCULAR'
        for p in pred_ops:
            if family in p and p != op:
                substituted.append(p)

    op_recall = len(ref_ops & pred_ops) / len(ref_ops) if ref_ops else None

    results.append({
        'sample_id': r['sample_id'],
        'matched_target_ops': matched,
        'ref_cat': ref_cat,
        'pred_cat': pred_cat,
        'cat_match': ref_cat == pred_cat,
        'ref_part_id': ref_part_id,
        'pred_part_id': pred_part_id,
        'part_id_hallucinated': pred_part_id != r['sample_id'],
        'has_target_op': has_target_op,
        'substituted_ops': substituted,
        'op_recall': op_recall,
        'ref_op_count': len(ref_ops),
        'pred_op_count': len(pred_ops),
        'ref_len': len(ref_ir),
        'pred_len': len(pred_ir),
        'ir_grammar_valid': grammar['valid'],
        'ends_with_end': ends_with_end,
    })

print(f'total samples with target ops: {len(results)}')
print()

# per-op breakdown
for op in TARGET_OPS:
    subset = [r for r in results if op in r['matched_target_ops']]
    n = len(subset)
    if n == 0:
        continue
    n_has_op = sum(r['has_target_op'] for r in subset)
    n_cat_match = sum(r['cat_match'] for r in subset)
    n_part_halluc = sum(r['part_id_hallucinated'] for r in subset)
    n_grammar_valid = sum(r['ir_grammar_valid'] for r in subset)
    n_ends_end = sum(r['ends_with_end'] for r in subset)
    avg_recall = sum(r['op_recall'] for r in subset if r['op_recall'] is not None) / n
    print(f'=== {op} (n={n}) ===')
    print(f'  has target op in predicted_ir: {n_has_op}/{n} ({n_has_op/n:.1%})')
    print(f'  CAT matches reference:         {n_cat_match}/{n} ({n_cat_match/n:.1%})')
    print(f'  PART id hallucinated:          {n_part_halluc}/{n} ({n_part_halluc/n:.1%})')
    print(f'  IR grammar valid:              {n_grammar_valid}/{n} ({n_grammar_valid/n:.1%})')
    print(f'  ends with END:                 {n_ends_end}/{n} ({n_ends_end/n:.1%})')
    print(f'  mean op-set recall:            {avg_recall:.1%}')
    subs = Counter(s for r in subset for s in r['substituted_ops'])
    if subs:
        print(f'  substituted op names seen: {dict(subs)}')
    print()

# template-collapse fingerprint: are hallucinated PART ids reused across
# multiple different real sample_ids?
halluc_id_to_samples = defaultdict(list)
for r in results:
    if r['part_id_hallucinated']:
        halluc_id_to_samples[r['pred_part_id']].append(r['sample_id'])

reused = {k: v for k, v in halluc_id_to_samples.items() if len(v) > 1}
print(f'=== template-collapse fingerprint ===')
print(f'distinct hallucinated PART ids: {len(halluc_id_to_samples)}')
print(f'hallucinated PART ids reused across >=2 different real samples: {len(reused)}')
for pid, samples in sorted(reused.items(), key=lambda x: -len(x[1]))[:10]:
    print(f'  {pid}: reused by {len(samples)} samples -> {samples[:6]}{"..." if len(samples)>6 else ""}')

with open('outputs/lora_ir_5k/stage3_rareop_audit.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print()
print('wrote outputs/lora_ir_5k/stage3_rareop_audit.json')
