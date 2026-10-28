"""Stage 8 — marketing-style LinkedIn promo with rotating tone."""

from __future__ import annotations

import json
import re

from pipeline import llm
from pipeline.config import HAIKU_MODEL, LINKEDIN_MAX_CHARS, PROMPTS_DIR

_EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")


def validate(text: str, patreon_url: str) -> list[str]:
    problems = []
    if len(text) > LINKEDIN_MAX_CHARS:
        problems.append(f"too long ({len(text)} > {LINKEDIN_MAX_CHARS})")
    if text.count(patreon_url) != 1:
        problems.append("Patreon URL must appear exactly once")
    if len(_EMOJI.findall(text)) > 2:
        problems.append("more than 2 emojis")
    tags = re.findall(r"#\w+", text)
    if not 3 <= len(tags) <= 5:
        problems.append("need 3-5 hashtags")
    return problems


def fallback(topic: dict, results: dict, patreon_url: str, tone: str) -> str:
    """Deterministic template used only if the LLM fails validation twice."""
    k, v = next(iter(results["summary"].items()))
    return (
        f"I ran a real experiment on: {topic['title']}.\n\n"
        f"One measured result: {k.replace('_', ' ')} = {v}.\n\n"
        f"Full demo, code and charts for members:\n{patreon_url}\n\n"
        f"What would you have expected here?\n\n"
        "#softwaretesting #AI #QA #SDET"
    )


def write(topic: dict, results: dict, patreon_url: str, tone: str, *, client=None) -> str:
    system = (PROMPTS_DIR / "linkedin_post.md").read_text(encoding="utf-8")
    payload = json.dumps({
        "topic": topic, "tone": tone, "patreon_url": patreon_url,
        "results": {k: v for k, v in results.items() if k != "_test_log"},
    })
    feedback = ""
    for _ in range(2):
        text = llm.complete(system, payload + feedback, model=HAIKU_MODEL, max_tokens=800,
                            client=client)
        problems = validate(text, patreon_url)
        if not problems:
            return text
        feedback = f"\n\nYour previous draft failed: {problems}. Fix and return only the post."
    return fallback(topic, results, patreon_url, tone)
