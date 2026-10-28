"""Stage 5 — write the Patreon post from real artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path

import markdown

from pipeline import llm
from pipeline.config import PROMPTS_DIR, SONNET_MODEL


def _numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+(?:\.\d+)?", text))


def check_numbers(post_md: str, results: dict, extra_allowed: str = "") -> list[str]:
    """Numbers in the post that are neither in results.json nor in allowed context text."""
    allowed = _numbers(json.dumps(results)) | _numbers(extra_allowed)
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
               *, client=None) -> str:
    code = {p.name: p.read_text(encoding="utf-8") for p in folder.glob("*.py")}
    payload = json.dumps({
        "topic": topic, "results": {k: v for k, v in results.items() if k != "_test_log"},
        "examples_url": examples_url, "signals": signals[:8], "code": code,
    })
    system = (PROMPTS_DIR / "patreon_post.md").read_text(encoding="utf-8")
    md = llm.complete(system, payload, model=SONNET_MODEL, max_tokens=6000, client=client)
    if results.get("status") == "harness_failed" and "harness" not in md.lower() and "broke" not in md.lower():
        raise RuntimeError("content: harness_failed run must be reported as such, not as a result")
    bad = check_numbers(md, results, extra_allowed=json.dumps(topic) + json.dumps(signals[:8]))
    if bad:
        md = llm.complete(
            system, payload + f"\n\nYour draft used numbers not present in results.json: {bad}. "
            "Rewrite without them.\n\nDraft:\n" + md,
            model=SONNET_MODEL, max_tokens=6000, client=client)
        bad = check_numbers(md, results, extra_allowed=json.dumps(topic) + json.dumps(signals[:8]))
        if bad:
            raise RuntimeError(f"content: unverifiable numbers remain in post: {bad}")
    return md


def to_html(md: str, images: dict[str, str]) -> str:
    """Render HTML; images maps placeholder name -> URL."""
    for key, url in images.items():
        md = md.replace("{{" + key + "}}", f"![{key.lower()}]({url})")
    md = re.sub(r"^\{\{IMG_\w+\}\}\s*$", "", md, flags=re.M)  # drop placeholders with no image
    return markdown.markdown(md, extensions=["tables", "fenced_code"])
