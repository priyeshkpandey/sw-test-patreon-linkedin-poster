# Progress Log (read first each session)

**Next action:** see the first unchecked item in IMPLEMENTATION_PLAN.md (currently Phase 4 – owner actions).

## Decisions
- 2026-10-28: Patreon via Playwright session-cookie automation, with artifact+issue fallback (no post-creation API exists).
- 2026-10-28: Python + pip (not uv) in CI; LLM = Anthropic (Sonnet for article/demo, Haiku for LinkedIn), same as social-media-intel.
- 2026-10-28: Cron left commented until first successful manual run.

## Sessions
- 2026-10-28 S1: repo initialised, docs written, all code in Phases 0–3 implemented, tests written.

## Blockers / open questions
- Examples repo `sw-testing-developing-tech-examples` is empty; first run creates the initial commit.
- Patreon selectors and cookie flow unverified; needs owner credentials.
- 2026-10-28 S1 (end): 21 tests pass, ruff clean, workflows YAML-valid. Initial commit made locally, NOT pushed yet. Not run end-to-end: needs ANTHROPIC_API_KEY + secrets.
