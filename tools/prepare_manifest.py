"""MIRAGE-CAD data preparation â€” build stratified JSONL manifests from FllumaOne-100K.

Reads the dataset split files (splits/{train,val,test}.txt) and resolves per-sample
file paths for programs, IR, images, point clouds, and STEP features.  Supports
stratified-level sampling to maintain the L1:L2:L3:L4 â‰ˆ 3:17:55:25 distribution
described in the paper.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from miragecad.data import deterministic_shuffle, find_sample_files, shard_relpath, write_jsonl


SCALES = {
    "smoke500": {"train": 500, "val": 100, "test": 100},
    "sanity": {"train": 1000, "val": 100, "test": 100},
    "10k": {"train": 10000, "val": 1000, "test": 1000},
    "50k": {"train": 50000, "val": 5000, "test": 5000},
    "full": {"train": None, "val": None, "test": None},
}

LEVEL_ORDER = ["L1", "L2", "L3", "L4"]
DEFAULT_LEVEL_WEIGHTS = {"L1": 3, "L2": 17, "L3": 55, "L4": 25}


def read_split(dataset_dir: Path, split: str) -> list[str]:
    path = dataset_dir / "splits" / f"{split}.txt"
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip().replace("\\", "/") for line in f if line.strip()]


def read_json(path: Path) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def load_template_level_map(dataset_dir: Path) -> dict[str, str]:
    manifest = read_json(dataset_dir / "dataset_manifest.json")
    mapping: dict[str, str] = {}
    for item in manifest.get("template_catalog", []) or []:
        name = item.get("name") or item.get("category")
        level = item.get("level")
        if name and level in LEVEL_ORDER:
            mapping[str(name)] = str(level)
        category = item.get("category")
        if category and level in LEVEL_ORDER:
            mapping[str(category)] = str(level)
    return mapping


def infer_level(dataset_dir: Path, relpath: str, template_level: dict[str, str]) -> tuple[str, str]:
    metadata = read_json(dataset_dir / relpath / "metadata.json")
    for key in ["level", "complexity_level"]:
        value = metadata.get(key)
        if value in LEVEL_ORDER:
            return str(value), "metadata"

    template = (
        metadata.get("template")
        or metadata.get("template_family")
        or metadata.get("category")
        or metadata.get("family")
        or ""
    )
    if template in template_level:
        return template_level[template], "template_catalog"

    ops = metadata.get("operations") or []
    num_features = int(metadata.get("num_features") or len(ops) or 0)
    op_count = len(ops)
    score = max(num_features, op_count)
    if score <= 1:
        return "L1", "feature_count_fallback"
    if score <= 3:
        return "L2", "feature_count_fallback"
    if score <= 7:
        return "L3", "feature_count_fallback"
    return "L4", "feature_count_fallback"


def infer_level_from_summary(summary: dict, template_level: dict[str, str]) -> tuple[str, str]:
    for key in ["level", "complexity_level"]:
        value = summary.get(key)
        if value in LEVEL_ORDER:
            return str(value), "parquet_metadata"
    category = summary.get("category") or summary.get("template") or ""
    if category in template_level:
        return template_level[category], "template_catalog_parquet"
    num_features = int(summary.get("num_features") or 0)
    op_count = int(summary.get("flluma_ops_count") or 0)
    score = max(num_features, op_count)
    if score <= 1:
        return "L1", "parquet_feature_count_fallback"
    if score <= 3:
        return "L2", "parquet_feature_count_fallback"
    if score <= 7:
        return "L3", "parquet_feature_count_fallback"
    return "L4", "parquet_feature_count_fallback"


def load_split_level_index(dataset_dir: Path, split: str, template_level: dict[str, str]) -> dict[str, tuple[str, str]]:
    parquet_path = dataset_dir / "parquet" / f"{split}.parquet"
    if not parquet_path.exists():
        return {}
    try:
        import pyarrow.parquet as pq
    except ImportError:
        return {}

    columns = ["sample_id", "category", "num_features", "flluma_ops_count"]
    table = pq.read_table(parquet_path, columns=columns)
    data = table.to_pydict()
    result: dict[str, tuple[str, str]] = {}
    for i, sample_id in enumerate(data["sample_id"]):
        summary = {column: data[column][i] for column in columns if column in data}
        level, source = infer_level_from_summary(summary, template_level)
        result[shard_relpath(str(sample_id))] = (level, source)
    return result


def allocate_level_quotas(limit: int, weights: dict[str, int] | None = None) -> dict[str, int]:
    weights = weights or DEFAULT_LEVEL_WEIGHTS
    total = sum(weights.get(level, 0) for level in LEVEL_ORDER)
    raw = {level: limit * weights.get(level, 0) / total for level in LEVEL_ORDER}
    quotas = {level: int(raw[level]) for level in LEVEL_ORDER}
    remainder = limit - sum(quotas.values())
    ranked = sorted(LEVEL_ORDER, key=lambda level: raw[level] - quotas[level], reverse=True)
    for level in ranked[:remainder]:
        quotas[level] += 1
    return quotas


def stratified_by_level(
    dataset_dir: Path,
    relpaths: list[str],
    limit: int | None,
    seed: int,
    template_level: dict[str, str],
    split_level_index: dict[str, tuple[str, str]] | None = None,
) -> tuple[list[str], dict]:
    if limit is None:
        selected = deterministic_shuffle(relpaths, seed)
    else:
        selected = []

    buckets: dict[str, list[str]] = defaultdict(list)
    level_source_counts: Counter[str] = Counter()
    all_level_counts: Counter[str] = Counter()
    rel_to_level: dict[str, str] = {}
    rel_to_source: dict[str, str] = {}
    split_level_index = split_level_index or {}

    for rel in relpaths:
        if rel in split_level_index:
            level, source = split_level_index[rel]
        else:
            level, source = infer_level(dataset_dir, rel, template_level)
        rel_to_level[rel] = level
        rel_to_source[rel] = source
        buckets[level].append(rel)
        all_level_counts[level] += 1
        level_source_counts[source] += 1

    for level in LEVEL_ORDER:
        buckets[level] = deterministic_shuffle(buckets[level], seed + LEVEL_ORDER.index(level) + 13)

    quotas = allocate_level_quotas(limit, DEFAULT_LEVEL_WEIGHTS) if limit is not None else {}
    if limit is not None:
        used = set()
        for level in LEVEL_ORDER:
            take = min(quotas[level], len(buckets[level]))
            chosen = buckets[level][:take]
            selected.extend(chosen)
            used.update(chosen)

        if len(selected) < limit:
            remainder = [rel for rel in deterministic_shuffle(relpaths, seed + 97) if rel not in used]
            selected.extend(remainder[: limit - len(selected)])

        selected = deterministic_shuffle(selected[:limit], seed + 193)

    selected_level_counts = Counter(rel_to_level[rel] for rel in selected)
    selected_source_counts = Counter(rel_to_source[rel] for rel in selected)
    report = {
        "all_level_counts": {level: all_level_counts.get(level, 0) for level in LEVEL_ORDER},
        "selected_level_counts": {level: selected_level_counts.get(level, 0) for level in LEVEL_ORDER},
        "requested_level_quotas": quotas,
        "level_source_counts": dict(level_source_counts),
        "selected_level_source_counts": dict(selected_source_counts),
    }
    return selected, report


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Prepare MIRAGE-CAD JSONL manifests from FllumaOne-100K.")
    p.add_argument("--dataset-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--scale", choices=sorted(SCALES), default="sanity")
    p.add_argument("--prompt-mode", choices=["deterministic", "llm", "mixed"], default="mixed")
    p.add_argument("--sampling", choices=["shuffle", "stratified-level"], default="shuffle")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--train-samples", type=int, default=None)
    p.add_argument("--val-samples", type=int, default=None)
    p.add_argument("--test-samples", type=int, default=None)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    scale = dict(SCALES[args.scale])
    overrides = {"train": args.train_samples, "val": args.val_samples, "test": args.test_samples}
    for k, v in overrides.items():
        if v is not None:
            scale[k] = v

    report = {
        "dataset_dir": str(args.dataset_dir),
        "output_dir": str(args.output_dir),
        "scale": args.scale,
        "prompt_mode": args.prompt_mode,
        "sampling": args.sampling,
        "seed": args.seed,
        "splits": {},
    }
    template_level = load_template_level_map(args.dataset_dir)
    report["template_level_map_size"] = len(template_level)

    for split in ["train", "val", "test"]:
        relpaths = read_split(args.dataset_dir, split)
        limit = scale[split]
        if args.sampling == "stratified-level":
            split_level_index = load_split_level_index(args.dataset_dir, split, template_level)
            relpaths, split_report = stratified_by_level(
                args.dataset_dir,
                relpaths,
                limit,
                args.seed + {"train": 0, "val": 1000, "test": 2000}[split],
                template_level,
                split_level_index,
            )
        else:
            split_level_index = load_split_level_index(args.dataset_dir, split, template_level)
            relpaths = deterministic_shuffle(relpaths, args.seed)
            if limit is not None:
                relpaths = relpaths[:limit]
            split_report = {}
        rows = []
        skipped_missing_image = 0
        for rel in relpaths:
            row = find_sample_files(args.dataset_dir, rel, prompt_mode=args.prompt_mode)
            if row.get("iso_image_missing"):
                skipped_missing_image += 1
                continue
            row["step_feature_path"] = str((args.output_dir / "step_features" / f"{row['sample_id']}.json").as_posix())
            if rel in split_level_index:
                level, source = split_level_index[rel]
            else:
                level, source = infer_level(args.dataset_dir, rel, template_level)
            row["complexity_level"] = level
            row["complexity_level_source"] = source
            rows.append(row)
        out_path = args.output_dir / f"{split}.jsonl"
        write_jsonl(out_path, rows)
        report["splits"][split] = {"rows": len(rows), "path": str(out_path), "skipped_missing_image": skipped_missing_image, **split_report}
        print(f"{split}: wrote {len(rows)} rows to {out_path}")

    manifest_path = args.output_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

