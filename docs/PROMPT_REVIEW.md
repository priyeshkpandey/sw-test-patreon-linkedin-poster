# Review of BUILD_PROMPT.md

Reviewed against the original brief (`patreon-linkedin-content-creator.rtf`) and owner feedback.

## Revision history
- **rev 1:** initial spec (auto-posting to Patreon via Playwright cookie, LinkedIn via API).
- **rev 2:** failing techniques are findings, not aborts (outcome-based reporting); Patreon credential login + Playwright-MCP self-repair.
- **rev 3 (owner feedback: "too complicated"):** all publishing removed. The pipeline only produces a ready-to-upload bundle; the owner posts to Patreon and LinkedIn manually. Removed: Patreon/LinkedIn publishers, credentials/tokens, repair and publish-held workflows, resume commands, exit codes. **This supersedes the brief's "post automatically" and "LinkedIn same as social-media-intel" instructions by explicit owner decision.**

## Coverage check (rev 3)
| Brief requirement | Status |
|---|---|
| Everything automated via GitHub Actions | Content generation yes; publishing deliberately manual (owner decision) |
| Approach to post on Patreon | Superseded: manual upload; bundle is paste-ready (§4) |
| LinkedIn posting like social-media-intel | Superseded: text generated, posted manually; `[PATREON_LINK]` placeholder |
| Content backed by real work; shows what works and what doesn't | §2.1–2.3, §6 |
| Digestible, visual | §4, §6 (images generated from real data) |
| Marketing-expert LinkedIn, tone varies each post | §5 rotation |
| Prompt doc + review + plan + cross-session tracking | this set of docs, §10 |

## Risks and resolutions
1. **Fabricated/untested content** — experiment must execute; numbers checked against `results.json`; harness failures reported honestly (§2.1–2.2).
2. **Patreon paste fidelity** — the HTML paste path is unverified against Patreon's editor; mitigated by separate image files, Markdown fallback, and the upload guide. No diagrams that Patreon can't render (§4).
3. **Examples repo is empty** — first push creates the initial commit; pushing is optional and the code ships in the bundle otherwise.
4. **Duplicate topics / repeated tone** — `state/history.json` rules (§5, §7). Note: topic history is recorded when the bundle is generated, even if the owner never posts it.
5. **Generated code execution** — runs on the ephemeral runner with a scrubbed environment; no secrets present.
6. **Unverifiable here:** an actual end-to-end run needs `ANTHROPIC_API_KEY`; not performed.

Verdict: approved.
