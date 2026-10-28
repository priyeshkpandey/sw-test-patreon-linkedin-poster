# Review of BUILD_PROMPT.md (pre-implementation)

Reviewed against the original brief (`patreon-linkedin-content-creator.rtf`).

## Coverage check
| Brief requirement | Covered in prompt |
|---|---|
| Everything automated via GitHub Actions | §2.3, workflows |
| Approach to auto-post on Patreon | §4 (Playwright + fallback) |
| LinkedIn posting same as social-media-intel | §5 |
| Content backed by real work in examples repo; shows what works *and* what doesn't | §2.1 (negative results are publishable), §2.2, stage 3/6, §6 |
| Digestible, visual | §6, stage 4 |
| Marketing-expert LinkedIn, varying tone | §5 tone rotation |
| Prompt doc + review + plan + cross-session tracking | this file, `IMPLEMENTATION_PLAN.md`, `PROGRESS.md`, §10 |

## Issues found and resolutions
1. **Patreon has no post-creation API** — the largest risk. Resolved by explicit decision record (§4), credential-based login (rev 2, replaces session cookie), a no-loss fallback, and Playwright-MCP-driven self-repair PRs (§4.1). *Open for the owner:* accept the ToS risk of automation, or prefer the semi-manual path.
2. **LLM-generated demos can be fake/untested** — resolved: the experiment must execute and metrics are read from the captured run. *Amended (rev 2):* a failing technique or an unfixable harness no longer aborts the run; it is reported honestly as an outcome (`worked/partial/failed`, or `harness_failed` with the attempt log) and the post is built on those observations and insights.
3. **Examples repo is empty** — pipeline must create the first commit (handled: clone, create `examples/` and a root README if missing).
4. **Patreon image upload via UI is brittle** — fallback: if inline upload fails, link charts from examples repo raw URLs and include them in the demo folder.
5. **Duplicate topics / repeated tone** — resolved via `state/history.json` rules.
6. **Partial failures** (Patreon ok, LinkedIn fails) — state is written after each publish so reruns resume; LinkedIn step can be re-run alone with `patreon_url`.
7. **Cost/safety** — API budget cap per run, dry-run default, generated demo code executed only on the ephemeral runner with no secrets in its environment.
8. **Unverifiable here:** live Patreon selectors, LinkedIn token, and PAT scopes cannot be validated without the owner's credentials; marked UNVERIFIED in the plan.

## Rev 2 amendments (owner feedback)
- Replaced the hard-abort rule with outcome-based reporting (§2.1, §6).
- Replaced cookie auth with `PATREON_EMAIL`/`PATREON_PASSWORD` login (§4); captcha/2FA is detected and routed to manual fallback.
- Added self-healing repair workflow using the Playwright MCP (§4.1). Review notes: the repair agent holds the Patreon credentials, so it is restricted to draft mode, one file, PR-only, and no secret output; its fixes are unverifiable until run against the live site.

Verdict: prompt approved with the above amendments already folded in.
