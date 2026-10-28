# BUILD_PROMPT — Patreon + LinkedIn AI-in-Testing Content Automation

> Authoritative spec. Read fully before changing code. Reviewed in `PROMPT_REVIEW.md`; work is tracked in `IMPLEMENTATION_PLAN.md` and `PROGRESS.md`.

## 1. Role
You are a senior SDET / QA engineer who tracks AI developments in software testing and ships working code. You are building a fully automated (GitHub Actions) pipeline that (a) researches a current AI-in-testing topic, (b) builds and *runs* a real experiment for it that shows **what works and what doesn't**, (c) writes a visual, digestible Patreon post for paid subscribers built on those observations and insights, (d) publishes it, and (e) promotes the Patreon link on LinkedIn with a post whose tone changes every time.

## 2. Non-negotiable principles
1. **Content must be backed by real work — including negative results.** Every Patreon post is derived from an experiment that was actually executed in CI. The goal of the experiment is to *learn*, not to prove the technique works: it must report honestly which cases worked, which failed, and why. Numbers/charts come from the captured run output (`results.json`), never from the LLM's imagination. A technique that fails, underperforms, or only works under conditions is a **valid, publishable outcome** — those posts carry the most useful insights. Never tune the experiment until it "looks good".
   **There is no hard failure on a failing technique.** The only repaired/retried errors are *harness* errors (the experiment code crashes or emits invalid `results.json`). If the harness still cannot be made to run after the retry budget, the run does **not** abort: it records an honest "what I tried and where it broke" outcome (`status: harness_failed`, with the attempt log) and the post is written from that. Only infrastructure failures (no signals, no API key, publisher errors) fail the run.
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
| 3 | Experiment build + run | `demo.py` | `work/demo/` files, `results.json` with `status` (`ok`/`harness_failed`), per-case `outcomes` (worked/partial/failed + evidence), metrics, `ATTEMPTS.md`; up to 3 *harness* repair attempts, never a hard abort |
| 4 | Visuals | `visuals.py` | PNG charts (matplotlib) from `results.json` (chart optional when the harness failed — then an outcomes/attempts card) + a Mermaid diagram in the post body |
| 5 | Patreon post | `content.py` | `patreon_post.md` + `patreon_post.html` embedding image placeholders |
| 6 | Push demo | `examples_repo.py` | commit to examples repo via `EXAMPLES_REPO_TOKEN` |
| 7 | Publish Patreon | `publishers/patreon.py` | `patreon_url` |
| 8 | LinkedIn post | `linkedin_post.py` | `linkedin_post.txt`, tone chosen by rotation |
| 9 | Publish LinkedIn | `publishers/linkedin.py` | post id (same UGC flow as `social-media-intel`) |
| 10 | Record state | `state.py` | append to `state/history.json`, committed back by workflow |

## 4. Patreon publishing approach (critical design decision)
Patreon's public API v2 is **read-only for posts**; there is no endpoint to create one. Options evaluated:
- **A. Browser automation (Playwright) that logs in with the owner's credentials** — chosen. Credentials are stored as GitHub secrets (`PATREON_EMAIL`, `PATREON_PASSWORD`); each run performs a fresh login, so there is no cookie to renew. Risks: Patreon ToS grey area, UI drift, and login challenges (captcha / email verification code / 2FA) which automation cannot solve — these raise `PatreonChallenge`, are *not* auto-repairable, and trigger the manual fallback. Use an account/password dedicated to this where possible.
- B. Reverse-engineered internal JSON API — more brittle/riskier; rejected.
- C. Semi-automatic hand-off (draft package + notification) — **built-in fallback**: if A fails, upload the content bundle as a workflow artifact and open a GitHub issue with the ready-to-paste post; LinkedIn is then skipped until the Patreon URL is supplied (`workflow_dispatch` input `patreon_url`).
Selectors/flow are isolated in `pipeline/publishers/patreon.py` (`SELECTORS`, `login()`, `_drive()`), overridable by env. `PATREON_MODE=draft|publish` — first live runs use `draft`.

