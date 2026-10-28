# CLAUDE.md
Spec: `docs/BUILD_PROMPT.md`. Tracking: `docs/IMPLEMENTATION_PLAN.md` + `docs/PROGRESS.md` — read both at session start, update both at session end.
- Python 3.11+, pip/venv, `pytest`, `ruff`. LLM: Anthropic only. Never publish fabricated results: numbers come from `results.json`.
- Publishing is gated by `--dry-run`/workflow input; keep dry-run the default.
- Patreon selectors live in `pipeline/publishers/patreon.py::SELECTORS`.
