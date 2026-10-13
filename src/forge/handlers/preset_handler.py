"""Thin handler for preset import/export and listing."""
from __future__ import annotations

from typing import Any

from forge.services.preset_service import Preset, PresetService


def handle_list_presets(_payload: dict[str, Any], svc: PresetService) -> dict[str, Any]:
    return {"ok": True, "presets": [p.name for p in svc.list()]}


def handle_import_preset(payload: dict[str, Any], svc: PresetService) -> dict[str, Any]:
    name = str(payload["name"])
    preset = Preset(
        name=name,
        mood_tags=list(payload.get("mood_tags", [])),
        bpm=int(payload.get("bpm", 120)),
        key=str(payload.get("key", "C")),
        palette=list(payload.get("palette", [])),
    )
    svc.save(preset)
    return {"ok": True, "saved": name}