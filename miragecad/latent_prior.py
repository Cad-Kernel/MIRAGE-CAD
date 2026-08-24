"""Latent-prior modules for MIRAGE-CAD.

MIRAGE-CAD predicts the Construction-IR latent from a query modality:

    z_modality -> Prior_m -> z_ir_hat

The predicted IR latent is then used for retrieval/reranking and for
soft-prefix conditioning of LoRA-IR through Qwen input embeddings.
"""
from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn


@dataclass
class LatentPriorConfig:
    modality: str
    embed_dim: int = 512
    hidden_dim: int = 512
    dropout: float = 0.05


class ResidualMLPBlock(nn.Module):
    def __init__(self, dim: int, dropout: float = 0.05):
        super().__init__()
        self.net = nn.Sequential(
            nn.LayerNorm(dim),
            nn.Linear(dim, dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(dim, dim),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.net(x)


class LatentPrior(nn.Module):
    """Small deterministic prior from modality latent to IR latent."""

    def __init__(self, config: LatentPriorConfig):
        super().__init__()
        self.config = config
        self.net = nn.Sequential(
            nn.LayerNorm(config.embed_dim),
            nn.Linear(config.embed_dim, config.hidden_dim),
            nn.GELU(),
            ResidualMLPBlock(config.hidden_dim, config.dropout),
            nn.LayerNorm(config.hidden_dim),
            nn.Linear(config.hidden_dim, config.embed_dim),
        )

    def forward(self, z_modality: torch.Tensor) -> torch.Tensor:
        return nn.functional.normalize(self.net(z_modality), dim=-1)


def prior_losses(
    z_pred: torch.Tensor,
    z_ir: torch.Tensor,
    temperature: float = 0.07,
    lambda_l2: float = 1.0,
    lambda_cos: float = 1.0,
    lambda_nce: float = 1.0,
) -> dict[str, torch.Tensor]:
    """Return L2, cosine, InfoNCE, and total latent-prior losses.

    All three weights default to 1.0 because that is what every released
    checkpoint was trained with. This default was 0.1 for lambda_l2, on the
    argument that both vectors are already L2-normalised so cosine alignment and
    InfoNCE discriminability should outweigh raw Euclidean distance -- but
    train_latent_prior.py called this function positionally and passed
    args.lambda_cos into the lambda_l2 slot, so 0.1 never reached a training run.
    The default now states what happened rather than what was intended: changing
    it back to 0.1 would mean the released code no longer reproduces the released
    models. Both call sites pass every weight by keyword, and --lambda-l2 exists,
    so the ablation the old docstring asked for is now actually runnable.
    """
    z_pred = nn.functional.normalize(z_pred, dim=-1)
    z_ir = nn.functional.normalize(z_ir, dim=-1)
    l2 = torch.mean((z_pred - z_ir) ** 2)
    cosine = torch.mean(1.0 - torch.sum(z_pred * z_ir, dim=-1))
    logits = (z_pred @ z_ir.t()) / temperature
    target = torch.arange(z_pred.shape[0], device=z_pred.device)
    nce_a = nn.functional.cross_entropy(logits, target)
    nce_b = nn.functional.cross_entropy(logits.t(), target)
    nce = 0.5 * (nce_a + nce_b)
    total = lambda_l2 * l2 + lambda_cos * cosine + lambda_nce * nce
    return {"loss": total, "l2": l2, "cosine": cosine, "nce": nce}


@torch.no_grad()
def retrieval_metrics(z_query: torch.Tensor, z_ir: torch.Tensor, ks=(1, 5, 10)) -> dict[str, float]:
    z_query = nn.functional.normalize(z_query, dim=-1)
    z_ir = nn.functional.normalize(z_ir, dim=-1)
    scores = z_query @ z_ir.t()
    target = torch.arange(scores.shape[0], device=scores.device)
    ranks = torch.argsort(scores, dim=1, descending=True)
    out: dict[str, float] = {}
    for k in ks:
        topk = ranks[:, : min(k, ranks.shape[1])]
        out[f"r@{k}"] = (topk == target[:, None]).any(dim=1).float().mean().item()
    positions = (ranks == target[:, None]).nonzero()
    if positions.numel():
        rank0 = positions[:, 1].float()          # 0-indexed rank of each query's positive
        out["median_rank"] = float(torch.median(rank0).item() + 1.0)
        out["mrr"] = float((1.0 / (rank0 + 1.0)).mean().item())
    return out

