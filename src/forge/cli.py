"""Entry/bootstrap for the forge CLI.

Thin by design: parse args, build a ForgeContext, hand off to a service.
No business logic lives here.
"""
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from forge.bootstrap import build_context
from forge.services.render_service import RenderRequest, RenderService

app = typer.Typer(
    name="forge",
    help="AI jingle / brand sound generator.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


@app.command()
def generate(
    brief: Annotated[str, typer.Option("--brief", "-b", help="Text brief for the jingle.")],
    out: Annotated[Path, typer.Option("--out", "-o", help="Output .wav path.")],
    kit: Annotated[Path | None, typer.Option("--kit", help="Brand kit YAML.")] = None,
    duration: Annotated[float, typer.Option("--duration", help="Target seconds.")] = 2.5,
    seed: Annotated[int | None, typer.Option("--seed", help="Deterministic seed.")] = None,
) -> None:
    """Render a single jingle from a brief."""
    ctx = build_context()
    svc: RenderService = ctx.render_service
    req = RenderRequest(brief=brief, out_path=out, kit_path=kit, duration_s=duration, seed=seed)
    result = svc.render(req)
    console.print(f"[green]wrote[/green] {result.out_path} ({result.duration_s:.2f}s, {result.sample_rate} Hz)")


@app.command()
def doctor() -> None:
    """Print environment + model status."""
    ctx = build_context()
    for line in ctx.diagnostics():
        console.print(line)


if __name__ == "__main__":
    app()