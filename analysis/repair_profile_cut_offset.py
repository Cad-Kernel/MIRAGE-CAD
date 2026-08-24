"""P0 repair: `Part.profile_cut_on_face()` requires a 3D `offset=[x, y, z]`, but
LoRA-Code reliably emits a hardcoded 2D `offset=[x, y]` template, causing
`exec error: offset must be a 3D sequence` on every affected sample (see
rare-op audit: OP_PROFILE_CUT / slotted_mount_plate, 5/5 sampled failures
had exactly this error, generated code was otherwise near-identical to
reference).

Rule (deliberately narrow, scoped only to this one call):
  - Only inside `profile_cut_on_face(...)` calls.
  - Only touches the `offset=[...]` keyword argument.
  - Only pads offsets with exactly 2 top-level elements to 3 by appending
    `, 0.0`.
  - Offsets that are already 3D (or any other shape) are left untouched.
  - No other function's `offset=` kwarg is touched.
"""
import json
import re
import sys as _sys
from pathlib import Path


def find_calls(text: str, func_name: str):
    pattern = re.compile(re.escape(func_name) + r"\(")
    for m in pattern.finditer(text):
        start = m.start()
        depth = 0
        i = m.end() - 1
        for j in range(i, len(text)):
            if text[j] == "(":
                depth += 1
            elif text[j] == ")":
                depth -= 1
                if depth == 0:
                    yield start, j + 1
                    break


def split_top_level_args(arg_text: str) -> list:
    parts = []
    depth = 0
    buf = []
    for ch in arg_text:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if buf:
        parts.append("".join(buf))
    return parts


def pad_offset_value(value: str, stats: dict) -> str:
    v = value.strip()
    if not (v.startswith("[") and v.endswith("]")):
        return value
    inner = v[1:-1]
    elems = [e for e in split_top_level_args(inner) if e.strip() != ""]
    if len(elems) != 2:
        stats["offset_left_alone"] += 1
        return value
    stats["offset_2d_to_3d"] += 1
    return "[" + ", ".join(e.strip() for e in elems) + ", 0.0]"


def repair_call(call_text: str, stats: dict) -> str:
    open_idx = call_text.index("(")
    head = call_text[: open_idx + 1]
    inner = call_text[open_idx + 1 : -1]
    args = split_top_level_args(inner)
    new_args = []
    for arg in args:
        m = re.match(r"^(\s*)(offset)(\s*=\s*)(.*)$", arg, re.S)
        if m:
            new_value = pad_offset_value(m.group(4), stats)
            new_args.append(f"{m.group(1)}offset{m.group(3)}{new_value}")
            continue
        new_args.append(arg)
    return head + ",".join(new_args) + ")"


def repair_text(text: str, stats: dict) -> str:
    spans = list(find_calls(text, "profile_cut_on_face"))
    if not spans:
        return text
    out = []
    last = 0
    for start, end in spans:
        out.append(text[last:start])
        out.append(repair_call(text[start:end], stats))
        last = end
    out.append(text[last:])
    return "".join(out)


def main():
    in_path = Path(_sys.argv[1]) if len(_sys.argv) > 1 else Path(
        "outputs/qwen25_coder_1_5b_program_5k_stage4b/gen_test500_from_predicted_ir_repaired.jsonl"
    )
    out_path = Path(_sys.argv[2]) if len(_sys.argv) > 2 else Path(
        "outputs/qwen25_coder_1_5b_program_5k_stage4b/gen_test500_from_predicted_ir_repaired_p0.jsonl"
    )
    stats = {"offset_2d_to_3d": 0, "offset_left_alone": 0}
    rows = [json.loads(l) for l in open(in_path, encoding="utf-8") if l.strip()]
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            row = dict(row)
            row["prediction"] = repair_text(row["prediction"], stats)
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("stats:", stats)
    print("wrote", out_path)


if __name__ == "__main__":
    main()
