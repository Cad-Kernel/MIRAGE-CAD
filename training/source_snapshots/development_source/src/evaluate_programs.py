"""MIRAGE-CAD program-level evaluation.

Computes text-based metrics from a generation JSONL (no kernel execution required):
  - syntax_valid: AST parse success rate.
  - defines_part: fraction of programs that construct a Flluma Part object.
  - source_similarity: normalised difflib ratio against the reference program.
  - operation_{precision,recall,f1,lcs_ratio,count_error}: based on regex-extracted
    Flluma API operation tokens.

Kernel-level metrics (build success, STEP validity, Chamfer distance) are handled
separately by the Flluma execution pipeline and are not computed here.
"""
from __future__ import annotations

import argparse
import ast
import difflib
import json
import re
from collections import Counter
from pathlib import Path


OP_PATTERN = re.compile(r"\b(?:add_|create_|make_|cut|union|intersect|extrude|revolve|fillet|chamfer|hole|pattern|mirror|shell|loft)\w*", re.I)


def read_jsonl(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def syntax_valid(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def defines_part(code: str) -> bool:
    return "Part(" in code or "part =" in code or "part=" in code or "return part" in code.lower()


def ops(text: str) -> list[str]:
    return [m.group(0).lower() for m in OP_PATTERN.finditer(text)]


def prf(pred_ops: list[str], ref_ops: list[str]) -> tuple[float, float, float]:
    pc = Counter(pred_ops)
    rc = Counter(ref_ops)
    overlap = sum((pc & rc).values())
    p = overlap / max(sum(pc.values()), 1)
    r = overlap / max(sum(rc.values()), 1)
    f = 2 * p * r / max(p + r, 1e-8)
    return p, r, f


def lcs_ratio(a: list[str], b: list[str]) -> float:
    return difflib.SequenceMatcher(a=a, b=b).ratio()


def parse_args():
    p = argparse.ArgumentParser(description="Evaluate generated Flluma programs or IR text.")
    p.add_argument("--predictions", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--limit", type=int, default=None)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, row in enumerate(read_jsonl(args.predictions)):
        if args.limit is not None and i >= args.limit:
            break
        pred = row.get("prediction", "")
        ref = row.get("reference", "")
        pred_ops = ops(pred)
        ref_ops = ops(ref)
        p, r, f1 = prf(pred_ops, ref_ops)
        is_program = row.get("target") == "program"
        result = {
            "sample_id": row.get("sample_id", ""),
            "syntax_valid": syntax_valid(pred) if is_program else None,
            "defines_part": defines_part(pred) if is_program else None,
            "source_similarity": difflib.SequenceMatcher(a=pred, b=ref).ratio(),
            "operation_precision": p,
            "operation_recall": r,
            "operation_f1": f1,
            "operation_lcs_ratio": lcs_ratio(pred_ops, ref_ops),
            "operation_count_error": abs(len(pred_ops) - len(ref_ops)),
        }
        rows.append(result)

    def mean(key: str) -> float:
        return sum(float(x[key]) for x in rows) / max(len(rows), 1)

    def mean_optional(key: str) -> float | None:
        values = [x[key] for x in rows if x.get(key) is not None]
        if not values:
            return None
        return sum(float(x) for x in values) / len(values)

    summary = {
        "predictions": str(args.predictions),
        "count": len(rows),
        "syntax_valid_rate": mean_optional("syntax_valid"),
        "defines_part_rate": mean_optional("defines_part"),
        "mean_source_similarity": mean("source_similarity"),
        "mean_operation_precision": mean("operation_precision"),
        "mean_operation_recall": mean("operation_recall"),
        "mean_operation_f1": mean("operation_f1"),
        "mean_operation_lcs_ratio": mean("operation_lcs_ratio"),
        "mean_operation_count_error": mean("operation_count_error"),
    }

    rows_path = args.output_dir / "evaluation_rows.jsonl"
    with open(rows_path, "w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    summary_path = args.output_dir / "evaluation_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))
    print(f"Rows: {rows_path}")
    print(f"Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

