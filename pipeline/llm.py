"""Thin Anthropic wrapper (single place to mock in tests)."""

from __future__ import annotations

import json
import logging
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


log = logging.getLogger(__name__)


STREAM_ABOVE = 16000

# Sonnet 5.5 thinks by default and the thinking tokens count against max_tokens: with the parameter
# omitted, experiment replies were 100% thinking (blocks=['thinking'], text_chars=0) at 16000 tokens.
# "between_tools" turns that off for Sonnet ("disabled" is rejected with a 400). Haiku 5.5 rejects
# "between_tools" ("not supported for this model"), so it gets no parameter. Verified from CI logs.
THINKING_PARAM: dict[str, dict] = {"claude-sonnet-5-5": {"type": "between_tools"}}


class TruncatedReply(RuntimeError):
    """The model hit max_tokens; `.partial` holds what it wrote."""

    def __init__(self, msg: str, partial: str):
        super().__init__(msg)
        self.partial = partial


def complete(system: str, user: str, *, model: str, max_tokens: int = 4096, client: Any = None,
             raise_on_truncate: bool = False) -> str:
    client = client or _client()
    kwargs = dict(model=model, max_tokens=max_tokens, system=system,
                  messages=[{"role": "user", "content": user}])
    if model in THINKING_PARAM:
        kwargs["thinking"] = THINKING_PARAM[model]
    if max_tokens > STREAM_ABOVE:
        # The SDK refuses non-streaming requests that may exceed ~10 minutes (max_tokens > ~21k).
        with client.messages.stream(**kwargs) as stream:
            resp = stream.get_final_message()
    else:
        resp = client.messages.create(**kwargs)
    truncated = getattr(resp, "stop_reason", None) == "max_tokens"
    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
    usage = getattr(resp, "usage", None)
    log.info("llm: model=%s stop=%s blocks=%s out_tokens=%s text_chars=%d", model,
             getattr(resp, "stop_reason", None), [getattr(b, "type", "?") for b in resp.content],
             getattr(usage, "output_tokens", "?"), len(text))
    if truncated:
        log.warning("llm: reply truncated at max_tokens=%d (model=%s)", max_tokens, model)
        if raise_on_truncate:
            raise TruncatedReply(f"reply was cut off at max_tokens={max_tokens}", text)
    return text


_FILE_RE = re.compile(r"^=== FILE: (\S+) ===[ \t]*\n(.*?)(?=^=== FILE: \S+ ===|^=== END ===|\Z)", re.S | re.M)


def extract_files(text: str) -> dict[str, str]:
    """Parse `=== FILE: name ===` blocks (code is not escaped, unlike JSON). Strips a wrapping ``` fence."""
    files = {}
    for name, body in _FILE_RE.findall(text):
        body = body.strip("\n")
        m = re.fullmatch(r"```\w*\n(.*)\n```", body, re.S)
        inner = m.group(1) if m else body
        # Only code files: a README legitimately contains fenced examples.
        if name.endswith(".py") and re.search(r"^```", inner, re.M):
            raise ValueError(
                f"{name}: contains markdown fences/prose inside the file body. Output each file "
                "as ONE clean file: no explanations, no notes, no extra code blocks, no dead code.")
        files[name] = inner + "\n"
    if not files:
        raise ValueError("no '=== FILE: name ===' blocks found in model reply")
    return files


def extract_json(text: str) -> Any:
    """Parse JSON from a model reply, tolerating ``` fences and surrounding prose."""
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if m:
        text = m.group(1)
    start = min((i for i in (text.find("{"), text.find("[")) if i >= 0), default=-1)
    if start < 0:
        raise ValueError("no JSON found in model reply")
    return json.JSONDecoder().raw_decode(text[start:])[0]
