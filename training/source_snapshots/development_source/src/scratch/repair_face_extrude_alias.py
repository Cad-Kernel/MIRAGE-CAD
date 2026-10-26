"""P1a repair: normalize hallucinated face-extrude operation-name aliases in
predicted_ir BEFORE it is handed to Stage 4 (LoRA-Code).

Background (see rare-op audit, docs/Todo.md "rare-op failure audit" section):
Stage 3 (LoRA-IR) frequently generates structurally-correct IR for the
`OP_FACE_EXTRUDE_ADD` / `OP_FACE_EXTRUDE_CUT` family but substitutes a
wrong-but-similar operation name (`OP_FACE_EXTRUDE`, `OP_BOOLEAN_ADD`,
`OP_FACE_CUT`, ...). Stage 4 then faithfully translates the wrong op name
into a nonexistent/wrong API call (`part.boolean_add()`, missing `sketch=`
kwarg, etc).

Empirically validated alias inventory + rule (dry-run against the 500-test
predicted_ir corpus, see chat log): `OP_BOOLEAN_CUT` is itself a CANONICAL
op (94 occurrences in training reference IR, generic solid-vs-solid cut) --
it must NOT be blanket-remapped. A context gate distinguishes legitimate
uses from face-extrude-cut aliases.

Rule, in order:
  1. GATE: only touch a candidate op if it is structurally part of a
     face-sketch chain -- its own feature id starts with `face_`, OR its
     DEP/TARGET references a variable containing "sketch". Anything else
     (e.g. `OP_BOOLEAN_CUT` on a plain solid DEP) is left untouched.
  2. Direction, first rule that applies wins:
     a. explicit `operation=`/`sub_operation=` param (join/add -> ADD,
        cut/remove -> CUT)
     b. unambiguous op name (OP_FACE_CUT/OP_EXTRUDE_CUT -> CUT;
        OP_FACE_BOSSES/OP_ADD_FACE/OP_EXTRUDE_ADD -> ADD)
     c. OP_BOOLEAN_ADD/OP_BOOLEAN_CUT: op name implies direction, UNLESS
        SEM hints the opposite direction with no support for the name's
        direction -> conflict, skip
     d. OP_FACE_EXTRUDE (genuinely directionless by name): SEM hint words
        only (boss/add/pad/raised/protrusion/rib -> ADD;
        cut/pocket/slot/hole/recess/remove -> CUT)
     e. nothing resolves -> ambiguous, skip

Only `predicted_ir` is touched. `reference_ir` / generated program are
never modified by this script.

Usage:
  python scratch/repair_face_extrude_alias.py --input IN.jsonl --output OUT.jsonl --log LOG.json
  (dry-run by default: prints stats + writes the log, does NOT write OUT.jsonl)
  add --apply to actually write OUT.jsonl
"""
import argparse
import json
import re
from pathlib import Path

TARGET_OPS = {
    "OP_FACE_EXTRUDE",
    "OP_FACE_CUT",
    "OP_BOOLEAN_ADD",
    "OP_BOOLEAN_CUT",
    "OP_FACE_BOSSES",
    "OP_ADD_FACE",
    "OP_EXTRUDE_ADD",
    "OP_EXTRUDE_CUT",
    # observed in the wild with 0 occurrences so far, but harmless to include
    # defensively -- they can never collide with a real canonical op name.
    "OP_BOSS_ON_FACE",
    "OP_CUT_ON_FACE",
    "OP_POCKET_ON_FACE",
    "OP_EXTRUDE_ADD_ON_FACE",
    "OP_EXTRUDE_CUT_ON_FACE",
}
UNAMBIGUOUS_ADD = {"OP_FACE_BOSSES", "OP_ADD_FACE", "OP_EXTRUDE_ADD", "OP_BOSS_ON_FACE", "OP_EXTRUDE_ADD_ON_FACE"}
UNAMBIGUOUS_CUT = {"OP_FACE_CUT", "OP_EXTRUDE_CUT", "OP_CUT_ON_FACE", "OP_POCKET_ON_FACE", "OP_EXTRUDE_CUT_ON_FACE"}
ADD_HINTS = re.compile(r"\b(boss|add|pad|raised|protrusion|rib)\w*", re.I)
CUT_HINTS = re.compile(r"\b(cut|pocket|slot|hole|recess|remove)\w*", re.I)

F_LINE = re.compile(r"^(F\s+)(\S+)(\s+)(OP_[A-Z0-9_]+)(\s+.*)$")


def parse_kv_field(line: str, field: str) -> str:
    m = re.search(rf"\b{field}\s+(\S+)", line)
    return m.group(1) if m else ""


def get_operation_param(line: str):
    m = re.search(r"\boperation=([A-Za-z_]+)", line)
    if m:
        return m.group(1).lower()
    m = re.search(r"\bsub_operation=([A-Za-z_]+)", line)
    if m:
        return m.group(1).lower()
    return None


def in_face_chain(feat_id: str, dep: str, target: str) -> bool:
    if feat_id.lower().startswith("face_"):
        return True
    if "sketch" in dep.lower() or "sketch" in target.lower():
        return True
    return False


