"""Run history + LinkedIn tone rotation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pipeline.config import STATE_FILE, TONES


def load(path: Path = STATE_FILE) -> list[dict]:
    if not path.is_file():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def append(entry: dict, path: Path = STATE_FILE) -> None:
    history = load(path)
    history.append(entry)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(history, indent=2) + "\n", encoding="utf-8")


def update_last(slug: str, fields: dict, path: Path = STATE_FILE) -> None:
    """Merge fields into the entry for slug (creates it if missing)."""
    history = load(path)
    for e in history:
        if e.get("slug") == slug:
            e.update(fields)
            break
    else:
        history.append({"slug": slug, **fields})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(history, indent=2) + "\n", encoding="utf-8")


def used_slugs(history: list[dict]) -> set[str]:
    return {e["slug"] for e in history if e.get("slug")}


def pick_tone(history: list[dict], slug: str) -> str:
    """Least-recently-used tone; never the same as the previous post's tone."""
    last_used: dict[str, int] = {}
    for i, e in enumerate(history):
        if e.get("tone"):
            last_used[e["tone"]] = i
    previous = next((e["tone"] for e in reversed(history) if e.get("tone")), None)
    candidates = [t for t in TONES if t != previous]
    # never-used tones sort first (-1); ties broken deterministically by slug hash
    return min(
        candidates,
        key=lambda t: (
            last_used.get(t, -1),
            hashlib.sha256(f"{slug}:{t}".encode()).hexdigest(),
        ),
    )
