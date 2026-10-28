# Progress Log (read first each session)

**Next action:** Phase 4 in IMPLEMENTATION_PLAN.md (owner actions: secrets, push, first run).

## Decisions
- 2026-10-28 rev 2: failing techniques/harness are not hard failures; outcome-based reporting; unfixable harness => `harness_failed` post.
- 2026-10-28 rev 3 (owner): NO automated posting to Patreon or LinkedIn (too complicated). Pipeline only generates a ready-to-upload bundle; owner uploads manually. Playwright, credentials, tokens, repair workflows removed. Supersedes rev 1/2 Patreon decisions.
- LLM = Anthropic (Sonnet for topic/experiment/post, Haiku for LinkedIn). Python + pip in CI. Cron left commented.

## Sessions
- 2026-10-28 S1: repo initialised; rev 1 built; rev 2 and rev 3 applied. 21 tests pass, ruff clean. Local commits only, not pushed. Pipeline never run end to end (needs ANTHROPIC_API_KEY).

## Blockers / open questions
- Examples repo `sw-testing-developing-tech-examples` is empty; first push creates the initial commit.
- Patreon HTML paste fidelity unverified (step 4.4).
