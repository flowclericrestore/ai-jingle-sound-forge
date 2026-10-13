"""Wraps the model's text encoder. Owns caching of brief -> vector."""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

from forge.adapters.model_adapter import OnnxModelAdapter
from forge.models.brand_kit import BrandKit
from forge.utils.log import get_logger

log = get_logger(__name__)

_CACHE_DIR = Path("cache/embeddings")


class EmbeddingService:
    """Text + brand-kit -> conditioning vector.

    Cache key is sha256(brief || kit.fingerprint()) truncated to 16 bytes.
    Vectors are float32, shape (768,).
    """

    def __init__(self, *, model: OnnxModelAdapter) -> None:
        self._model = model
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def encode(self, brief: str, kit: BrandKit) -> np.ndarray:
        key = hashlib.sha256(f"{brief}|{kit.fingerprint()}".encode()).hexdigest()[:32]
        cached = self._load(key)
        if cached is not None:
            log.debug("embed.cache_hit", key=key)
            return cached
        vec = self._model.encode_text(brief, kit)
        self._save(key, vec)
        return vec

    def _load(self, key: str) -> np.ndarray | None:
        path = _CACHE_DIR / f"{key}.npy"
        if not path.is_file():
            return None
        try:
            return np.load(path, allow_pickle=False)
        except (OSError, ValueError):
            return None

    def _save(self, key: str, vec: np.ndarray) -> None:
        try:
            np.save(_CACHE_DIR / f"{key}.npy", vec, allow_pickle=False)
        except OSError as exc:
            log.warning("embed.cache_write_failed", key=key, err=str(exc))