# sw-test-patreon-linkedin-poster

Automated weekly content: research AI-in-software-testing signals → build and **actually run** an experiment that shows what works *and* what doesn't (pushed to [sw-testing-developing-tech-examples](https://github.com/priyeshkpandey/sw-testing-developing-tech-examples)) → write a visual Patreon post of the observations and insights for paid members → promote it on LinkedIn with a tone that rotates every post. All on GitHub Actions.

Spec: [`docs/BUILD_PROMPT.md`](docs/BUILD_PROMPT.md) · Review: [`docs/PROMPT_REVIEW.md`](docs/PROMPT_REVIEW.md) · Plan: [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md) · Progress: [`docs/PROGRESS.md`](docs/PROGRESS.md)

## Important caveat — Patreon
Patreon's API cannot create posts. Publishing drives the Patreon web editor with Playwright, logging in with your email/password (stored as secrets) on every run. This is unofficial and may conflict with Patreon's ToS; use `patreon_mode=draft` first.

- **UI changed (exit 2):** `patreon-repair.yml` runs Claude Code with the Playwright MCP, explores the live Patreon UI, fixes `pipeline/publishers/patreon.py`, tests in draft mode, and opens a PR. Review and merge it, then run **Publish held Patreon bundle** with the failed run's id.
- **Captcha / verification code / 2FA / bad credentials (exit 3):** not auto-repairable. Publish the `content-bundle` artifact by hand, then re-run the content workflow with the `patreon_url` input to do the LinkedIn step.
- The repair agent holds your Patreon credentials; it is restricted to draft mode, one file, and PR-only. Still, review its PRs.

## One-time setup (Settings → Secrets and variables → Actions)
| Secret | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | topic, experiment, post generation, and the repair agent |
| `EXAMPLES_REPO_TOKEN` | fine-grained PAT, Contents: read/write on the examples repo |
| `PATREON_EMAIL`, `PATREON_PASSWORD` | Patreon login (a dedicated password is advisable; accounts with 2FA can't log in headlessly) |
| `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_PERSON_URN`, `LINKEDIN_TOKEN_EXPIRES_AT` | same values/process as `social-media-intel` |

Then: Actions → "Create and publish content" → run with `dry_run=true` → inspect the `content-bundle` artifact → run `dry_run=false, patreon_mode=draft` → finally `publish`, and uncomment the `schedule:` in `content.yml`.

## Local
`make install && make test && ANTHROPIC_API_KEY=… make run` (dry run, publishes nothing).
