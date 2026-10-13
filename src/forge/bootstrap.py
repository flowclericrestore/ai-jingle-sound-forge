"""Wires config, adapters, and services into a single ForgeContext.

Called once from the CLI or the desktop shell. Keeps construction out of
the services so they stay unit-testable.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from forge.adapters.audio_adapter import SoundFileAudioAdapter
from forge.adapters.model_adapter import OnnxModelAdapter
from forge.adapters.storage_adapter import LocalStorageAdapter
from forge.config.settings import load_settings
from forge.services.embedding_service import EmbeddingService
from forge.services.preset_service import PresetService
from forge.services.render_service import RenderService
from forge.utils.log import get_logger

log = get_logger(__name__)


@dataclass(slots=True)
class ForgeContext:
    settings_root: Path
    render_service: RenderService
    preset_service: PresetService
    embedding_service: EmbeddingService

    def diagnostics(self) -> list[str]:
        lines = [f"settings_root = {self.settings_root}"]
        lines.extend(self.render_service.diagnose())
        lines.extend(self.preset_service.diagnose())
        return lines


def build_context(settings_root: Path | None = None) -> ForgeContext:
    root = settings_root or Path.cwd()
    settings = load_settings(root)
    log.info("bootstrap.context", root=str(root), model=settings.model_id)

    audio = SoundFileAudioAdapter(sample_rate=settings.sample_rate)
    model = OnnxModelAdapter(model_path=settings.model_path, device=settings.device)
    storage = LocalStorageAdapter(cache_dir=settings.cache_dir)

    embed = EmbeddingService(model=model)
    presets = PresetService(storage=storage, preset_dir=settings.preset_dir)
    render = RenderService(
        model=model,
        audio=audio,
        storage=storage,
        embed=embed,
        presets=presets,
        sample_rate=settings.sample_rate,
    )
    return ForgeContext(
        settings_root=root,
        render_service=render,
        preset_service=presets,
        embedding_service=embed,
    )