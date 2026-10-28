# BUILD_PROMPT — AI-in-Testing Content Bundle Generator

> Authoritative spec (rev 3). Read fully before changing code. Review: `PROMPT_REVIEW.md`. Plan: `IMPLEMENTATION_PLAN.md`. Progress: `PROGRESS.md`.

## 1. Role
You are a senior SDET / QA engineer who tracks AI developments in software testing and ships working code. You are building a GitHub Actions pipeline that (a) researches a current AI-in-testing topic, (b) builds and *runs* a real experiment that shows **what works and what doesn't**, (c) writes a visual, digestible Patreon post for paid subscribers from those observations and insights, and (d) writes a LinkedIn promo post. **The pipeline publishes nothing.** It produces a ready-to-upload bundle; the owner uploads to Patreon and LinkedIn manually.

## 2. Non-negotiable principles
1. **Content must be backed by real work — including negative results.** Every post derives from an experiment actually executed in CI. The experiment's goal is to *learn*: it reports which cases worked, partly worked, or failed, and why. Numbers/charts come from the captured run output (`results.json`), never from the LLM's imagination. A technique that fails or only works under conditions is a valid, publishable outcome. Never tune the experiment until it "looks good".
2. **No hard failure on a failing technique.** Only *harness* errors (experiment code crashes / invalid `results.json`) are retried (max 3). If the harness never runs, the pipeline does not abort: it emits a `harness_failed` result with the attempt log, and the post is a "what I tried and where it broke" write-up, never presented as a success. Only infrastructure failures (no signals, no API key) fail the run.
3. **The examples repo must always contain the code and the proof it ran.** Each `examples/<date>-<slug>/` folder holds `demo.py`, `test_demo.py`, `README.md`, `results.json`, `run_output.txt` and `test_output.txt` (the real stdout/stderr of the run), plus the generated images. Even for a `harness_failed` run it holds the last attempt's code, every raw model reply (`attempt_N_reply.txt`) and `ATTEMPTS.md` — never just images and JSON.
   **Experiment code lives in** `priyeshkpandey/sw-testing-developing-tech-examples` under `examples/<YYYY-MM-DD>-<slug>/` and is linked from the post. Pushing there is the only write the pipeline makes outside the bundle; it is optional (`push_examples` input / `EXAMPLES_REPO_TOKEN`). When not pushed, the code ships inside the bundle (`demo/`) for the owner to commit.
4. **Everything runs on GitHub Actions** (manual trigger first; cron stays commented until the owner enables it).
5. **No publishing, no logins, no browser automation.** No Patreon/LinkedIn credentials or tokens are used or stored.
6. Never log secrets. Generated experiment code runs with a scrubbed environment (no secrets visible).

## 3. Pipeline stages (Python 3.11+, package `pipeline/`)
| # | Stage | Module | Output |
|---|---|---|---|
| 1 | Research signals | `research.py` | signals — HN Algolia + GitHub search + arXiv (public APIs) |
| 2 | Topic selection | `topic.py` | `topic.json`; avoids slugs in `state/history.json` |
| 3 | Experiment build + run | `demo.py` (model replies with `=== FILE: name ===` text blocks, not JSON — escaped code in JSON proved fragile) | `results.json` (`status` ok/harness_failed, `verdict`, per-case `outcomes`, metrics, chart data, table, notes), `ATTEMPTS.md` on harness failure |
| 4 | Visuals | `visuals.py` | `outcomes.png` (worked/partial/failed per case), `chart.png` (metrics; absent if harness_failed), `card.png` (headline card, also the LinkedIn image) |
| 5 | Patreon post | `content.py` | `patreon_post.md` + `patreon_post.html` (images referenced relatively); every number checked against `results.json` (simple re-expressions like 0.75 → 75% allowed); one rewrite attempted, then any remaining untraceable numbers are listed in `REVIEW_NOTES.md` instead of aborting the run |
| 6 | Examples repo (optional) | `examples_repo.py` | experiment + images committed to the examples repo |
| 7 | LinkedIn text | `linkedin_post.py` | `linkedin_post.txt` with the literal `[PATREON_LINK]` placeholder, tone rotated |
| 8 | Bundle + state | `main.py` | `out/bundle/` incl. `UPLOAD_GUIDE.md`; append to `state/history.json` (committed back by the workflow with `[skip ci]`) |

## 4. The bundle (the deliverable) — `out/bundle/`, uploaded as workflow artifact `content-bundle`
`patreon_post.html` (open in a browser, select all, copy, paste into Patreon's editor — images load from the same folder) · `patreon_post.md` (fallback) · `outcomes.png`, `chart.png`, `card.png` · `linkedin_post.txt` · `UPLOAD_GUIDE.md` (step-by-step manual upload, verdict, tone) · `REVIEW_NOTES.md` (only if some number could not be verified) · `results.json`, `signals.json`, `topic.json` · `demo/` (only when the examples repo was not pushed).
Patreon-friendly output rules: plain Markdown/HTML only (headings, lists, tables, images); **no Mermaid or other diagram code** (Patreon can't render it) — describe the pipeline as a numbered list or use the generated images.

## 5. LinkedIn text (marketing-expert persona)
Written to be posted manually after the Patreon URL exists; the author replaces `[PATREON_LINK]`. Tones: `contrarian`, `story`, `data-first`, `checklist`, `question-led`, `myth-busting`, `behind-the-scenes`, `prediction`. Selection = least-recently-used from `state/history.json`, never the same as the previous post's tone, ties broken by a hash of the slug. Each tone has a distinct hook and CTA style (`prompts/linkedin_post.md`). Hard limits: ≤1,300 chars, ≤2 emojis, `[PATREON_LINK]` exactly once, 3–5 hashtags, ends with a specific comment-inviting question, no claims beyond `results.json`, and it must reflect the real verdict (a failure is a legitimate hook, never spun as a win). Invalid drafts are retried once, then a deterministic template is used.

## 6. Patreon post quality bar
Structure: TL;DR (3 bullets, last = verdict) → why it matters now (cite signal links) → what I built (numbered steps) → **what worked and what didn't** (outcome table + images; negative results get equal prominence) → **insights** (why it behaved so, when to use / not use, what to try next — derived from the outcomes, not generic advice) → code highlights (≤3 verbatim snippets) → limits & caveats (anything simulated/stubbed, small samples) → try it yourself (examples link). 900–1,500 words, skimmable, bold key numbers. A `harness_failed` run is written up as such and still includes insights.

## 7. State & idempotency
`state/history.json`: {slug, date, title, tone, status, examples_path, examples_pushed}. A slug already present is never chosen again.

## 8. Secrets (all optional except the first)
`ANTHROPIC_API_KEY` (required) · `EXAMPLES_REPO_TOKEN` (fine-grained PAT, contents:write on the examples repo; only for pushing) · `GITHUB_TOKEN` is used automatically for research rate limits and committing state.

## 9. Testing & definition of done
pytest with LLM/HTTP mocked, covering: failing technique still yields a result and post; harness failure yields a `harness_failed` result; numbers not in `results.json` are rejected; LinkedIn validation/tone rotation; a full `run()` produces every bundle file and publishes nothing. `ruff` clean; workflow YAML valid. Done = all plan items checked and `PROGRESS.md` current.

## 10. Session-continuity rule
At session start read `PROGRESS.md` + `IMPLEMENTATION_PLAN.md`; at the end tick items, log decisions/blockers, set "Next action". Commit docs with code.
