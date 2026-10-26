from __future__ import annotations

import re
from pathlib import Path

import numpy as np

from miragecad.data import load_step_brep_tensors


OP_TOKEN_PATTERN = re.compile(r"\bOP_[A-Z0-9]+(?:_[A-Z0-9]+)*\b")

# PART id and SEED are random per-sample identifiers with no construction semantics.
# They should not be scored as part of IR quality (cosine / op-F1 / LCS), and are
# stripped to a fixed placeholder before comparison.
_PART_ID_PATTERN = re.compile(r"(?m)^(PART\s+)\S+")
_SEED_PATTERN = re.compile(r"\bSEED\s+\S+")

COMPLEXITY_LABELS: list[str] = ["L1", "L2", "L3", "L4"]


def normalize_ir_text(text: str) -> str:
    """Replace random PART id / SEED fields with fixed placeholders.

    Keeps CAT and everything else untouched so semantic content still scores
    normally; only the two nuisance identifier fields are neutralized.
    """
    text = _PART_ID_PATTERN.sub(r"\1<PART_ID>", text)
    text = _SEED_PATTERN.sub("SEED <SEED>", text)
    return text


# --- IR grammar validity -------------------------------------------------
# `ir_cosine` / `op_set_f1` only measure semantic similarity and OP-token
# overlap; they don't catch outright grammar breakdown (e.g. the PART header
# degenerating into invented fields, or feature lines collapsing into
# repeated tokens / non-IR nested structures). This is a lightweight,
# deliberately loose structural check meant to flag gross malformation, not
# to enforce exact formatting.

_IR_PART_LINE = re.compile(r"^PART\s+\S+\s+CAT\s+\S+\s+UNITS\s+\S+\s+SEED\s+-?\d+\s*$")
_IR_PARAM_LINE = re.compile(
    r"^PARAM\s+\S+\s+-?[\d.]+\s+MIN\s+-?[\d.]+\s+MAX\s+-?[\d.]+(\s+EXPR\s+\S+)?\s+SEM\s+\S+\s*$"
)
_IR_F_LINE = re.compile(r"^F\s+\S+\s+OP_[A-Z0-9_]+\s+SEM\s+\S+\s+ROLE\s+\S+")
_IR_FORBIDDEN_SUBSTRINGS = ("[PLANE", "[CYLINDER", "[SPHERE", ", POINT ", "MIN_VERSION")


def validate_ir_grammar(text: str) -> dict:
    """Heuristically check whether `text` looks like well-formed Construction IR.

    Returns {"valid": bool, "issues": list[str]} — issues are deduplicated
    reason codes, not per-line detail (callers doing bulk stats care about
    which failure modes are present, not exact line numbers).
    """
    lines = [l for l in text.splitlines() if l.strip()]
    issues: set[str] = set()
    if not lines:
        return {"valid": False, "issues": ["empty"]}

    if not _IR_PART_LINE.match(lines[0].strip()):
        issues.add("bad_part_header")
    if lines[-1].strip() != "END":
        issues.add("missing_end")

    body = lines[1:-1] if lines[-1].strip() == "END" else lines[1:]
    for line in body:
        s = line.strip()
        if s.startswith("PARAM"):
            if not _IR_PARAM_LINE.match(s):
                issues.add("bad_param_line")
            if s.count(" MIN ") > 1 or s.count(" MAX ") > 1:
                issues.add("degenerate_repetition")
        elif s.startswith("F "):
            if not _IR_F_LINE.match(s):
                issues.add("bad_feature_line")
            if s.count(" MIN ") > 0 or s.count(" MAX ") > 0:
                # Feature lines never carry bare MIN/MAX tokens in well-formed
                # IR (those only belong on PARAM lines) — their presence here
                # is a strong signal of degenerate/garbled generation.
                issues.add("degenerate_repetition")
        else:
            issues.add("unknown_line_prefix")
        if any(bad in s for bad in _IR_FORBIDDEN_SUBSTRINGS):
            issues.add("forbidden_structure")

    return {"valid": not issues, "issues": sorted(issues)}


def get_observation_text(modality: str) -> str:
    labels = {
        "text": "Natural-language query encoded into the Construction-IR latent space.",
        "image": "CAD image query encoded into the Construction-IR latent space.",
        "point": "Surface point-cloud query encoded into the Construction-IR latent space.",
        "step": "STEP/B-Rep query encoded into the Construction-IR latent space.",
    }
    return labels.get(modality, "Query encoded into the Construction-IR latent space.")


