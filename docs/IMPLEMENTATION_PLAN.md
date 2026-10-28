# Implementation Plan

Legend: [x] done · [ ] todo. Update this file and `PROGRESS.md` after every work item.

## Phase 0 — Foundation
- [x] 0.1 git init, remote `origin` = sw-test-patreon-linkedin-poster
- [x] 0.2 BUILD_PROMPT, PROMPT_REVIEW, plan, progress, CLAUDE.md
- [x] 0.3 pyproject, .gitignore, Makefile, config
## Phase 1 — Core pipeline
- [x] 1.1 state.py (history, tone rotation)
- [x] 1.2 research.py (HN, GitHub, arXiv)
- [x] 1.3 topic.py
- [x] 1.4 demo.py (experiment; only harness errors retried; `harness_failed` result instead of abort)
- [x] 1.5 visuals.py (outcomes chart, metrics chart, summary card)
- [x] 1.6 content.py (post from outcomes + insights; number check; harness_failed honesty guard)
- [x] 1.7 examples_repo.py (optional push)
## Phase 2 — Bundle (rev 3: no publishing)
- [x] 2.1 linkedin_post.py (text only, `[PATREON_LINK]` placeholder, tone rotation)
- [x] 2.2 main.py: build `out/bundle/` incl. UPLOAD_GUIDE.md; record state
- [x] 2.3 Removed: Patreon/LinkedIn publishers, repair + publish-held workflows, Playwright
## Phase 2b — Fix: examples repo had images/JSON but no code (first live run, 2026-10-28)
- [x] 2b.1 Root cause: model reply was JSON-wrapped code; parse failed 3x ("no JSON found"), so no files were written. Switched to `=== FILE ===` blocks (`llm.extract_files`), max_tokens 8000 -> 16000, truncation warning
- [x] 2b.2 Save run evidence in the folder: `run_output.txt`, `test_output.txt`; on failure keep `attempt_N_reply.txt` + last attempt's code
- [x] 2b.3 Tests for the above (24 pass)
- [ ] 2b.4 Re-run the workflow; confirm the new examples folder has code + run output. The old `examples/2026-10-28-coverage-criteria-vs-llm-style-bugs` folder is image+JSON only; its slug is marked used in `state/history.json` (delete that entry to retry the topic)

## Phase 2c — Fix: topic stage crashed (run 2026-10-28 18:45)
- [x] 2c.1 Root cause: topic reply truncated at max_tokens=1000 -> invalid JSON -> uncaught JSONDecodeError. Raised limits (topic 4000, post 8000, LinkedIn 2000), topic retries up to 3x, bad JSON now exits cleanly via RuntimeError/ValueError handling
- [x] 2c.2 Tests (26 pass)
- [ ] 2c.3 Re-run workflow to confirm

## Phase 2d — Fix: harness_failed on all 3 attempts (run 2026-10-28 18:53)
- [x] 2d.1 Evidence: every attempt stopped at max_tokens=16000 yet the visible reply was EMPTY (0 bytes, `attempt_N_reply.txt`), so no `=== FILE ===` blocks. Likely cause (inferred, not yet confirmed): thinking tokens consumed the whole budget before any text. Fix: `thinking={"type": "disabled"}` on every call; per-call log of stop reason, block types, output tokens, text length
- [x] 2d.2 Test (27 pass)
- [x] 2d.2b Regression from 2d.1: the API returned HTTP 400 for `thinking: {"type": "disabled"}` on this model ("send between_tools instead"; the model "does not think before responding"). Now sends `{"type": "between_tools"}`. This also makes the "thinking ate the budget" explanation doubtful — the true cause of the empty replies is still unconfirmed
- [ ] 2d.3 Re-run and check the new log line `llm: ... blocks=[...] out_tokens=...`; if replies are still empty/truncated, reduce the experiment size or split into one call per file

