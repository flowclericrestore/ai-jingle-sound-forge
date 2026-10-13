"""BrandKit — the brand's sonic identity. Loads from YAML, hashes for cache keys."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True, slots=True)
class BrandKit:
    bpm: int
    key: str
    mood_tags: tuple[str, ...] = ()
    palette: tuple[str, ...] = ()
    sample_rate: int = 44100

    @classmethod
    def defaults(cls, *, sample_rate: int = 44100) -> "BrandKit":
        return cls(bpm=120, key="C", mood_tags=("clean", "modern"), palette=(), sample_rate=sample_rate)

    @classmethod
    def from_yaml(cls, path: Path) -> "BrandKit":
        with path.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
        return cls(
            bpm=int(raw.get("bpm", 120)),
            key=str(raw.get("key", "C")),
            mood_tags=tuple(str(t) for t in raw.get("mood_tags", [])),
            palette=tuple(str(p) for p in raw.get("palette", [])),
            sample_rate=int(raw.get("sample_rate", 44100)),
        )

    def fingerprint(self) -> str:
        payload = f"{self.bpm}|{self.key}|{','.join(self.mood_tags)}|{','.join(self.palette)}"
        return hashlib.sha1(payload.encode()).hexdigest()[:12]