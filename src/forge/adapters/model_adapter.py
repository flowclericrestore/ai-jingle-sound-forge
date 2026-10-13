"""ONNX Runtime adapter for the jingle model. Owns session + IO binding."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import onnxruntime as ort

from forge.models.brand_kit import BrandKit
from forge.models.latent import LatentBatch
from forge.utils.log import get_logger

log = get_logger(__name__)


class OnnxModelAdapter:
    """Wraps the three ONNX graphs: text encoder, sampler, decoder.

    Expects a sibling directory of .onnx files next to `model_path`:
      <stem>-text.onnx, <stem>-sampler.onnx, <stem>-decoder.onnx
    Falls back to a sine-bank stub if files are missing so the CLI works
    before `scripts/fetch_models.py` has been run.
    """

    def __init__(self, *, model_path: Path, device: str = "cpu") -> None:
        self._model_path = model_path
        self._device = device
        self._sessions: dict[str, ort.InferenceSession] = {}
        self._stub = not model_path.is_file()
        if self._stub:
            log.warning("model.stub_mode", path=str(model_path))
        else:
            self._load_sessions(model_path)

    def describe(self) -> str:
        mode = "stub" if self._stub else "onnx"
        return f"{self._model_path.name} [{mode}, {self._device}]"

    def _load_sessions(self, model_path: Path) -> None:
        stem = model_path.with_suffix("")
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"] if self._device == "cuda" else ["CPUExecutionProvider"]
        for role in ("text", "sampler", "decoder"):
            path = stem.with_name(f"{stem.name}-{role}.onnx")
            if path.is_file():
                self._sessions[role] = ort.InferenceSession(str(path), providers=providers)

    def encode_text(self, brief: str, kit: BrandKit) -> np.ndarray:
        if self._stub or "text" not in self._sessions:
            return self._stub_encode(brief, kit)
        toks = np.frombuffer(brief.encode("utf-8", "ignore")[:96].ljust(96, b"\0"), dtype=np.uint8)
        out = self._sessions["text"].run(None, {"tokens": toks[None, :]})[0]
        return np.asarray(out, dtype=np.float32).reshape(-1)

    def sample(self, cond: np.ndarray, *, duration_s: float, rng: np.random.Generator) -> LatentBatch:
        if self._stub or "sampler" not in self._sessions:
            frames = max(1, int(duration_s * 86))
            vals = rng.standard_normal((1, 64, frames)).astype(np.float32) * 0.5
            return LatentBatch(values=vals)
        noise = rng.standard_normal((1, 64, int(duration_s * 86))).astype(np.float32)
        out = self._sessions["sampler"].run(None, {"cond": cond[None, :], "noise": noise})[0]
        return LatentBatch(values=np.asarray(out, dtype=np.float32))

    def decode(self, latents: LatentBatch, *, sample_rate: int) -> np.ndarray:
        if self._stub or "decoder" not in self._sessions:
            return self._stub_decode(latents, sample_rate)
        out = self._sessions["decoder"].run(None, {"latents": latents.values})[0]
        return np.asarray(out, dtype=np.float32).reshape(-1)

    # --- stub fallbacks (used before weights are fetched) ---

    def _stub_encode(self, brief: str, kit: BrandKit) -> np.ndarray:
        seed = int.from_bytes(brief.encode()[:32].ljust(32, b"\0"), "little") ^ (kit.bpm * 31 + len(kit.key))
        return np.random.default_rng(seed).standard_normal(768).astype(np.float32)

    def _stub_decode(self, latents: LatentBatch, sample_rate: int) -> np.ndarray:
        n = int(latents.duration_s * sample_rate)
        t = np.linspace(0.0, latents.duration_s, n, endpoint=False, dtype=np.float32)
        freqs = np.array([220.0, 330.0, 440.0], dtype=np.float32)
        wave = sum(np.sin(2 * np.pi * f * t) for f in freqs) / len(freqs)
        env = np.exp(-3.0 * t)
        return (wave * env).astype(np.float32)