# Contributing to ai-jingle-sound-forge

Thanks for considering a contribution. This project generates short brand
jingles, stingers, logo motifs, and UI sounds from a text brief plus a
brand kit (palette, tempo, mood tags).

## Ground rules

- One feature per PR. Keep diffs reviewable.
- Every new service goes in `src/forge/services/` and must have a matching
  test under `tests/`.
- Handlers stay thin. Business logic lives in services. Adapters wrap
  third-party or platform-specific code only.
- No binary blobs in git. Model weights are pulled by `scripts/fetch_models.py`.

## Dev setup

```
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
python -m forge.cli generate --brief "warm synthwave logo sting" --out demo.wav
```

## Style

- `ruff` for lint, `black` for format, `mypy --strict` for types.
- Type every public function. No bare `except`.
- Log via `structlog` through `forge.utils.log`. Never `print` in library code.

## Commit messages

`area: short imperative summary` — e.g. `services: add stem-separator fallback`.

## Reporting bugs

Use the issue template. Attach the brief, the brand kit YAML, and the
`forge doctor` output. Audio bugs without a repro brief are hard to chase.

## Code of conduct

Be decent. Critique the code, not the person.