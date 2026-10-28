# CLAUDE.md
Spec: `docs/BUILD_PROMPT.md`. Tracking: `docs/IMPLEMENTATION_PLAN.md` + `docs/PROGRESS.md` — read both at session start, update both at session end.
- Python 3.11+, pip/venv, `pytest`, `ruff`. LLM: Anthropic only.
- The pipeline publishes NOTHING (no Patreon/LinkedIn automation, no logins). It builds `out/bundle/` for manual upload.
- Experiments report what worked AND what didn't; a failing technique is a valid post. Only harness errors are retried; never abort for a negative result. Numbers come from `results.json` only.
- Patreon output must be plain Markdown/HTML + images; no Mermaid.
