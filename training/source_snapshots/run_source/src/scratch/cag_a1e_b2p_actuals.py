"""Preflight and provenance recorder for the CAG A1E/B2P frozen comparison.

This file is intentionally separate from the original experiment runners. It is
used by training_25k/cag_run_frozen_a1e_b2p_seed.sh to enforce the frozen
protocol before GPU work starts, and to write a richer actuals file after a run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def line_count(path: Path) -> int | None:
    if not path.exists() or not path.is_file():
        return None
    n = 0
    with path.open("rb") as f:
        for _ in f:
            n += 1
    return n


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def run_text(cmd: list[str]) -> str | None:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    except Exception as exc:  # pragma: no cover - diagnostic only
        return f"unavailable: {exc}"
    if out.returncode != 0:
        msg = (out.stderr or out.stdout).strip()
        return f"unavailable: {msg[-300:]}"
    return out.stdout.strip()


def parse_eval_losses(log_path: Path) -> list[float]:
    if not log_path.exists():
        return []
    text = log_path.read_text(encoding="utf-8", errors="replace")
    vals = re.findall(r"'eval_loss':\s*'?([0-9.eE+-]+)'?", text)
    return [float(v) for v in vals]


def collect_reports(out_dir: Path) -> dict[str, Any]:
    reports: dict[str, Any] = {}
    if not out_dir.exists():
        return reports
    for path in sorted(out_dir.glob("*report*.json")):
        try:
            reports[path.name] = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            reports[path.name] = f"unreadable: {exc}"
    return reports


def frozen_paths(args: argparse.Namespace) -> dict[str, Path]:
    modality = args.modality
    seed = args.seed
    gen_dir = ROOT / args.gen_dir
    return {
        "train": ROOT / "data/25k/train.jsonl",
        "b2p_train": ROOT / f"data/25k/train_b2pred_{modality}.jsonl",
        "test": ROOT / "data/25k/test.jsonl",
        "pred_ir_test": gen_dir / f"pred_ir_{modality}_present.jsonl",
        "a_out": ROOT / f"outputs/b1_1epoch_{modality}_s{seed}",
        "b_out": ROOT / f"outputs/b2_pred_matched_{modality}_s{seed}",
        "a_pred": gen_dir / f"gen_code_{modality}_A1E_s{seed}.jsonl",
        "b_pred": gen_dir / f"gen_code_{modality}_B2P_s{seed}.jsonl",
        "legacy_actuals": gen_dir / f"seed_{seed}_actuals.json",
        "cag_actuals": gen_dir / f"cag_seed_{seed}_actuals.json",
        "preflight": gen_dir / f"cag_seed_{seed}_preflight.json",
        "a_log": ROOT / f"outputs/b1_1epoch_{modality}_s{seed}.train.log",
        "b_log": ROOT / f"outputs/b2_pred_matched_{modality}_s{seed}.train.log",
    }


def output_status(paths: dict[str, Path]) -> dict[str, Any]:
    a_final = paths["a_out"] / "adapter_model.safetensors"
    a_prefix = paths["a_out"] / "soft_prefix.pt"
    b_final = paths["b_out"] / "adapter_model.safetensors"
    return {
        "a_out_exists": paths["a_out"].exists(),
        "a_out_complete": a_final.exists() and a_prefix.exists(),
        "b_out_exists": paths["b_out"].exists(),
        "b_out_complete": b_final.exists(),
        "a_pred_exists": paths["a_pred"].exists(),
        "a_pred_rows": line_count(paths["a_pred"]),
        "b_pred_exists": paths["b_pred"].exists(),
        "b_pred_rows": line_count(paths["b_pred"]),
        "legacy_actuals_exists": paths["legacy_actuals"].exists(),
        "cag_actuals_exists": paths["cag_actuals"].exists(),
        "a_log_exists": paths["a_log"].exists(),
        "b_log_exists": paths["b_log"].exists(),
    }


def script_hashes() -> dict[str, str | None]:
    rels = [
        "training_25k/cag_run_frozen_a1e_b2p_seed.sh",
        "training_25k/44_seeds_a1e_b2p.sh",
        "training_25k/scripts/gen_b1_direct_latent.py",
        "training_25k/scripts/gen_code_from_predicted_ir.py",
        "gen_scripts/train_soft_prefix_ir.py",
        "train_program_lora.py",
        "scratch/cag_a1e_b2p_actuals.py",
    ]
    return {r: sha256_file(ROOT / r) for r in rels}


def build_common_record(args: argparse.Namespace, paths: dict[str, Path]) -> dict[str, Any]:
    train_rows = line_count(paths["train"])
    b2p_rows = line_count(paths["b2p_train"])
    expected_updates = math.ceil((train_rows or 0) / args.accum) * args.epochs
    return {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "CAG frozen A1E/B2P exact-match comparison",
        "seed": args.seed,
        "protocol": {
            "modality": args.modality,
            "limit": args.limit,
            "epochs": args.epochs,
            "gradient_accumulation_steps": args.accum,
            "batch_size": args.batch_size,
            "repair": False,
            "checkpoint_selection": "final",
            "expected_updates": expected_updates,
            "expected_updates_formula": "ceil(train_rows / grad_accum) * epochs",
        },
        "paths": {k: rel(v) for k, v in paths.items()},
        "inputs": {
            "train_rows": train_rows,
            "train_sha256": sha256_file(paths["train"]),
            "b2p_train_rows": b2p_rows,
            "b2p_train_sha256": sha256_file(paths["b2p_train"]),
            "test_rows": line_count(paths["test"]),
            "test_sha256": sha256_file(paths["test"]),
            "pred_ir_test_rows": line_count(paths["pred_ir_test"]),
            "pred_ir_test_sha256": sha256_file(paths["pred_ir_test"]),
        },
        "script_hashes": script_hashes(),
    }


def cmd_preflight(args: argparse.Namespace) -> int:
    paths = frozen_paths(args)
    rec = build_common_record(args, paths)
    status = output_status(paths)
    rec["output_status_before"] = status

    failures: list[str] = []
    if args.seed == 42:
        failures.append("seed 42 is reserved as the existing reference run")
    if args.modality != "step":
        failures.append(f"MODALITY must be step, got {args.modality}")
    if args.limit != 500:
        failures.append(f"LIMIT must be 500, got {args.limit}")
    if args.accum != 8:
        failures.append(f"ACCUM must be 8, got {args.accum}")
    if args.epochs != 1:
        failures.append(f"EPOCHS must be 1, got {args.epochs}")

    inputs = rec["inputs"]
    if inputs["train_rows"] != 25000:
        failures.append(f"data/25k/train.jsonl must have 25000 rows, got {inputs['train_rows']}")
    if inputs["b2p_train_rows"] != 25000:
        failures.append(
            f"data/25k/train_b2pred_step.jsonl must have 25000 rows, got {inputs['b2p_train_rows']}"
        )
    if inputs["pred_ir_test_rows"] != 500:
        failures.append(
            "outputs/e1_observation_bypass/pred_ir_step_present.jsonl "
            f"must have 500 rows, got {inputs['pred_ir_test_rows']}"
        )
    if rec["protocol"]["expected_updates"] != 3125:
        failures.append(f"expected updates must be 3125, got {rec['protocol']['expected_updates']}")

    existing = [
        name for name, value in status.items()
        if name.endswith("_exists") and value
    ]
    if existing and not args.allow_existing:
        failures.append(
            "existing output/provenance detected for this seed; archive/remove it first: "
            + ", ".join(existing)
        )
    if status["a_out_exists"] and not status["a_out_complete"]:
        failures.append("A1E output directory exists but is incomplete/partial")
    if status["b_out_exists"] and not status["b_out_complete"]:
        failures.append("B2P output directory exists but is incomplete/partial")

    rec["preflight_failures"] = failures
    paths["preflight"].parent.mkdir(parents=True, exist_ok=True)
    paths["preflight"].write_text(json.dumps(rec, indent=2, sort_keys=True), encoding="utf-8")

    if failures:
        print("CAG preflight failed:")
        for item in failures:
            print(f"  - {item}")
        print(f"preflight record: {rel(paths['preflight'])}")
        return 1

    print("CAG preflight passed")
    print(f"preflight record: {rel(paths['preflight'])}")
    return 0


def environment_record() -> dict[str, Any]:
    py = sys.version.replace("\n", " ")
    torch_info: dict[str, Any] = {}
    try:
        import torch  # type: ignore

        torch_info = {
            "torch": getattr(torch, "__version__", None),
            "cuda_available": torch.cuda.is_available(),
            "cuda_version": getattr(torch.version, "cuda", None),
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        }
    except Exception as exc:
        torch_info = {"torch": f"unavailable: {exc}"}
    try:
        import transformers  # type: ignore

        transformers_version = getattr(transformers, "__version__", None)
    except Exception as exc:
        transformers_version = f"unavailable: {exc}"
    return {
        "python": py,
        "platform": platform.platform(),
        "torch": torch_info,
        "transformers": transformers_version,
        "nvidia_smi": run_text(["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"]),
    }


def cmd_post(args: argparse.Namespace) -> int:
    paths = frozen_paths(args)
    rec = build_common_record(args, paths)
    rec["environment"] = environment_record()
    rec["output_status_after"] = output_status(paths)

    rec["arms"] = {
        "A1E": {
            "output_dir": rel(paths["a_out"]),
            "reports": collect_reports(paths["a_out"]),
            "train_log": rel(paths["a_log"]),
            "eval_loss_all": parse_eval_losses(paths["a_log"]),
            "prediction_file": rel(paths["a_pred"]),
            "prediction_rows": line_count(paths["a_pred"]),
            "prediction_sha256": sha256_file(paths["a_pred"]),
        },
        "B2P": {
            "output_dir": rel(paths["b_out"]),
            "reports": collect_reports(paths["b_out"]),
            "train_log": rel(paths["b_log"]),
            "eval_loss_all": parse_eval_losses(paths["b_log"]),
            "prediction_file": rel(paths["b_pred"]),
            "prediction_rows": line_count(paths["b_pred"]),
            "prediction_sha256": sha256_file(paths["b_pred"]),
        },
    }
    rec["validation"] = {
        "a_prediction_complete": line_count(paths["a_pred"]) == args.limit,
        "b_prediction_complete": line_count(paths["b_pred"]) == args.limit,
        "a_final_artifacts_present": (paths["a_out"] / "adapter_model.safetensors").exists()
        and (paths["a_out"] / "soft_prefix.pt").exists(),
        "b_final_artifacts_present": (paths["b_out"] / "adapter_model.safetensors").exists(),
    }

    paths["cag_actuals"].parent.mkdir(parents=True, exist_ok=True)
    paths["cag_actuals"].write_text(json.dumps(rec, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {rel(paths['cag_actuals'])}")

    if not all(rec["validation"].values()):
        print("CAG post-run validation has missing/incomplete artifacts:")
        for k, v in rec["validation"].items():
            if not v:
                print(f"  - {k}")
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("preflight", "post"):
        p = sub.add_parser(name)
        p.add_argument("--seed", type=int, required=True)
        p.add_argument("--modality", default="step")
        p.add_argument("--limit", type=int, default=500)
        p.add_argument("--accum", type=int, default=8)
        p.add_argument("--epochs", type=int, default=1)
        p.add_argument("--batch-size", type=int, default=16)
        p.add_argument("--gen-dir", default="outputs/e1_observation_bypass")
        p.add_argument("--allow-existing", action="store_true")
    args = ap.parse_args(argv)
    if args.cmd == "preflight":
        return cmd_preflight(args)
    if args.cmd == "post":
        return cmd_post(args)
    raise AssertionError(args.cmd)


if __name__ == "__main__":
    raise SystemExit(main())
