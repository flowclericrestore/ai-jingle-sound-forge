"""JingleResult — immutable render output record."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class JingleResult:
    out_path: Path
    duration_s: float
    sample_rate: int
    seed: int | None
    brief: str