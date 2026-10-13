# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.4.x   | yes       |
| 0.3.x   | security fixes only |
| < 0.3   | no        |

## Reporting a vulnerability

Email `security@ai-jingle-sound-forge.dev` or open a private advisory on
GitHub. Do not file a public issue for exploitable bugs.

We aim to acknowledge within 72 hours and ship a fix or mitigation within
14 days for high-severity issues.

## Scope

In scope:
- Remote code execution via crafted preset, brand-kit, or model files.
- Path traversal in the render pipeline / export writer.
- Arbitrary file write through the plugin adapter loader.
- Unsafe deserialization in `services/preset_service.py`.

Out of scope:
- Denial of service from absurdly long briefs (rate-limit at the CLI).
- Local-only attacks requiring an already-compromised host.
- Model output quality, hallucinations, or "the jingle sounds bad."

## Hardening notes for users

- Run renders with `--sandbox` to disable the plugin adapter loader.
- Keep `models/` on a trusted path; the ONNX runtime loads it directly.
- Presets from third parties are data-only; review before importing.