def get_query_evidence(row: dict, modality: str, point_xyz: np.ndarray | None = None) -> str:
    """Return query-derived evidence only; no hidden IR/program/text leakage."""
    if modality == "text":
        return row.get("text", "")[:400]

    if modality == "image":
        return ""

    if modality == "point":
        if point_xyz is not None and len(point_xyz) > 0:
            n = len(point_xyz)
            mn = point_xyz.min(axis=0)
            mx = point_xyz.max(axis=0)
            centroid = point_xyz.mean(axis=0)
            std = point_xyz.std(axis=0)
            dx, dy, dz = float(mx[0] - mn[0]), float(mx[1] - mn[1]), float(mx[2] - mn[2])
            max_side = max(dx, dy, dz, 1e-8)
            centered = point_xyz - centroid
            try:
                cov = np.cov(centered.T)
                eigvals = np.linalg.eigvalsh(cov)
                eigvals = np.sort(np.maximum(eigvals, 0.0))[::-1]
                eig_sum = float(eigvals.sum()) or 1.0
                pca = eigvals / eig_sum
                pca_text = f"PCA ratios: {pca[0]:.2f}, {pca[1]:.2f}, {pca[2]:.2f}."
            except Exception:
                pca_text = "PCA ratios unavailable."
            return (
                f"Point cloud evidence: point_count={n}. "
                f"bbox_size={dx:.3f}, {dy:.3f}, {dz:.3f}. "
                f"bbox_ratios={dx/max_side:.3f}, {dy/max_side:.3f}, {dz/max_side:.3f}. "
                f"centroid={centroid[0]:.3f}, {centroid[1]:.3f}, {centroid[2]:.3f}. "
                f"std_xyz={std[0]:.3f}, {std[1]:.3f}, {std[2]:.3f}. "
                f"{pca_text}"
            )
        return "Point cloud query."

    if modality == "step":
        step_feature_path = row.get("step_feature_path")
        if not step_feature_path:
            return "STEP/B-Rep query."
        try:
            tensors = load_step_brep_tensors(step_feature_path)
            g = tensors["global"]
            brep_valid = bool(g[0] > 0.5)
            face_count = float(np.expm1(g[3]))
            edge_count = float(np.expm1(g[5]))
            dx = float(np.expm1(g[7]))
            dy = float(np.expm1(g[8]))
            dz = float(np.expm1(g[9]))
            area = float(np.expm1(g[10]))
            volume = float(np.expm1(g[11]))
            planar_count = float(np.expm1(g[12]))
            cyl_count = float(np.expm1(g[13]))
            cone_count = float(np.expm1(g[14]))
            curve_line = float(np.expm1(g[23]))
            curve_circle = float(np.expm1(g[24]))
            valid_str = "valid" if brep_valid else "invalid"
            return (
                f"STEP/B-Rep evidence: validity={valid_str}. "
                f"bbox_size={dx:.3f}, {dy:.3f}, {dz:.3f}. "
                f"face_count={face_count:.0f}; edge_count={edge_count:.0f}. "
                f"surface_counts: plane={planar_count:.0f}, cylinder={cyl_count:.0f}, cone={cone_count:.0f}. "
                f"curve_counts: line={curve_line:.0f}, circle={curve_circle:.0f}. "
                f"area={area:.3f}; volume={volume:.3f}."
            )
        except Exception:
            return "STEP/B-Rep query."

    return ""


def get_geometry_summary(row: dict, modality: str, point_xyz: np.ndarray | None = None) -> str:
    return get_query_evidence(row, modality, point_xyz=point_xyz)


def build_ir_prompt(
    row: dict,
    modality: str,
    evidence_text: str | None = None,
    retrieved_ir: list[dict] | None = None,
    point_xyz: np.ndarray | None = None,
) -> str:
    assert modality in {"text", "image", "point", "step"}, f"Unknown modality: {modality!r}"
    evidence = get_query_evidence(row, modality, point_xyz=point_xyz) if evidence_text is None else evidence_text
    blocks: list[str] = [
        "You are a CAD construction planner.\n"
        "Generate a concise Construction IR plan for an editable Flluma CAD model.\n"
        "Do not output Python code.",
        f"Input modality: {modality}",
    ]
    if evidence:
        blocks.append("Query-derived evidence:\n" + evidence)
    if retrieved_ir:
        ex_lines = ["Optional reference IR examples:"]
        for i, item in enumerate(retrieved_ir[:3], start=1):
            ex_lines.append(f"Example {i}:")
            ex_lines.append(str(item.get("ir", ""))[:1200])
        blocks.append("\n".join(ex_lines))
    blocks.append("Output Construction IR:")
    return "\n\n".join(blocks)


def build_program_prompt(
    row: dict,
    modality: str,
    predicted_ir: str,
    retrieved_programs: list[dict] | None = None,
    point_xyz: np.ndarray | None = None,
    evidence_text: str | None = None,
    include_plan: bool = True,
) -> str:
    """Build the LoRA-Code prompt.

    include_plan=False removes the construction plan entirely -- both the plan block and
    the instruction line telling the model to use it, since an instruction referring to a
    block that is not there would be its own confound. This is the no-plan ablation: it
    asks whether the plan-mediated pathway earns its place against fine-tuning a code
    model directly on the query. Note that it removes the plan AND, transitively, every
    trace of the query encoder -- what remains is the observation block. So it ablates
    the pathway as a whole, not the plan text in isolation.

    The default reproduces every published prompt byte-for-byte.
    """
    assert modality in {"text", "image", "point", "step"}, f"Unknown modality: {modality!r}"
    evidence = get_query_evidence(row, modality, point_xyz=point_xyz) if evidence_text is None else evidence_text
    if include_plan:
        blocks: list[str] = [
            "Generate an executable Flluma Python CAD program.\n"
            "Use the Construction IR plan as the primary guide.\n"
            "The program must define a variable named `part`.",
            f"Input modality: {modality}",
            "Construction IR plan:\n" + predicted_ir,
        ]
    else:
        blocks = [
            "Generate an executable Flluma Python CAD program.\n"
            "The program must define a variable named `part`.",
            f"Input modality: {modality}",
        ]
    if evidence:
        blocks.append("Query-derived evidence:\n" + evidence)
    if retrieved_programs:
        ex_lines = ["Retrieved program examples:"]
        for i, item in enumerate(retrieved_programs[:3], start=1):
            ir_snippet = str(item.get("ir", ""))[:600]
            prog_snippet = str(item.get("program", ""))[:1000]
            ex_lines.append(f"Example {i}:")
            if ir_snippet:
                ex_lines.append("IR:")
                ex_lines.append(ir_snippet)
            if prog_snippet:
                ex_lines.append("Program:")
                ex_lines.append(prog_snippet)
        blocks.append("\n".join(ex_lines))
    blocks.append("Output executable Flluma Python program:")
    return "\n\n".join(blocks)


def extract_operation_types(text: str) -> list[str]:
    return OP_TOKEN_PATTERN.findall(text.upper())
