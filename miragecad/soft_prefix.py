"""Soft-prefix conditioning modules for MIRAGE-CAD.

The adapter maps the predicted Construction-IR latent z_ir_hat into a small
sequence of Qwen hidden-size embeddings. These embeddings are prepended to the
LoRA-IR text prompt embeddings and are trained jointly with the LoRA-IR adapter.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import torch
from torch import nn


@dataclass
class SoftPrefixConfig:
    latent_dim: int = 512
    hidden_size: int = 1536
    prefix_len: int = 4
    dropout: float = 0.0


class SoftPrefixAdapter(nn.Module):
    """Project z_ir_hat [latent_dim] → [B, prefix_len, hidden_size] prefix tokens."""

    def __init__(self, config: SoftPrefixConfig):
        super().__init__()
        self.config = config
        self.norm  = nn.LayerNorm(config.latent_dim)
        self.proj1 = nn.Linear(config.latent_dim, config.hidden_size)
        # Dropout is only added to the graph when explicitly requested (dropout > 0).
        # nn.Identity is used as a no-op placeholder so forward() stays uniform.
        self.drop  = nn.Dropout(config.dropout) if config.dropout > 0.0 else nn.Identity()
        self.proj2 = nn.Linear(config.hidden_size, config.prefix_len * config.hidden_size)

    def forward(self, z_ir_hat: torch.Tensor) -> torch.Tensor:
        z_ir_hat = z_ir_hat.to(dtype=self.norm.weight.dtype)
        x = torch.nn.functional.gelu(self.proj1(self.norm(z_ir_hat)))
        return self.proj2(self.drop(x)).view(z_ir_hat.shape[0], self.config.prefix_len, self.config.hidden_size)


def save_soft_prefix_adapter(path: str | Path, adapter: SoftPrefixAdapter) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "config": asdict(adapter.config),
            "state_dict": adapter.state_dict(),
        },
        path,
    )


def load_soft_prefix_adapter(
    path: str | Path,
    device: torch.device | str = "cpu",
    dtype: torch.dtype | None = None,
) -> SoftPrefixAdapter:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    config = SoftPrefixConfig(**payload["config"])
    adapter = SoftPrefixAdapter(config)
    adapter.load_state_dict(payload["state_dict"], strict=True)
    adapter = adapter.to(device)
    if dtype is not None:
        adapter = adapter.to(dtype=dtype)
    return adapter.eval()


def resolve_soft_prefix_path(adapter_dir: str | Path, explicit_path: str | Path | None = None) -> Path:
    if explicit_path is not None:
        return Path(explicit_path)
    return Path(adapter_dir) / "soft_prefix.pt"
