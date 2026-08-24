"""MIRAGE-CAD data utilities.

Covers three concerns:
  1. Per-sample file resolution (programs, IR, images, point clouds, STEP features).
  2. B-Rep feature vector construction: 50-dim log1p-normalised descriptor extracted
     from STEP/OpenCASCADE topology (see step_feature_vector_from_json).
  3. RAG prompt assembly: combines retrieved construction examples with a target query
     for the LoRA-adapted Qwen2.5-Coder-1.5B generator (see build_generation_prompt).
"""
from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from PIL import Image


CANONICAL_IMAGES = [
    "00_pos_x.png",
    "01_neg_x.png",
    "02_pos_y.png",
    "03_neg_y.png",
    "04_pos_z_top.png",
    "05_neg_z_bottom.png",
    "06_iso_posx_posy_posz.png",
    "07_iso_negx_negy_posz.png",
]

STEP_SURFACE_TYPES = [
    "plane",
    "cylinder",
    "cone",
    "sphere",
    "torus",
    "bezier_surface",
    "bspline_surface",
    "surface_of_revolution",
    "surface_of_extrusion",
    "offset_surface",
    "other_surface",
]

STEP_CURVE_TYPES = [
    "line",
    "circle",
    "ellipse",
    "hyperbola",
    "parabola",
    "bezier_curve",
    "bspline_curve",
    "offset_curve",
    "other_curve",
]

# Global B-Rep descriptor used by the STEP/B-Rep encoder branch of MIRAGE-CAD.
# Layout: 1 validity flag + 6 topology counts + 3 bbox dims + 2 shape stats
#       + 11 surface type counts + 9 curve type counts + 4 valence buckets
#       + 6 incidence/manifold stats + 8 face/edge area-length stats = 50 dims.
STEP_FEATURE_DIM = 50

# Lightweight Global-Local-Relation STEP/B-Rep encoder dimensions.
STEP_GLOBAL_DIM = STEP_FEATURE_DIM
STEP_FACE_COUNT = 64
STEP_EDGE_COUNT = 128
STEP_FACE_DIM = len(STEP_SURFACE_TYPES) + 17
STEP_EDGE_DIM = len(STEP_CURVE_TYPES) + 15
STEP_RELATION_DIM = 32


def read_json(path: str | Path, default: Any = None, *, strict: bool = False) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        if strict:
            raise FileNotFoundError(f"read_json: file not found: {path}") from None
        return default
    except json.JSONDecodeError as exc:
        if strict:
            raise ValueError(f"read_json: invalid JSON in {path}: {exc}") from exc
        return default


