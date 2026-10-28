"""Patreon publisher.

Patreon's public API v2 cannot create posts, so this drives the creator web UI with Playwright,
logging in with the owner's credentials on every run. UNVERIFIED against the live site: when the
UI drifts, a failure writes debug evidence to out/patreon_debug/ and the `patreon-repair` workflow
uses the Playwright MCP to explore the live UI and open a fix PR (see docs/BUILD_PROMPT.md §4.1).

Env:
    PATREON_EMAIL / PATREON_PASSWORD   login credentials (GitHub secrets)
    PATREON_MODE                       "draft" (default; saves unpublished) or "publish"
    PATREON_SEL_<KEY>                  optional selector overrides
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

LOGIN_URL = "https://www.patreon.com/login"
NEW_POST_URL = "https://www.patreon.com/posts/new"
DEBUG_DIR = Path(os.environ.get("OUT_DIR", "out")) / "patreon_debug"
SELECTORS: dict[str, str] = {
    "email": 'input[type="email"], input[name="email"]',
    "password": 'input[type="password"], input[name="password"]',
    "continue": 'button:has-text("Continue"), button:has-text("Log in"), button[type="submit"]',
    "challenge": 'iframe[src*="captcha"], iframe[title*="captcha" i], input[autocomplete="one-time-code"], '
                 ':text("verification code"), :text("Verify it\'s you")',
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
    """Flow broke (likely UI drift) — eligible for the MCP repair workflow."""


class PatreonChallenge(PatreonError):
    """Captcha / verification code / 2FA / bad credentials — NOT auto-repairable; needs the owner."""


def save_debug(page, step: str) -> None:
    """Write evidence for the repair agent. Never includes credentials."""
    try:
        DEBUG_DIR.mkdir(parents=True, exist_ok=True)
        (DEBUG_DIR / "step.txt").write_text(f"failing step: {step}\nurl: {page.url}\n", encoding="utf-8")
        page.screenshot(path=str(DEBUG_DIR / "screenshot.png"), full_page=True)
        (DEBUG_DIR / "page.html").write_text(page.content(), encoding="utf-8")
    except Exception as exc:  # noqa: BLE001 — evidence is best-effort
        log.warning("patreon: could not save debug evidence: %s", exc)


def login(page, email: str, password: str) -> None:
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_selector(selector("email"), timeout=30_000)
    page.fill(selector("email"), email)
    if not page.locator(selector("password")).count():  # two-step login: email first
        page.locator(selector("continue")).first.click()
        page.wait_for_selector(selector("password"), timeout=30_000)
    page.fill(selector("password"), password)
    page.locator(selector("continue")).first.click()
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(3000)
    if page.locator(selector("challenge")).count():
        raise PatreonChallenge("Patreon asked for a captcha/verification code — complete it manually")
    if "/login" in page.url:
        raise PatreonChallenge("Patreon login did not complete (bad credentials or unexpected challenge)")


def publish(title: str, html_body: str, *, mode: str | None = None, page_factory=None) -> str:
    """Log in, create the post, return its URL. `page_factory` lets tests inject a fake page."""
    mode = mode or os.environ.get("PATREON_MODE", "draft")
    if mode not in ("draft", "publish"):
        raise PatreonError(f"PATREON_MODE must be draft|publish, got {mode!r}")
    email, password = os.environ.get("PATREON_EMAIL"), os.environ.get("PATREON_PASSWORD")
    if page_factory is None and not (email and password):
        raise PatreonChallenge("PATREON_EMAIL / PATREON_PASSWORD are not set")

    if page_factory is not None:
        return _run(page_factory(), title, html_body, mode, email or "", password or "")

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_context(viewport={"width": 1400, "height": 1000}).new_page()
        try:
            return _run(page, title, html_body, mode, email, password)
        finally:
            browser.close()


def _run(page, title: str, html_body: str, mode: str, email: str, password: str) -> str:
    step = "login"
    try:
        login(page, email, password)
        step = "create-post"
        return _drive(page, title, html_body, mode)
    except PatreonChallenge:
        save_debug(page, step)
        raise
    except Exception as exc:
        save_debug(page, step)
        raise PatreonError(f"Patreon flow broke at step '{step}': {exc}") from exc


def _drive(page, title: str, html_body: str, mode: str) -> str:
    page.goto(NEW_POST_URL, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_selector(selector("title"), timeout=30_000)
    page.fill(selector("title"), title)
    page.locator(selector("body")).first.click()
    # Insert rich HTML (images, tables) directly into the editor and fire an input event.
    page.evaluate(
        """([sel, html]) => {
            const el = document.querySelector(sel.split(',')[0].trim()) || document.querySelector(sel);
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
