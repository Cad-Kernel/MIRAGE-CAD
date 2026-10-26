#!/usr/bin/env python3
"""Train-only STEP descriptor NN baseline for construction-disjoint split.

No model is trained or loaded. For each construction-disjoint test row, this
retrieves the nearest construction-disjoint train row by the same global STEP
descriptor used by the STEP pathway, then emits the train row's reference
program as the candidate prediction.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

import sys
sys.path.insert(0, ".")
from miragecad.data import load_step_feature_vector, read_text


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--train-jsonl", type=Path, default=Path("data/construction_disjoint_step_v1/train.jsonl"))
    p.add_argument("--test-jsonl", type=Path, default=Path("data/construction_disjoint_step_v1/test.jsonl"))
    p.add_argument("--manifest-csv", type=Path, default=Path("data/construction_disjoint_step_v1/construction_split_manifest.csv"))
    p.add_argument("--split-actuals", type=Path, default=Path("data/construction_disjoint_step_v1/cag_construction_split_actuals.json"))
    p.add_argument("--output-jsonl", type=Path, default=Path("outputs/construction_disjoint_step_v1/nn_step_descriptor_train_only.jsonl"))
    p.add_argument("--actuals-json", type=Path, default=Path("outputs/construction_disjoint_step_v1/nn_step_descriptor_train_only_actuals.json"))
    p.add_argument("--distance", choices=["zscore_l2", "cosine"], default="zscore_l2")
    return p.parse_args()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_manifest(path: Path) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            out[row["sample_id"]] = row
    return out


def op_tokens_from_sig(sig_json: str) -> list[str]:
    try:
        rows = json.loads(sig_json)
    except Exception:
        return []
    return [str(r.get("op", "")) for r in rows if isinstance(r, dict) and r.get("op")]


def lcs_ratio(a: list[str], b: list[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0] * (len(b) + 1)
        for j, y in enumerate(b, 1):
            cur[j] = prev[j - 1] + 1 if x == y else max(prev[j], cur[j - 1])
        prev = cur
    return prev[-1] / max(len(a), len(b))


def set_f1(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    tp = len(a & b)
    p = tp / len(a)
    r = tp / len(b)
    return 2 * p * r / (p + r) if p + r else 0.0


def pct(values: list[float], q: float) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    idx = (len(xs) - 1) * q
    lo = math.floor(idx)
    hi = math.ceil(idx)
    if lo == hi:
        return xs[lo]
    return xs[lo] * (hi - idx) + xs[hi] * (idx - lo)


def summary(values: list[float]) -> dict[str, float | int | None]:
    vals = [float(v) for v in values]
    if not vals:
        return {"n": 0, "mean": None, "sd": None, "min": None, "q25": None, "median": None, "q75": None, "max": None}
    return {
        "n": len(vals),
        "mean": sum(vals) / len(vals),
        "sd": statistics.stdev(vals) if len(vals) > 1 else 0.0,
        "min": min(vals),
        "q25": pct(vals, 0.25),
        "median": pct(vals, 0.5),
        "q75": pct(vals, 0.75),
        "max": max(vals),
    }


def normalize_train_test(train_x: np.ndarray, test_x: np.ndarray, mode: str) -> tuple[np.ndarray, np.ndarray]:
    if mode == "cosine":
        train_norm = np.linalg.norm(train_x, axis=1, keepdims=True)
        test_norm = np.linalg.norm(test_x, axis=1, keepdims=True)
        return train_x / np.maximum(train_norm, 1e-8), test_x / np.maximum(test_norm, 1e-8)
    mean = train_x.mean(axis=0, keepdims=True)
    std = train_x.std(axis=0, keepdims=True)
    return (train_x - mean) / np.maximum(std, 1e-6), (test_x - mean) / np.maximum(std, 1e-6)


def main() -> int:
    args = parse_args()
    split_actuals = json.loads(args.split_actuals.read_text(encoding="utf-8"))
    if split_actuals.get("overlap_audit", {}).get("status") != "PASS":
        raise SystemExit("split overlap audit is not PASS; refusing baseline generation")

    train_rows = read_jsonl(args.train_jsonl)
    test_rows = read_jsonl(args.test_jsonl)
    manifest = load_manifest(args.manifest_csv)

    train_ids = {r["sample_id"] for r in train_rows}
    test_ids = {r["sample_id"] for r in test_rows}
    if train_ids & test_ids:
        raise SystemExit("train/test sample_id leakage detected")

    train_x = np.stack([load_step_feature_vector(r["step_feature_path"], strict=True) for r in train_rows])
    test_x = np.stack([load_step_feature_vector(r["step_feature_path"], strict=True) for r in test_rows])
    train_z, test_z = normalize_train_test(train_x, test_x, args.distance)

    train_programs = [read_text(r["program_path"]) for r in train_rows]
    train_meta = [manifest[r["sample_id"]] for r in train_rows]
    test_meta = [manifest[r["sample_id"]] for r in test_rows]

    out_rows: list[dict[str, Any]] = []
    distances: list[float] = []
    op_set_f1s: list[float] = []
    op_lcs: list[float] = []
    exact_sig = 0
    exact_seq = 0

    for i, row in enumerate(test_rows):
        if args.distance == "cosine":
            scores = train_z @ test_z[i]
            nn_idx = int(np.argmax(scores))
            distance = float(1.0 - scores[nn_idx])
        else:
            diff = train_z - test_z[i]
            d = np.sqrt(np.sum(diff * diff, axis=1))
            nn_idx = int(np.argmin(d))
            distance = float(d[nn_idx])

        tm = test_meta[i]
        nm = train_meta[nn_idx]
        test_ops = op_tokens_from_sig(tm.get("op_graph_sig_v1", ""))
        nn_ops = op_tokens_from_sig(nm.get("op_graph_sig_v1", ""))
        op_f1 = set_f1(set(test_ops), set(nn_ops))
        lcs = lcs_ratio(test_ops, nn_ops)
        sig_match = tm.get("op_graph_sig_v1_hash") == nm.get("op_graph_sig_v1_hash")
        seq_match = test_ops == nn_ops
        exact_sig += int(sig_match)
        exact_seq += int(seq_match)
        distances.append(distance)
        op_set_f1s.append(op_f1)
        op_lcs.append(lcs)

        prediction = train_programs[nn_idx]
        out_rows.append({
            "sample_id": row.get("sample_id", ""),
            "modality": "step",
            "baseline": "train_only_step_descriptor_nn",
            "prediction": prediction,
            "reference": read_text(row.get("program_path", "")),
            "all_candidates": [prediction],
            "point_path": row.get("point_path", ""),
            "nn_sample_id": train_rows[nn_idx].get("sample_id", ""),
            "nn_distance": distance,
            "nn_distance_mode": args.distance,
            "nn_template_family": nm.get("template_family", ""),
            "test_template_family": tm.get("template_family", ""),
            "nn_op_graph_sig_v1_hash": nm.get("op_graph_sig_v1_hash", ""),
            "test_op_graph_sig_v1_hash": tm.get("op_graph_sig_v1_hash", ""),
            "exact_signature_match": sig_match,
            "exact_operation_sequence_match": seq_match,
            "operation_set_f1": op_f1,
            "operation_sequence_lcs": lcs,
        })

    if exact_sig:
        raise SystemExit(f"found {exact_sig} exact signature matches; refusing to write baseline")

    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with args.output_jsonl.open("w", encoding="utf-8", newline="\n") as f:
        for row in out_rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    actuals = {
        "purpose": "construction-disjoint STEP train-only descriptor NN baseline",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "train_jsonl": str(args.train_jsonl),
        "test_jsonl": str(args.test_jsonl),
        "manifest_csv": str(args.manifest_csv),
        "split_actuals": str(args.split_actuals),
        "distance": args.distance,
        "rows": len(out_rows),
        "train_rows": len(train_rows),
        "test_rows": len(test_rows),
        "exact_signature_matches": exact_sig,
        "exact_operation_sequence_matches": exact_seq,
        "nn_distance": summary(distances),
        "operation_set_f1": summary(op_set_f1s),
        "operation_sequence_lcs": summary(op_lcs),
        "hashes": {
            "train_jsonl_sha256": sha256_file(args.train_jsonl),
            "test_jsonl_sha256": sha256_file(args.test_jsonl),
            "manifest_csv_sha256": sha256_file(args.manifest_csv),
            "split_actuals_sha256": sha256_file(args.split_actuals),
            "output_jsonl_sha256": sha256_file(args.output_jsonl),
            "script_sha256": sha256_file(Path(__file__).resolve()),
        },
    }
    args.actuals_json.parent.mkdir(parents=True, exist_ok=True)
    args.actuals_json.write_text(json.dumps(actuals, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(actuals, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
