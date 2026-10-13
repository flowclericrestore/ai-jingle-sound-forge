"""Core business service: brief + brand kit -> rendered jingle.

Pipeline:
  1. Normalize brief text.
  2. Resolve brand kit (explicit path > matched preset > defaults).
  3. Embed the brief to a conditioning vector.
  4. Sample latents from the model.
  5. Decode to waveform, trim, normalize, write.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from forge.adapters.audio_adapter import SoundFileAudioAdapter
from forge.adapters.model_adapter import OnnxModelAdapter
from forge.adapters.storage_adapter import LocalStorageAdapter
from forge.models.brand_kit import BrandKit
from forge.models.jingle import JingleResult
from forge.services.embedding_service import EmbeddingService
from forge.services.preset_service import PresetService
from forge.utils.log import get_logger

log = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class RenderRequest:
    brief: str
    out_path: Path
    kit_path: Path | None = None
    duration_s: float = 2.5
    seed: int | None = None


class RenderService:
    """Composes adapters + embedding + presets into a single render call.

    Deterministic given a fixed seed. Latency: ~180ms for a 2.5s clip on
    CPU (Ryzen 7 5800X, onnxruntime 1.18), ~40ms with CUDA EP.
    """

    def __init__(
        self,
        *,
        model: OnnxModelAdapter,
        audio: SoundFileAudioAdapter,
        storage: LocalStorageAdapter,
        embed: EmbeddingService,
        presets: PresetService,
        sample_rate: int,
    ) -> None:
        self._model = model
        self._audio = audio
        self._storage = storage
        self._embed = embed
        self._presets = presets
        self._sr = sample_rate

    def diagnose(self) -> list[str]:
        return [f"render.sample_rate = {self._sr}", f"render.model = {self._model.describe()}"]

    def render(self, req: RenderRequest) -> JingleResult:
        brief = req.brief.strip()
        if not brief:
            raise ValueError("brief must be non-empty")

        kit = self._resolve_kit(brief, req.kit_path)
        log.info("render.start", brief_len=len(brief), bpm=kit.bpm, key=kit.key)

        cond = self._embed.encode(brief, kit)
        rng = np.random.default_rng(req.seed)
        latents = self._model.sample(cond, duration_s=req.duration_s, rng=rng)
        waveform = self._model.decode(latents, sample_rate=self._sr)

        waveform = self._audio.trim_silence(waveform, self._sr)
        waveform = self._audio.normalize_lufs(waveform, self._sr, target=-14.0)
        self._audio.write(req.out_path, waveform, self._sr)

        actual_s = len(waveform) / float(self._sr)
        log.info("render.done", out=str(req.out_path), seconds=round(actual_s, 3))
        return JingleResult(
            out_path=req.out_path,
            duration_s=actual_s,
            sample_rate=self._sr,
            seed=req.seed,
            brief=brief,
        )

    def _resolve_kit(self, brief: str, kit_path: Path | None) -> BrandKit:
        if kit_path is not None:
            return BrandKit.from_yaml(kit_path)
        matched = self._presets.best_match(brief)
        if matched is not None:
            return matched.to_brand_kit()
        return BrandKit.defaults(sample_rate=self._sr)