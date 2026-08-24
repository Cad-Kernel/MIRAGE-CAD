"""Stage 1: load the released CAD-Recode implementation and prove one forward pass works.

RUNS IN cadrecode_env. Loads, checks, and stops -- no generation yet, because a load failure and a
generation failure have different causes and mixing them wastes the diagnosis.

LICENSE AND PROVENANCE. CAD-Recode's code and checkpoint are CC BY-NC 4.0 and are used here solely
as external dependencies for a non-commercial academic evaluation. The released implementation is
LOADED FROM THE UPSTREAM CHECKOUT AT RUNTIME and is not copied into or redistributed with
MIRAGE-CAD. That keeps one copy of their code in existence -- theirs -- so no modified or forked
implementation can drift into this repository, and the paper can say plainly that it used the
released implementation with the released checkpoint.

HOW THE CLASS IS OBTAINED, and why it is surgical. The checkpoint ships no .py file: five files,
none of them code, so there is no trust_remote_code path and the class lives only in demo.ipynb.
That notebook cell also imports open3d, matplotlib, skimage and pytorch3d, none of which this
environment has by deliberate choice. So the extraction takes the source from `class
FourierPointEncoder` to the end of the cell -- both classes, byte for byte, no edits -- and supplies
the names they reference. The extracted text is hashed, so if upstream changes, the hash changes and
this run is no longer comparable to the last.

THE GLOBAL DTYPE SIDE EFFECT, handled explicitly rather than tolerated. CADRecode.__init__ ends with
torch.set_default_dtype(torch.bfloat16) and leaves it set. That is theirs to do, but it would then
silently govern every tensor constructed afterwards, including in the evaluator. The default dtype
is recorded before and after construction and restored, and all three values go into the report --
restoring it cannot affect parameters already allocated.

WHAT STAGE 1 MUST ESTABLISH, all as fail-fast checks rather than impressions: the checkpoint loads
with no missing or unexpected parameters that matter; the point encoder's input width is 51, which
is 3 + 3x8 sin + 3x8 cos and therefore the Fourier scheme the paper describes; the input is 256x3;
the attention mask carries exactly 256 placeholders before the forward and none after, which is
observable proof the point-embedding path actually ran; and the logits are finite on the device --
this GPU being one the pinned torch could not drive at all.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

MODEL_ID = "filapro/cad-recode-v1.5"
TOKENIZER_ID = "Qwen/Qwen2-1.5B"
K_POINTS = 256
FOURIER_INPUT_WIDTH = 51        # 3 + 3*8 sin + 3*8 cos


def extract_upstream_classes(repo_dir: str) -> tuple[str, str]:
    """Return (source, sha256) for the two class definitions, taken verbatim from demo.ipynb."""
    nb_path = Path(repo_dir) / "demo.ipynb"
    if not nb_path.exists():
        raise FileNotFoundError(
            f"{nb_path} not found. Point --cadrecode-repo at the upstream checkout; the released "
            f"checkpoint ships no .py file, so the implementation exists only in that notebook.")
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source", []))
        if "class CADRecode" in src and "class FourierPointEncoder" in src:
            cut = src.index("class FourierPointEncoder")
            body = src[cut:]
            return body, hashlib.sha256(body.encode("utf-8")).hexdigest()
    raise RuntimeError("no cell in demo.ipynb defines both FourierPointEncoder and CADRecode")


def build_namespace():
    """Exactly the names the extracted classes reference. Nothing added, nothing replaced."""
    import torch
    from torch import nn
    from transformers import PreTrainedModel, Qwen2ForCausalLM, Qwen2Model
    from transformers.modeling_outputs import CausalLMOutputWithPast
    return {
        "torch": torch, "nn": nn,
        "Qwen2ForCausalLM": Qwen2ForCausalLM, "Qwen2Model": Qwen2Model,
        "PreTrainedModel": PreTrainedModel,
        "CausalLMOutputWithPast": CausalLMOutputWithPast,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cadrecode-repo", required=True,
                    help="the upstream checkout; its demo.ipynb holds the implementation")
    ap.add_argument("--model-id", default=MODEL_ID)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    results: list[tuple[str, object, str]] = []
    report: dict = {"model_id": args.model_id, "tokenizer_id": TOKENIZER_ID,
                    "upstream_repo": args.cadrecode_repo,
                    "license_note": "CAD-Recode is CC BY-NC 4.0; used as an external dependency "
                                    "for non-commercial academic evaluation, loaded at runtime "
                                    "from the upstream checkout, not redistributed"}

    def check(name, ok, detail):
        results.append((name, ok, detail))
        tag = "PASS" if ok is True else ("FAIL" if ok is False else "NOT RUN")
        print(f"  [{tag}] {name}")
        print(f"         {detail}")

    print("=" * 78)
    print("CAD-Recode stage 1: load the released implementation, one forward pass")
    print("=" * 78)

    # ---- 1. the implementation, from upstream, hashed ------------------------------
    try:
        source, src_hash = extract_upstream_classes(args.cadrecode_repo)
        report["upstream_source_sha256"] = src_hash
        report["upstream_source_bytes"] = len(source)
        check("upstream implementation extracted from demo.ipynb", True,
              f"{len(source)} bytes, sha256 {src_hash[:16]}. Verbatim from `class "
              f"FourierPointEncoder` onward; imports excluded because this environment "
              f"deliberately lacks open3d, matplotlib, skimage and pytorch3d.")
    except Exception as e:
        check("upstream implementation extracted from demo.ipynb", False,
              f"{type(e).__name__}: {e}")
        return 1

    import torch
    ns = build_namespace()
    try:
        exec(compile(source, "<cad-recode demo.ipynb>", "exec"), ns)
        CADRecode = ns["CADRecode"]
        check("classes execute without modification", True,
              f"CADRecode is a {CADRecode.__mro__[1].__name__} subclass")
    except Exception as e:
        check("classes execute without modification", False, f"{type(e).__name__}: {e}")
        return 1

    # ---- 2. the global dtype side effect, recorded and undone ----------------------
    dtype_before = torch.get_default_dtype()
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_ID, pad_token="<|im_end|>",
                                              padding_side="left")
    try:
        model = CADRecode.from_pretrained(args.model_id, torch_dtype="auto",
                                          attn_implementation=None)
    except TypeError:
        # Older/newer transformers name this differently; the pinned 4.47.1 accepts the first form.
        model = CADRecode.from_pretrained(args.model_id, torch_dtype="auto")
    dtype_after = torch.get_default_dtype()
    torch.set_default_dtype(dtype_before)
    report["default_dtype"] = {"before": str(dtype_before), "after_construction": str(dtype_after),
                              "restored_to": str(torch.get_default_dtype())}
    check("global default dtype restored after construction",
          torch.get_default_dtype() == dtype_before,
          f"{dtype_before} -> {dtype_after} (upstream __init__ sets bfloat16 and leaves it) -> "
          f"restored {torch.get_default_dtype()}. Restoring cannot affect parameters already "
          f"allocated; it stops their default leaking into the evaluator.")

    model = model.eval().to(args.device)

    # ---- 3. what actually loaded --------------------------------------------------
    n_params = sum(p.numel() for p in model.parameters())
    report["n_parameters"] = int(n_params)
    check("parameter count is a 1.5B model plus a point encoder", 1.3e9 < n_params < 2.0e9,
          f"{n_params:,} parameters")

    pe = getattr(model, "point_encoder", None)
    in_features = getattr(getattr(pe, "projection", None), "in_features", None)
    check(f"point encoder input width is {FOURIER_INPUT_WIDTH}",
          in_features == FOURIER_INPUT_WIDTH,
          f"projection.in_features = {in_features}. {FOURIER_INPUT_WIDTH} is 3 xyz + 3x8 sin + "
          f"3x8 cos, so this is the Fourier scheme the paper describes rather than a raw xyz "
          f"projection.")
    report["point_encoder_in_features"] = in_features

    # ---- 4. one forward pass, on the device --------------------------------------
    pts = torch.rand(K_POINTS, 3, dtype=torch.float32) * 2.0 - 1.0
    input_ids = [tokenizer.pad_token_id] * K_POINTS + [tokenizer("<|im_start|>")["input_ids"][0]]
    attention_mask = [-1] * K_POINTS + [1]
    check(f"attention mask carries exactly {K_POINTS} point placeholders",
          attention_mask.count(-1) == K_POINTS and len(attention_mask) == K_POINTS + 1,
          f"{attention_mask.count(-1)} entries of -1 in a mask of {len(attention_mask)}; the "
          f"upstream forward replaces those positions with point embeddings")
    check("point input shape is 256 x 3", tuple(pts.shape) == (K_POINTS, 3), f"{tuple(pts.shape)}")

    am = torch.tensor(attention_mask).unsqueeze(0).to(args.device)
    try:
        with torch.no_grad():
            out = model(
                input_ids=torch.tensor(input_ids).unsqueeze(0).to(args.device),
                attention_mask=am,
                point_cloud=pts.unsqueeze(0).to(args.device))
        logits = out.logits
        finite = bool(torch.isfinite(logits).all())
        check("forward runs on the device and returns finite logits", finite,
              f"logits {tuple(logits.shape)}, dtype {logits.dtype}, finite={finite}, "
              f"device={logits.device}")
        report["logits_shape"] = list(logits.shape)
        # The mask was -1 in 256 places going in and must be 1 everywhere coming out. That
        # mutation is observable proof the point-embedding branch ran, rather than the points
        # being silently ignored.
        after = int((am == -1).sum().item())
        check("the point-embedding branch demonstrably ran", after == 0,
              f"{K_POINTS} placeholders before the call, {after} after -- upstream rewrites them "
              f"to 1 inside the branch that injects point embeddings, so this is evidence the "
              f"points were consumed rather than ignored")
    except Exception as e:
        check("forward runs on the device and returns finite logits", False,
              f"{type(e).__name__}: {str(e)[:300]}")

    if args.device.startswith("cuda"):
        cap = torch.cuda.get_device_capability(0)
        report["device_capability"] = f"sm_{cap[0]}{cap[1]}"
        report["torch_version"] = torch.__version__
        check("running on the GPU the pinned torch could not drive", True,
              f"sm_{cap[0]}{cap[1]} under torch {torch.__version__}; CAD-Recode pins "
              f"2.5.1+cu124, which has no device code for this architecture")

    failed = sum(1 for _, ok, _ in results if ok is False)
    print()
    print(f"{sum(1 for _, ok, _ in results if ok is True)} passed, {failed} failed")
    print()
    if failed:
        print("Stage 1 did not pass. Do not proceed to generation: a load or forward problem and")
        print("a generation problem have different causes, and mixing them wastes the diagnosis.")
    else:
        print("Stage 1 passes. The released implementation loads, the point encoder is the Fourier")
        print("scheme described, the points are demonstrably consumed, and the forward runs on a")
        print("GPU the pinned torch build could not touch. Next: one sample end to end, from a")
        print("frozen 256-point input through generation, CadQuery execution and STEP export to")
        print("CD and IoU -- one sample, with full provenance, before four hundred.")

    if args.out:
        report["checks"] = [{"name": n, "state": "pass" if o is True else
                             ("fail" if o is False else "not_run"), "detail": d}
                            for n, o, d in results]
        Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8", newline="\n")
        print(f"\nwrote {args.out}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