## Phase 2e — Fix: run died at the post stage (run 2026-10-28 19:06)
- [x] 2e.1 Evidence: experiment succeeded on attempt 2 (attempt 1 IndexError, repaired); then `content: unverifiable numbers remain in post: ['75']` aborted the whole run, discarding the experiment. Root causes: (a) check treated 0.75 -> "75%" as invented; (b) a stray number was fatal
- [x] 2e.2 Derived forms (x100, 100-x, rounding) now count as traceable; remaining untraceable numbers no longer abort — post is kept, listed in `REVIEW_NOTES.md` in the bundle for the owner to check. Spec §2 / §4 updated
- [x] 2e.3 Tests
- [ ] 2e.4 Re-run and confirm a full bundle (and code) lands in the examples repo

## Phase 2f — Fix: LinkedIn step crashed (400) + experiment harness failing (run 2026-10-28 19:14)
- [x] 2f.1 Crash: `thinking: between_tools` is rejected by the Haiku model ("not supported for this model"); `disabled` was rejected by Sonnet. Accepted values differ per model, so the parameter is now omitted entirely (Sonnet already "does not think before responding"). Lesson: stop guessing model-specific params; the `llm:` log line shows replies are fine without it
- [x] 2f.2 Harness: attempt 1 put prose + several fenced blocks inside `demo.py` (a leading ``` -> SyntaxError). Now rejected with an explicit "output ONE clean file" message, and the system prompt forbids notes/dead code. Attempts 2-3 failed the model's own self-check (`suite fails on original discount`: expected 81.0, got 72.0) — an arithmetic mistake in the generated expected values; prompt now tells it to hand-verify expected values
- [x] 2f.3 Tests (29 pass)
- [ ] 2f.4 Re-run. If harness_failed persists from the model's own wrong expectations, consider raising DEMO_MAX_ATTEMPTS to 4-5 or simplifying the experiment scope in the topic prompt

## Phase 2g — Fix: experiment replies truncated at max_tokens=16000 (owner report, run 2026-10-28 19:22)
- [x] 2g.1 Experiment limit raised 16000 -> 32000 (`config.DEMO_MAX_TOKENS`). Requests above 16000 use streaming (`client.messages.stream`), since the SDK rejects long non-streaming requests (>10 min)
- [x] 2g.2 A truncated reply is now detected (`TruncatedReply`), its partial text is saved as `attempt_N_reply.txt`, and the retry feedback tells the model to write a much smaller experiment (previously a cut-off reply was parsed as if complete)
- [x] 2g.3 Tests (32 pass)
- [x] 2g.3b Run 19:22 (old 16000 code) showed the real cause: with no `thinking` param Sonnet returned `blocks=['thinking']`, `text_chars=0`, `out_tokens=16000` on all 3 attempts — thinking consumed the entire budget. Removing the param in 2f.1 caused this. Fix: per-model setting (`llm.THINKING_PARAM`): Sonnet = `between_tools`, Haiku = none (it rejects both values). LinkedIn max_tokens 4000 (Haiku still emits thinking blocks)
- [ ] 2g.4 Re-run. Unverified: that 32000 is accepted for this model and that streaming works against the live API. The earlier replies in the logs were ~7.6-11.9k output tokens, so truncation at 16k looked unusual; if it persists at 32k, the model is over-writing and the prompt's size cap matters more than the limit

## Phase 3 — Automation
- [x] 3.1 ci.yml (lint + tests)
- [x] 3.2 content.yml (manual trigger → bundle artifact → commit state)
## Phase 4 — Owner actions
- [x] 4.1 unit tests green locally
- [ ] 4.2 add secrets `ANTHROPIC_API_KEY` (and `EXAMPLES_REPO_TOKEN` if pushing examples)
- [ ] 4.3 `git push -u origin main`
- [ ] 4.4 run "Create content bundle", download `content-bundle`, check quality; test paste into Patreon editor (verify images/tables survive)
- [ ] 4.5 tune prompts from the first real output; then enable the cron in content.yml
