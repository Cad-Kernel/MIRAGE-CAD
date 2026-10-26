"""Point-cloud loading and sampling for MIRAGE-CAD.

The point-cloud branch uses normalized xyz coordinates only. Normals are not
used, so the protocol remains comparable with CAD datasets that provide only
positions. FllumaOne stores 2,048 surface samples per model; MIRAGE-CAD uses
1,024 sampled points by default:

- training: hybrid random/FPS sampling
- validation/testing: deterministic FPS sampling

This avoids order-dependent sampling while keeping the memory footprint small
on a 16 GB GPU.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np


def normalize_xyz(points: np.ndarray) -> np.ndarray:
    points = np.asarray(points, dtype=np.float32)
    center = points.mean(axis=0, keepdims=True)
    points = points - center
    scale = np.max(np.linalg.norm(points, axis=1))
    if scale > 1e-8:
        points = points / scale
    return points.astype(np.float32)


def farthest_point_sampling(points: np.ndarray, count: int, seed: int = 0) -> np.ndarray:
    """CPU FPS for small CAD point clouds.

    The expected input size is 2,048 points and the default output size is
    1,024, so a NumPy implementation is sufficient for offline/pilot training.
    """
    points = np.asarray(points, dtype=np.float32)
    n = len(points)
    if n <= count:
        return np.arange(n, dtype=np.int64)

    rng = np.random.default_rng(seed)
    selected = np.empty(count, dtype=np.int64)
    selected[0] = int(rng.integers(0, n))
    dist = np.full(n, np.inf, dtype=np.float32)

    for i in range(1, count):
        last = points[selected[i - 1]]
        d = np.sum((points - last) ** 2, axis=1)
        dist = np.minimum(dist, d)
        selected[i] = int(np.argmax(dist))
    return selected


def sample_indices(points: np.ndarray, count: int, mode: str, seed: int = 0) -> np.ndarray:
    n = len(points)
    if n <= count:
        base = np.arange(n, dtype=np.int64)
        if n == count:
            return base
        rng = np.random.default_rng(seed)
        extra = rng.choice(base, size=count - n, replace=True)
        return np.concatenate([base, extra]).astype(np.int64)

    if mode == "random":
        rng = np.random.default_rng(seed)
        return rng.choice(n, size=count, replace=False).astype(np.int64)
    if mode == "fps":
        return farthest_point_sampling(points, count=count, seed=seed)
    if mode == "hybrid":
        return sample_indices(points, count, "fps" if seed % 2 == 0 else "random", seed)
    raise ValueError(f"Unsupported point sampling mode: {mode}")


def _pick_array(data: np.lib.npyio.NpzFile, names: list[str]) -> np.ndarray | None:
    for name in names:
        if name in data:
            return np.asarray(data[name])
    return None


def load_point_cloud_sampled(
    path: str | Path,
    point_count: int = 1024,
    sampling: str = "fps",
    seed: int = 0,
) -> np.ndarray:
    data = np.load(path)
    points = _pick_array(data, ["points", "xyz", "point_cloud"])
    if points is None:
        points = np.asarray(data[data.files[0]])
    points = np.asarray(points, dtype=np.float32)
    if points.ndim != 2 or points.shape[1] < 3:
        points = points.reshape(-1, 3)
    xyz = normalize_xyz(points[:, :3])
    idx = sample_indices(xyz, point_count, sampling, seed=seed)
    return xyz[idx].astype(np.float32)
