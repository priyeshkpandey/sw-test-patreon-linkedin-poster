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
## Phase 3 — Automation
- [x] 3.1 ci.yml (lint + tests)
- [x] 3.2 content.yml (manual trigger → bundle artifact → commit state)
## Phase 4 — Owner actions
- [x] 4.1 unit tests green locally
- [ ] 4.2 add secrets `ANTHROPIC_API_KEY` (and `EXAMPLES_REPO_TOKEN` if pushing examples)
- [ ] 4.3 `git push -u origin main`
- [ ] 4.4 run "Create content bundle", download `content-bundle`, check quality; test paste into Patreon editor (verify images/tables survive)
- [ ] 4.5 tune prompts from the first real output; then enable the cron in content.yml
