"""Orchestrator. Generates a ready-to-upload content bundle; publishes nothing.

    python -m pipeline.main run [--no-push-examples]

Bundle (out/bundle/): patreon_post.html (open in a browser, copy, paste into Patreon), patreon_post.md,
the images, linkedin_post.txt (replace [PATREON_LINK]), UPLOAD_GUIDE.md, results/signals/topic JSON.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import sys

from pipeline import content, demo, examples_repo, linkedin_post, research, state, topic, visuals
from pipeline.config import OUT_DIR, WORK_DIR

log = logging.getLogger("pipeline")

GUIDE = """# Upload guide — {title}

Verdict from the experiment: **{verdict}** (status: {status})

## Patreon
1. Open `patreon_post.html` in a browser (keep it in this folder so the images load).
2. Select all, copy, and paste into a new Patreon post (Create → Text). Set the audience to paid members.
   If an image does not paste, upload the file from this folder at the matching spot
   ({images}).
3. Title: **{title}**
4. Fallback: `patreon_post.md` is the same content as Markdown.
5. The post links to the code at {examples_url}. {examples_note}

## LinkedIn (after the Patreon post is live)
1. Open `linkedin_post.txt` (tone: **{tone}**).
2. Replace `[PATREON_LINK]` with the Patreon post URL.
3. Attach `card.png` as the image.
"""


def run(push_examples: bool = True) -> int:
    bundle = OUT_DIR / "bundle"
    bundle.mkdir(parents=True, exist_ok=True)
    date = dt.date.today().isoformat()
    history = state.load()

    signals = research.gather()
    tp = topic.choose(signals, state.used_slugs(history))
    slug = tp["slug"]

    folder = WORK_DIR / "demo" / slug
    results = demo.build_and_run(tp, folder)

    chart = visuals.bar_chart(results, bundle / "chart.png")  # None when harness_failed
    outcomes = visuals.outcomes_chart(results, bundle / "outcomes.png")
    card = visuals.summary_card(results, tp["title"], bundle / "card.png")
    images = [p for p in (chart, outcomes, card) if p]

    tree_url, _ = examples_repo.public_urls(date, slug)
    md, unverified = content.write_post(tp, results, folder, tree_url, signals)
    html = content.to_html(md, {f"IMG_{p.stem.upper()}": p.name for p in images})
    tone = state.pick_tone(history, slug)
    log.info("topic=%s tone=%s status=%s", slug, tone, results["status"])

    pushed = False
    if push_examples and os.environ.get("EXAMPLES_REPO_TOKEN"):
        examples_repo.push(folder, images, date, slug, checkout=WORK_DIR / "examples-checkout")
        pushed = True
    elif push_examples:
        log.warning("EXAMPLES_REPO_TOKEN not set — examples not pushed")

    public = {k: v for k, v in results.items() if k != "_test_log"}
    (bundle / "patreon_post.md").write_text(md, encoding="utf-8")
    (bundle / "patreon_post.html").write_text(f'<meta charset="utf-8">\n{html}', encoding="utf-8")
    if unverified:
        (bundle / "REVIEW_NOTES.md").write_text(
            "# Check before posting\n\nThese numbers appear in `patreon_post.md` but could not be traced to "
            "`results.json` (even after one rewrite). Verify each one or edit it out:\n\n"
            + "\n".join(f"- {n}" for n in unverified) + "\n", encoding="utf-8")
    (bundle / "linkedin_post.txt").write_text(linkedin_post.write(tp, results, tone), encoding="utf-8")
    (bundle / "results.json").write_text(json.dumps(public, indent=2), encoding="utf-8")
    (bundle / "signals.json").write_text(json.dumps(signals, indent=2), encoding="utf-8")
    (bundle / "topic.json").write_text(json.dumps(tp, indent=2), encoding="utf-8")
    (bundle / "UPLOAD_GUIDE.md").write_text(GUIDE.format(
        title=tp["title"], verdict=results["verdict"], status=results["status"],
        images=", ".join(p.name for p in images), tone=tone, examples_url=tree_url,
        examples_note="(pushed to the examples repo)" if pushed else
        "NOT pushed this run — commit the `demo/` folder there yourself so the link works."),
        encoding="utf-8")
    if not pushed:
        import shutil
        shutil.copytree(folder, bundle / "demo", dirs_exist_ok=True)

    state.update_last(slug, {"date": date, "title": tp["title"], "tone": tone,
                             "status": results["status"],
                             "examples_path": examples_repo.folder_name(date, slug),
                             "examples_pushed": pushed})
    log.info("bundle ready in %s", bundle)
    return 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(name)s :: %(message)s",
                        stream=sys.stderr)
    p = argparse.ArgumentParser(prog="pipeline")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--no-push-examples", action="store_true")
    a = p.parse_args(argv)
    try:
        return run(push_examples=not a.no_push_examples)
    except (RuntimeError, ValueError) as exc:
        log.error("%s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