def read_text(path: str | Path, default: str = "") -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return default


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: str | Path, rows: Iterable[dict[str, Any]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize_path(path: str | Path) -> str:
    return str(Path(path).as_posix())


def sample_id_from_relpath(relpath: str) -> str:
    return Path(relpath).name


def shard_relpath(sample_id: str) -> str:
    idx = int(sample_id.split("_")[-1])
    return f"shard_{idx // 1000:04d}/{sample_id}"


def load_descriptions(sample_dir: Path, prompt_mode: str = "mixed") -> dict[str, str]:
    desc = read_json(sample_dir / "text" / "descriptions.json", default={}) or {}
    llm_rows: list[dict[str, Any]] = []
    llm_path = sample_dir / "text" / "llm_descriptions.jsonl"
    if llm_path.exists():
        with open(llm_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        llm_rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

    deterministic = ""
    for key in [
        "caption",
        "short_caption",
        "summary",
        "description",
        "deterministic_caption",
        "construction_steps",
    ]:
        value = desc.get(key)
        if isinstance(value, str) and value.strip():
            deterministic = value.strip()
            break
        if isinstance(value, list) and value:
            deterministic = " ".join(str(x) for x in value[:4]).strip()
            break

    llm_text = ""
    for row in llm_rows:
        for key in ["caption", "description", "text", "prompt", "short_caption"]:
            value = row.get(key)
            if isinstance(value, str) and value.strip():
                llm_text = value.strip()
                break
        if llm_text:
            break

    if prompt_mode == "deterministic":
        text = deterministic or llm_text
    elif prompt_mode == "llm":
        text = llm_text or deterministic
    else:
        if deterministic and llm_text:
            text = deterministic + "\n" + llm_text
        else:
            text = deterministic or llm_text

    if not text:
        metadata = read_json(sample_dir / "metadata.json", default={}) or {}
        template = metadata.get("template") or metadata.get("template_family") or "CAD part"
        text = f"Generate an editable CAD model for a {template}."

    return {
        "text": text,
        "deterministic_text": deterministic,
        "llm_text": llm_text,
    }


def find_sample_files(dataset_dir: str | Path, relpath: str, prompt_mode: str = "mixed") -> dict[str, Any]:
    root = Path(dataset_dir)
    sample_dir = root / relpath
    sample_id = sample_dir.name
    canonical_dir = sample_dir / "images" / "canonical"
    image_paths = [canonical_dir / name for name in CANONICAL_IMAGES]
    image_paths = [p for p in image_paths if p.exists()]
    iso_image = canonical_dir / "06_iso_posx_posy_posz.png"
    if not iso_image.exists() and image_paths:
        iso_image = image_paths[-1]
    iso_image_missing = not iso_image.exists()

    text_info = load_descriptions(sample_dir, prompt_mode=prompt_mode)
    metadata = read_json(sample_dir / "metadata.json", default={}) or {}

    return {
        "sample_id": sample_id,
        "relpath": relpath.replace("\\", "/"),
        "dataset_root": normalize_path(root),
        "sample_dir": normalize_path(sample_dir),
        "program_path": normalize_path(sample_dir / "program.py"),
        "ir_path": normalize_path(sample_dir / "training_ir.txt"),
        "feature_tree_path": normalize_path(sample_dir / "feature_tree.json"),
        "metadata_path": normalize_path(sample_dir / "metadata.json"),
        "step_path": normalize_path(sample_dir / "model.step"),
        "point_path": normalize_path(sample_dir / "point_cloud.npz"),
        "image_paths": [normalize_path(p) for p in image_paths],
        "iso_image_path": "" if iso_image_missing else normalize_path(iso_image),
        "iso_image_missing": iso_image_missing,
        "text": text_info["text"],
        "deterministic_text": text_info["deterministic_text"],
        "llm_text": text_info["llm_text"],
        "template": metadata.get("template") or metadata.get("template_family") or metadata.get("family") or "",
        "complexity": metadata.get("complexity") or metadata.get("complexity_level") or metadata.get("level") or "",
    }


def load_image(path: str | Path, image_size: int = 224) -> Image.Image:
    image = Image.open(path).convert("RGB")
    if image_size:
        image = image.resize((image_size, image_size), Image.BICUBIC)
    return image


def _log1p_number(value: Any) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = 0.0
    if value < 0:
        value = 0.0
    return float(math.log1p(value))


def _nested_get(data: dict[str, Any], keys: list[str], default: Any = 0.0) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def step_feature_vector_from_json(data: dict[str, Any]) -> np.ndarray:
    features = data.get("features", data)
    topo = features.get("brep_topology", {}) if isinstance(features, dict) else {}
    bbox_size = _nested_get(features, ["bbox", "size"], [0.0, 0.0, 0.0])
    if not isinstance(bbox_size, list) or len(bbox_size) < 3:
        bbox_size = [0.0, 0.0, 0.0]

    values: list[float] = []
    values.append(1.0 if features.get("brep_valid") else 0.0)
    for key in ["solid_count", "shell_count", "face_count", "wire_count", "edge_count", "vertex_count"]:
        values.append(_log1p_number(features.get(key)))
    for value in bbox_size[:3]:
        values.append(_log1p_number(value))
    values.append(_log1p_number(features.get("surface_area")))
    values.append(_log1p_number(features.get("volume")))

    surface_counts = topo.get("surface_type_counts", {}) if isinstance(topo, dict) else {}
    for key in STEP_SURFACE_TYPES:
        values.append(_log1p_number(surface_counts.get(key, 0)))

    curve_counts = topo.get("curve_type_counts", {}) if isinstance(topo, dict) else {}
    for key in STEP_CURVE_TYPES:
        values.append(_log1p_number(curve_counts.get(key, 0)))

    valence_counts = topo.get("edge_face_valence_counts", {}) if isinstance(topo, dict) else {}
    values.append(_log1p_number(valence_counts.get("1", 0)))
    values.append(_log1p_number(valence_counts.get("2", 0)))
    values.append(_log1p_number(valence_counts.get("3", 0)))
    values.append(_log1p_number(sum(v for k, v in valence_counts.items() if str(k).isdigit() and int(k) >= 4)))

    for key in [
        "face_wire_incidence_count",
        "face_edge_incidence_count",
        "face_edge_adjacency_count",
        "boundary_edge_count",
        "manifold_edge_count",
        "non_manifold_edge_count",
    ]:
        values.append(_log1p_number(topo.get(key, 0)))

    face_stats = topo.get("face_area_stats", {}) if isinstance(topo, dict) else {}
    edge_stats = topo.get("edge_length_stats", {}) if isinstance(topo, dict) else {}
    for stats in [face_stats, edge_stats]:
        for key in ["min", "max", "mean", "sum"]:
            values.append(_log1p_number(stats.get(key, 0)))

    if len(values) != STEP_FEATURE_DIM:
        raise ValueError(f"STEP feature vector length mismatch: {len(values)} != {STEP_FEATURE_DIM}")
    return np.asarray(values, dtype=np.float32)


def _one_hot(name: Any, choices: list[str]) -> list[float]:
    text = str(name or "").lower()
    return [1.0 if text == choice else 0.0 for choice in choices]


def _vector3(value: Any) -> list[float]:
    if isinstance(value, dict):
        value = [value.get("x", 0.0), value.get("y", 0.0), value.get("z", 0.0)]
    if not isinstance(value, (list, tuple)) or len(value) < 3:
        return [0.0, 0.0, 0.0]
    return [float(value[0] or 0.0), float(value[1] or 0.0), float(value[2] or 0.0)]


def _bool_number(value: Any) -> float:
    return 1.0 if bool(value) else 0.0


def face_descriptor_from_dict(face: dict[str, Any], total_area: float = 0.0) -> np.ndarray:
    """Convert one optional per-face record to the fixed 28-d descriptor.

    Current Flluma/OpenCASCADE extraction may not provide per-face rows yet. This
    function is intentionally permissive so future extractor versions can add
    face descriptors without changing the training code.
    """
    area = float(face.get("area", 0.0) or 0.0)
    values: list[float] = []
    values.extend(_one_hot(face.get("surface_type") or face.get("type"), STEP_SURFACE_TYPES))
    values.append(_log1p_number(area))
    values.append(float(area / total_area) if total_area > 1e-8 else 0.0)
    values.extend(_vector3(face.get("center") or face.get("centroid")))
    values.extend(_vector3(face.get("bbox_size") or face.get("bbox") or face.get("size")))
    values.extend(_vector3(face.get("normal")))
    values.append(_log1p_number(face.get("num_boundary_wires", face.get("boundary_wires", 0))))
    values.append(_log1p_number(face.get("num_inner_loops", face.get("inner_loops", 0))))
    values.append(_log1p_number(face.get("num_boundary_edges", face.get("boundary_edges", 0))))
    surface_type = str(face.get("surface_type") or face.get("type") or "").lower()
    values.append(_bool_number(face.get("is_planar", surface_type == "plane")))
    values.append(_bool_number(face.get("is_cylindrical", surface_type == "cylinder")))
    values.append(_bool_number(face.get("is_curved", surface_type not in {"", "plane"})))
    if len(values) != STEP_FACE_DIM:
        raise ValueError(f"STEP face descriptor length mismatch: {len(values)} != {STEP_FACE_DIM}")
    return np.asarray(values, dtype=np.float32)


def edge_descriptor_from_dict(edge: dict[str, Any], total_length: float = 0.0) -> np.ndarray:
    """Convert one optional per-edge record to the fixed 24-d descriptor."""
    length = float(edge.get("length", 0.0) or 0.0)
    values: list[float] = []
    values.extend(_one_hot(edge.get("curve_type") or edge.get("type"), STEP_CURVE_TYPES))
    values.append(_log1p_number(length))
    values.append(float(length / total_length) if total_length > 1e-8 else 0.0)
    values.extend(_vector3(edge.get("center") or edge.get("midpoint")))
    values.extend(_vector3(edge.get("start") or edge.get("start_point")))
    values.extend(_vector3(edge.get("end") or edge.get("end_point")))
    values.append(_log1p_number(edge.get("radius", 0.0)))
    values.append(_bool_number(edge.get("is_closed", False)))
    values.append(_log1p_number(edge.get("adjacent_face_count", edge.get("face_count", 0))))
    values.append(float(edge.get("dihedral_angle", 0.0) or 0.0))
    if len(values) != STEP_EDGE_DIM:
        raise ValueError(f"STEP edge descriptor length mismatch: {len(values)} != {STEP_EDGE_DIM}")
    return np.asarray(values, dtype=np.float32)


def relation_feature_vector_from_json(features: dict[str, Any]) -> np.ndarray:
    """Build a compact relation descriptor from available topology statistics.

    This is deliberately lightweight. It uses current Flluma topology counts when
    full face-edge adjacency descriptors are not available.
    """
    topo = features.get("brep_topology", {}) if isinstance(features, dict) else {}
    valence = topo.get("edge_face_valence_counts", {}) if isinstance(topo, dict) else {}
    relation = features.get("relation_descriptors", {}) if isinstance(features, dict) else {}
    if not isinstance(relation, dict):
        relation = {}

    values: list[float] = []
    for key in [
        "plane_plane",
        "plane_cylinder",
        "plane_cone",
        "cylinder_cylinder",
        "curved_plane",
    ]:
        values.append(_log1p_number(relation.get(key, 0)))
    for key in [
        "circular_edge_planar_face",
        "circular_edge_cylindrical_face",
        "line_edge_plane_plane",
    ]:
        values.append(_log1p_number(relation.get(key, 0)))
    for key in [
        "mean_wires_per_face",
        "max_wires_per_face",
        "total_inner_loops",
        "circular_inner_loop_count",
    ]:
        values.append(_log1p_number(relation.get(key, 0)))
    for key in ["mean_face_degree", "max_face_degree"]:
        values.append(_log1p_number(relation.get(key, 0)))
    for bucket in ["0", "1", "2", "3", "4plus"]:
        values.append(_log1p_number(relation.get(f"face_degree_{bucket}", 0)))
    for key in ["sharp_angles", "near_right_angles", "smooth_angles"]:
        values.append(_log1p_number(relation.get(key, 0)))
    values.append(_log1p_number(valence.get("1", 0)))
    values.append(_log1p_number(valence.get("2", 0)))
    values.append(_log1p_number(valence.get("3", 0)))
    values.append(_log1p_number(sum(v for k, v in valence.items() if str(k).isdigit() and int(k) >= 4)))
    for key in [
        "face_wire_incidence_count",
        "face_edge_incidence_count",
        "face_edge_adjacency_count",
        "boundary_edge_count",
        "manifold_edge_count",
        "non_manifold_edge_count",
    ]:
        values.append(_log1p_number(topo.get(key, 0)))

    if len(values) < STEP_RELATION_DIM:
        values.extend([0.0] * (STEP_RELATION_DIM - len(values)))
    values = values[:STEP_RELATION_DIM]
    return np.asarray(values, dtype=np.float32)


def step_brep_tensors_from_json(data: dict[str, Any]) -> dict[str, np.ndarray]:
    """Return Global + Local + Relation STEP/B-Rep tensors.

    If the extractor only provides global topology statistics, local face/edge
    matrices are zero-padded with zero masks. Future extractor versions can add
    `face_descriptors` and `edge_descriptors` lists to enable the local branch.
    """
    features = data.get("features", data)
    if not isinstance(features, dict):
        features = {}

    global_vec = step_feature_vector_from_json(data)
    relation_vec = relation_feature_vector_from_json(features)
    face_rows = features.get("face_descriptors", features.get("faces", []))
    edge_rows = features.get("edge_descriptors", features.get("edges", []))
    if not isinstance(face_rows, list):
        face_rows = []
    if not isinstance(edge_rows, list):
        edge_rows = []

    total_area = float(features.get("surface_area", 0.0) or 0.0)
    topo = features.get("brep_topology", {}) if isinstance(features, dict) else {}
    edge_stats = topo.get("edge_length_stats", {}) if isinstance(topo, dict) else {}
    total_length = float(edge_stats.get("sum", 0.0) or 0.0)

    face_rows = sorted(
        [x for x in face_rows if isinstance(x, dict)],
        key=lambda x: float(x.get("area", 0.0) or 0.0),
        reverse=True,
    )[:STEP_FACE_COUNT]
    edge_rows = sorted(
        [x for x in edge_rows if isinstance(x, dict)],
        key=lambda x: float(x.get("length", 0.0) or 0.0),
        reverse=True,
    )[:STEP_EDGE_COUNT]

    faces = np.zeros((STEP_FACE_COUNT, STEP_FACE_DIM), dtype=np.float32)
    face_mask = np.zeros((STEP_FACE_COUNT,), dtype=np.float32)
    for i, face in enumerate(face_rows):
        faces[i] = face_descriptor_from_dict(face, total_area=total_area)
        face_mask[i] = 1.0

    edges = np.zeros((STEP_EDGE_COUNT, STEP_EDGE_DIM), dtype=np.float32)
    edge_mask = np.zeros((STEP_EDGE_COUNT,), dtype=np.float32)
    for i, edge in enumerate(edge_rows):
        edges[i] = edge_descriptor_from_dict(edge, total_length=total_length)
        edge_mask[i] = 1.0

    return {
        "global": global_vec.astype(np.float32),
        "faces": faces,
        "face_mask": face_mask,
        "edges": edges,
        "edge_mask": edge_mask,
        "relation": relation_vec.astype(np.float32),
    }


def load_step_feature_vector(path: str | Path, *, strict: bool = False) -> np.ndarray:
    data = read_json(path, default=None, strict=strict)
    if not isinstance(data, dict):
        if strict:
            raise ValueError(f"load_step_feature_vector: no usable JSON at {path}")
        return np.zeros((STEP_FEATURE_DIM,), dtype=np.float32)
    return step_feature_vector_from_json(data)


def load_step_brep_tensors(path: str | Path, *, strict: bool = False) -> dict[str, np.ndarray]:
    data = read_json(path, default=None, strict=strict)
    if not isinstance(data, dict):
        if strict:
            raise ValueError(f"load_step_brep_tensors: no usable JSON at {path}")
        return {
            "global": np.zeros((STEP_GLOBAL_DIM,), dtype=np.float32),
            "faces": np.zeros((STEP_FACE_COUNT, STEP_FACE_DIM), dtype=np.float32),
            "face_mask": np.zeros((STEP_FACE_COUNT,), dtype=np.float32),
            "edges": np.zeros((STEP_EDGE_COUNT, STEP_EDGE_DIM), dtype=np.float32),
            "edge_mask": np.zeros((STEP_EDGE_COUNT,), dtype=np.float32),
            "relation": np.zeros((STEP_RELATION_DIM,), dtype=np.float32),
        }
    return step_brep_tensors_from_json(data)


def collate_step_brep_batch(items: list[dict[str, np.ndarray]]) -> dict[str, Any]:
    import torch

    keys = ["global", "faces", "face_mask", "edges", "edge_mask", "relation"]
    return {key: torch.tensor(np.stack([item[key] for item in items], axis=0), dtype=torch.float32) for key in keys}


@dataclass
class ProgramExample:
    prompt: str
    target: str
    sample_id: str


def build_generation_prompt(row: dict[str, Any], target: str = "program", retrieved: list[dict[str, Any]] | None = None) -> str:
    """Build the RAG prompt for the LoRA generator.

    Retrieved construction-similar examples are prepended as few-shot demonstrations.
    Loss is masked over all prompt tokens; only the target program tokens are trained.
    """
    if target == "ir":
        task = "Generate the Flluma training IR for the target CAD model."
        output = "Return only the training IR."
    else:
        task = "Generate an executable Flluma Python program for the target CAD model."
        output = "Return only Python code."

    target_text = row.get("prompt_text", row.get("text", "")).strip()
    parts = [
        "You are a CAD program generation model.",
        task,
        output,
        "",
        "Target description:",
        target_text,
    ]
    target_observation = row.get("target_observation", "").strip()
    if target_observation:
        parts.extend(["", "Target observation:", target_observation])

    if retrieved:
        parts.append("")
        parts.append("Retrieved similar CAD examples:")
        for i, item in enumerate(retrieved, start=1):
            parts.append(f"Example {i}:")
            parts.append("Description:")
            parts.append(str(item.get("text", ""))[:800])
            ir = item.get("ir", "")
            program = item.get("program", "")
            if ir:
                parts.append("IR:")
                parts.append(ir[:1200])
            if program:
                parts.append("Program:")
                parts.append(program[:1800])

    parts.append("")
    parts.append("Output:")
    return "\n".join(parts).strip()


def load_program_example(row: dict[str, Any], target: str = "program", retrieved: list[dict[str, Any]] | None = None) -> ProgramExample:
    prompt = build_generation_prompt(row, target=target, retrieved=retrieved)
    if target == "ir":
        target_text = read_text(row["ir_path"])
    else:
        target_text = read_text(row["program_path"])
    return ProgramExample(prompt=prompt, target=target_text.strip(), sample_id=row["sample_id"])


def deterministic_shuffle(rows: list[Any], seed: int) -> list[Any]:
    rows = list(rows)
    rng = random.Random(seed)
    rng.shuffle(rows)
    return rows
