"""Brand preset store: list, save, best_match. Backed by storage adapter."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

from forge.adapters.storage_adapter import LocalStorageAdapter
from forge.models.brand_kit import BrandKit
from forge.utils.log import get_logger
from forge.utils.text import tokenize

log = get_logger(__name__)


@dataclass(slots=True)
class Preset:
    name: str
    mood_tags: list[str] = field(default_factory=list)
    bpm: int = 120
    key: str = "C"
    palette: list[str] = field(default_factory=list)

    def to_brand_kit(self) -> BrandKit:
        return BrandKit(
            bpm=self.bpm,
            key=self.key,
            mood_tags=list(self.mood_tags),
            palette=list(self.palette),
        )


class PresetService:
    def __init__(self, *, storage: LocalStorageAdapter, preset_dir: Path) -> None:
        self._storage = storage
        self._dir = preset_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def diagnose(self) -> list[str]:
        return [f"presets.dir = {self._dir}", f"presets.count = {len(self.list())}"]

    def list(self) -> list[Preset]:
        out: list[Preset] = []
        for path in sorted(self._dir.glob("*.yaml")):
            try:
                out.append(Preset(**self._storage.load_yaml(path)))
            except (OSError, TypeError, ValueError) as exc:
                log.warning("preset.load_failed", path=str(path), err=str(exc))
        return out

    def save(self, preset: Preset) -> Path:
        path = self._dir / f"{preset.name}.yaml"
        self._storage.save_yaml(path, asdict(preset))
        log.info("preset.saved", name=preset.name, path=str(path))
        return path

    def best_match(self, brief: str) -> Preset | None:
        tokens = set(tokenize(brief))
        best: tuple[int, Preset] | None = None
        for preset in self.list():
            score = len(tokens & set(preset.mood_tags))
            if score and (best is None or score > best[0]):
                best = (score, preset)
        return best[1] if best else None