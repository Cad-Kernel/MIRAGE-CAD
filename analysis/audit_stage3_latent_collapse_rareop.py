"""Extend the swept_pipe_bracket latent-collapse finding (docs/MIRAGE-CAD_debug_report.md
8.1, originally checked on a 7-sample pilot) to the FULL population of
500-test samples containing OP_SWEEP_TUBE / OP_CIRCULAR_PATTERN, to confirm
(or refute) that the same STEP-encoder collapse explains these rare-op
failures at full scale, not just in the small pilot.

For each op group, computes pairwise cosine similarity of:
  - z_m       (STEP encoder output, pre-prior)
  - z_ir_hat  (prior output, what LoRA-IR actually conditions on)
  - raw 'global' B-Rep feature vector (pre-encoder, sanity check that the
    input data itself is NOT degenerate -- rules out a data-extraction bug)
against a random contrast group of 'normal' (non-rare-op) test samples.
"""
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, '.')
from miragecad.data import read_jsonl, load_step_brep_tensors
from miragecad.gen_prompts import OP_TOKEN_PATTERN
from miragecad.models import load_alignment_checkpoint
from gen_scripts.run_miragecad import load_prior, encode_query

TARGET_OPS = ['OP_SWEEP_TUBE', 'OP_CIRCULAR_PATTERN']
SEED = 42

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
aligner, _, _, _ = load_alignment_checkpoint(Path('outputs/align_smoke5k_ep10/best.pt'), map_location='cpu')
aligner = aligner.to(device).eval()
prior = load_prior(Path('outputs/prior_step_5k/best.pt'), device)

test_rows = {r['sample_id']: r for r in read_jsonl(Path('data/smoke5k/test.jsonl'))}
pred_rows = {r['sample_id']: r for r in read_jsonl(Path('outputs/lora_ir_5k/predicted_ir_test500_full_p1a.jsonl'))}

groups = {op: [] for op in TARGET_OPS}
normal_ids = []
for sid, r in pred_rows.items():
    ref_ir = r.get('reference_ir', '')
    if not ref_ir:
        continue
    ops = set(OP_TOKEN_PATTERN.findall(ref_ir.upper()))
    matched = [op for op in TARGET_OPS if op in ops]
    if matched:
        for op in matched:
            groups[op].append(sid)
    else:
        normal_ids.append(sid)

rng = random.Random(SEED)
normal_sample = rng.sample(normal_ids, 20)

class Args:
    modality = 'step'
args = Args()

def encode_all(sample_ids):
    z_ms, z_irs, globals_ = [], [], []
    for sid in sample_ids:
        row = test_rows[sid]
        z_m, z_ir_hat = encode_query(row, 'step', aligner, prior, args, device)
        z_ms.append(z_m)
        z_irs.append(z_ir_hat)
        tensors = load_step_brep_tensors(row['step_feature_path'], strict=True)
        globals_.append(tensors['global'])
    return np.stack(z_ms), np.stack(z_irs), np.stack(globals_)

def mean_pairwise_cos(mat):
    n = mat.shape[0]
    if n < 2:
        return None
    normed = mat / (np.linalg.norm(mat, axis=1, keepdims=True) + 1e-8)
    sim = normed @ normed.T
    off_diag = sim[np.triu_indices(n, k=1)]
    return float(off_diag.mean())

print('Encoding normal contrast group (n=20)...')
n_zm, n_zir, n_glob = encode_all(normal_sample)
print(f'normal z_m pairwise cos:     {mean_pairwise_cos(n_zm):.4f}')
print(f'normal z_ir_hat pairwise cos:{mean_pairwise_cos(n_zir):.4f}')
print(f'normal global-feat pairwise cos: {mean_pairwise_cos(n_glob):.4f}')
print()

for op in TARGET_OPS:
    ids = groups[op]
    print(f'=== {op} (n={len(ids)}) ===')
    zm, zir, glob = encode_all(ids)
    print(f'  z_m pairwise cos:      {mean_pairwise_cos(zm)}')
    print(f'  z_ir_hat pairwise cos: {mean_pairwise_cos(zir)}')
    print(f'  global-feat pairwise cos: {mean_pairwise_cos(glob)}')
    print()

print('done')
