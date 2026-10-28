"""Stage 1 — gather recent AI-in-testing signals from public, ToS-clean APIs."""

from __future__ import annotations

import logging
import os
import time
import xml.etree.ElementTree as ET

import requests

from pipeline.config import SIGNAL_LOOKBACK_DAYS

log = logging.getLogger(__name__)
_UA = {"User-Agent": "sw-test-patreon-linkedin-poster/0.1"}
_QUERIES = ["AI test generation", "LLM software testing", "agentic testing", "AI flaky tests"]


def fetch_hn(days: int = SIGNAL_LOOKBACK_DAYS, get=requests.get) -> list[dict]:
    since = int(time.time()) - days * 86400
    out: list[dict] = []
    for q in _QUERIES:
        r = get(
            "https://hn.algolia.com/api/v1/search",
            params={"query": q, "tags": "story", "numericFilters": f"created_at_i>{since}",
                    "hitsPerPage": 8},
            headers=_UA, timeout=30,
        )
        r.raise_for_status()
        for h in r.json().get("hits", []):
            out.append({
                "source": "hackernews", "title": h.get("title"),
                "url": h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}",
                "score": h.get("points") or 0,
            })
    return out


def fetch_github(get=requests.get) -> list[dict]:
    headers = dict(_UA)
    if tok := os.environ.get("GITHUB_SEARCH_TOKEN"):
        headers["Authorization"] = f"Bearer {tok}"
    out: list[dict] = []
    for q in ("llm testing", "ai test generation"):
        r = get(
            "https://api.github.com/search/repositories",
            params={"q": f"{q} pushed:>{time.strftime('%Y-%m-%d', time.gmtime(time.time() - 14 * 86400))}",
                    "sort": "stars", "order": "desc", "per_page": 6},
            headers=headers, timeout=30,
        )
        r.raise_for_status()
        for it in r.json().get("items", []):
            out.append({"source": "github", "title": f"{it['full_name']}: {it.get('description') or ''}",
                        "url": it["html_url"], "score": it["stargazers_count"]})
    return out


def fetch_arxiv(get=requests.get) -> list[dict]:
    r = get(
        "http://export.arxiv.org/api/query",
        params={"search_query": 'all:"software testing" AND all:"large language model"',
                "sortBy": "submittedDate", "sortOrder": "descending", "max_results": 8},
        headers=_UA, timeout=30,
    )
    r.raise_for_status()
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(r.text)
    return [
        {"source": "arxiv", "title": " ".join(e.findtext("a:title", "", ns).split()),
         "url": e.findtext("a:id", "", ns), "score": 0}
        for e in root.findall("a:entry", ns)
    ]


def gather(fetchers=(fetch_hn, fetch_github, fetch_arxiv)) -> list[dict]:
    """Collect signals; a failing source is logged and skipped, but at least one must succeed."""
    signals: list[dict] = []
    for f in fetchers:
        try:
            signals.extend(f())
        except Exception as exc:  # noqa: BLE001 — network sources are best-effort
            log.warning("research: %s failed: %s", f.__name__, exc)
    if not signals:
        raise RuntimeError("research: no signals gathered from any source")
    seen: set[str] = set()
    unique = [s for s in signals if s["url"] not in seen and not seen.add(s["url"])]
    return sorted(unique, key=lambda s: s["score"], reverse=True)[:40]
