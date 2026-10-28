# CLAUDE.md
Spec: `docs/BUILD_PROMPT.md`. Tracking: `docs/IMPLEMENTATION_PLAN.md` + `docs/PROGRESS.md` — read both at session start, update both at session end.
- Python 3.11+, pip/venv, `pytest`, `ruff`. LLM: Anthropic only.
- The pipeline publishes NOTHING (no Patreon/LinkedIn automation, no logins). It builds `out/bundle/` for manual upload.
- Experiments report what worked AND what didn't; a failing technique is a valid post. Only harness errors are retried; never abort for a negative result. Numbers come from `results.json` only.
- Patreon output must be plain Markdown/HTML + images; no Mermaid.
- LLM call gotchas (learned from CI logs, see `docs/PROGRESS.md`): the `thinking` param is per model in `pipeline/llm.py::THINKING_PARAM` (Sonnet `between_tools`; Haiku none); thinking tokens eat `max_tokens`; calls above 16000 tokens must stream. Always read the `llm:` log line (`blocks=`, `out_tokens=`, `text_chars=`) before changing these.
- Workflow: `gh run list --workflow content.yml` / `gh run view <id> --log` to inspect runs; verify claims against logs before fixing.
