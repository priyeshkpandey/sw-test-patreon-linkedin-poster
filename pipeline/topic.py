"""Stage 2 — choose a topic that can be demonstrated with a small runnable experiment."""

from __future__ import annotations

import re

from pipeline import llm
from pipeline.config import SONNET_MODEL

SYSTEM = """You are a senior SDET who ships working demos. From the signals, pick ONE
AI-in-software-testing topic that can be demonstrated by a small, self-contained, deterministic
Python experiment (stdlib only, no network, no API keys, runs in <60s) producing measurable
before/after numbers. Avoid the already-covered slugs. Reply with JSON only:
{"title": str, "slug": "kebab-case", "angle": str, "hypothesis": str, "signal_urls": [str]}"""


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60]


def choose(signals: list[dict], used: set[str], *, client=None) -> dict:
    lines = "\n".join(f"- {s['title']} ({s['url']})" for s in signals[:30])
    reply = llm.complete(
        SYSTEM, f"Signals:\n{lines}\n\nAlready covered slugs: {sorted(used)}",
        model=SONNET_MODEL, max_tokens=1000, client=client,
    )
    topic = llm.extract_json(reply)
    topic["slug"] = slugify(topic.get("slug") or topic["title"])
    if topic["slug"] in used:
        raise RuntimeError(f"topic: model chose an already-used slug {topic['slug']!r}")
    return topic
