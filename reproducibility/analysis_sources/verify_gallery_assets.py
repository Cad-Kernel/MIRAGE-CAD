"""Read-only image/STEP-envelope/local HTML reference validation, no rendering."""
import hashlib
import json
import os
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit
from PIL import Image

R = Path("__EVIDENCE_SOURCE_ROOT__")
OUT = R / "09_cpu_preparation/gallery_assets_v3"


def main():
    if OUT.exists():
        raise ValueError("Do not overwrite gallery audit")
    OUT.mkdir()
    media, errors, links = [], [], []
    for name in ("05_qualitative", "06_fusion360"):
        for parent, directories, names in os.walk(R / name):
            directories[:] = [d for d in directories if d not in {"node_modules", ".git", "__pycache__"}]
            for filename in names:
                p = Path(parent) / filename
                ext = p.suffix.lower()
                if ext in {".png", ".jpg", ".jpeg", ".webp"}:
                    try:
                        with Image.open(p) as im:
                            dimensions = list(im.size)
                            im.verify()
                        media.append({"path": str(p), "kind": "image", "dimensions": dimensions, "bytes": p.stat().st_size})
                    except Exception as e:
                        errors.append({"path": str(p), "error": str(e)})
                elif ext in {".step", ".stp"}:
                    raw = p.read_bytes()
                    valid = b"ISO-10303-21" in raw[:200] and b"END-ISO-10303-21" in raw[-500:]
                    media.append({"path": str(p), "kind": "step_text_envelope", "valid_envelope": valid, "bytes": len(raw)})
                    if not valid:
                        errors.append({"path": str(p), "error": "Missing STEP exchange-file text envelope"})
                elif ext == ".html":
                    text = p.read_text(encoding="utf-8")
                    for match in re.finditer(r'''(?:src|href)\s*=\s*["']([^"']+)["']''', text, re.I):
                        value = match.group(1)
                        parsed = urlsplit(value)
                        if parsed.scheme in {"https", "http", "data", "javascript", "mailto"} or not parsed.path or value.startswith("#"):
                            continue
                        target = unquote(parsed.path)
                        if parsed.scheme == "file" and parsed.netloc:
                            target = "//" + parsed.netloc + target
                        if parsed.scheme == "file" and re.match(r"/[A-Za-z]:/", target):
                            target = target[1:]
                        candidate = Path(target)
                        if not candidate.is_absolute():
                            candidate = p.parent / candidate
                        links.append({"html": str(p), "target": str(candidate), "exists": candidate.exists()})
    report = {"status": "PASS_SCOPED_ASSET_READABILITY" if not errors and all(l["exists"] for l in links) else "ISSUES_FOUND",
              "images_checked": sum(m["kind"] == "image" for m in media),
              "step_envelopes_checked": sum(m["kind"] == "step_text_envelope" for m in media),
              "html_local_links_checked": len(links), "missing_html_local_links": [l for l in links if not l["exists"]],
              "errors": errors, "author_semantic_signoff": "PENDING_UNCHANGED",
              "scope": "No mesh/solid validity, semantic judgement, rerendering or metric recomputation", "originals_modified": False}
    (OUT / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (OUT / "asset_records.jsonl").write_text("".join(json.dumps(m) + "\n" for m in media), encoding="utf-8")
    (OUT / "local_link_records.jsonl").write_text("".join(json.dumps(l) + "\n" for l in links), encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k not in {"missing_html_local_links", "errors"}}, indent=2))
    print(f"errors={len(errors)}, missing_links={len(report['missing_html_local_links'])}")


if __name__ == "__main__":
    main()
