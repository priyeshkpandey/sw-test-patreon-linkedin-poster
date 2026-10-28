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
- [x] 1.4 demo.py (generate experiment, execute, repair *harness* errors, capture outcomes; `harness_failed` result instead of abort)
- [x] 1.5 visuals.py (bar chart, outcomes worked/partial/failed chart, summary card)
- [x] 1.6 content.py (Patreon post built on outcomes + insights; harness_failed honesty guard)
- [x] 1.7 examples_repo.py
## Phase 2 — Publishing
- [x] 2.1 publishers/linkedin.py (ported)
- [x] 2.2 linkedin_post.py + tone prompts
- [~] 2.3 publishers/patreon.py (Playwright, credential login, challenge vs. breakage exit codes 3/2, debug evidence; selectors unverified)
- [x] 2.5 `main.py patreon --bundle` resume command + exit codes
- [x] 2.4 main.py CLI orchestration
## Phase 3 — Automation
- [x] 3.1 ci.yml (lint+tests)
- [x] 3.2 content.yml (generate → patreon → linkedin → state commit; fallback issue)
- [x] 3.3 token expiry checks
- [~] 3.4 patreon-repair.yml + .github/prompts/patreon_repair.md (Claude Code + Playwright MCP → PR; unverified, needs live run)
- [x] 3.5 publish-held.yml (publish held bundle after repair PR merged)
## Phase 4 — Verification & go-live (owner actions)
- [x] 4.1 unit tests green locally
- [ ] 4.2 add secrets (README): incl. `PATREON_EMAIL`, `PATREON_PASSWORD`
- [ ] 4.2b confirm Patreon login works headless for the account (no captcha/2FA); if it challenges, use manual fallback
- [ ] 4.3 manual dry_run workflow run
- [ ] 4.4 Patreon `draft` mode live run; verify selectors
- [ ] 4.4b deliberately break a selector (`PATREON_SEL_TITLE=bogus`) to test the repair workflow end to end
- [ ] 4.5 publish mode run; then enable cron in content.yml
