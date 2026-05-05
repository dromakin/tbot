from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_BASE = Path(__file__).resolve().parent.parent / "graph-src"
_cache: dict[str, dict[str, Any]] = {}


def _load(block: str) -> dict[str, Any]:
    if block not in _cache:
        path = _BASE / f"{block}.json"
        _cache[block] = json.loads(path.read_text(encoding="utf-8"))
    return _cache[block]


def _resolve(payload: dict[str, Any], key: str) -> str:
    current: Any = payload
    for part in key.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(f"Missing text key: {key}")
        current = current[part]
    if not isinstance(current, str):
        raise KeyError(f"Text key is not a string: {key}")
    return current


def t(block: str, key: str, **ctx: object) -> str:
    raw = _resolve(_load(block), key)
    return raw.format(**ctx) if ctx else raw
