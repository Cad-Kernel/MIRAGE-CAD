import json
info = {}
try:
    import torch
    info['torch'] = torch.__version__
except Exception as e:
    info['torch_error'] = str(e)
try:
    import transformers
    info['transformers'] = transformers.__version__
except Exception as e:
    info['transformers_error'] = str(e)
with open(r'__TEMP_RUN_ROOT__\exec_eval\probe_torch.json', 'w') as f:
    json.dump(info, f, indent=2)
