"""Post-process repair for a systematic LoRA-Code keyword-argument mismatch:

`Part.extrude_on_face()` expects `sketch=`, but the model reliably generates
`profile=` (leaking IR vocabulary like `profile_type`) or `top_face=`.

Rules:
  - `profile=` inside an `extrude_on_face(...)` call -> always renamed to `sketch=`
    (the model virtually always means "sketch" when it writes "profile" here).
  - `top_face=` inside an `extrude_on_face(...)` call -> only renamed to `sketch=`
    if the bound expression looks sketch/profile-like (heuristic keyword match on
    the expression text); otherwise left untouched and recorded, since it may be
    a genuine (if misplaced) face reference rather than a renamed sketch.
"""
import json
import re
from pathlib import Path

SKETCH_LIKE = re.compile(r"sketch|profile|rect|circle|slot|polygon|wire", re.I)
FACE_SELECTOR = re.compile(r"\.\s*\w*face\w*\s*\(")


def find_calls(text: str, func_name: str):
    """Yield (start, end) spans covering `func_name(...)` calls, honoring nested parens."""
    pattern = re.compile(re.escape(func_name) + r"\(")
    for m in pattern.finditer(text):
        start = m.start()
        depth = 0
        i = m.end() - 1  # position of the opening '('
        for j in range(i, len(text)):
            if text[j] == "(":
                depth += 1
            elif text[j] == ")":
                depth -= 1
                if depth == 0:
                    yield start, j + 1
                    break


def split_top_level_args(arg_text: str) -> list[str]:
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


def repair_call(call_text: str, stats: dict) -> str:
    # call_text looks like "extrude_on_face(arg1, kw=val, ...)"
    open_idx = call_text.index("(")
    head = call_text[: open_idx + 1]
    inner = call_text[open_idx + 1 : -1]
    tail = ")"
    args = split_top_level_args(inner)
    new_args = []
    for arg in args:
        m = re.match(r"^(\s*)(profile)(\s*=\s*)(.*)$", arg, re.S)
        if m:
            stats["profile_to_sketch"] += 1
            new_args.append(f"{m.group(1)}sketch{m.group(3)}{m.group(4)}")
            continue
        m = re.match(r"^(\s*)(top_face)(\s*=\s*)(.*)$", arg, re.S)
        if m:
            value = m.group(4)
            if SKETCH_LIKE.search(value):
                stats["top_face_to_sketch"] += 1
                new_args.append(f"{m.group(1)}sketch{m.group(3)}{value}")
            else:
                stats["top_face_left_alone"] += 1
                new_args.append(arg)
            continue
        new_args.append(arg)

    # Second pass: some samples swap the *values* bound to target= and sketch=
    # (target should be a face reference like `x.top_face()`; sketch should be a
    # bare profile/sketch variable). If target doesn't look face-like but sketch
    # does, swap them back.
    target_idx = sketch_idx = None
    for i, arg in enumerate(new_args):
        head_match = re.match(r"^\s*(\w+)\s*=", arg)
        if not head_match:
            continue
        if head_match.group(1) == "target":
            target_idx = i
        elif head_match.group(1) == "sketch":
            sketch_idx = i
    if target_idx is not None and sketch_idx is not None:
        t_key, _, t_val = new_args[target_idx].partition("=")
        s_key, _, s_val = new_args[sketch_idx].partition("=")
        if not FACE_SELECTOR.search(t_val) and FACE_SELECTOR.search(s_val):
            stats["target_sketch_value_swap"] += 1
            new_args[target_idx] = f"{t_key}={s_val}"
            new_args[sketch_idx] = f"{s_key}={t_val}"

    return head + ",".join(new_args) + tail


def repair_text(text: str, stats: dict) -> str:
    spans = list(find_calls(text, "extrude_on_face"))
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
    import sys as _sys

    in_path = Path(_sys.argv[1]) if len(_sys.argv) > 1 else Path("outputs/qwen25_coder_1_5b_program_5k/gen_test100_from_gt_ir_mnt1536.jsonl")
    out_path = Path(_sys.argv[2]) if len(_sys.argv) > 2 else Path("outputs/qwen25_coder_1_5b_program_5k/gen_test100_from_gt_ir_mnt1536_repaired_v2.jsonl")
    stats = {"profile_to_sketch": 0, "top_face_to_sketch": 0, "top_face_left_alone": 0, "target_sketch_value_swap": 0}
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
