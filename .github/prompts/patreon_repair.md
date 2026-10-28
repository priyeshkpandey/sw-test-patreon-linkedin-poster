The automated Patreon posting flow in `pipeline/publishers/patreon.py` has broken, most likely because Patreon changed its UI.

Evidence from the failed run is in `out/patreon_debug/` (`step.txt` = failing step, `screenshot.png`, `page.html`). The held post is `out/patreon_post.html`.

Your task:
1. Read `out/patreon_debug/step.txt`, the screenshot and the HTML, and `pipeline/publishers/patreon.py`.
2. Use the Playwright MCP tools to open https://www.patreon.com/login, log in with the credentials in the environment variables PATREON_EMAIL and PATREON_PASSWORD (read them via the Bash tool only to type them into the form; NEVER print, log, echo, write them to any file, or include them in a commit message/PR), then explore the post-creation flow (https://www.patreon.com/posts/new): title field, body editor, audience (paid members only), save draft, publish.
3. Update ONLY `SELECTORS`, `login()` and `_drive()` in `pipeline/publishers/patreon.py` (and `tests/test_publishers.py` if the flow's shape changed) so the flow works with the current UI.
4. Verify by creating a DRAFT (never publish) through the MCP or by running the publisher in draft mode with a short test body titled "[repair test] delete me". Then run `pytest -q` and `ruff check .`.

Hard rules:
- Never click Publish. Draft only.
- If you meet a captcha, verification code, or 2FA prompt, STOP, make no edits, and say so — that needs the owner.
- Do not edit any other file. Do not commit or push; the workflow opens the PR.
- Keep selectors resilient (prefer role/text/data-tag over generated class names).
