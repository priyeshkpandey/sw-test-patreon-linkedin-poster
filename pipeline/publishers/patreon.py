"""Patreon publisher.

Patreon's public API v2 cannot create posts, so this drives the creator web UI with Playwright,
authenticated by the `session_id` cookie of a logged-in browser. UNVERIFIED against the live site:
selectors are isolated in SELECTORS and individually overridable via PATREON_SEL_<KEY> env vars.

Env:
    PATREON_SESSION_ID   value of the `session_id` cookie on patreon.com (expires; renew manually)
    PATREON_MODE         "draft" (default, saves without publishing) or "publish"
"""

from __future__ import annotations

import logging
import os

log = logging.getLogger(__name__)

NEW_POST_URL = "https://www.patreon.com/posts/new"
SELECTORS: dict[str, str] = {
    "title": 'input[name="title"], [data-tag="post-title"] input, textarea[placeholder*="itle"]',
    "body": '[contenteditable="true"][role="textbox"], .ProseMirror, [data-tag="post-editor"] [contenteditable="true"]',
    "paid_only": '[data-tag="access-tier-paid"], label:has-text("Paid members")',
    "save_draft": 'button:has-text("Save draft"), button:has-text("Save")',
    "publish": 'button:has-text("Publish")',
    "confirm": '[role="dialog"] button:has-text("Publish")',
}


def selector(key: str) -> str:
    return os.environ.get(f"PATREON_SEL_{key.upper()}", SELECTORS[key])


class PatreonError(RuntimeError):
    pass


def publish(title: str, html_body: str, *, mode: str | None = None, page_factory=None) -> str:
    """Create the post; return its URL. `page_factory` lets tests inject a fake page."""
    mode = mode or os.environ.get("PATREON_MODE", "draft")
    if mode not in ("draft", "publish"):
        raise PatreonError(f"PATREON_MODE must be draft|publish, got {mode!r}")
    session = os.environ.get("PATREON_SESSION_ID")
    if not session and page_factory is None:
        raise PatreonError("PATREON_SESSION_ID is not set")

    if page_factory is not None:
        return _drive(page_factory(), title, html_body, mode)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1400, "height": 1000})
        ctx.add_cookies([{"name": "session_id", "value": session, "domain": ".patreon.com",
                          "path": "/", "secure": True, "httpOnly": True}])
        page = ctx.new_page()
        try:
            return _drive(page, title, html_body, mode)
        except Exception:
            try:
                page.screenshot(path="out/patreon_failure.png")
            except Exception:  # noqa: BLE001
                pass
            raise
        finally:
            browser.close()


def _drive(page, title: str, html_body: str, mode: str) -> str:
    page.goto(NEW_POST_URL, wait_until="domcontentloaded", timeout=60_000)
    if "login" in page.url:
        raise PatreonError("Patreon session cookie rejected (redirected to login) — renew PATREON_SESSION_ID")
    page.wait_for_selector(selector("title"), timeout=30_000)
    page.fill(selector("title"), title)
    body = page.locator(selector("body")).first
    body.click()
    # Insert rich HTML (images, tables) directly into the editor and fire an input event.
    page.evaluate(
        """([sel, html]) => {
            const el = document.querySelector(sel.split(',')[0].trim()) ||
                       document.querySelector(sel);
            el.focus(); el.innerHTML = html;
            el.dispatchEvent(new InputEvent('input', {bubbles: true}));
        }""",
        [selector("body"), html_body],
    )
    if page.locator(selector("paid_only")).count():
        page.locator(selector("paid_only")).first.click()
    else:
        log.warning("patreon: paid-only control not found — verify the post's audience manually")
    if mode == "draft":
        page.locator(selector("save_draft")).first.click()
    else:
        page.locator(selector("publish")).first.click()
        if page.locator(selector("confirm")).count():
            page.locator(selector("confirm")).first.click()
    page.wait_for_url("**/posts/**", timeout=60_000)
    url = page.url.split("?")[0]
    if "/posts/" not in url or url.rstrip("/").endswith("/posts/new"):
        raise PatreonError(f"unexpected URL after save: {url}")
    log.info("patreon: %s saved (%s)", mode, url)
    return url
