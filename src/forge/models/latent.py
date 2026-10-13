"""Latent buffer + shape helpers for the sampler/decoder boundary."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class LatentBatch:
    """Sampled latents. Shape (n_samples, latent_dim, frames)."""

    values: np.ndarray
    frames_per_second: int = 86

    @property
    def duration_s(self) -> float:
        if self.values.ndim != 3:
            raise ValueError(f"expected (N, D, T), got {self.values.shape}")
        return self.values.shape[2] / float(self.frames_per_second)

    def for_duration(self, duration_s: float) -> "LatentBatch":
        target = int(round(duration_s * self.frames_per_second))
        if target <= 0:
            raise ValueError("duration_s must be positive")
        return LatentBatch(values=self.values[:, :, :target], frames_per_second=self.frames_per_second)