# Implementation Plan

Legend: [x] done · [ ] todo · [~] done but UNVERIFIED against live services.
Update this file and `PROGRESS.md` after every work item.

## Phase 0 — Foundation
- [x] 0.1 git init, remote `origin` = sw-test-patreon-linkedin-poster
- [x] 0.2 BUILD_PROMPT, PROMPT_REVIEW, plan, progress, CLAUDE.md
- [x] 0.3 pyproject, .gitignore, Makefile, config
## Phase 1 — Core pipeline
- [x] 1.1 state.py (history, tone rotation)
- [x] 1.2 research.py (HN, GitHub, arXiv)
- [x] 1.3 topic.py
- [x] 1.4 demo.py (generate, execute, repair, capture results)
- [x] 1.5 visuals.py
- [x] 1.6 content.py (Patreon post)
- [x] 1.7 examples_repo.py
## Phase 2 — Publishing
- [x] 2.1 publishers/linkedin.py (ported)
- [x] 2.2 linkedin_post.py + tone prompts
- [~] 2.3 publishers/patreon.py (Playwright; selectors unverified)
- [x] 2.4 main.py CLI orchestration
## Phase 3 — Automation
- [x] 3.1 ci.yml (lint+tests)
- [x] 3.2 content.yml (generate → patreon → linkedin → state commit; fallback issue)
- [x] 3.3 token expiry checks
## Phase 4 — Verification & go-live (owner actions)
- [x] 4.1 unit tests green locally
- [ ] 4.2 add secrets (README)
- [ ] 4.3 manual dry_run workflow run
- [ ] 4.4 Patreon `draft` mode live run; verify selectors
- [ ] 4.5 publish mode run; then enable cron in content.yml