### 4.1 Self-healing with the Playwright MCP
When the Patreon flow breaks because the UI changed (not a challenge), the publisher saves debug evidence (`out/patreon_debug/`: screenshot, page HTML, URL, failing step) and the run fails into the fallback. A separate workflow, `patreon-repair.yml`, then launches Claude Code with the **Playwright MCP server** (`npx @playwright/mcp`) to: read the debug evidence → log in and explore the live Patreon creator UI through the MCP → update `SELECTORS`/`login()`/`_drive()` → verify by running the unit tests and a `draft`-mode post → **open a pull request** (never push to `main`; the owner reviews and merges). Rules for the repair agent: change only `pipeline/publishers/patreon.py` and its tests; never print or commit credentials; never publish (draft only); stop and report if a captcha/verification challenge is encountered. After merge, re-run the content workflow (or `patreon` resume command) to publish the held bundle.

## 5. LinkedIn posting
Reuse the `social-media-intel` implementation (`pipeline/publishers/linkedin.py`): UGC Posts API, `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_PERSON_URN`, `LINKEDIN_TOKEN_EXPIRES_AT`, optional image upload, 60-day token expiry issue. Difference: the post contains the Patreon link (as the call to action) and optionally the first chart as the image.

### Tone rotation (marketing-expert persona)
Tones: `contrarian`, `story`, `data-first`, `checklist`, `question-led`, `myth-busting`, `behind-the-scenes`, `prediction`. Selection = least-recently-used from `state/history.json` (ties broken deterministically by hash of the slug); the same tone may never be used in two consecutive posts. Each tone has a distinct hook formula and CTA style in `prompts/linkedin_post.md`. Hard limits: ≤1,300 chars, ≤2 emojis, exactly one link (Patreon), 3–5 hashtags, ends with a comment-inviting question, must not claim facts absent from `results.json`.

## 6. Patreon post quality bar
Structure: TL;DR (3 bullets, incl. the verdict) → why it matters now (cite signals with links) → what I built (architecture diagram) → **what worked / what didn't** (outcome table + charts from real data; negative results get equal prominence) → **insights** (why it behaved this way, when to use it, when not to, what I'd try next) → code highlights (short snippets, link to repo folder) → limits & caveats (simulated parts, small samples) → try-it-yourself. 900–1,500 words. Skimmable: short paragraphs, bold key numbers, alt text on images. A `harness_failed` run becomes a "what I tried and where it broke" post with the same insight section — never presented as a success. LinkedIn promos must reflect the real verdict (a failure is a legitimate hook, never spun as a win).

## 7. State & idempotency
`state/history.json`: list of {date, slug, title, tone, patreon_url, linkedin_id, examples_path}. A run for an already-used slug is skipped. Workflow commits state back with `[skip ci]`.

## 8. Secrets
`ANTHROPIC_API_KEY`, `EXAMPLES_REPO_TOKEN` (fine-grained PAT, contents:write on examples repo), `PATREON_EMAIL`, `PATREON_PASSWORD`, `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_PERSON_URN`, `LINKEDIN_TOKEN_EXPIRES_AT`. Optional `GITHUB_SEARCH_TOKEN`.

## 9. Testing & definition of done
pytest unit tests for every pure stage with LLM/HTTP/Playwright mocked (including: failing technique still yields a post; harness failure yields a `harness_failed` post; login-challenge is distinguished from selector breakage); ruff clean; workflow YAML valid; `python -m pipeline.main run --dry-run` (needs `ANTHROPIC_API_KEY`) produces all artifacts locally without publishing. Done = all plan items in `IMPLEMENTATION_PLAN.md` checked and `PROGRESS.md` current.

## 10. Session-continuity rule
At the start of every session read `PROGRESS.md` + `IMPLEMENTATION_PLAN.md`; at the end tick completed items, log decisions/blockers, and set "Next action". Commit docs with code.
