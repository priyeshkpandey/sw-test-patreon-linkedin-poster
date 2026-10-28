# sw-test-patreon-linkedin-poster

A GitHub Actions pipeline that researches current AI-in-software-testing developments, **runs a real experiment** showing what works and what doesn't, and produces a ready-to-upload bundle: a visual Patreon post, a LinkedIn promo text (tone rotates each time), and the experiment code (optionally pushed to [sw-testing-developing-tech-examples](https://github.com/priyeshkpandey/sw-testing-developing-tech-examples)).

**It posts nothing.** You upload to Patreon and LinkedIn yourself.

Spec: [`docs/BUILD_PROMPT.md`](docs/BUILD_PROMPT.md) · Review: [`docs/PROMPT_REVIEW.md`](docs/PROMPT_REVIEW.md) · Plan: [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md) · Progress: [`docs/PROGRESS.md`](docs/PROGRESS.md)

## Setup
Settings → Secrets and variables → Actions:
| Secret | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | required: topic, experiment and post generation |
| `EXAMPLES_REPO_TOKEN` | optional: fine-grained PAT, Contents read/write on the examples repo, to push the experiment |

### Creating `EXAMPLES_REPO_TOKEN` (optional)
Only needed if you want the workflow to push each experiment to the examples repo.
1. GitHub → your avatar → **Settings** → **Developer settings** → **Personal access tokens** → **Fine-grained tokens** → **Generate new token**.
2. **Token name:** e.g. `examples-repo-push`. **Expiration:** your choice (e.g. 90 days; set a reminder to renew).
3. **Resource owner:** `priyeshkpandey`.
4. **Repository access:** *Only select repositories* → choose `sw-testing-developing-tech-examples`.
5. **Permissions → Repository permissions:** set **Contents** to *Read and write*. (Metadata: Read-only is added automatically.) Nothing else is needed.
6. **Generate token** and copy it now; GitHub shows it only once.
7. In *this* repo: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**, name `EXAMPLES_REPO_TOKEN`, paste the token.

If the token expires or is missing, the run still succeeds: the experiment code is included in the bundle's `demo/` folder instead, and you can commit it yourself.

## Use
1. Actions → **Create content bundle** → Run workflow.
2. Download the `content-bundle` artifact and unzip it.
3. Follow `UPLOAD_GUIDE.md` inside: open `patreon_post.html`, copy, paste into a new Patreon post (paid members); then post `linkedin_post.txt` with `[PATREON_LINK]` replaced and `card.png` attached.

## Local
`make install && make test`; `ANTHROPIC_API_KEY=… make run` writes `out/bundle/`.
