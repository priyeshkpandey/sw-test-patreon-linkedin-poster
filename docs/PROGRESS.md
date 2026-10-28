# Progress Log (read first each session)

_Last updated: 2026-10-29 (session S2)._

## Current state
- **Working end to end.** Run `40755779914` (workflow "Create content bundle", 2026-10-28 19:36 UTC) finished with `status=ok`: the experiment ran on attempt 2, a real result was produced, the code and run output were pushed to the examples repo, and a full bundle was built. The only warning was one untraceable number (`18`) flagged for review.
- Examples repo now holds `examples/2026-10-28-coverage-vs-mutation-llm-generated-code/` with `demo.py`, `test_demo.py`, `README.md`, `run_output.txt`, `test_output.txt`, `results.json`, `chart.png`, `outcomes.png`, `card.png`.
- 32 unit tests pass, `ruff` clean, `main` pushed (latest code commit `e796952`; the bot adds `chore: update run history [skip ci]` commits after each run).
- `state/history.json` currently holds the one entry from that successful run. Clear it (`[]`) if you want the topic re-picked.
- **Nothing is published automatically.** The owner uploads the bundle to Patreon and LinkedIn by hand (decision rev 3).

## Next actions (in order)
1. Download the `content-bundle` artifact of run `40755779914` (or re-run) and review it: read `patreon_post.md`, check `REVIEW_NOTES.md` (number `18`), `linkedin_post.txt`, `UPLOAD_GUIDE.md`.
2. Test pasting `patreon_post.html` into Patreon's editor; confirm images and tables survive (plan 4.4). Unverified so far.
3. Tune the post/LinkedIn prompts from what the first real output looks like (plan 4.5).
4. Optional cleanup in the examples repo: delete the failed-run folders `2026-10-28-coverage-criteria-vs-llm-style-bugs`, `2026-10-28-coverage-adequate-tests-miss-llm-code-bugs`, `2026-10-28-coverage-vs-mutation-score-llm-generated-code` (images/JSON/empty replies only). Also remove the stale `attempt_N_reply.txt` (0 bytes) and `ATTEMPTS.md` inside the successful folder (see known issues).
5. When satisfied, enable the commented `schedule:` in `.github/workflows/content.yml`.

## Decisions
- **rev 2:** a failing technique is a finding, not an error. The experiment reports worked/partial/failed outcomes. Only harness errors (crash, invalid `results.json`) are retried (max 3); if the harness never runs, a `harness_failed` result and an honest "what I tried and where it broke" post are produced instead of aborting.
- **rev 3 (owner, "too complicated"):** no automated posting to Patreon or LinkedIn; no logins, tokens, Playwright or repair workflows. The pipeline generates a ready-to-upload bundle. This supersedes rev 1/2 Patreon decisions.
- **Untraceable numbers do not abort a run:** one rewrite is attempted, then remaining numbers are listed in `REVIEW_NOTES.md`. Simple re-expressions (0.75 -> 75%) count as traceable.
- **Models:** Sonnet 5.5 for topic/experiment/post, Haiku 5.5 for LinkedIn. Python + pip in CI. Cron stays commented.
- **Examples repo must contain code + proof it ran** (`run_output.txt`, `test_output.txt`), and on failure the raw model replies.

## API gotchas learned from CI logs (do not re-learn)
| Finding | Evidence | Handling |
|---|---|---|
| Sonnet thinks by default and thinking tokens consume `max_tokens` | run 19:22: `blocks=['thinking']`, `text_chars=0`, `out_tokens=16000` on all attempts | `thinking={"type":"between_tools"}` for Sonnet |
| Sonnet rejects `thinking: disabled` | HTTP 400 | use `between_tools` |
| Haiku rejects `between_tools` | HTTP 400 "not supported for this model" | send no thinking param for Haiku (it still returns thinking blocks, so give it a roomy `max_tokens`) |
| JSON-wrapped code fails to parse | 3x "no JSON found" | model returns `=== FILE: name ===` blocks |
| Requests with large `max_tokens` need streaming | SDK refuses long non-streaming calls | `llm.complete` streams above 16000; experiment limit is 32000 |
| Model sometimes puts prose/extra fences inside `demo.py` | SyntaxError on line 1 | `.py` files with fences are rejected with a clear repair message |

The per-model settings live in `pipeline/llm.py` (`THINKING_PARAM`, `STREAM_ABOVE`). Model-specific parameters have been wrong three times: check the `llm:` log line (`blocks=`, `out_tokens=`, `text_chars=`) before changing them.

## Known issues / open questions
- **Stale files in a reused examples folder:** `examples_repo.push` copies into the existing `examples/<date>-<slug>/` without deleting old files, so a rerun of the same slug on the same day keeps leftovers (`attempt_N_reply.txt`, `ATTEMPTS.md`) from an earlier failed run. Not fixed yet. Likely fix: remove the destination folder before copying.
- **Experiment quality:** the successful run's attempt 1 crashed (`TypeError: compile()`) and was repaired on attempt 2; earlier runs failed on wrong self-check values. Retries remain 3 (`DEMO_MAX_ATTEMPTS`); raise it if `harness_failed` recurs.
- **Number check noise:** `18` was flagged; it may be legitimate (e.g. a count not in `results.json`). Review `REVIEW_NOTES.md` each time.
- **Topic marked used on generation**, even if the owner never posts it.
- **Patreon paste fidelity** of `patreon_post.html` is untested.
- **Model-written experiments are simulations** (the prompt requires them to say so); the post must not present them as measurements of real LLMs.

## Session log
- **S1 (2026-10-28):** repo initialised; rev 1 built; rev 2 and rev 3 applied; pushed.
- **S2 (2026-10-28/29):** first live runs. Fixed in order: examples repo had no code (JSON parsing) -> topic JSON truncation -> empty replies (thinking ate the budget; proven by logs) -> wrong per-model thinking params (3 iterations) -> number check aborting a good run -> stray fences/prose in generated files -> raised experiment limit to 32000 with streaming and handled truncation. README gained `EXAMPLES_REPO_TOKEN` instructions. Final run succeeded.
