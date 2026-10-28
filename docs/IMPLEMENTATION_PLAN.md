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
## Phase 2b — Live-run fixes (all done; details and evidence in PROGRESS.md "API gotchas")
- [x] 2b.1 Examples repo had images/JSON but no code: model replies are `=== FILE: name ===` blocks (`llm.extract_files`), not JSON
- [x] 2b.2 Run evidence saved in each examples folder: `run_output.txt`, `test_output.txt`; on failure also `attempt_N_reply.txt` and the last attempt's code
- [x] 2b.3 Topic stage: larger `max_tokens`, up to 3 retries on bad JSON, clean error exit
- [x] 2b.4 Empty experiment replies: Sonnet's thinking consumed all `max_tokens`; per-model `THINKING_PARAM` (Sonnet `between_tools`, Haiku none); per-call `llm:` diagnostics log line
- [x] 2b.5 Number check: derived forms allowed; untraceable numbers listed in `REVIEW_NOTES.md` instead of aborting
- [x] 2b.6 Generated `.py` files with stray fences/prose are rejected with a repair message; prompt forbids notes/dead code and asks the model to hand-verify expected values
- [x] 2b.7 Experiment `max_tokens` 32000 with streaming; truncated replies are detected, saved, and retried with a "write a smaller experiment" instruction
- [x] 2b.8 Verified live: run `40755779914` succeeded with code + run output in the examples repo (32 tests pass)
- [ ] 2b.9 Known issue: `examples_repo.push` does not clear an existing same-day/same-slug folder, leaving stale files from earlier failed runs

## Phase 3 — Automation
- [x] 3.1 ci.yml (lint + tests)
- [x] 3.2 content.yml (manual trigger → bundle artifact → commit state)
## Phase 4 — Owner actions
- [x] 4.1 unit tests green locally
- [x] 4.2 secrets added (`ANTHROPIC_API_KEY`, `EXAMPLES_REPO_TOKEN`)
- [x] 4.3 pushed to origin/main
- [x] 4.4a workflow run succeeded (`40755779914`)
- [ ] 4.4b download `content-bundle`, review quality, `REVIEW_NOTES.md`; test paste into Patreon editor (images/tables survive?)
- [ ] 4.5 tune prompts from the first real output; then enable the cron in content.yml
