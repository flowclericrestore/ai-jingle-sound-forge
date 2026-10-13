"""Local filesystem storage. Sandboxed to a cache dir for writes."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from forge.utils.log import get_logger

log = get_logger(__name__)


class LocalStorageAdapter:
    def __init__(self, *, cache_dir: Path) -> None:
        self._cache = cache_dir
        self._cache.mkdir(parents=True, exist_ok=True)

    def load_yaml(self, path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        if not isinstance(data, dict):
            raise TypeError(f"expected mapping at {path}")
        return data

    def save_yaml(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(data, fh, sort_keys=True)

    def cache_path(self, name: str) -> Path:
        safe = "".join(c for c in name if c.isalnum() or c in "-_.")
        return self._cache / safe