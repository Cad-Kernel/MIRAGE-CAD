"""MIRAGE-CAD loss functions.

Star-topology alignment: each input modality (text, image, point, STEP) is aligned
to the construction IR anchor via symmetric InfoNCE.  No direct cross-modal pairs
are needed, which reduces loss terms from C(N,2)=10 to N-1=4.
"""
from __future__ import annotations

import torch
import torch.nn.functional as F


def symmetric_info_nce(a: torch.Tensor, b: torch.Tensor, temperature: float = 0.07) -> torch.Tensor:
    """Symmetric InfoNCE loss between two L2-normalized embedding matrices (B, D).

    Treats each sample as its own positive and all others in the batch as negatives.
    Both directions (a→b and b→a) are averaged to make the loss symmetric.
    """
    logits = a @ b.t() / temperature
    labels = torch.arange(a.shape[0], device=a.device)
    return 0.5 * (F.cross_entropy(logits, labels) + F.cross_entropy(logits.t(), labels))


def retrieval_accuracy(query: torch.Tensor, target: torch.Tensor, topk=(1, 5, 10)) -> dict[str, float]:
    """Compute recall@k for a batch of (query, target) embedding pairs.

    Positive is defined as the diagonal: query[i] should retrieve target[i].
    Used during validation to track alignment quality independently of generation.
    """
    sim = query @ target.t()
    labels = torch.arange(query.shape[0], device=query.device)
    max_k = min(max(topk), target.shape[0])
    pred = sim.topk(max_k, dim=1).indices
    out = {}
    for k in topk:
        kk = min(k, target.shape[0])
        correct = (pred[:, :kk] == labels[:, None]).any(dim=1).float().mean().item()
        out[f"r@{k}"] = correct
    return out