def classify(feat_id: str, op: str, line: str):
    """Returns (new_op_or_None, reason_str)."""
    dep = parse_kv_field(line, "DEP")
    target = parse_kv_field(line, "TARGET")
    if not in_face_chain(feat_id, dep, target):
        return None, "gated_out"

    sem_m = re.search(r"\bSEM\s+(\S+)", line)
    sem = sem_m.group(1) if sem_m else ""

    opparam = get_operation_param(line)
    if opparam in ("join", "add"):
        return "OP_FACE_EXTRUDE_ADD", "operation_param"
    if opparam in ("cut", "remove"):
        return "OP_FACE_EXTRUDE_CUT", "operation_param"
    if op in UNAMBIGUOUS_ADD:
        return "OP_FACE_EXTRUDE_ADD", "op_name_unambiguous"
    if op in UNAMBIGUOUS_CUT:
        return "OP_FACE_EXTRUDE_CUT", "op_name_unambiguous"
    if op == "OP_BOOLEAN_ADD":
        if CUT_HINTS.search(sem) and not ADD_HINTS.search(sem):
            return None, "conflict_skip:name=ADD,sem=CUT"
        return "OP_FACE_EXTRUDE_ADD", "op_name_boolean_add"
    if op == "OP_BOOLEAN_CUT":
        if ADD_HINTS.search(sem) and not CUT_HINTS.search(sem):
            return None, "conflict_skip:name=CUT,sem=ADD"
        return "OP_FACE_EXTRUDE_CUT", "op_name_boolean_cut"
    if op == "OP_FACE_EXTRUDE":
        has_add, has_cut = ADD_HINTS.search(sem), CUT_HINTS.search(sem)
        if has_add and not has_cut:
            return "OP_FACE_EXTRUDE_ADD", "sem_hint"
        if has_cut and not has_add:
            return "OP_FACE_EXTRUDE_CUT", "sem_hint"
        return None, "ambiguous_skip:face_extrude_no_hint"
    return None, "ambiguous_skip:unhandled_op"


def repair_ir_text(sample_id: str, text: str, log: list) -> str:
    out_lines = []
    for line in text.splitlines():
        m = F_LINE.match(line)
        if not m:
            out_lines.append(line)
            continue
        prefix, feat_id, gap, op, rest = m.groups()
        if op not in TARGET_OPS:
            out_lines.append(line)
            continue
        new_op, reason = classify(feat_id, op, line)
        if new_op is None:
            log.append(
                {
                    "sample_id": sample_id,
                    "feature_id": feat_id,
                    "old_op": op,
                    "new_op": None,
                    "direction": None,
                    "reason": reason,
                    "line_before": line,
                    "line_after": line,
                }
            )
            out_lines.append(line)
            continue
        new_line = f"{prefix}{feat_id}{gap}{new_op}{rest}"
        direction = "ADD" if new_op.endswith("_ADD") else "CUT"
        log.append(
            {
                "sample_id": sample_id,
                "feature_id": feat_id,
                "old_op": op,
                "new_op": new_op,
                "direction": direction,
                "reason": reason,
                "line_before": line,
                "line_after": new_line,
            }
        )
        out_lines.append(new_line)
    return "\n".join(out_lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, default=Path("outputs/lora_ir_5k/predicted_ir_test500_full.jsonl"))
    ap.add_argument("--output", type=Path, default=Path("outputs/lora_ir_5k/predicted_ir_test500_full_p1a.jsonl"))
    ap.add_argument("--log", type=Path, default=Path("outputs/lora_ir_5k/repair_face_extrude_alias_log.json"))
    ap.add_argument("--apply", action="store_true", help="Actually write --output. Without this flag, dry-run only (stats + log, no jsonl written).")
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(args.input, encoding="utf-8") if l.strip()]
    log = []
    out_rows = []
    for row in rows:
        row = dict(row)
        row["predicted_ir"] = repair_ir_text(row["sample_id"], row["predicted_ir"], log)
        out_rows.append(row)

    counts = {"ADD": 0, "CUT": 0, "gated_out": 0, "conflict_skip": 0, "ambiguous_skip": 0}
    for entry in log:
        if entry["new_op"] is not None:
            counts[entry["direction"]] += 1
        elif entry["reason"] == "gated_out":
            counts["gated_out"] += 1
        elif entry["reason"].startswith("conflict_skip"):
            counts["conflict_skip"] += 1
        elif entry["reason"].startswith("ambiguous_skip"):
            counts["ambiguous_skip"] += 1

    touched_samples = sorted({e["sample_id"] for e in log if e["new_op"] is not None})
    print("counts:", counts)
    print("distinct samples with >=1 remap:", len(touched_samples))

    with open(args.log, "w", encoding="utf-8") as f:
        json.dump({"counts": counts, "touched_samples": touched_samples, "entries": log}, f, indent=2, ensure_ascii=False)
    print("wrote log:", args.log)

    if args.apply:
        with open(args.output, "w", encoding="utf-8", newline="\n") as f:
            for row in out_rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print("wrote (APPLIED):", args.output)
    else:
        print("DRY RUN: no output jsonl written. Re-run with --apply once counts look right.")


if __name__ == "__main__":
    main()
