import json, re

TARGET_OPS = {'OP_FACE_EXTRUDE','OP_FACE_CUT','OP_BOOLEAN_ADD','OP_BOOLEAN_CUT','OP_FACE_BOSSES','OP_ADD_FACE','OP_EXTRUDE_ADD','OP_EXTRUDE_CUT'}
UNAMBIGUOUS_ADD = {'OP_FACE_BOSSES','OP_ADD_FACE','OP_EXTRUDE_ADD'}
UNAMBIGUOUS_CUT = {'OP_FACE_CUT','OP_EXTRUDE_CUT'}
ADD_HINTS = re.compile(r'\b(boss|add|pad|raised|protrusion|rib)\w*', re.I)
CUT_HINTS = re.compile(r'\b(cut|pocket|slot|hole|recess|remove)\w*', re.I)

F_LINE = re.compile(r'^F\s+(\S+)\s+(OP_[A-Z0-9_]+)\s+(.*)$')

def parse_kv_field(line, field):
    m = re.search(rf'\b{field}\s+(\S+)', line)
    return m.group(1) if m else ''

def get_operation_param(line):
    m = re.search(r'\boperation=([A-Za-z_]+)', line)
    if m: return m.group(1).lower()
    m = re.search(r'\bsub_operation=([A-Za-z_]+)', line)
    if m: return m.group(1).lower()
    return None

def in_face_chain(feat_id, dep, target):
    if feat_id.lower().startswith('face_'):
        return True
    if 'sketch' in dep.lower() or 'sketch' in target.lower():
        return True
    return False

results = {'ADD':0,'CUT':0,'ambiguous':0,'gated_out':0}
decisions = []

for l in open('outputs/lora_ir_5k/predicted_ir_test500_full.jsonl'):
    row = json.loads(l)
    sid = row['sample_id']
    pir = row.get('predicted_ir','')
    for line in pir.splitlines():
        line = line.strip()
        m = F_LINE.match(line)
        if not m: continue
        feat_id, op, rest = m.groups()
        if op not in TARGET_OPS: continue
        dep = parse_kv_field(line, 'DEP')
        target = parse_kv_field(line, 'TARGET')
        sem_m = re.search(r'\bSEM\s+(\S+)', line)
        sem = sem_m.group(1) if sem_m else ''
        gated = in_face_chain(feat_id, dep, target)
        if not gated:
            results['gated_out'] += 1
            continue
        opparam = get_operation_param(line)
        direction = None
        if opparam in ('join','add'):
            direction = 'ADD'
        elif opparam in ('cut','remove'):
            direction = 'CUT'
        elif op in UNAMBIGUOUS_ADD:
            direction = 'ADD'
        elif op in UNAMBIGUOUS_CUT:
            direction = 'CUT'
        elif op == 'OP_BOOLEAN_ADD':
            direction = None if (CUT_HINTS.search(sem) and not ADD_HINTS.search(sem)) else 'ADD'
        elif op == 'OP_BOOLEAN_CUT':
            direction = None if (ADD_HINTS.search(sem) and not CUT_HINTS.search(sem)) else 'CUT'
        elif op == 'OP_FACE_EXTRUDE':
            has_add, has_cut = ADD_HINTS.search(sem), CUT_HINTS.search(sem)
            direction = 'ADD' if (has_add and not has_cut) else ('CUT' if (has_cut and not has_add) else None)
        if direction is None:
            results['ambiguous'] += 1
        else:
            results[direction] += 1
            decisions.append((sid, op, direction, feat_id))

print('counts:', results)
sids = sorted(set(d[0] for d in decisions))
print('distinct samples with >=1 remap:', len(sids))
print(sids)
