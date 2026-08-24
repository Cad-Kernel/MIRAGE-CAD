"""Stage 2: one sample end to end through the frozen protocol, with complete provenance.

RUNS IN cadrecode_env. This validates the PIPELINE, not the model. Its success criterion is that
every stage completes and every artefact exists -- a sample that executes, exports and scores at
CD 100 and IoU 0.1 is a Stage 2 PASS, because that is a statement about CAD-Recode's accuracy on
one part and not about whether the plumbing works. Confusing the two would invite tuning the
protocol until the geometry looked better, which is precisely what freezing it beforehand was for.

THE PROTOCOL IS FROZEN AND NOTHING HERE MAY CHANGE IT. alpha = 1e-6 relative, angular = 0.3, 8192
surface samples at seed 0, FPS to 256 from index 0, greedy generation at max_new_tokens 768. If
this sample executes but scores badly, that is a result. Normalisation, tolerance, FPS, decoding and
repair stay as they are unless an implementation BUG is demonstrated -- the protocol was fixed
before any CAD-Recode output was seen, and that is worth more than a better-looking number.

FIVE STAGES, each with its own failure states so a late problem is not attributed to an early one:

  A  input      STEP -> canonical mesh -> normalise -> 8192 -> FPS 256, hashed at every step
  B  generation released checkpoint, released implementation, greedy, one candidate
  C  extraction raw text -> the program between the sentinels. Failures are recorded, not repaired
  D  execution  an ISOLATED SUBPROCESS with a timeout, its own directory, and captured streams
  E  evaluation the generated STEP re-tessellated by the COMMON operator, then CD and IoU

WHY THE DEMO'S OWN MESH IS NOT USED IN E. The demo tessellates its prediction at (0.001, 0.1) and
scores that. Doing the same would mean the two arms were meshed by different operators at different
relative fidelities, which is the confound the whole of Phase 1 exists to remove. The demo's mesh is
released-behaviour reference; the measurement goes through the frozen operator.

CD AND IOU FAIL INDEPENDENTLY. A part can export cleanly, score a CD, and have its IoU boolean fail
-- 1 part in 10 does, per the calibration -- and that is not a failed sample. The frozen reporting
contract is that the two metrics may have different denominators.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

MODEL_ID = "filapro/cad-recode-v1.5"
TOKENIZER_ID = "Qwen/Qwen2-1.5B"
MAX_NEW_TOKENS = 768          # demo cell 5
K_POINTS = 256
EXEC_TIMEOUT_S = 60

# Refused, never rewritten. A generated program containing these is reported as
# UNSAFE_CODE_REJECTED: the released demo execs whatever it produces, and over 400 samples the
# chance that none of them touches the filesystem or network is not one worth taking. Deleting the
# offending lines would measure the edit rather than the model.
UNSAFE_PATTERNS = ("import os", "import sys", "import subprocess", "import socket",
                   "import shutil", "import requests", "open(", "exec(", "eval(",
                   "__import__(", "compile(", "globals()", "locals()")

STATUSES = ("INPUT_OK", "MODEL_LOAD_FAILED", "GENERATION_FAILED", "CODE_EXTRACTION_FAILED",
            "UNSAFE_CODE_REJECTED", "EXECUTION_TIMEOUT", "EXECUTION_FAILED", "RESULT_R_MISSING",
            "CADQUERY_OBJECT_FAILED", "STEP_EXPORT_FAILED", "REMESH_FAILED", "CD_FAILED",
            "IOU_FAILED", "SUCCESS")


def sha256_file(p: str | Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def sha256_arr(a: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


# ---------------------------------------------------------------------------
# A. input
# ---------------------------------------------------------------------------
def build_input(step_path: str) -> dict:
    import trimesh
    from cadrecode_input_pipeline import (N_PRE_POINTS, TARGET_EXTENT, DEMO_SEED,
                                          normalise_for_model, sample_farthest_points_np)
    from probe_cadrecode_mesh import ALPHA, ANGULAR_DEFLECTION, tessellate_step, to_trimesh

    v, f = tessellate_step(step_path)
    raw = to_trimesh(v, f, merge=True)
    bbox_before = [float(x) for x in raw.extents]
    mesh = normalise_for_model(raw)

    np.random.seed(DEMO_SEED)
    pre, _ = trimesh.sample.sample_surface(mesh, N_PRE_POINTS)
    pre = np.asarray(pre, dtype=np.float64)
    idx = sample_farthest_points_np(pre, K_POINTS, start_index=0)
    if len(set(idx.tolist())) != len(idx):
        raise ValueError(f"FPS repeated an index: only {len(set(idx.tolist()))} distinct positions")
    pts = pre[idx]

    return {
        "source_step_sha256": sha256_file(step_path),
        "alpha": ALPHA, "angular_deflection": ANGULAR_DEFLECTION,
        "canonical_mesh_sha256": sha256_arr(np.asarray(mesh.vertices)) + "/"
                                 + sha256_arr(np.asarray(mesh.faces)),
        "mesh_vertex_count": int(len(mesh.vertices)),
        "mesh_triangle_count": int(len(mesh.faces)),
        "mesh_watertight": bool(mesh.is_watertight),
        "bbox_before_normalization": bbox_before,
        "normalization_target_extent": TARGET_EXTENT,
        "normalization_scale": TARGET_EXTENT / float(max(raw.extents)),
        "sampling_seed": DEMO_SEED,
        "n_pre_points": N_PRE_POINTS,
        "cloud_8192_sha256": sha256_arr(pre),
        "fps_indices_sha256": sha256_arr(idx),
        "fps_implementation": "sample_farthest_points_np, start_index=0, squared euclidean, "
                              "numpy argmax tie-breaking; COMPATIBLE with pytorch3d, not verified "
                              "index-for-index against it",
        "cloud_256_sha256": sha256_arr(pts),
        "_points": pts, "_mesh": mesh,
    }


# ---------------------------------------------------------------------------
# B. generation
# ---------------------------------------------------------------------------
def load_model(repo_dir: str, device: str):
    import torch
    from transformers import AutoTokenizer
    from cadrecode_infer import build_namespace, extract_upstream_classes

    source, src_hash = extract_upstream_classes(repo_dir)
    ns = build_namespace()
    exec(compile(source, "<cad-recode demo.ipynb>", "exec"), ns)
    dtype_before = torch.get_default_dtype()
    tok = AutoTokenizer.from_pretrained(TOKENIZER_ID, pad_token="<|im_end|>", padding_side="left")
    model = ns["CADRecode"].from_pretrained(MODEL_ID, torch_dtype="auto").eval().to(device)
    torch.set_default_dtype(dtype_before)   # upstream __init__ leaves bfloat16 set
    meta = {
        "checkpoint": MODEL_ID, "tokenizer": TOKENIZER_ID,
        "upstream_repo": repo_dir, "upstream_source_sha256": src_hash,
        "demo_notebook_sha256": sha256_file(Path(repo_dir) / "demo.ipynb"),
        "torch": torch.__version__, "device": device,
        "device_capability": (f"sm_{torch.cuda.get_device_capability(0)[0]}"
                              f"{torch.cuda.get_device_capability(0)[1]}"
                              if device.startswith("cuda") else None),
        "n_parameters": int(sum(p.numel() for p in model.parameters())),
        "generation": {"strategy": "greedy", "num_candidates": 1,
                       "max_new_tokens": MAX_NEW_TOKENS},
    }
    import transformers
    meta["transformers"] = transformers.__version__
    return model, tok, meta


def generate(model, tok, points: np.ndarray, device: str) -> tuple[str, float]:
    import torch
    input_ids = [tok.pad_token_id] * len(points) + [tok("<|im_start|>")["input_ids"][0]]
    attention_mask = [-1] * len(points) + [1]
    t0 = time.time()
    with torch.no_grad():
        out = model.generate(
            input_ids=torch.tensor(input_ids).unsqueeze(0).to(device),
            attention_mask=torch.tensor(attention_mask).unsqueeze(0).to(device),
            point_cloud=torch.tensor(points.astype(np.float32)).unsqueeze(0).to(device),
            max_new_tokens=MAX_NEW_TOKENS,
            pad_token_id=tok.pad_token_id)
    return tok.batch_decode(out)[0], time.time() - t0


def extract_code(raw: str) -> tuple[str | None, str]:
    """The demo's extraction, unchanged: between <|im_start|> and <|endoftext|>."""
    b = raw.find("<|im_start|>")
    e = raw.find("<|endoftext|>")
    if b < 0:
        return None, "no <|im_start|> in the generated text"
    if e < 0:
        return None, "no <|endoftext|>: generation probably hit max_new_tokens"
    code = raw[b + 12:e]
    if not code.strip():
        return None, "the region between the sentinels is empty"
    return code, "ok"


