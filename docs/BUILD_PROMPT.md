# BUILD_PROMPT — Patreon + LinkedIn AI-in-Testing Content Automation

> Authoritative spec. Read fully before changing code. Reviewed in `PROMPT_REVIEW.md`; work is tracked in `IMPLEMENTATION_PLAN.md` and `PROGRESS.md`.

## 1. Role
You are a senior SDET / QA engineer who tracks AI developments in software testing and ships working code. You are building a fully automated (GitHub Actions) pipeline that (a) researches a current AI-in-testing topic, (b) builds and *runs* a real demo for it, (c) writes a visual, digestible Patreon post for paid subscribers, (d) publishes it, and (e) promotes the Patreon link on LinkedIn with a post whose tone changes every time.

## 2. Non-negotiable principles
1. **Content must be backed by real work.** Every Patreon post is derived from a demo that was actually executed in CI. Numbers/charts come from the captured run output (`results.json`), never from the LLM's imagination. If the demo fails after retries, the run aborts — no post is published.
2. **Demo code lives in** `priyeshkpandey/sw-testing-developing-tech-examples` (empty at start), under `examples/<YYYY-MM-DD>-<slug>/`, and is linked from the post.
3. **Everything runs on GitHub Actions.** No local-only steps except one-time secret setup.
4. **Safe by default:** manual runs default to `dry_run=true`; nothing is published to Patreon/LinkedIn unless dry_run is false. Cron is disabled until a successful manual run (mirrors `social-media-intel`).
5. **LLM optional where possible:** research/state/visuals work without a key; generation stages require `ANTHROPIC_API_KEY` and fail loudly (no fake fallback content for the Patreon post). LinkedIn has a heuristic template fallback.
6. **Never** log secrets; never scrape LinkedIn.

## 3. Pipeline stages (Python 3.11+, package `pipeline/`)
| # | Stage | Module | Output |
|---|---|---|---|
| 1 | Research signals | `research.py` | `signals.json` — HN Algolia + GitHub search + arXiv (public APIs, no auth) |
| 2 | Topic selection | `topic.py` | `topic.json` {title, slug, angle, hypothesis}; avoids topics in `state/history.json` |
| 3 | Demo build + run | `demo.py` | `work/demo/` files, `results.json` (metrics from real execution), pytest log; up to 3 repair attempts |
| 4 | Visuals | `visuals.py` | PNG charts (matplotlib) from `results.json` + a Mermaid diagram source in the post body |
| 5 | Patreon post | `content.py` | `patreon_post.md` + `patreon_post.html` embedding image placeholders |
| 6 | Push demo | `examples_repo.py` | commit to examples repo via `EXAMPLES_REPO_TOKEN` |
| 7 | Publish Patreon | `publishers/patreon.py` | `patreon_url` |
| 8 | LinkedIn post | `linkedin_post.py` | `linkedin_post.txt`, tone chosen by rotation |
| 9 | Publish LinkedIn | `publishers/linkedin.py` | post id (same UGC flow as `social-media-intel`) |
| 10 | Record state | `state.py` | append to `state/history.json`, committed back by workflow |

## 4. Patreon publishing approach (critical design decision)
Patreon's public API v2 is **read-only for posts**; there is no endpoint to create one. Options evaluated:
- **A. Browser automation (Playwright) with a stored logged-in session cookie** — chosen. Works headless on Actions. Risks: Patreon ToS grey area, UI selector drift, cookie expiry (re-login manually every few weeks), possible bot challenges.
- B. Reverse-engineered internal JSON API — more brittle/riskier; rejected.
- C. Semi-automatic hand-off (draft package + notification) — **built-in fallback**: if A fails, upload the content bundle as a workflow artifact and open a GitHub issue with the ready-to-paste post; LinkedIn is then skipped until the Patreon URL is supplied (`workflow_dispatch` input `patreon_url`).
Selectors are isolated in one dict and overridable by env so drift is a small fix. `PATREON_MODE=draft|publish` — first live runs use `draft`.

## 5. LinkedIn posting
Reuse the `social-media-intel` implementation (`pipeline/publishers/linkedin.py`): UGC Posts API, `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_PERSON_URN`, `LINKEDIN_TOKEN_EXPIRES_AT`, optional image upload, 60-day token expiry issue. Difference: the post contains the Patreon link (as the call to action) and optionally the first chart as the image.

### Tone rotation (marketing-expert persona)
Tones: `contrarian`, `story`, `data-first`, `checklist`, `question-led`, `myth-busting`, `behind-the-scenes`, `prediction`. Selection = least-recently-used from `state/history.json` (ties broken deterministically by hash of the slug); the same tone may never be used in two consecutive posts. Each tone has a distinct hook formula and CTA style in `prompts/linkedin_post.md`. Hard limits: ≤1,300 chars, ≤2 emojis, exactly one link (Patreon), 3–5 hashtags, ends with a comment-inviting question, must not claim facts absent from `results.json`.

## 6. Patreon post quality bar
Structure: TL;DR (3 bullets) → why it matters now (cite signals with links) → what I built (architecture diagram) → results (≥2 charts, 1 table, from real data) → code highlights (short snippets, link to repo folder) → pitfalls/limits (honest failures) → takeaways/try-it-yourself. 900–1,500 words. Skimmable: short paragraphs, bold key numbers, alt text on images.

## 7. State & idempotency
`state/history.json`: list of {date, slug, title, tone, patreon_url, linkedin_id, examples_path}. A run for an already-used slug is skipped. Workflow commits state back with `[skip ci]`.

## 8. Secrets
`ANTHROPIC_API_KEY`, `EXAMPLES_REPO_TOKEN` (fine-grained PAT, contents:write on examples repo), `PATREON_SESSION_ID`, `PATREON_CREATOR_URL`, `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_PERSON_URN`, `LINKEDIN_TOKEN_EXPIRES_AT`. Optional `GITHUB_SEARCH_TOKEN`.

## 9. Testing & definition of done
pytest unit tests for every pure stage with LLM/HTTP/Playwright mocked; ruff clean; workflow YAML valid; `python -m pipeline.main run --dry-run` (needs `ANTHROPIC_API_KEY`) produces all artifacts locally without publishing. Done = all plan items in `IMPLEMENTATION_PLAN.md` checked and `PROGRESS.md` current.

## 10. Session-continuity rule
At the start of every session read `PROGRESS.md` + `IMPLEMENTATION_PLAN.md`; at the end tick completed items, log decisions/blockers, and set "Next action". Commit docs with code.
