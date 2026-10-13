"""Thin handler: turn a raw request dict into a RenderRequest and call the service.

Used by the desktop shell and the local HTTP bridge. No rendering logic here.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from forge.services.render_service import RenderRequest, RenderService


def handle_generate(payload: dict[str, Any], svc: RenderService) -> dict[str, Any]:
    brief = str(payload.get("brief", "")).strip()
    if not brief:
        return {"ok": False, "error": "brief is required"}

    req = RenderRequest(
        brief=brief,
        out_path=Path(str(payload["out"])),
        kit_path=Path(str(payload["kit"])) if payload.get("kit") else None,
        duration_s=float(payload.get("duration", 2.5)),
        seed=int(payload["seed"]) if payload.get("seed") is not None else None,
    )
    result = svc.render(req)
    return {
        "ok": True,
        "out": str(result.out_path),
        "duration_s": result.duration_s,
        "sample_rate": result.sample_rate,
    }