def screen_code(code: str) -> list[str]:
    return [p for p in UNSAFE_PATTERNS if p in code]


# ---------------------------------------------------------------------------
# E. evaluation, through the COMMON operator
# ---------------------------------------------------------------------------
def evaluate(gt_mesh, pred_step: str) -> dict:
    from external_geometry_eval import (N_SURFACE_POINTS, chamfer_x1000, iou_meshes,
                                        normalise_per_shape, sample_surface)
    from probe_cadrecode_mesh import tessellate_step, to_trimesh
    out: dict = {}
    try:
        v, f = tessellate_step(pred_step)            # the FROZEN operator, not the demo's
        pred = to_trimesh(v, f, merge=True)
        out["pred_mesh_triangles"] = int(len(pred.faces))
        out["pred_mesh_watertight"] = bool(pred.is_watertight)
    except Exception as e:
        out["remesh_status"] = f"REMESH_FAILED: {type(e).__name__}: {e}"
        return out
    out["remesh_status"] = "ok"

    g, p = normalise_per_shape(gt_mesh), normalise_per_shape(pred)
    try:
        out["cd_x1000"] = chamfer_x1000(sample_surface(g, N_SURFACE_POINTS, 0),
                                        sample_surface(p, N_SURFACE_POINTS, 1))
        # The floor for THIS pair, so the number is readable against its own resolution.
        out["cd_floor_gt"] = chamfer_x1000(sample_surface(g, N_SURFACE_POINTS, 10),
                                           sample_surface(g, N_SURFACE_POINTS, 11))
        out["cd_status"] = "ok"
    except Exception as e:
        out["cd_status"] = f"CD_FAILED: {type(e).__name__}: {e}"
    try:
        iou, st = iou_meshes(g, p)
        out["iou"], out["iou_status"] = iou, st
        # Whether IoU can be trusted on this GT at all, per the frozen contract.
        self_iou, self_st = iou_meshes(g, normalise_per_shape(gt_mesh.copy()))
        out["gt_self_iou"] = self_iou
        out["gt_self_iou_dev"] = None if self_iou is None else abs(self_iou - 1.0)
        out["iou_eligible"] = bool(self_iou is not None and abs(self_iou - 1.0) <= 1e-4
                                   and iou is not None)
    except Exception as e:
        out["iou_status"] = f"IOU_FAILED: {type(e).__name__}: {e}"
        out["iou_eligible"] = False
    return out


