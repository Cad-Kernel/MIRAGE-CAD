#!/usr/bin/env python3
"""Parse gate inputs with native-version Python3.11.11; never execute programs/CAD."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import warnings

PACKAGE = Path(__file__).resolve().parents[1]
SCRATCH = Path(r"__DEV_ROOT__\scratch")
STAGING = Path(r"__TEMP_RUN_ROOT__\exec_eval")


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def file_record(path):
    p = Path(path).resolve()
    wsl = "/mnt/" + p.drive[0].lower() + "/" + p.relative_to(p.anchor).as_posix()
    return {"path": wsl, "windows_path": str(p), "sha256": digest(p), "bytes": p.stat().st_size}


def rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def main():
    destination = PACKAGE / "execution/exposure_gate_native311_syntax_20261021.json"
    if destination.exists():
        raise ValueError("No overwrite of existing native syntax audit")
    if sys.version_info[:3] != (3, 11, 11):
        raise ValueError("Use the matching standalone native Python3.11.11, not the WSL interpreter")
    groups = {}
    for arm in ("A", "B"):
        groups[arm] = {}
        for modality in ("step", "point", "text", "image"):
            run_id = f"exec_r04_{modality}_{arm}"
            input_path = STAGING / run_id / "input.jsonl"
            gate_path = SCRATCH / run_id / "execution_rows.jsonl"
            predictions, evaluated = rows(input_path), rows(gate_path)
            if len(predictions) != 2500 or [r["sample_id"] for r in predictions] != [r["sample_id"] for r in evaluated]:
                raise ValueError(f"Native AST ID/count mismatch: {run_id}")
            parsed = []
            for prediction, gate in zip(predictions, evaluated):
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", SyntaxWarning)
                    try:
                        ast.parse(prediction["prediction"])
                        valid, error = True, ""
                    except SyntaxError as exc:
                        valid, error = False, str(exc)
                if not gate["error"].startswith("kernel access") and valid != gate["syntax_ok"]:
                    raise ValueError(f"Actual3.11.11 AST mismatch: {run_id}/{prediction['sample_id']}")
                parsed.append({"sample_id": prediction["sample_id"], "syntax_ok": valid, "error": error,
                    "code_sha256": hashlib.sha256(prediction["prediction"].encode("utf-8")).hexdigest()})
            groups[arm][modality] = {"input": file_record(input_path), "gate_rows": file_record(gate_path), "rows": parsed}
            print(f"Native Python3.11.11 AST PASS {arm}/{modality}:2500; no code execution", flush=True)
    result = {"status": "PASS_NATIVE311_AST_ONLY", "python_version": list(sys.version_info[:3]),
              "python_full_version": sys.version, "executable": file_record(sys.executable),
              "audit_source": file_record(__file__), "groups": groups, "program_or_CAD_execution": False}
    with destination.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    print(f"Native AST audit saved: {destination}; no CAD/model execution", flush=True)


if __name__ == "__main__":
    main()
