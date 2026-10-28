"""Thin Anthropic wrapper (single place to mock in tests)."""

from __future__ import annotations

import json
import os
import re
from typing import Any


class LLMUnavailable(RuntimeError):
    pass


def _client() -> Any:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise LLMUnavailable("ANTHROPIC_API_KEY is not set")
    import anthropic

    return anthropic.Anthropic(api_key=key)


def complete(system: str, user: str, *, model: str, max_tokens: int = 4096, client: Any = None) -> str:
    client = client or _client()
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()


def extract_json(text: str) -> Any:
    """Parse JSON from a model reply, tolerating ``` fences and surrounding prose."""
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if m:
        text = m.group(1)
    start = min((i for i in (text.find("{"), text.find("[")) if i >= 0), default=-1)
    if start < 0:
        raise ValueError("no JSON found in model reply")
    return json.JSONDecoder().raw_decode(text[start:])[0]
