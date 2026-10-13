"""Audio IO adapter — soundfile + numpy. No torch, no librosa."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

from forge.utils.log import get_logger

log = get_logger(__name__)


class SoundFileAudioAdapter:
    def __init__(self, *, sample_rate: int) -> None:
        self._sr = sample_rate

    def write(self, path: Path, waveform: np.ndarray, sample_rate: int) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        clipped = np.clip(waveform, -1.0, 1.0).astype(np.float32)
        sf.write(str(path), clipped, sample_rate, subtype="PCM_16")
        log.debug("audio.write", path=str(path), frames=len(clipped))

    def trim_silence(self, waveform: np.ndarray, sample_rate: int, *, thresh_db: float = -45.0) -> np.ndarray:
        if waveform.size == 0:
            return waveform
        thresh = 10 ** (thresh_db / 20.0)
        loud = np.flatnonzero(np.abs(waveform) > thresh)
        if loud.size == 0:
            return waveform
        pad = int(0.01 * sample_rate)
        start = max(0, int(loud[0]) - pad)
        end = min(len(waveform), int(loud[-1]) + pad)
        return waveform[start:end]

    def normalize_lufs(self, waveform: np.ndarray, sample_rate: int, *, target: float = -14.0) -> np.ndarray:
        """Approximate LUFS via RMS. Good enough for short stingers."""
        if waveform.size == 0:
            return waveform
        rms = float(np.sqrt(np.mean(waveform**2)))
        if rms < 1e-6:
            return waveform
        current_db = 20.0 * np.log10(rms)
        gain = 10 ** ((target - current_db) / 20.0)
        return (waveform * gain).astype(np.float32)