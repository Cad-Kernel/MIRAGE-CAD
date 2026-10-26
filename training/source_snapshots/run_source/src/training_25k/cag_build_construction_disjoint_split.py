#!/usr/bin/env python3
"""Build and audit a construction-signature-disjoint STEP split.

This script is intentionally model-output agnostic. It reads source manifests and
reference training_ir.txt files, computes op_graph_sig_v1 signatures, assigns
whole signature groups to splits, and writes leakage/distribution audits.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import shutil
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROTOCOL_VERSION = "construction_disjoint_step_v1"
SIGNATURE_VERSION = "op_graph_sig_v1"
ASSIGNMENT_POLICY = "hash_dp_group_disjoint_v1"
ASSIGNMENT_SEED = "MIRAGE-CAD-CAG-construction-disjoint-2026-09-29"

FEATURE_RE = re.compile(r"^F\s+(\S+)\s+(OP_[A-Z0-9_]+)\b(.*)$")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--src-root", type=Path, default=Path("."))
    p.add_argument("--out-dir", type=Path, default=Path("data/construction_disjoint_step_v1"))
    p.add_argument("--review-out-dir", type=Path, default=None)
    p.add_argument("--train-target", type=int, default=25000)
    p.add_argument("--val-target", type=int, default=2500)
    p.add_argument("--test-target", type=int, default=500)
    p.add_argument("--source-splits", default="train,val,test")
    return p.parse_args()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def resolve_path(src_root: Path, row: dict[str, Any], value: str | None) -> Path | None:
    if not value:
        return None
    p = Path(value)
    if p.is_absolute():
        return p
    return src_root / p


def parse_ir(ir_text: str) -> dict[str, Any]:
    category = ""
    op_records: list[dict[str, Any]] = []
    op_sequence: list[str] = []
    name_to_idx: dict[str, int] = {}

    for raw in ir_text.splitlines():
        line = raw.strip()
        upper = line.upper()
        if upper.startswith("PART "):
            m = re.search(r"\bCAT\s+(\S+)", upper)
            if m:
                category = m.group(1)
            continue

        m = FEATURE_RE.match(upper)
        if not m:
            continue

        feature_name, op_token, rest = m.groups()
        role = ""
        role_m = re.search(r"\bROLE\s+(\S+)", rest)
        if role_m:
            role = role_m.group(1)

        deps: list[int] = []
        dep_m = re.search(r"\bDEP\s+(.+?)(?:\s+TARGET\b|\s+PARAMS\b|$)", rest)
        if dep_m:
            dep_tokens = [d for d in re.split(r"[,\s]+", dep_m.group(1).strip()) if d]
            for dep in dep_tokens:
                if dep in name_to_idx:
                    deps.append(name_to_idx[dep])
                else:
                    deps.append(-1)

        target_kind = "none"
        target_m = re.search(r"\bTARGET\s+(.+?)(?:\s+PARAMS\b|$)", rest)
        if target_m:
            targets = [t for t in re.split(r"[,\s]+", target_m.group(1).strip()) if t]
            if len(targets) > 1:
                target_kind = "multi"
            elif targets:
                t = targets[0]
                if ".TOP_FACE" in t or ".BOTTOM_FACE" in t or ".FACE" in t:
                    target_kind = "face"
                elif "." in t:
                    target_kind = "subfeature"
                else:
                    target_kind = "feature"

        rec = {
            "op": op_token,
            "role": role,
            "deps": deps,
            "target": target_kind,
        }
        op_records.append(rec)
        op_sequence.append(op_token)
        name_to_idx[feature_name] = len(op_records) - 1

    sig_json = stable_json(op_records)
    sig_hash = sha256_bytes(sig_json.encode("utf-8"))
    return {
        "category": category,
        "op_graph_sig_v1": sig_json,
        "op_graph_sig_v1_hash": sig_hash,
        "op_sequence": op_sequence,
        "op_set": sorted(set(op_sequence)),
        "operation_count": len(op_sequence),
    }


def load_step_stats(path: Path | None) -> dict[str, Any]:
    empty = {
        "bbox_x": None,
        "bbox_y": None,
        "bbox_z": None,
        "bbox_diag": None,
        "volume": None,
        "surface_area": None,
    }
    if path is None or not path.exists():
        return empty
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        features = data.get("features", {})
        bbox = features.get("bbox", {})
        size = bbox.get("size") or [None, None, None]
        sx, sy, sz = (size + [None, None, None])[:3] if isinstance(size, list) else (None, None, None)
        diag = None
        if all(isinstance(v, (int, float)) for v in [sx, sy, sz]):
            diag = math.sqrt(sx * sx + sy * sy + sz * sz)
        return {
            "bbox_x": sx,
            "bbox_y": sy,
            "bbox_z": sz,
            "bbox_diag": diag,
            "volume": features.get("volume"),
            "surface_area": features.get("surface_area"),
        }
    except Exception:
        return empty


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


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
    precision = tp / len(a)
    recall = tp / len(b)
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


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


def numeric_summary(values: list[float]) -> dict[str, float | int | None]:
    vals = [float(v) for v in values if isinstance(v, (int, float))]
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


def group_sort_key(label: str, sig_hash: str) -> str:
    return sha256_bytes(f"{ASSIGNMENT_SEED}:{label}:{sig_hash}".encode("utf-8"))


def assign_split(
    groups: dict[str, list[dict[str, Any]]],
    available: set[str],
    label: str,
    target_rows: int,
) -> tuple[set[str], int]:
    ordered = sorted(available, key=lambda h: group_sort_key(label, h))
    # Deterministic subset-sum over signature groups. This avoids underfilling a
    # split merely because an early hash-ordered group was too large, while still
    # keeping the assignment independent of model outputs.
    possible: dict[int, tuple[str, ...]] = {0: ()}
    for sig_hash in ordered:
        group_size = len(groups[sig_hash])
        for rows_so_far, chosen in sorted(list(possible.items()), reverse=True):
            new_rows = rows_so_far + group_size
            if new_rows > target_rows or new_rows in possible:
                continue
            possible[new_rows] = chosen + (sig_hash,)
    rows = max(possible)
    selected = set(possible[rows])
    available.difference_update(selected)
    return selected, rows


def summarize_split(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "unique_signatures": len({r["op_graph_sig_v1_hash"] for r in rows}),
        "operation_count": numeric_summary([r["operation_count"] for r in rows]),
        "bbox_diag": numeric_summary([r["bbox_diag"] for r in rows]),
        "volume": numeric_summary([r["volume"] for r in rows]),
        "surface_area": numeric_summary([r["surface_area"] for r in rows]),
        "complexity_counts": dict(sorted(Counter(r["complexity_tier"] for r in rows).items())),
        "template_family_top20": dict(Counter(r["template_family"] for r in rows).most_common(20)),
        "operation_token_counts": dict(Counter(op for r in rows for op in r["op_sequence"]).most_common()),
    }


def write_ids(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(str(row["sample_id"]) + "\n")


def copy_for_review(paths: list[Path], review_out_dir: Path | None) -> None:
    if review_out_dir is None:
        return
    review_out_dir.mkdir(parents=True, exist_ok=True)
    for path in paths:
        shutil.copy2(path, review_out_dir / path.name)


def main() -> int:
    args = parse_args()
    src_root = args.src_root.resolve()
    out_dir = args.out_dir if args.out_dir.is_absolute() else src_root / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    source_split_names = [s.strip() for s in args.source_splits.split(",") if s.strip()]
    source_paths = [src_root / "data" / "25k" / f"{split}.jsonl" for split in source_split_names]

    print(f"[1/7] loading source rows from {src_root}", flush=True)
    rows: list[dict[str, Any]] = []
    source_hashes = {}
    for split_name, path in zip(source_split_names, source_paths):
        source_hashes[str(path)] = sha256_file(path)
        for row in read_jsonl(path):
            row = dict(row)
            row["_source_split"] = split_name
            rows.append(row)
    print(f"  source rows: {len(rows)}", flush=True)

    print("[2/7] computing op_graph_sig_v1 inventory", flush=True)
    records: list[dict[str, Any]] = []
    for i, row in enumerate(rows, 1):
        ir_path = resolve_path(src_root, row, row.get("ir_path"))
        if ir_path is None or not ir_path.exists():
            raise FileNotFoundError(f"missing ir_path for {row.get('sample_id')}: {ir_path}")
        ir_text = ir_path.read_text(encoding="utf-8", errors="replace")
        parsed = parse_ir(ir_text)
        step_stats = load_step_stats(resolve_path(src_root, row, row.get("step_feature_path")))
        template_family = parsed["category"] or str(row.get("template") or "")
        rec = {
            "sample_id": row.get("sample_id", ""),
            "source_split": row.get("_source_split", ""),
            "split": "unused",
            "op_graph_sig_v1_hash": parsed["op_graph_sig_v1_hash"],
            "op_graph_sig_v1": parsed["op_graph_sig_v1"],
            "template_family": template_family,
            "operation_count": parsed["operation_count"],
            "op_sequence": parsed["op_sequence"],
            "op_set": parsed["op_set"],
            "complexity_tier": row.get("complexity_level") or row.get("complexity") or "",
            "complexity_level_source": row.get("complexity_level_source", ""),
            "ir_path": str(ir_path),
            "step_path": str(resolve_path(src_root, row, row.get("step_path")) or row.get("step_path") or ""),
            "program_path": str(resolve_path(src_root, row, row.get("program_path")) or row.get("program_path") or ""),
            "relpath": row.get("relpath", ""),
            "row": row,
            **step_stats,
        }
        records.append(rec)
        if i % 5000 == 0:
            print(f"  processed {i}/{len(rows)}", flush=True)

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rec in records:
        groups[rec["op_graph_sig_v1_hash"]].append(rec)
    print(f"  unique signatures: {len(groups)}", flush=True)

    print("[3/7] assigning group-disjoint splits", flush=True)
    available = set(groups)
    test_sigs, test_rows = assign_split(groups, available, "test", args.test_target)
    val_sigs, val_rows = assign_split(groups, available, "val", args.val_target)
    train_sigs, train_rows = assign_split(groups, available, "train", args.train_target)

    sig_to_split = {h: "unused" for h in groups}
    for h in train_sigs:
        sig_to_split[h] = "train"
    for h in val_sigs:
        sig_to_split[h] = "val"
    for h in test_sigs:
        sig_to_split[h] = "test"
    for rec in records:
        rec["split"] = sig_to_split[rec["op_graph_sig_v1_hash"]]

    split_rows = {
        split: sorted([r for r in records if r["split"] == split], key=lambda r: r["sample_id"])
        for split in ["train", "val", "test", "unused"]
    }
    print(f"  rows: train={train_rows}, val={val_rows}, test={test_rows}, unused={len(split_rows['unused'])}", flush=True)

    print("[4/7] running hard leakage audit", flush=True)
    split_sigs = {split: {r["op_graph_sig_v1_hash"] for r in rs} for split, rs in split_rows.items()}
    overlaps = {
        "train_val": sorted(split_sigs["train"] & split_sigs["val"]),
        "train_test": sorted(split_sigs["train"] & split_sigs["test"]),
        "val_test": sorted(split_sigs["val"] & split_sigs["test"]),
    }
    if any(overlaps.values()):
        raise RuntimeError(f"construction signature leakage detected: { {k: len(v) for k, v in overlaps.items()} }")
    print("  overlap audit: PASS", flush=True)

    print("[5/7] computing nearest-train construction audit", flush=True)
    train_reps = []
    seen_train = set()
    for r in split_rows["train"]:
        h = r["op_graph_sig_v1_hash"]
        if h in seen_train:
            continue
        seen_train.add(h)
        train_reps.append(r)

    nn_rows: list[dict[str, Any]] = []
    for i, r in enumerate(split_rows["test"], 1):
        test_set = set(r["op_set"])
        best: dict[str, Any] | None = None
        for tr in train_reps:
            op_f1 = set_f1(test_set, set(tr["op_set"]))
            seq_lcs = lcs_ratio(r["op_sequence"], tr["op_sequence"])
            exact_seq = r["op_sequence"] == tr["op_sequence"]
            key = (op_f1, seq_lcs, 1.0 if exact_seq else 0.0, tr["sample_id"])
            if best is None or key > best["_key"]:
                best = {
                    "_key": key,
                    "sample_id": r["sample_id"],
                    "test_signature": r["op_graph_sig_v1_hash"],
                    "nearest_train_sample_id": tr["sample_id"],
                    "nearest_train_signature": tr["op_graph_sig_v1_hash"],
                    "operation_set_f1": op_f1,
                    "operation_sequence_lcs": seq_lcs,
                    "exact_op_sequence_match": exact_seq,
                    "exact_signature_match": r["op_graph_sig_v1_hash"] == tr["op_graph_sig_v1_hash"],
                    "test_op_count": r["operation_count"],
                    "nearest_train_op_count": tr["operation_count"],
                    "test_template_family": r["template_family"],
                    "nearest_train_template_family": tr["template_family"],
                }
        if best is None:
            raise RuntimeError("no train signatures available for nearest-neighbor audit")
        best.pop("_key")
        nn_rows.append(best)
        if i % 100 == 0:
            print(f"  nearest audit {i}/{len(split_rows['test'])}", flush=True)

    if any(r["exact_signature_match"] for r in nn_rows):
        raise RuntimeError("nearest-neighbor audit found exact signature match despite split audit")

    print("[6/7] writing manifests and datasets", flush=True)
    for split in ["train", "val", "test"]:
        write_ids(out_dir / f"{split}_ids.txt", split_rows[split])
        write_jsonl(out_dir / f"{split}.jsonl", [r["row"] for r in split_rows[split]])

    inventory_path = out_dir / "signature_inventory.jsonl"
    with inventory_path.open("w", encoding="utf-8", newline="\n") as f:
        for rec in sorted(records, key=lambda r: r["sample_id"]):
            out = {k: v for k, v in rec.items() if k != "row"}
            f.write(json.dumps(out, ensure_ascii=False, sort_keys=True) + "\n")

    manifest_csv = out_dir / "construction_split_manifest.csv"
    csv_fields = [
        "sample_id", "split", "source_split", "op_graph_sig_v1_hash", "op_graph_sig_v1",
        "template_family", "operation_count", "complexity_tier", "complexity_level_source",
        "ir_path", "step_path", "program_path", "relpath",
        "bbox_x", "bbox_y", "bbox_z", "bbox_diag", "volume", "surface_area",
    ]
    with manifest_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields)
        writer.writeheader()
        for rec in sorted(records, key=lambda r: r["sample_id"]):
            writer.writerow({k: rec.get(k) for k in csv_fields})

    nn_csv = out_dir / "nearest_train_construction_audit.csv"
    with nn_csv.open("w", encoding="utf-8", newline="") as f:
        fields = [
            "sample_id", "test_signature", "nearest_train_sample_id", "nearest_train_signature",
            "operation_set_f1", "operation_sequence_lcs", "exact_op_sequence_match",
            "exact_signature_match", "test_op_count", "nearest_train_op_count",
            "test_template_family", "nearest_train_template_family",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(nn_rows)

    split_manifest = {
        "protocol_version": PROTOCOL_VERSION,
        "signature_version": SIGNATURE_VERSION,
        "assignment_policy": ASSIGNMENT_POLICY,
        "assignment_seed": ASSIGNMENT_SEED,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "src_root": str(src_root),
        "out_dir": str(out_dir),
        "source_splits": source_split_names,
        "targets": {"train": args.train_target, "val": args.val_target, "test": args.test_target},
        "counts": {
            split: {
                "rows": len(split_rows[split]),
                "unique_signatures": len(split_sigs[split]),
            }
            for split in ["train", "val", "test", "unused"]
        },
        "overlap_audit": {
            "status": "PASS",
            "train_val_overlap": len(overlaps["train_val"]),
            "train_test_overlap": len(overlaps["train_test"]),
            "val_test_overlap": len(overlaps["val_test"]),
        },
        "source_hashes": source_hashes,
        "split_summaries": {split: summarize_split(split_rows[split]) for split in ["train", "val", "test", "unused"]},
        "nearest_train_audit": {
            "test_rows": len(nn_rows),
            "exact_signature_matches": sum(1 for r in nn_rows if r["exact_signature_match"]),
            "exact_op_sequence_matches": sum(1 for r in nn_rows if r["exact_op_sequence_match"]),
            "operation_set_f1": numeric_summary([r["operation_set_f1"] for r in nn_rows]),
            "operation_sequence_lcs": numeric_summary([r["operation_sequence_lcs"] for r in nn_rows]),
        },
    }

    split_manifest_path = out_dir / "split_manifest.json"
    split_manifest_path.write_text(json.dumps(split_manifest, indent=2, sort_keys=True), encoding="utf-8")

    print("[7/7] writing actuals and hashes", flush=True)
    output_hashes = {
        "train_ids_sha256": sha256_file(out_dir / "train_ids.txt"),
        "val_ids_sha256": sha256_file(out_dir / "val_ids.txt"),
        "test_ids_sha256": sha256_file(out_dir / "test_ids.txt"),
        "train_jsonl_sha256": sha256_file(out_dir / "train.jsonl"),
        "val_jsonl_sha256": sha256_file(out_dir / "val.jsonl"),
        "test_jsonl_sha256": sha256_file(out_dir / "test.jsonl"),
        "construction_split_manifest_csv_sha256": sha256_file(manifest_csv),
        "signature_inventory_jsonl_sha256": sha256_file(inventory_path),
        "nearest_train_construction_audit_csv_sha256": sha256_file(nn_csv),
        "split_manifest_json_sha256": sha256_file(split_manifest_path),
        "split_script_sha256": sha256_file(Path(__file__).resolve()),
    }
    actuals = {
        **split_manifest,
        "actuals_file": str(out_dir / "cag_construction_split_actuals.json"),
        "output_hashes": output_hashes,
        "freeze_status": {
            "protocol": "FROZEN",
            "split_criterion": "FROZEN",
            "sample_ids": "FROZEN",
            "leakage_audit": "PASS",
            "training": "NOT_STARTED",
        },
    }
    actuals_path = out_dir / "cag_construction_split_actuals.json"
    actuals_path.write_text(json.dumps(actuals, indent=2, sort_keys=True), encoding="utf-8")

    copy_for_review(
        [
            out_dir / "train_ids.txt",
            out_dir / "val_ids.txt",
            out_dir / "test_ids.txt",
            split_manifest_path,
            actuals_path,
            nn_csv,
        ],
        args.review_out_dir,
    )

    print("\nConstruction-disjoint split built successfully.")
    print(json.dumps({
        "counts": split_manifest["counts"],
        "overlap_audit": split_manifest["overlap_audit"],
        "nearest_train_audit": split_manifest["nearest_train_audit"],
        "out_dir": str(out_dir),
        "review_out_dir": str(args.review_out_dir) if args.review_out_dir else None,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
