# Progress Log (read first each session)

**Next action:** plan 2b.4 (re-run workflow), then Phase 4 in IMPLEMENTATION_PLAN.md (owner actions: secrets, push, first run).

## Decisions
- 2026-10-28 rev 2: failing techniques/harness are not hard failures; outcome-based reporting; unfixable harness => `harness_failed` post.
- 2026-10-28 rev 3 (owner): NO automated posting to Patreon or LinkedIn (too complicated). Pipeline only generates a ready-to-upload bundle; owner uploads manually. Playwright, credentials, tokens, repair workflows removed. Supersedes rev 1/2 Patreon decisions.
- LLM = Anthropic (Sonnet for topic/experiment/post, Haiku for LinkedIn). Python + pip in CI. Cron left commented.

## Sessions
- 2026-10-28 S1: repo initialised; rev 1 built; rev 2 and rev 3 applied. 21 tests pass, ruff clean. Local commits only, not pushed. Pipeline never run end to end (needs ANTHROPIC_API_KEY).

- 2026-10-29 S2: first live run found (via owner) that the examples repo got only images + JSON. Cause: JSON-wrapped code failed to parse 3x -> harness_failed -> no code written. Fixed (see plan 2b). Needs a re-run to confirm.
- 2026-10-29 S2: workflow run failed in topic stage (truncated JSON at max_tokens=1000). Fixed, see plan 2c. Not yet re-run.
- 2026-10-29 S2: re-run still harness_failed x3: replies empty at the 16000-token cap. Disabled thinking + added diagnostics (plan 2d). Cause inferred, not confirmed; needs another run.
- 2026-10-29 S2: my thinking={'disabled'} change broke the topic call (HTTP 400). Switched to 'between_tools'. Cause of the empty experiment replies remains unconfirmed; read the new `llm:` log line on the next run.
- 2026-10-29 S2: first run where the experiment worked (attempt 2). Died at post stage on number check ('75' = 0.75 as %). Check loosened + non-fatal with REVIEW_NOTES.md (plan 2e).

## Blockers / open questions
- Examples repo `sw-testing-developing-tech-examples` is empty; first push creates the initial commit.
- Patreon HTML paste fidelity unverified (step 4.4).
