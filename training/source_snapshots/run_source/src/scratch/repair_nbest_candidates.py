"""Apply P0 (profile_cut offset) + extrude_on_face repairs to every candidate
in `all_candidates` (not just a single `prediction` field), for Table 4
N-best geometry evaluation.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, ".")
from scratch.repair_extrude_on_face import repair_text as repair_extrude_on_face
from scratch.repair_profile_cut_offset import repair_text as repair_profile_cut_offset

in_path = Path(sys.argv[1])
out_path = Path(sys.argv[2])

stats1 = {"profile_to_sketch": 0, "top_face_to_sketch": 0, "top_face_left_alone": 0, "target_sketch_value_swap": 0}
stats2 = {"offset_2d_to_3d": 0, "offset_left_alone": 0}

rows = [json.loads(l) for l in open(in_path, encoding="utf-8") if l.strip()]
with open(out_path, "w", encoding="utf-8", newline="\n") as f:
    for row in rows:
        row = dict(row)
        row["all_candidates"] = [
            repair_profile_cut_offset(repair_extrude_on_face(c, stats1), stats2)
            for c in row["all_candidates"]
        ]
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

print("extrude_on_face stats:", stats1)
print("P0 stats:", stats2)
print("wrote", out_path)
