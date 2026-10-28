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
- [ ] 2d.3 Re-run and check the new log line `llm: ... blocks=[...] out_tokens=...`; if replies are still empty/truncated, reduce the experiment size or split into one call per file

## Phase 3 — Automation
- [x] 3.1 ci.yml (lint + tests)
- [x] 3.2 content.yml (manual trigger → bundle artifact → commit state)
## Phase 4 — Owner actions
- [x] 4.1 unit tests green locally
- [ ] 4.2 add secrets `ANTHROPIC_API_KEY` (and `EXAMPLES_REPO_TOKEN` if pushing examples)
- [ ] 4.3 `git push -u origin main`
- [ ] 4.4 run "Create content bundle", download `content-bundle`, check quality; test paste into Patreon editor (verify images/tables survive)
- [ ] 4.5 tune prompts from the first real output; then enable the cron in content.yml
