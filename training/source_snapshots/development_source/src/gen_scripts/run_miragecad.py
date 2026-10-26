"""Unified MIRAGE-CAD-Gen inference script.

Pipeline modes:
  A. direct_rag        - z_m -> direct retrieval -> LoRA-Code
  B. prior_rag         - z_m -> prior -> z_ir_hat -> prior/rerank retrieval -> LoRA-Code
  C. gen_ir            - z_ir_hat -> soft prefix (no retrieval) -> LoRA-IR -> LoRA-Code
  D. gen_ir_retrieval  - z_ir_hat -> soft prefix + retrieval -> LoRA-IR -> LoRA-Code
  E. full              - D + N candidates + Flluma execution selection

LoRA adapters are loaded sequentially for gen pipelines to respect 16 GB VRAM budget:
  Pass 1: encode all rows, generate predicted_ir via LoRA-IR, unload LoRA-IR.
  Pass 2: load LoRA-Code, generate programs for all rows.
"""
from __future__ import annotations

import argparse
import ast
import gc
import json
import math
import os
import random
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from peft import PeftModel
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer

from miragecad.data import (
    build_generation_prompt,
    load_image,
    load_step_brep_tensors,
    read_jsonl,
    read_text,
)
from miragecad.gen_prompts import (
    build_program_prompt,
    build_ir_prompt,
    get_observation_text,
)
from miragecad.soft_prefix import load_soft_prefix_adapter, resolve_soft_prefix_path
from miragecad.latent_prior import LatentPrior, LatentPriorConfig
from miragecad.models import load_alignment_checkpoint
from miragecad.point_sampling import load_point_cloud_sampled


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="MIRAGE-CAD-Gen unified inference.")
    p.add_argument("--pipeline", choices=["direct_rag", "prior_rag", "gen_ir", "gen_ir_retrieval", "full"], required=True)
    p.add_argument("--modality", choices=["text", "image", "point", "step"], required=True)
    p.add_argument("--alignment-checkpoint", type=Path, required=True)
    p.add_argument("--prior-checkpoint", type=Path, required=True)
    p.add_argument("--retrieval-index", type=Path, default=None)
    p.add_argument("--lora-ir-dir", type=Path, default=None)
    p.add_argument("--lora-code-dir", type=Path, required=True)
    p.add_argument("--soft-prefix-checkpoint", type=Path, default=None)
    p.add_argument("--model-name", default="Qwen/Qwen2.5-Coder-1.5B")
    p.add_argument("--input-jsonl", type=Path, required=True)
    p.add_argument("--output-jsonl", type=Path, required=True)
    p.add_argument("--retrieval-mode", choices=["direct", "prior", "rerank"], default="prior")
    p.add_argument("--rerank-alpha", type=float, default=0.75,
                   help="Rerank blending weight: score = (1-alpha)*direct + alpha*prior. Ablate in {0,0.25,0.5,0.75,1}.")
    p.add_argument("--candidate-pool", type=int, default=128)
    p.add_argument("--retrieval-top-k", type=int, default=3)
    p.add_argument("--num-candidates", type=int, default=1)
    p.add_argument("--execution-selection", action="store_true", help="Only valid for full + point/step.")
    p.add_argument("--point-count", type=int, default=1024)
    p.add_argument("--eval-point-sampling", choices=["random", "fps", "hybrid"], default="fps")
    p.add_argument("--max-length", type=int, default=2048)
    p.add_argument("--max-new-tokens", type=int, default=1024)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--top-p", type=float, default=1.0)
    p.add_argument("--bf16", action="store_true")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def validate_args(args: argparse.Namespace) -> str | None:
    if args.pipeline in ("gen_ir", "gen_ir_retrieval", "full") and not args.lora_ir_dir:
        return f"--lora-ir-dir is required for pipeline={args.pipeline}"
    if args.pipeline in ("gen_ir_retrieval", "full") and not args.retrieval_index:
        return f"--retrieval-index is required for pipeline={args.pipeline}"
    if args.pipeline in ("direct_rag", "prior_rag") and not args.retrieval_index:
        return f"--retrieval-index is required for pipeline={args.pipeline}"
    return None


