# sw-test-patreon-linkedin-poster

Automated weekly content: research AI-in-software-testing signals → build and **actually run** a demo (pushed to [sw-testing-developing-tech-examples](https://github.com/priyeshkpandey/sw-testing-developing-tech-examples)) → write a visual Patreon post for paid members → promote it on LinkedIn with a tone that rotates every post. All on GitHub Actions.

Spec: [`docs/BUILD_PROMPT.md`](docs/BUILD_PROMPT.md) · Review: [`docs/PROMPT_REVIEW.md`](docs/PROMPT_REVIEW.md) · Plan: [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md) · Progress: [`docs/PROGRESS.md`](docs/PROGRESS.md)

## Important caveat — Patreon
Patreon's API cannot create posts. Publishing drives the Patreon web editor with Playwright using your session cookie. This is unofficial, may break when Patreon changes its UI, may conflict with Patreon's ToS, and the cookie must be renewed periodically. Start with `patreon_mode=draft`. If it fails, the workflow uploads the content bundle and opens an issue so you can publish by hand, then re-run with the `patreon_url` input to do the LinkedIn step.

## One-time setup (Settings → Secrets and variables → Actions)
| Secret | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | topic, demo, post generation |
| `EXAMPLES_REPO_TOKEN` | fine-grained PAT, Contents: read/write on the examples repo |
| `PATREON_SESSION_ID` | `session_id` cookie from a logged-in patreon.com browser session |
| `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_PERSON_URN`, `LINKEDIN_TOKEN_EXPIRES_AT` | same values/process as `social-media-intel` |

Then: Actions → "Create and publish content" → run with `dry_run=true` → inspect the `content-bundle` artifact → run `dry_run=false, patreon_mode=draft` → finally `publish`, and uncomment the `schedule:` in `content.yml`.

## Local
`make install && make test && ANTHROPIC_API_KEY=… make run` (dry run, publishes nothing).
