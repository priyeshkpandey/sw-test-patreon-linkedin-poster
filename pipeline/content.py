"""Stage 5 — write the Patreon post from real artifacts."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import markdown

from pipeline import llm
from pipeline.config import PROMPTS_DIR, SONNET_MODEL

log = logging.getLogger(__name__)


def _numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+(?:\.\d+)?", text))


def _derived(text: str) -> set[str]:
    """Obvious re-expressions of measured values: 0.75 -> 75, 12.5 -> 12/13, 100 - 25 -> 75, etc."""
    out: set[str] = set()
    for n in _numbers(text):
        v = float(n)
        for d in (v * 100, 100 - v, 100 - v * 100, v, float(round(v)), float(int(v))):
            if d == int(d):
                out.add(str(int(d)))
            out.add(f"{d:.1f}".rstrip("0").rstrip(".") if d != int(d) else str(int(d)))
    return out


def check_numbers(post_md: str, results: dict, extra_allowed: str = "") -> list[str]:
    """Numbers in the post that are neither in results.json (or simple re-expressions of it) nor in
    allowed context text."""
    measured = json.dumps({k: v for k, v in results.items() if k != "attempt_log"})
    allowed = _numbers(measured) | _derived(measured) | _numbers(extra_allowed)
    # strip fenced code, urls and image/heading noise before checking prose numbers
    prose = re.sub(r"```.*?```", "", post_md, flags=re.S)
    prose = re.sub(r"https?://\S+", "", prose)
    prose = re.sub(r"^#+ .*$", "", prose, flags=re.M)
    suspicious = []
    for n in sorted(_numbers(prose) - allowed):
        if len(n) >= 2 or "." in n:  # ignore lone digits ("3 bullets", "1 table")
            suspicious.append(n)
    return suspicious


def write_post(topic: dict, results: dict, folder: Path, examples_url: str, signals: list[dict],
               *, client=None) -> tuple[str, list[str]]:
    """Return (markdown, unverified_numbers). Never raises for unverifiable numbers: a whole run
    (and its experiment) must not be thrown away over a figure; the caller flags it for review."""
    code = {p.name: p.read_text(encoding="utf-8") for p in folder.glob("*.py")}
    payload = json.dumps({
        "topic": topic, "results": {k: v for k, v in results.items() if k != "_test_log"},
        "examples_url": examples_url, "signals": signals[:8], "code": code,
    })
    system = (PROMPTS_DIR / "patreon_post.md").read_text(encoding="utf-8")
    md = llm.complete(system, payload, model=SONNET_MODEL, max_tokens=8000, client=client)
    if results.get("status") == "harness_failed" and "harness" not in md.lower() and "broke" not in md.lower():
        raise RuntimeError("content: harness_failed run must be reported as such, not as a result")
    bad = check_numbers(md, results, extra_allowed=json.dumps(topic) + json.dumps(signals[:8]))
    if bad:
        md = llm.complete(
            system, payload + f"\n\nYour draft used numbers not present in results.json: {bad}. "
            "Rewrite without them.\n\nDraft:\n" + md,
            model=SONNET_MODEL, max_tokens=8000, client=client)
        bad = check_numbers(md, results, extra_allowed=json.dumps(topic) + json.dumps(signals[:8]))
        if bad:
            log.warning("content: numbers not traceable to results.json remain: %s — flagged for review", bad)
    return md, bad


def to_html(md: str, images: dict[str, str]) -> str:
    """Render HTML; images maps placeholder name -> URL."""
    for key, url in images.items():
        md = md.replace("{{" + key + "}}", f"![{key.lower()}]({url})")
    md = re.sub(r"^\{\{IMG_\w+\}\}\s*$", "", md, flags=re.M)  # drop placeholders with no image
    return markdown.markdown(md, extensions=["tables", "fenced_code"])
