# CLAUDE.md
Spec: `docs/BUILD_PROMPT.md`. Tracking: `docs/IMPLEMENTATION_PLAN.md` + `docs/PROGRESS.md` — read both at session start, update both at session end.
- Python 3.11+, pip/venv, `pytest`, `ruff`. LLM: Anthropic only. Never publish fabricated results: numbers come from `results.json`.
- Experiments report what worked AND what didn't; a failing technique is a valid post. Only harness errors are retried; never abort for a negative result.
- Patreon: credential login via Playwright. If it breaks, use the Playwright MCP to explore the live UI and fix `pipeline/publishers/patreon.py` (draft only, never print credentials, stop at captcha/2FA).
- Publishing is gated by `--dry-run`/workflow input; keep dry-run the default.
- Patreon selectors/login live in `pipeline/publishers/patreon.py` (`SELECTORS`, `login`, `_drive`).
