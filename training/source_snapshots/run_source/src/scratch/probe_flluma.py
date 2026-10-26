import json
try:
    import flluma
    info = {
        'flluma_dir': [n for n in dir(flluma) if not n.startswith('_')],
    }
except Exception as e:
    info = {'error': str(e)}
with open(r'__TEMP_RUN_ROOT__\exec_eval\probe.json', 'w') as f:
    json.dump(info, f, indent=2)
print(json.dumps(info, indent=2))