def load_prior(path: Path, device: torch.device) -> LatentPrior:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    cfg = payload["config"]
    if "modality" not in cfg:
        raise ValueError(f"Prior checkpoint {path} is missing 'modality' in config. Re-save with updated train_latent_prior.py.")
    config = LatentPriorConfig(**cfg)
    prior = LatentPrior(config)
    prior.load_state_dict(payload["state_dict"], strict=True)
    return prior.to(device).eval()


def load_lm(model_name: str, adapter_dir: Path, dtype, device: torch.device):
    model_kwargs: dict[str, Any] = {"trust_remote_code": True}
    if dtype is not None:
        model_kwargs["torch_dtype"] = dtype
    base = AutoModelForCausalLM.from_pretrained(model_name, **model_kwargs)
    model = PeftModel.from_pretrained(base, adapter_dir)
    return model.to(device).eval()


def unload_lm() -> None:
    # Caller must `del` the model binding before calling this; only handles gc + cache.
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


@torch.no_grad()
def encode_query(row: dict, modality: str, aligner, prior: LatentPrior, args: argparse.Namespace, device: torch.device) -> tuple[np.ndarray, np.ndarray]:
    if modality == "text":
        z_m = aligner.encode_text([row.get("text", "")], device)
    elif modality == "image":
        img = load_image(row["iso_image_path"])
        z_m = aligner.encode_image([img], device)
    elif modality == "step":
        tensors = load_step_brep_tensors(row["step_feature_path"], strict=True)
        batch = {k: torch.tensor(v[None], dtype=torch.float32).to(device) for k, v in tensors.items()}
        z_m = aligner.encode_step(batch)
    elif modality == "point":
        pts = load_point_cloud_sampled(
            row["point_path"],
            point_count=args.point_count,
            sampling=args.eval_point_sampling,
            seed=args.seed,
        )
        z_m = aligner.encode_point(torch.tensor(pts[None], dtype=torch.float32).to(device))
    else:
        raise ValueError(modality)
    z_ir_hat = prior(z_m)
    return z_m.cpu().numpy()[0], z_ir_hat.cpu().numpy()[0]


def retrieve_candidates(index, z_direct: np.ndarray, z_prior: np.ndarray, args: argparse.Namespace) -> tuple[list[int], list[str]]:
    embeddings = index["embeddings"]
    if args.retrieval_mode == "direct":
        scores = embeddings @ z_direct
        order = np.argsort(-scores)[: args.retrieval_top_k]
    elif args.retrieval_mode == "prior":
        scores = embeddings @ z_prior
        order = np.argsort(-scores)[: args.retrieval_top_k]
    else:  # rerank — blended score: (1-alpha)*direct + alpha*prior
        direct_scores = embeddings @ z_direct
        pool = np.argsort(-direct_scores)[: args.candidate_pool]
        alpha = args.rerank_alpha
        blended = (1.0 - alpha) * direct_scores[pool] + alpha * (embeddings[pool] @ z_prior)
        order = pool[np.argsort(-blended)[: args.retrieval_top_k]]
    return list(order), [str(index["sample_ids"][i]) for i in order]


def build_retrieved_examples(index, order: list[int], row: dict) -> list[dict]:
    dataset_root = Path(row.get("dataset_root", "."))
    out: list[dict] = []
    for i in order:
        relpath = str(index["relpaths"][i])
        sample_dir = dataset_root / relpath
        out.append({
            "sample_id": str(index["sample_ids"][i]),
            "text": str(index["texts"][i]) if "texts" in index else "",
            "ir": read_text(sample_dir / "training_ir.txt"),
            "program": read_text(sample_dir / "program.py"),
        })
    return out


def load_point_xyz(row: dict, args: argparse.Namespace) -> np.ndarray | None:
    if args.modality != "point":
        return None
    try:
        return load_point_cloud_sampled(
            row["point_path"],
            point_count=args.point_count,
            sampling=args.eval_point_sampling,
            seed=args.seed,
        )
    except Exception:
        return None


