"""Typed settings loader. Reads config/default.toml, overlays config/local.toml."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    model_id: str
    model_path: Path
    device: str
    sample_rate: int
    cache_dir: Path
    preset_dir: Path


_DEFAULTS: dict[str, object] = {
    "model_id": "forge-jingle-v0.4",
    "model_path": "models/forge-jingle-v0.4.onnx",
    "device": "cpu",
    "sample_rate": 44100,
    "cache_dir": "cache",
    "preset_dir": "presets",
}


def _merge(base: dict[str, object], overlay: dict[str, object]) -> dict[str, object]:
    out = dict(base)
    for k, v in overlay.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)  # type: ignore[arg-type]
        else:
            out[k] = v
    return out


def load_settings(root: Path) -> Settings:
    data = dict(_DEFAULTS)
    default_toml = root / "config" / "default.toml"
    local_toml = root / "config" / "local.toml"
    for path in (default_toml, local_toml):
        if path.is_file():
            with path.open("rb") as fh:
                data = _merge(data, tomllib.load(fh))
    return Settings(
        model_id=str(data["model_id"]),
        model_path=root / str(data["model_path"]),
        device=str(data["device"]),
        sample_rate=int(data["sample_rate"]),  # type: ignore[arg-type]
        cache_dir=root / str(data["cache_dir"]),
        preset_dir=root / str(data["preset_dir"]),
    )