import json
import flluma
info = {}
info['evaluate_doc'] = getattr(flluma.evaluate, '__doc__', None)
info['Part_methods'] = [n for n in dir(flluma.Part) if not n.startswith('_')]
info['has_build_toplevel'] = hasattr(flluma, 'build')
info['has_is_valid_toplevel'] = hasattr(flluma, 'is_valid')
with open(r'__TEMP_RUN_ROOT__\exec_eval\probe2.json', 'w') as f:
    json.dump(info, f, indent=2, default=str)
