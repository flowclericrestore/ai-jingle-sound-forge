"""Tokenization helpers. Lowercase, strip punctuation, split on whitespace."""
from __future__ import annotations

import re

_WORD = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def slugify(text: str, *, max_len: int = 48) -> str:
    tokens = tokenize(text)[:8]
    slug = "-".join(tokens)
    return slug[:max_len] or "jingle"