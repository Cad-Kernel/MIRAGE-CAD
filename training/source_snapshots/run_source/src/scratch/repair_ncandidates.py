"""Apply the extrude_on_face repair to every candidate in `all_candidates`
(list field), for N-best execution-selection experiments.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repair_extrude_on_face import repair_text  # noqa: E402

in_path = Path(sys.argv[1])
out_path = Path(sys.argv[2])
stats = {"profile_to_sketch": 0, "top_face_to_sketch": 0, "top_face_left_alone": 0, "target_sketch_value_swap": 0}
rows = [json.loads(l) for l in open(in_path, encoding="utf-8") if l.strip()]
with open(out_path, "w", encoding="utf-8", newline="\n") as f:
    for row in rows:
        row = dict(row)
        row["all_candidates"] = [repair_text(c, stats) for c in row["all_candidates"]]
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
print("stats:", stats)
print("wrote", out_path)
