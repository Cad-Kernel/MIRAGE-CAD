"""Additive Fusion 360 gallery helpers; previously sealed evidence is read-only."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GALLERY = ROOT / "gallery_v1"
ARCHIVE = ROOT / "raw_archive_v1"
POLICY = ROOT / "04_case_selection_and_render_protocol.md"
METHODS = ("reference", "cadr", "mirage", "nn")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=True, allow_nan=False)
        stream.write("\n")


def text_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(value)


def utc():
    return datetime.now(timezone.utc).isoformat()


def verify_prior():
    counts = {}
    for label, rel in (("step1", "audit/step1_package_seal_v1.json"),
                       ("step2", "taxonomy/step2_package_seal_v1.json")):
        manifest = read(ROOT / rel)
        for name, item in manifest["files"].items():
            require(sha(ROOT / name) == item["sha256"], "Prior seal changed: " + name)
        counts[label] = len(manifest["files"])
    return counts