def generate_text(model, tokenizer, prompt: str, max_length: int, max_new_tokens: int, temperature: float, top_p: float, device: torch.device, repetition_penalty: float = None) -> str:
    inputs = tokenizer(prompt, truncation=True, max_length=max_length, return_tensors="pt").to(device)
    do_sample = temperature > 0
    gen_kwargs = dict(
        max_new_tokens=max_new_tokens,
        do_sample=do_sample,
        temperature=temperature if do_sample else None,
        top_p=top_p if do_sample else None,
        pad_token_id=tokenizer.eos_token_id,
    )
    if repetition_penalty is not None:
        gen_kwargs["repetition_penalty"] = repetition_penalty
    with torch.no_grad():
        gen = model.generate(**inputs, **gen_kwargs)
    return tokenizer.decode(gen[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()


def generate_text_batch(model, tokenizer, prompts: list, max_length: int, max_new_tokens: int, temperature: float, top_p: float, device: torch.device, repetition_penalty: float = None) -> list:
    """Batched version of generate_text -- same greedy (temperature=0) semantics,
    processes `prompts` as one batch instead of one sequential call per prompt.
    Requires left-padding so every row's generated continuation starts at the
    same tensor column regardless of that row's original prompt length.
    """
    prev_padding_side = tokenizer.padding_side
    tokenizer.padding_side = "left"
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    try:
        inputs = tokenizer(prompts, truncation=True, max_length=max_length, padding=True, return_tensors="pt").to(device)
    finally:
        tokenizer.padding_side = prev_padding_side
    do_sample = temperature > 0
    gen_kwargs = dict(
        max_new_tokens=max_new_tokens,
        do_sample=do_sample,
        temperature=temperature if do_sample else None,
        top_p=top_p if do_sample else None,
        pad_token_id=tokenizer.eos_token_id,
    )
    if repetition_penalty is not None:
        gen_kwargs["repetition_penalty"] = repetition_penalty
    with torch.no_grad():
        gen = model.generate(**inputs, **gen_kwargs)
    prompt_len = inputs["input_ids"].shape[1]
    return [tokenizer.decode(row[prompt_len:], skip_special_tokens=True).strip() for row in gen]


def generate_text_with_soft_prefix(
    model,
    tokenizer,
    prefix_adapter,
    z_ir_hat: np.ndarray,
    prompt: str,
    max_length: int,
    max_new_tokens: int,
    device: torch.device,
) -> str:
    inputs = tokenizer(prompt, truncation=True, max_length=max_length, return_tensors="pt").to(device)
    text_embeds = model.get_input_embeddings()(inputs["input_ids"])
    z_tensor = torch.tensor(z_ir_hat[None], dtype=torch.float32, device=device)
    soft_prefix = prefix_adapter(z_tensor).to(device=text_embeds.device, dtype=text_embeds.dtype)
    inputs_embeds = torch.cat([soft_prefix, text_embeds], dim=1)
    prefix_mask = torch.ones(
        inputs["attention_mask"].shape[0],
        soft_prefix.shape[1],
        dtype=inputs["attention_mask"].dtype,
        device=device,
    )
    attention_mask = torch.cat([prefix_mask, inputs["attention_mask"]], dim=1)
    with torch.no_grad():
        gen = model.generate(
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    return tokenizer.decode(gen[0], skip_special_tokens=True).strip()


# ─── Execution-guided candidate selection (architecture §16 Steps 8–10) ───────

# Validity levels: each gate is a prerequisite for the next.
_V_SYNTAX = 1   # ast.parse succeeds
_V_EXEC   = 2   # exec runs, `part` variable defined
_V_BUILD  = 3   # solid built via part.build()
_V_SOLID  = 4   # part.validate() passes
_V_STEP   = 5   # STEP file exported via part.export_step()
_V_SCORED = 6   # point cloud sampled, CD + 0.1*bbox_err computed


def _flluma_exec_namespace() -> dict[str, Any]:
    """Build the exec() namespace generated Flluma programs run in.

    `Parameters`/`Part`/primitives (box, cylinder, ...) are top-level
    attributes of the native `flluma` module, not something generated
    programs import — the Flluma harness injects them instead. This only
    works inside FllumaCLI.exe's embedded Python; a plain venv/conda
    interpreter cannot `import flluma` at all, so failure here is fatal,
    not something to silently fall back from.
    """
    import flluma  # type: ignore

    return {name: getattr(flluma, name) for name in dir(flluma) if not name.startswith("_")}


@dataclass
class _CandResult:
    idx: int
    validity: int = 0
    syntax_ok: bool = False
    build_ok: bool = False
    solid_valid: bool = False
    step_export_ok: bool = False
    scored: bool = False
    cd: float = math.nan
    bbox_err: float = math.nan
    score: float = math.inf     # CD + 0.1*bbox_err; inf until scored
    error: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        for k in ("cd", "bbox_err", "score"):
            v = d[k]
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                d[k] = None
        return d


def _symmetric_chamfer(P: np.ndarray, Q: np.ndarray) -> float:
    """Symmetric squared Chamfer distance (architecture §16)."""
    try:
        from scipy.spatial import cKDTree
        d_PQ, _ = cKDTree(Q).query(P)
        d_QP, _ = cKDTree(P).query(Q)
        return float(0.5 * np.mean(d_PQ ** 2) + 0.5 * np.mean(d_QP ** 2))
    except ImportError:
        # O(N·M) numpy fallback — safe for N,M ≤ ~512
        d2_PQ = ((P[:, None, :] - Q[None, :, :]) ** 2).sum(-1)
        d2_QP = ((Q[:, None, :] - P[None, :, :]) ** 2).sum(-1)
        return float(0.5 * d2_PQ.min(1).mean() + 0.5 * d2_QP.min(1).mean())


def _bbox_error(P: np.ndarray, Q: np.ndarray) -> float:
    return float(np.mean(np.abs((P.max(0) - P.min(0)) - (Q.max(0) - Q.min(0)))))


def _sample_step(step_path: str, n: int = 1024) -> np.ndarray | None:
    """Sample n FPS points from a STEP file. Tries flluma, then OCC."""
    try:
        import flluma  # type: ignore
        arr = np.array(flluma.sample_point_cloud(step_path, n=n), dtype=np.float32)
        return arr if len(arr) > 0 else None
    except Exception:
        pass
    try:
        from OCC.Core.STEPControl import STEPControl_Reader
        from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
        from OCC.Core.BRep import BRep_Tool
        from OCC.Core.TopExp import TopExp_Explorer
        from OCC.Core.TopAbs import TopAbs_FACE

        reader = STEPControl_Reader()
        if reader.ReadFile(step_path) != 1:
            return None
        reader.TransferRoots()
        shape = reader.OneShape()
        BRepMesh_IncrementalMesh(shape, 0.1).Perform()
        pts: list[list[float]] = []
        exp = TopExp_Explorer(shape, TopAbs_FACE)
        while exp.More():
            face = exp.Current()
            tri, _ = BRep_Tool.Triangulation_s(face, face.Location())
            if tri is not None:
                for i in range(1, tri.NbNodes() + 1):
                    node = tri.Node(i)
                    pts.append([node.X(), node.Y(), node.Z()])
            exp.Next()
        if not pts:
            return None
        arr = np.array(pts, dtype=np.float32)
        if len(arr) > n:
            arr = arr[np.random.choice(len(arr), n, replace=False)]
        return arr
    except Exception:
        return None


def _load_target_points(
    row: dict,
    modality: str,
    point_xyz: np.ndarray | None,
    point_count: int,
) -> np.ndarray | None:
    """Return [N, 3] float32 P_target for geometry comparison, or None."""
    if modality == "point":
        if point_xyz is not None and len(point_xyz) > 0:
            return point_xyz[:point_count].astype(np.float32)
        point_path = row.get("point_path", "")
        if point_path and Path(point_path).exists():
            try:
                from miragecad.point_sampling import load_point_cloud_sampled
                return load_point_cloud_sampled(point_path, point_count=point_count, sampling="fps").astype(np.float32)
            except Exception:
                return None
        return None
    if modality == "step":
        step_path = row.get("step_path", "")
        if step_path and Path(step_path).exists():
            return _sample_step(step_path, n=point_count)
        return None
    # text / image: no geometry input, cannot score
    return None


def _evaluate_one(
    code: str,
    P_target: np.ndarray | None,
    point_count: int,
) -> _CandResult:
    """Run one candidate through the §16 Step 8 pipeline and return its result."""
    res = _CandResult(idx=-1)

    # Gate 1: syntax
    try:
        ast.parse(code)
    except SyntaxError as exc:
        res.error = f"SyntaxError: {exc}"
        return res
    res.syntax_ok = True
    res.validity = _V_SYNTAX

    # `import flluma` only succeeds inside FllumaCLI.exe's embedded Python.
    # This is a hard prerequisite for every remaining gate — fail loudly and
    # immediately rather than falling back to nonexistent alternate APIs.
    try:
        ns = _flluma_exec_namespace()
    except ImportError as exc:
        raise RuntimeError(
            "_evaluate_one requires the native `flluma` module (run via FllumaCLI.exe); "
            f"got ImportError: {exc}"
        ) from exc

    # Gate 2: execute, must define `part`
    try:
        exec(compile(code, "<candidate>", "exec"), ns)  # noqa: S102
        part = ns.get("part")
        if part is None:
            res.error = "no `part` variable after execution"
            return res
    except Exception as exc:
        res.error = f"exec error: {exc}"
        return res
    res.validity = _V_EXEC

    # Gate 3: build solid — `Part.build()` is an instance method; there is no
    # top-level `flluma.build()`.
    try:
        part.build()
    except Exception as exc:
        res.error = f"build error: {exc}"
        return res
    res.build_ok = True
    res.validity = _V_BUILD

    # Gate 4: validate — `Part.validate()` is an instance method; there is no
    # top-level `flluma.is_valid()`.
    try:
        if part.validate() is False:
            res.error = "part failed geometric validity check"
            return res
    except Exception as exc:
        res.error = f"validity check error: {exc}"
        return res
    res.solid_valid = True
    res.validity = _V_SOLID

    # Gate 5: export STEP — `Part.export_step()` is an instance method; there
    # is no top-level `flluma.export_step()`.
    with tempfile.TemporaryDirectory() as tmpdir:
        step_out = os.path.join(tmpdir, "candidate.step")
        try:
            part.export_step(step_out)
        except Exception as exc:
            res.error = f"STEP export error: {exc}"
            return res
        res.step_export_ok = True
        res.validity = _V_STEP

        # Gate 6: sample generated point cloud and score
        if P_target is None:
            # No geometry target (text/image input) — record validity only
            return res
        P_gen = _sample_step(step_out, n=point_count)
        if P_gen is None or len(P_gen) == 0:
            res.error = "point cloud sampling failed on generated STEP"
            return res
        res.scored = True
        res.validity = _V_SCORED
        res.cd = _symmetric_chamfer(P_gen, P_target)
        res.bbox_err = _bbox_error(P_gen, P_target)
        res.score = res.cd + 0.1 * res.bbox_err

    return res


def select_best_candidate(
    candidates: list[str],
    row: dict,
    modality: str,
    point_xyz: np.ndarray | None = None,
    point_count: int = 1024,
) -> tuple[int, list[dict]]:
    """Score all candidates and return (best_idx, list-of-result-dicts).

    Selection priority (architecture §16 Step 10):
      1. Fully scored (V_SCORED): pick lowest score = CD + 0.1*bbox_err.
      2. Partial validity: pick highest validity level (best partial effort).
      3. All syntax-invalid: fall back to index 0.
    Results are always len(candidates) long for paper-reporting purposes.
    """
    if not candidates:
        return 0, []
    P_target = _load_target_points(row, modality, point_xyz, point_count)
    results: list[_CandResult] = []
    for i, code in enumerate(candidates):
        r = _evaluate_one(code, P_target, point_count)
        r.idx = i
        results.append(r)
    scored = [r for r in results if r.validity == _V_SCORED]
    if scored:
        best = min(scored, key=lambda r: r.score)
        return best.idx, [r.to_dict() for r in results]
    partial = [r for r in results if r.validity > 0]
    if partial:
        best = max(partial, key=lambda r: r.validity)
        return best.idx, [r.to_dict() for r in results]
    return 0, [r.to_dict() for r in results]


def load_tokenizer(adapter_dir: Path) -> AutoTokenizer:
    tok = AutoTokenizer.from_pretrained(adapter_dir, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    return tok


def main() -> int:
    args = parse_args()

    # direct_rag must use direct retrieval (by z_m); prior_rag must NOT use direct
    if args.pipeline == "direct_rag":
        args.retrieval_mode = "direct"
    elif args.pipeline == "prior_rag" and args.retrieval_mode == "direct":
        print("WARNING: prior_rag pipeline with --retrieval-mode direct overridden to 'prior'.")
        args.retrieval_mode = "prior"

    err = validate_args(args)
    if err:
        print(f"ERROR: {err}")
        return 1

    torch.manual_seed(args.seed)
    random.seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dtype = torch.bfloat16 if args.bf16 else None

    aligner, _, _, _ = load_alignment_checkpoint(args.alignment_checkpoint, map_location="cpu")
    aligner.to(device).eval()
    prior = load_prior(args.prior_checkpoint, device)

    index = None
    if args.retrieval_index and args.retrieval_index.exists():
        index = np.load(args.retrieval_index, allow_pickle=True)


    rows = read_jsonl(args.input_jsonl)
    if args.limit:
        rows = rows[: args.limit]

    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    is_gen = args.pipeline in ("gen_ir", "gen_ir_retrieval", "full")

    if is_gen:
        # --- Pass 1: encode + retrieve + generate predicted_ir via LoRA-IR ---
        lora_ir = load_lm(args.model_name, args.lora_ir_dir, dtype, device)
        lora_ir_tok = load_tokenizer(args.lora_ir_dir)
        prefix_path = resolve_soft_prefix_path(args.lora_ir_dir, args.soft_prefix_checkpoint)
        prefix_adapter = load_soft_prefix_adapter(prefix_path, device=device, dtype=dtype)

        # Cache per-row state (z_ir_hat, retrieved examples, point_xyz)
        row_states: list[dict] = []
        predicted_irs: list[str] = []

        for row in tqdm(rows, desc="pass1-encode+ir"):
            try:
                z_direct, z_ir_hat = encode_query(row, args.modality, aligner, prior, args, device)
            except Exception as e:
                print(f"WARNING: encoding failed for {row.get('sample_id', '?')}: {e}. Skipping row.")
                row_states.append(None)
                predicted_irs.append("")
                continue

            point_xyz = load_point_xyz(row, args)

            retrieved_ids: list[str] = []
            retrieved_examples: list[dict] = []
            # gen_ir (C) must NOT access the retrieval index
            if index is not None and args.pipeline != "gen_ir":
                order, retrieved_ids = retrieve_candidates(index, z_direct, z_ir_hat, args)
                retrieved_examples = build_retrieved_examples(index, order, row)

            ir_retrieved = [{"ir": e["ir"]} for e in retrieved_examples] if retrieved_examples else None
            ir_prompt = build_ir_prompt(
                row, args.modality,
                retrieved_ir=ir_retrieved,
                point_xyz=point_xyz,
            )
            # IR generation is always greedy and conditioned by soft prefix embeddings.
            predicted_ir = generate_text_with_soft_prefix(
                lora_ir, lora_ir_tok, prefix_adapter, z_ir_hat, ir_prompt, args.max_length, args.max_new_tokens, device
            )

            row_states.append({
                "z_ir_hat": z_ir_hat,
                "point_xyz": point_xyz,
                "retrieved_ids": retrieved_ids,
                "retrieved_examples": retrieved_examples,
            })
            predicted_irs.append(predicted_ir)

        assert len(row_states) == len(predicted_irs) == len(rows), (
            f"Pass 1 incomplete: rows={len(rows)}, row_states={len(row_states)}, predicted_irs={len(predicted_irs)}"
        )

        # Unload LoRA-IR before loading LoRA-Code to free VRAM
        del lora_ir, lora_ir_tok, prefix_adapter
        unload_lm()

        # --- Pass 2: generate programs via LoRA-Code ---
        lora_code = load_lm(args.model_name, args.lora_code_dir, dtype, device)
        lora_code_tok = load_tokenizer(args.lora_code_dir)

        with open(args.output_jsonl, "w", encoding="utf-8", newline="\n") as f_out:
            for row, state, predicted_ir in tqdm(
                zip(rows, row_states, predicted_irs), desc="pass2-lora-code", total=len(rows)
            ):
                if state is None:
                    continue  # row failed in Pass 1
                prog_retrieved = state["retrieved_examples"] if args.pipeline != "gen_ir" else None
                prog_prompt = build_program_prompt(
                    row, args.modality, predicted_ir,
                    retrieved_programs=prog_retrieved,
                    point_xyz=state["point_xyz"],
                )

                if args.pipeline == "full" and args.num_candidates > 1:
                    candidates: list[str] = []
                    # Candidate 0 always greedy; rest sampled
                    candidates.append(generate_text(lora_code, lora_code_tok, prog_prompt, args.max_length, args.max_new_tokens, 0.0, 1.0, device))
                    for _ in range(args.num_candidates - 1):
                        t = args.temperature if args.temperature > 0 else 0.8
                        candidates.append(generate_text(lora_code, lora_code_tok, prog_prompt, args.max_length, args.max_new_tokens, t, args.top_p, device))
                    if args.execution_selection:
                        best_idx, candidate_results = select_best_candidate(
                            candidates, row, args.modality,
                            point_xyz=state["point_xyz"],
                            point_count=args.point_count,
                        )
                    else:
                        best_idx, candidate_results = 0, []
                    prediction = candidates[best_idx]
                    all_candidates = candidates
                else:
                    prediction = generate_text(lora_code, lora_code_tok, prog_prompt, args.max_length, args.max_new_tokens, args.temperature, args.top_p, device)
                    all_candidates = [prediction]
                    candidate_results = []

                out = {
                    "sample_id": row.get("sample_id", ""),
                    "modality": args.modality,
                    "pipeline": args.pipeline,
                    "predicted_ir": predicted_ir,
                    "reference_ir": read_text(row.get("ir_path", "")),
                    "prediction": prediction,
                    "all_candidates": all_candidates,
                    "candidate_results": candidate_results,
                    "reference": read_text(row.get("program_path", "")),
                    "retrieved": state["retrieved_ids"],
                    "retrieval_mode": args.retrieval_mode,
                }
                f_out.write(json.dumps(out, ensure_ascii=False) + "\n")

    else:
        # Lite pipelines (direct_rag, prior_rag): single LoRA-Code pass
        lora_code = load_lm(args.model_name, args.lora_code_dir, dtype, device)
        lora_code_tok = load_tokenizer(args.lora_code_dir)

        with open(args.output_jsonl, "w", encoding="utf-8", newline="\n") as f_out:
            for row in tqdm(rows, desc=f"miragecad-{args.pipeline}"):
                z_direct, z_ir_hat = encode_query(row, args.modality, aligner, prior, args, device)

                retrieved_ids: list[str] = []
                retrieved_examples: list[dict] = []
                if index is not None:
                    order, retrieved_ids = retrieve_candidates(index, z_direct, z_ir_hat, args)
                    retrieved_examples = build_retrieved_examples(index, order, row)

                prompt_row = dict(row)
                prompt_row["target_observation"] = get_observation_text(args.modality)
                prompt = build_generation_prompt(prompt_row, target="program", retrieved=retrieved_examples)
                prediction = generate_text(lora_code, lora_code_tok, prompt, args.max_length, args.max_new_tokens, args.temperature, args.top_p, device)

                out = {
                    "sample_id": row.get("sample_id", ""),
                    "modality": args.modality,
                    "pipeline": args.pipeline,
                    "predicted_ir": None,
                    "prediction": prediction,
                    "all_candidates": [prediction],
                    "reference": read_text(row.get("program_path", "")),
                    "retrieved": retrieved_ids,
                    "retrieval_mode": args.retrieval_mode,
                }
                f_out.write(json.dumps(out, ensure_ascii=False) + "\n")

    print(f"Wrote predictions: {args.output_jsonl}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
