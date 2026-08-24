"""Evaluate IR generation quality against reference IR."""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

import torch

from miragecad.data import read_jsonl
from miragecad.gen_prompts import extract_operation_types, normalize_ir_text
from miragecad.models import load_alignment_checkpoint


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Evaluate predicted IR quality vs reference IR.")
    p.add_argument("--predicted-jsonl", type=Path, required=True)
    p.add_argument("--alignment-checkpoint", type=Path, required=True)
    p.add_argument("--output-json", type=Path, default=None)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--batch-size", type=int, default=32)
    return p.parse_args()


def lcs_length(a: list[str], b: list[str]) -> int:
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[m][n]


def op_seq_lcs_ratio(pred_text: str, ref_text: str) -> float:
    pred_ops = extract_operation_types(pred_text)
    ref_ops = extract_operation_types(ref_text)
    if not pred_ops and not ref_ops:
        return 1.0
    if not pred_ops or not ref_ops:
        return 0.0
    lcs = lcs_length(pred_ops, ref_ops)
    return lcs / max(len(pred_ops), len(ref_ops))


def op_set_metrics(pred_text: str, ref_text: str) -> dict[str, float]:
    pred_set = set(extract_operation_types(pred_text))
    ref_set = set(extract_operation_types(ref_text))
    if not pred_set and not ref_set:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    if not pred_set or not ref_set:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    tp = len(pred_set & ref_set)
    precision = tp / len(pred_set)
    recall = tp / len(ref_set)
    f1 = 2 * precision * recall / (precision + recall + 1e-8) if (precision + recall) > 0 else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


@torch.no_grad()
def encode_ir_batch(aligner, texts: list[str], device: torch.device) -> torch.Tensor:
    return aligner.encode_ir(texts, device)


def main() -> int:
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    aligner, _, _, _ = load_alignment_checkpoint(args.alignment_checkpoint, map_location="cpu")
    aligner.to(device).eval()

    rows = read_jsonl(args.predicted_jsonl)
    if args.limit:
        rows = rows[: args.limit]

    # Filter to rows that have both predicted_ir and reference_ir
    valid_rows = [r for r in rows if r.get("predicted_ir") and r.get("reference_ir")]
    cosine_valid = True
    if not valid_rows:
        # Fall back to rows that only have predicted_ir (from run_miragecad.py output)
        valid_rows = [r for r in rows if r.get("predicted_ir")]
        if valid_rows:
            print(
                "WARNING: No rows have 'reference_ir'. Falling back — cosine metrics compare "
                "predicted_ir against 'reference' field or empty string and may be meaningless."
            )
            cosine_valid = False

    results: list[dict[str, Any]] = []

    # PART id / SEED are random per-sample identifiers with no construction
    # semantics; normalize them to placeholders so they don't pollute cosine
    # similarity or operation-set scoring.
    all_pred_ir = [normalize_ir_text(r.get("predicted_ir", "")) for r in valid_rows]
    all_ref_ir = [normalize_ir_text(r.get("reference_ir", r.get("reference", ""))) for r in valid_rows]

    cosines: list[float] = []
    for i in range(0, len(valid_rows), args.batch_size):
        pred_batch = all_pred_ir[i: i + args.batch_size]
        ref_batch = all_ref_ir[i: i + args.batch_size]
        if not any(pred_batch) or not any(ref_batch):
            cosines.extend([0.0] * len(pred_batch))
            continue
        z_pred = encode_ir_batch(aligner, pred_batch, device)
        z_ref = encode_ir_batch(aligner, ref_batch, device)
        cos = torch.sum(z_pred * z_ref, dim=-1).cpu().tolist()
        cosines.extend(cos)

    for idx, row in enumerate(valid_rows):
        pred = all_pred_ir[idx]
        ref = all_ref_ir[idx]
        z_ir_hat = row.get("z_ir_hat")

        sample_result: dict[str, Any] = {
            "sample_id": row.get("sample_id", ""),
            "ir_cosine": cosines[idx] if idx < len(cosines) else None,
        }
        if z_ir_hat is not None:
            # If z_ir_hat stored in JSONL, compute cosine with encoded reference
            sample_result["ir_hat_cosine"] = None  # placeholder; full impl requires re-encoding

        op_metrics = op_set_metrics(pred, ref)
        sample_result["op_set_precision"] = op_metrics["precision"]
        sample_result["op_set_recall"] = op_metrics["recall"]
        sample_result["op_set_f1"] = op_metrics["f1"]
        sample_result["op_seq_lcs"] = op_seq_lcs_ratio(pred, ref)

        cos_val = sample_result["ir_cosine"]
        cos_str = f"{cos_val:.4f}" if cos_val is not None else "N/A"
        print(
            f"[{row.get('sample_id', idx)}] "
            f"ir_cos={cos_str}  "
            f"op_f1={sample_result['op_set_f1']:.4f}  "
            f"lcs={sample_result['op_seq_lcs']:.4f}"
        )
        results.append(sample_result)

    if not results:
        print("No valid rows to evaluate.")
        return 1

    def _mean(key: str) -> float:
        vals = [r[key] for r in results if r.get(key) is not None]
        return statistics.mean(vals) if vals else 0.0

    def _median(key: str) -> float:
        vals = [r[key] for r in results if r.get(key) is not None]
        return statistics.median(vals) if vals else 0.0

    summary: dict[str, Any] = {
        "n": len(results),
        "ir_cosine_mean": _mean("ir_cosine"),
        "ir_cosine_median": _median("ir_cosine"),
        "op_set_f1_mean": _mean("op_set_f1"),
        "op_set_f1_median": _median("op_set_f1"),
        "op_set_precision_mean": _mean("op_set_precision"),
        "op_set_recall_mean": _mean("op_set_recall"),
        "op_seq_lcs_mean": _mean("op_seq_lcs"),
        "op_seq_lcs_median": _median("op_seq_lcs"),
    }

    print("\n=== Aggregate ===")
    for k, v in summary.items():
        print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump({"summary": summary, "per_sample": results}, f, indent=2)
        print(f"Wrote summary: {args.output_json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
