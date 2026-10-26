"""MIRAGE-CAD encoder models.

Architecture overview (Section 4 of the paper):
  - TextBackbone / ImageBackbone: frozen pretrained encoders (DistilBERT, CLIP ViT-B/32).
  - PointNetEncoder: lightweight shared-MLP + global max-pool for 2048-point clouds.
  - StepBREPEncoder: lightweight Global-Local-Relation encoder over kernel-derived
    STEP/B-Rep descriptors.
  - ProjectionHead: two-layer GELU MLP followed by L2 normalisation → 512-d unit sphere.
  - MIRAGECADAligner: assembles all encoders; IR encoder is fine-tuned, others frozen.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import torch
from torch import nn
from transformers import AutoImageProcessor, AutoModel, AutoTokenizer


def mean_pool(last_hidden_state: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    # Masked average over token positions; used when pooler_output is unavailable.
    mask = attention_mask.unsqueeze(-1).type_as(last_hidden_state)
    summed = (last_hidden_state * mask).sum(dim=1)
    denom = mask.sum(dim=1).clamp(min=1e-6)
    return summed / denom


class TextBackbone(nn.Module):
    def __init__(self, model_name: str, max_length: int, train_backbone: bool = False):
        super().__init__()
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        self.model = AutoModel.from_pretrained(model_name, trust_remote_code=True)
        self.max_length = max_length
        self.out_dim = int(getattr(self.model.config, "hidden_size", 768))
        if not train_backbone:
            for p in self.model.parameters():
                p.requires_grad_(False)

    def encode_texts(self, texts: list[str], device: torch.device) -> torch.Tensor:
        batch = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )
        batch = {k: v.to(device) for k, v in batch.items()}
        out = self.model(**batch)
        if hasattr(out, "pooler_output") and out.pooler_output is not None:
            emb = out.pooler_output
        else:
            emb = mean_pool(out.last_hidden_state, batch["attention_mask"])
        return emb


class ImageBackbone(nn.Module):
    def __init__(self, model_name: str, train_backbone: bool = False):
        super().__init__()
        self.processor = AutoImageProcessor.from_pretrained(model_name, trust_remote_code=True)
        self.model = AutoModel.from_pretrained(model_name, trust_remote_code=True)
        self.out_dim = int(getattr(self.model.config, "hidden_size", getattr(self.model.config, "projection_dim", 768)))
        if hasattr(self.model.config, "vision_config"):
            self.out_dim = int(getattr(self.model.config, "projection_dim", getattr(self.model.config.vision_config, "hidden_size", self.out_dim)))
        if not train_backbone:
            for p in self.model.parameters():
                p.requires_grad_(False)

    def encode_images(self, images: list, device: torch.device) -> torch.Tensor:
        batch = self.processor(images=images, return_tensors="pt")
        batch = {k: v.to(device) for k, v in batch.items()}
        if hasattr(self.model, "get_image_features"):
            features = self.model.get_image_features(**batch)
            if isinstance(features, torch.Tensor):
                return features
        if hasattr(self.model, "vision_model") and "pixel_values" in batch:
            out = self.model.vision_model(pixel_values=batch["pixel_values"])
            if hasattr(out, "pooler_output") and out.pooler_output is not None:
                emb = out.pooler_output
            elif hasattr(out, "last_hidden_state"):
                emb = out.last_hidden_state[:, 0]
            elif isinstance(out, (tuple, list)):
                emb = out[0][:, 0]
            else:
                raise TypeError(f"Unsupported vision model output type: {type(out)!r}")
            if hasattr(self.model, "visual_projection"):
                emb = self.model.visual_projection(emb)
            return emb
        out = self.model(**batch)
        if hasattr(out, "pooler_output") and out.pooler_output is not None:
            emb = out.pooler_output
        elif hasattr(out, "last_hidden_state"):
            emb = out.last_hidden_state[:, 0]
        elif isinstance(out, (tuple, list)):
            emb = out[0][:, 0]
        else:
            raise TypeError(f"Unsupported image model output type: {type(out)!r}")
        return emb


class PointNetEncoder(nn.Module):
    """Lightweight PointNet without spatial transformer (3→64→128→256, global max-pool).

    No STN keeps the parameter count low while preserving permutation invariance.
    Input: (B, N, 3) float32 normalised point cloud.
    """
    def __init__(self, out_dim: int = 512):
        super().__init__()
        self.out_dim = out_dim
        self.net = nn.Sequential(
            nn.Linear(3, 64),
            nn.LayerNorm(64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 128),
            nn.LayerNorm(128),
            nn.ReLU(inplace=True),
            nn.Linear(128, 256),
            nn.LayerNorm(256),
            nn.ReLU(inplace=True),
        )
        self.head = nn.Sequential(
            nn.Linear(256, 512),
            nn.ReLU(inplace=True),
            nn.Linear(512, out_dim),
        )

    def forward(self, points: torch.Tensor) -> torch.Tensor:
        x = self.net(points)
        x = x.max(dim=1).values  # global max-pool over N points
        return self.head(x)


class StepFeatureEncoder(nn.Module):
    """Legacy global-vector STEP encoder kept for backward compatibility."""

    def __init__(self, in_dim: int, out_dim: int = 512):
        super().__init__()
        self.out_dim = out_dim
        self.net = nn.Sequential(
            nn.LayerNorm(in_dim),
            nn.Linear(in_dim, 256),
            nn.GELU(),
            nn.Linear(256, 512),
            nn.GELU(),
            nn.LayerNorm(512),
            nn.Linear(512, out_dim),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.net(features)


class StepBREPEncoder(nn.Module):
    """Lightweight Global-Local-Relation STEP/B-Rep encoder.

    Expected input dictionary:
      global:    (B, dg)
      faces:     (B, 64, df)
      face_mask: (B, 64)
      edges:     (B, 128, de)
      edge_mask: (B, 128)
      relation:  (B, dr)

    The local branches use shared MLPs plus masked mean/max pooling. This gives
    a CAD-native STEP branch without a full UV-Net or B-Rep graph transformer.
    """

    def __init__(
        self,
        global_dim: int,
        face_dim: int,
        edge_dim: int,
        relation_dim: int,
        out_dim: int = 512,
    ):
        super().__init__()
        self.out_dim = out_dim
        self.global_dim = global_dim
        self.face_dim = face_dim
        self.edge_dim = edge_dim
        self.relation_dim = relation_dim
        self.global_mlp = nn.Sequential(
            nn.LayerNorm(global_dim),
            nn.Linear(global_dim, 128),
            nn.GELU(),
            nn.Linear(128, 128),
            nn.GELU(),
        )
        self.face_mlp = nn.Sequential(
            nn.LayerNorm(face_dim),
            nn.Linear(face_dim, 128),
            nn.GELU(),
            nn.Linear(128, 128),
            nn.GELU(),
        )
        self.edge_mlp = nn.Sequential(
            nn.LayerNorm(edge_dim),
            nn.Linear(edge_dim, 128),
            nn.GELU(),
            nn.Linear(128, 128),
            nn.GELU(),
        )
        self.relation_mlp = nn.Sequential(
            nn.LayerNorm(relation_dim),
            nn.Linear(relation_dim, 128),
            nn.GELU(),
            nn.Linear(128, 128),
            nn.GELU(),
        )
        self.fusion = nn.Sequential(
            nn.LayerNorm(128 * 6),
            nn.Linear(128 * 6, 512),
            nn.GELU(),
            nn.Linear(512, out_dim),
        )

    @staticmethod
    def _masked_pool(x: torch.Tensor, mask: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        mask = mask.to(dtype=x.dtype, device=x.device).unsqueeze(-1)
        denom = mask.sum(dim=1).clamp(min=1.0)
        mean = (x * mask).sum(dim=1) / denom
        has_any = (mask.sum(dim=1) > 0)
        masked = x.masked_fill(mask <= 0, -1e4)
        max_pooled = masked.max(dim=1).values
        max_pooled = torch.where(has_any, max_pooled, torch.zeros_like(max_pooled))
        return mean, max_pooled

    def _coerce_legacy_vector(self, features: torch.Tensor) -> dict[str, torch.Tensor]:
        batch = features.shape[0]
        device = features.device
        dtype = features.dtype
        return {
            "global": features,
            "faces": torch.zeros(batch, 64, self.face_dim, device=device, dtype=dtype),
            "face_mask": torch.zeros(batch, 64, device=device, dtype=dtype),
            "edges": torch.zeros(batch, 128, self.edge_dim, device=device, dtype=dtype),
            "edge_mask": torch.zeros(batch, 128, device=device, dtype=dtype),
            "relation": torch.zeros(batch, self.relation_dim, device=device, dtype=dtype),
        }

    def forward(self, features: dict[str, torch.Tensor] | torch.Tensor) -> torch.Tensor:
        if isinstance(features, torch.Tensor):
            features = self._coerce_legacy_vector(features)
        h_g = self.global_mlp(features["global"])
        h_f = self.face_mlp(features["faces"])
        h_f_mean, h_f_max = self._masked_pool(h_f, features["face_mask"])
        h_e = self.edge_mlp(features["edges"])
        h_e_mean, h_e_max = self._masked_pool(h_e, features["edge_mask"])
        h_r = self.relation_mlp(features["relation"])
        fused = torch.cat([h_g, h_f_mean, h_f_max, h_e_mean, h_e_max, h_r], dim=-1)
        return self.fusion(fused)


class ProjectionHead(nn.Module):
    """Two-layer GELU MLP + LayerNorm, followed by L2 normalisation onto the unit hypersphere.

    All modality encoders share this identical head design so that the 512-d output
    space is directly comparable via dot product (cosine similarity).
    """
    def __init__(self, in_dim: int, out_dim: int = 512):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, out_dim),
            nn.GELU(),
            nn.Linear(out_dim, out_dim),
            nn.LayerNorm(out_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return nn.functional.normalize(self.net(x), dim=-1)


@dataclass
class MIRAGECADConfig:
    """Hyperparameters for the MIRAGE-CAD multimodal alignment stage."""
    text_model: str = "distilbert-base-uncased"
    image_model: str = "openai/clip-vit-base-patch32"
    embed_dim: int = 512
    max_text_length: int = 128
    max_ir_length: int = 256
    step_feature_dim: int = 50
    step_encoder_type: str = "global_local_relation"
    step_face_count: int = 64
    step_edge_count: int = 128
    step_face_dim: int = 28
    step_edge_dim: int = 24
    step_relation_dim: int = 32
    train_text_backbone: bool = False   # text backbone frozen by default
    train_image_backbone: bool = False  # CLIP vision backbone frozen by default
    # Dataclass default only. train_alignment.py always overrides it with
    # `train_ir_backbone=not args.freeze_ir_backbone`, and the flag is
    # --freeze-ir-backbone (store_true, so False unless passed). No training script
    # passes it, including training_25k/03_train_alignment.sh, so every run in the
    # paper FINE-TUNES the IR backbone. That is not an ablation: it is the anchor
    # design, and Sec. "Limitations" locates the rare-operation collapse in the anchor
    # space precisely because this backbone moves while the text and image ones do not.
    train_ir_backbone: bool = False


class MIRAGECADAligner(nn.Module):
    """MIRAGE-CAD star-topology multimodal aligner.

    Aligns text, image, point-cloud, and STEP/B-Rep encoders to a shared
    Construction IR anchor embedding via symmetric InfoNCE.  At inference,
    any single modality can query the IR-indexed retrieval corpus.
    """
    def __init__(self, config: MIRAGECADConfig, modalities: Iterable[str]):
        super().__init__()
        self.config = config
        self.modalities = set(modalities)
        if "text" in self.modalities or "ir" in self.modalities:
            self.text_encoder = TextBackbone(config.text_model, config.max_text_length, config.train_text_backbone)
            self.ir_encoder = TextBackbone(config.text_model, config.max_ir_length, config.train_ir_backbone)
            self.text_proj = ProjectionHead(self.text_encoder.out_dim, config.embed_dim)
            self.ir_proj = ProjectionHead(self.ir_encoder.out_dim, config.embed_dim)
        if "image" in self.modalities:
            self.image_encoder = ImageBackbone(config.image_model, config.train_image_backbone)
            self.image_proj = ProjectionHead(self.image_encoder.out_dim, config.embed_dim)
        if "point" in self.modalities:
            self.point_encoder = PointNetEncoder(out_dim=config.embed_dim)
            self.point_proj = ProjectionHead(config.embed_dim, config.embed_dim)
        if "step" in self.modalities:
            if config.step_encoder_type == "global_vector":
                self.step_encoder = StepFeatureEncoder(config.step_feature_dim, config.embed_dim)
            else:
                self.step_encoder = StepBREPEncoder(
                    global_dim=config.step_feature_dim,
                    face_dim=config.step_face_dim,
                    edge_dim=config.step_edge_dim,
                    relation_dim=config.step_relation_dim,
                    out_dim=config.embed_dim,
                )
            self.step_proj = ProjectionHead(config.embed_dim, config.embed_dim)

    def encode_text(self, texts: list[str], device: torch.device) -> torch.Tensor:
        return self.text_proj(self.text_encoder.encode_texts(texts, device))

    def encode_ir(self, texts: list[str], device: torch.device) -> torch.Tensor:
        return self.ir_proj(self.ir_encoder.encode_texts(texts, device))

    def encode_image(self, images: list, device: torch.device) -> torch.Tensor:
        return self.image_proj(self.image_encoder.encode_images(images, device))

    def encode_point(self, points: torch.Tensor) -> torch.Tensor:
        return self.point_proj(self.point_encoder(points))

    def encode_step(self, features: dict[str, torch.Tensor] | torch.Tensor) -> torch.Tensor:
        return self.step_proj(self.step_encoder(features))

    @staticmethod
    def _move_batch_to_device(batch: Any, device: torch.device) -> Any:
        if isinstance(batch, torch.Tensor):
            return batch.to(device)
        if isinstance(batch, dict):
            return {key: MIRAGECADAligner._move_batch_to_device(value, device) for key, value in batch.items()}
        return batch

    def encode_modality(self, modality: str, batch, device: torch.device) -> torch.Tensor:
        if modality == "text":
            return self.encode_text(batch, device)
        if modality == "ir":
            return self.encode_ir(batch, device)
        if modality == "image":
            return self.encode_image(batch, device)
        if modality == "point":
            return self.encode_point(batch.to(device))
        if modality == "step":
            return self.encode_step(self._move_batch_to_device(batch, device))
        raise ValueError(f"Unsupported modality: {modality}")


def save_alignment_checkpoint(path, model: MIRAGECADAligner, config: MIRAGECADConfig, modalities: list[str], extra: dict | None = None) -> None:
    """Persist a MIRAGE-CAD alignment checkpoint (weights + config + modality list)."""
    payload = {
        "state_dict": model.state_dict(),
        "config": config.__dict__,
        "modalities": modalities,
        "extra": extra or {},
    }
    torch.save(payload, path)


def load_alignment_checkpoint(path, map_location="cpu") -> tuple[MIRAGECADAligner, MIRAGECADConfig, list[str], dict]:
    """Restore a MIRAGE-CAD alignment checkpoint.  Returns (model, config, modalities, extra)."""
    payload = torch.load(path, map_location=map_location, weights_only=False)
    config_dict = dict(payload["config"])
    state_dict = payload["state_dict"]
    if "step_encoder_type" not in config_dict and "step_encoder.net.1.weight" in state_dict:
        config_dict["step_encoder_type"] = "global_vector"
    config = MIRAGECADConfig(**config_dict)
    modalities = list(payload["modalities"])
    model = MIRAGECADAligner(config, modalities)
    model.load_state_dict(state_dict, strict=True)
    return model, config, modalities, payload.get("extra", {})
