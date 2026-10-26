"""Read-only candidate inputs and versioned qualitative-render contracts."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "rendering/cpu_v1"
NATIVE = Path(r"__FLLUMA_ROOT__\build\Desktop_Qt_6_8_3_MSVC2022_64bit-Release\bin")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_new(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=True, allow_nan=False)
        f.write("\n")


def utc():
    return datetime.now(timezone.utc).isoformat()


def local_path(value):
    if os.name == "nt":
        if str(value).startswith("/home/"):
            return Path("//wsl.localhost/Ubuntu" + str(value))
        return Path(str(value).replace("/mnt/c/", "C:/"))
    value = str(value).replace("\\", "/")
    return Path("/mnt/c/" + value[3:] if value.startswith("C:/") else value)


def verify_original_lock():
    lock = read(ROOT / "selection/path_lock_manifest_v1.json")
    for item in lock["files"].values():
        p = local_path(item["path"])
        require(p.is_file() and sha(p) == item["sha256"], f"Original lock drift: {p}")
    return len(lock["files"])


def cases():
    lock = read(ROOT / "selection/path_lock_manifest_v1.json")
    return [read(ROOT / "cases" / key / "case.json") for key in lock["case_ids"]]


def artifact(path):
    path = Path(path)
    return {"path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "bytes": path.stat().st_size, "sha256": sha(path)}