def run_one(step_path: str, sample_id: str, run_dir: str, model, tok, model_meta: dict,
            device: str = "cuda", timeout: int = EXEC_TIMEOUT_S, verbose: bool = True) -> dict:
    """One sample, end to end. THE only implementation -- Stage 2 and the batch both call this.

    What Stage 2 validated is this function. A batch runner with its own copy would mean the code
    checked on one sample and the code producing the paper's numbers were two things that merely
    resemble each other, which is the failure this project has already paid for three times.

    Writes a RUNNING manifest before any work and a terminal one at the end, so resume can tell a
    finished sample from a half-written one.
    """
    sid = sample_id
    run = Path(run_dir) / sid
    run.mkdir(parents=True, exist_ok=True)
    man: dict = {"sample_id": sid, "step_path": step_path,
                 "protocol": "frozen before any CAD-Recode output was seen; this sample's geometry "
                             "quality must not change it",
                 "pipeline_status": "RUNNING", "terminal": False,
                 "cd_status": None, "iou_status": None}

    def write(terminal: bool):
        (run / "run_manifest.json").write_text(json.dumps(man, indent=2, default=str),
                                              encoding="utf-8", newline="\n")

    def save(status: str) -> dict:
        man["pipeline_status"] = status
        man["terminal"] = True
        write(True)
        if verbose:
            print(f"  pipeline_status = {status}")
        return man

    def say(*a):
        if verbose:
            print(*a)

    write(False)     # RUNNING, so an interrupted sample is visibly unfinished

    # ---- A ----------------------------------------------------------------
    try:
        inp = build_input(step_path)
    except Exception as e:
        man["input_error"] = f"{type(e).__name__}: {e}"
        return save("EXECUTION_FAILED")
    man["input"] = {k: v for k, v in inp.items() if not k.startswith("_")}
    np.save(run / "cloud_256.npy", inp["_points"])
    say(f"  A input      mesh {inp['mesh_triangle_count']} tri, 256 points, "
        f"cloud sha {inp['cloud_256_sha256'][:16]}")

    # ---- B ----------------------------------------------------------------
    # The model is loaded by the caller and reused across samples; the generated CODE is not.
    man["model"] = model_meta
    try:
        raw, secs = generate(model, tok, inp["_points"], device)
    except Exception as e:
        man["generation_error"] = f"{type(e).__name__}: {e}"
        return save("GENERATION_FAILED")
    (run / "raw_generation.txt").write_text(raw, encoding="utf-8", newline="\n")
    man["generation"] = {"seconds": round(secs, 2), "raw_chars": len(raw),
                         "raw_sha256": hashlib.sha256(raw.encode()).hexdigest()}
    say(f"  B generation {secs:.1f}s, {len(raw)} chars")

    # ---- C ----------------------------------------------------------------
    code, why = extract_code(raw)
    man["extraction_status"] = why
    if code is None:
        return save("CODE_EXTRACTION_FAILED")
    (run / "extracted_code.py").write_text(code, encoding="utf-8", newline="\n")
    man["extracted_code_sha256"] = hashlib.sha256(code.encode()).hexdigest()
    man["extracted_code_lines"] = len(code.splitlines())
    hits = screen_code(code)
    man["unsafe_patterns_found"] = hits
    say(f"  C extraction {len(code.splitlines())} lines"
        + (f", UNSAFE: {hits}" if hits else ""))
    if hits:
        # Refused, not rewritten: editing it would measure the edit.
        return save("UNSAFE_CODE_REJECTED")

    # ---- D ----------------------------------------------------------------
    runner = Path(__file__).resolve().parent / "cadrecode_generated_runner.py"
    pred_step = run / "prediction.step"
    res_json = run / "execution_result.json"
    t0 = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, str(runner), "--code", str(run / "extracted_code.py"),
             "--out-step", str(pred_step), "--result", str(res_json)],
            cwd=str(run), capture_output=True, text=True, timeout=timeout)
        timed_out = False
    except subprocess.TimeoutExpired as e:
        proc = None
        timed_out = True
        (run / "execution_stdout.txt").write_text(e.stdout or "", encoding="utf-8", newline="\n")
        (run / "execution_stderr.txt").write_text(e.stderr or "", encoding="utf-8", newline="\n")
    wall = time.time() - t0
    man["execution"] = {"timeout_s": timeout, "wall_seconds": round(wall, 2),
                        "timed_out": timed_out, "cwd": str(run)}
    if timed_out:
        say(f"  D execution  TIMED OUT after {timeout}s")
        return save("EXECUTION_TIMEOUT")
    (run / "execution_stdout.txt").write_text(proc.stdout, encoding="utf-8", newline="\n")
    (run / "execution_stderr.txt").write_text(proc.stderr, encoding="utf-8", newline="\n")
    man["execution"]["return_code"] = proc.returncode
    sub = json.loads(res_json.read_text(encoding="utf-8")) if res_json.exists() else {
        "status": "EXECUTION_FAILED", "error": "the runner wrote no result file"}
    man["execution"]["runner_result"] = sub
    say(f"  D execution  {sub.get('status')} in {wall:.1f}s, rc={proc.returncode}")
    if sub.get("status") != "SUCCESS":
        return save(sub.get("status", "EXECUTION_FAILED"))
    man["artifacts"] = {"prediction_step": str(pred_step),
                        "prediction_step_sha256": sha256_file(pred_step),
                        "prediction_step_bytes": pred_step.stat().st_size}

    # ---- E ----------------------------------------------------------------
    ev = evaluate(inp["_mesh"], str(pred_step))
    man["evaluation"] = ev
    say(f"  E evaluation remesh {ev.get('remesh_status')}, "
        f"CD {ev.get('cd_x1000')} (floor {ev.get('cd_floor_gt')}), "
        f"IoU {ev.get('iou')} [{ev.get('iou_status')}]")
    if ev.get("remesh_status", "").startswith("REMESH_FAILED"):
        return save("REMESH_FAILED")

    # CD and IoU fail independently, per the frozen reporting contract: a part can export
    # cleanly, score a CD, and still have its IoU boolean fail -- 1 in 10 do -- and that is not
    # a failed sample.
    # Two layers. The pipeline either completed or it did not; CD and IoU succeed or fail
    # independently of it and of each other. A boolean failure on one part is not a system
    # failure -- 1 part in 10 fails IoU per the calibration -- and this is the frozen contract
    # that the two metrics may have different denominators, in the data model rather than a
    # footnote.
    man["cd_status"] = "ok" if ev.get("cd_status") == "ok" else ev.get("cd_status")
    man["iou_status"] = ("ok" if ev.get("iou_eligible")
                         else (ev.get("iou_status") or "ineligible"))
    if ev.get("cd_x1000") is not None and ev.get("cd_floor_gt"):
        man["cd_floor_ratio"] = ev["cd_x1000"] / ev["cd_floor_gt"]
    if not ev.get("iou_eligible"):
        say("  note: IoU not eligible for this part -- recorded, NOT a pipeline failure.")
    return save("SUCCESS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--step", required=True)
    ap.add_argument("--sample-id", default=None)
    ap.add_argument("--cadrecode-repo", required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--timeout", type=int, default=EXEC_TIMEOUT_S)
    args = ap.parse_args()

    sid = args.sample_id or Path(args.step).stem
    print("=" * 78)
    print(f"Stage 2: {sid}")
    print("=" * 78)
    try:
        model, tok, meta = load_model(args.cadrecode_repo, args.device)
    except Exception as e:
        print(f"MODEL_LOAD_FAILED: {type(e).__name__}: {e}")
        return 1
    man = run_one(args.step, sid, args.run_dir, model, tok, meta, args.device, args.timeout)
    print()
    print("Stage 2 validates the PIPELINE, not the model. A completed run with poor geometry is a")
    print("PASS: CD and IoU here describe CAD-Recode's accuracy on one part, and the protocol was")
    print("frozen before any of its output was seen. Nothing in this result may be used to retune")
    print("normalisation, tolerance, FPS, decoding or repair unless an implementation bug is shown.")
    print(f"manifest -> {Path(args.run_dir) / sid / 'run_manifest.json'}")
    return 0 if man["pipeline_status"] == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
