# Review of BUILD_PROMPT.md (pre-implementation)

Reviewed against the original brief (`patreon-linkedin-content-creator.rtf`).

## Coverage check
| Brief requirement | Covered in prompt |
|---|---|
| Everything automated via GitHub Actions | §2.3, workflows |
| Approach to auto-post on Patreon | §4 (Playwright + fallback) |
| LinkedIn posting same as social-media-intel | §5 |
| Content backed by real work in examples repo | §2.1, §2.2, stage 3/6 |
| Digestible, visual | §6, stage 4 |
| Marketing-expert LinkedIn, varying tone | §5 tone rotation |
| Prompt doc + review + plan + cross-session tracking | this file, `IMPLEMENTATION_PLAN.md`, `PROGRESS.md`, §10 |

## Issues found and resolutions
1. **Patreon has no post-creation API** — the largest risk. Resolved by explicit decision record (§4) and a no-loss fallback. *Open for the owner:* accept the ToS risk of automation, or prefer the semi-manual path.
2. **LLM-generated demos can be fake/untested** — resolved: demo must execute, metrics are read from the captured run, failure aborts.
3. **Examples repo is empty** — pipeline must create the first commit (handled: clone, create `examples/` and a root README if missing).
4. **Patreon image upload via UI is brittle** — fallback: if inline upload fails, link charts from examples repo raw URLs and include them in the demo folder.
5. **Duplicate topics / repeated tone** — resolved via `state/history.json` rules.
6. **Partial failures** (Patreon ok, LinkedIn fails) — state is written after each publish so reruns resume; LinkedIn step can be re-run alone with `patreon_url`.
7. **Cost/safety** — API budget cap per run, dry-run default, generated demo code executed only on the ephemeral runner with no secrets in its environment.
8. **Unverifiable here:** live Patreon selectors, LinkedIn token, and PAT scopes cannot be validated without the owner's credentials; marked UNVERIFIED in the plan.

Verdict: prompt approved with the above amendments already folded in.
