# Progress Log (read first each session)

**Next action:** see the first unchecked item in IMPLEMENTATION_PLAN.md (currently Phase 4 – owner actions).

## Decisions
- 2026-10-28: Patreon via Playwright (no post-creation API exists) with artifact+issue fallback. Superseded in rev 2 below: session cookie -> credential login.
- 2026-10-28: Python + pip (not uv) in CI; LLM = Anthropic (Sonnet for article/demo, Haiku for LinkedIn), same as social-media-intel.
- 2026-10-28: Cron left commented until first successful manual run.

- 2026-10-28 (rev 2, owner feedback): (a) failing techniques/harness are NOT hard failures — experiment reports worked/partial/failed outcomes and the post is built on observations + insights; unfixable harness => `harness_failed` post. (b) Patreon auth = stored credentials (`PATREON_EMAIL`/`PATREON_PASSWORD`), fresh login each run, replaces session cookie. (c) Patreon breakage => `patreon-repair` workflow uses Claude Code + Playwright MCP to fix and open a PR; captcha/2FA is never auto-repaired.

## Sessions
- 2026-10-28 S1: repo initialised, docs written, all code in Phases 0–3 implemented, tests written.

## Blockers / open questions
- Examples repo `sw-testing-developing-tech-examples` is empty; first run creates the initial commit.
- Patreon login/selectors unverified; headless login may hit captcha/verification (then manual fallback). Repair workflow gives the agent the Patreon credentials — draft-only, PR-only, one file; review PRs carefully.
- `patreon-repair` uses `@anthropic-ai/claude-code` CLI flags (`--mcp-config`, `--allowedTools`) as I understand them; unverified in CI.
- 2026-10-28 S1 (end): 21 tests pass, ruff clean, workflows YAML-valid. Initial commit made locally, NOT pushed yet. Not run end-to-end: needs ANTHROPIC_API_KEY + secrets.
- 2026-10-28 S1 rev 2: owner feedback applied across spec, review, plan, code, workflows, tests (30 pass, ruff clean, YAML valid). Still not pushed, not run end to end.
