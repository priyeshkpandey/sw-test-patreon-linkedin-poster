"""Orchestrator.

    python -m pipeline.main run [--dry-run] [--patreon-url URL]
    python -m pipeline.main linkedin --patreon-url URL      # resume after a Patreon-only success
    python -m pipeline.main patreon --bundle DIR            # publish a held bundle (after a repair), then LinkedIn

Exit codes: 0 ok · 1 other failure · 2 Patreon UI flow broke (repairable by patreon-repair) ·
3 Patreon login challenge / missing credentials (needs the owner).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import sys
from pathlib import Path

from pipeline import content, demo, examples_repo, linkedin_post, research, state, topic, visuals
from pipeline.config import OUT_DIR, WORK_DIR
from pipeline.publishers import linkedin as li
from pipeline.publishers import patreon

log = logging.getLogger("pipeline")


def run(dry_run: bool, patreon_url: str | None = None) -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    date = dt.date.today().isoformat()
    history = state.load()

    signals = research.gather()
    (OUT_DIR / "signals.json").write_text(json.dumps(signals, indent=2))
    tp = topic.choose(signals, state.used_slugs(history))
    slug = tp["slug"]
    (OUT_DIR / "topic.json").write_text(json.dumps(tp, indent=2))

    folder = WORK_DIR / "demo" / slug
    results = demo.build_and_run(tp, folder)
    (OUT_DIR / "results.json").write_text(json.dumps(results, indent=2))

    chart = visuals.bar_chart(results, OUT_DIR / "chart.png")  # None when harness_failed
    outcomes = visuals.outcomes_chart(results, OUT_DIR / "outcomes.png")
    card = visuals.summary_card(results, tp["title"], OUT_DIR / "card.png")
    images = [p for p in (chart, outcomes, card) if p]

    tree_url, raw_base = examples_repo.public_urls(date, slug)
    md = content.write_post(tp, results, folder, tree_url, signals)
    html = content.to_html(md, {f"IMG_{p.stem.upper()}": f"{raw_base}/{p.name}" for p in images})
    (OUT_DIR / "patreon_post.md").write_text(md)
    (OUT_DIR / "patreon_post.html").write_text(html)

    tone = state.pick_tone(history, slug)
    log.info("topic=%s tone=%s dry_run=%s", slug, tone, dry_run)

    if dry_run:
        preview_url = patreon_url or "https://www.patreon.com/posts/DRY-RUN-PREVIEW"
        (OUT_DIR / "linkedin_post.txt").write_text(linkedin_post.write(tp, results, preview_url, tone))
        log.info("dry run complete — artifacts in %s; nothing published", OUT_DIR)
        return 0

    examples_repo.push(folder, images, date, slug,
                       checkout=WORK_DIR / "examples-checkout")
    state.update_last(slug, {"date": date, "title": tp["title"], "tone": tone,
                             "status": results["status"],
                             "examples_path": examples_repo.folder_name(date, slug),
                             "topic": tp,
                             "results": {k: v for k, v in results.items() if k != "_test_log"}})

    if not patreon_url:
        patreon_url = patreon.publish(tp["title"], html)
    state.update_last(slug, {"patreon_url": patreon_url})
    return _post_linkedin(tp, results, patreon_url, tone, slug, card)


def _post_linkedin(tp: dict, results: dict, patreon_url: str, tone: str, slug: str, image: Path) -> int:
    text = linkedin_post.write(tp, results, patreon_url, tone)
    (OUT_DIR / "linkedin_post.txt").write_text(text)
    li.cmd_post(str(OUT_DIR / "linkedin_post.txt"), image_file=str(image))
    state.update_last(slug, {"linkedin_posted": True})
    return 0


def resume_linkedin(patreon_url: str) -> int:
    """Re-run only the LinkedIn step for the latest recorded post (after a manual Patreon publish)."""
    history = state.load()
    if not history:
        raise RuntimeError("no state to resume from")
    last = history[-1]
    results, tp = last["results"], last["topic"]
    state.update_last(last["slug"], {"patreon_url": patreon_url})
    return _post_linkedin(tp, results, patreon_url, last["tone"], last["slug"], OUT_DIR / "card.png")


def resume_patreon(bundle: Path) -> int:
    """Publish a previously generated bundle (patreon_post.html + card.png) to Patreon, then LinkedIn."""
    history = state.load()
    if not history:
        raise RuntimeError("no state to resume from")
    last = history[-1]
    topic_, results = last["topic"], last["results"]
    html = (bundle / "patreon_post.html").read_text(encoding="utf-8")
    url = patreon.publish(topic_["title"], html)
    state.update_last(last["slug"], {"patreon_url": url})
    return _post_linkedin(topic_, results, url, last["tone"], last["slug"], bundle / "card.png")


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(name)s :: %(message)s",
                        stream=sys.stderr)
    p = argparse.ArgumentParser(prog="pipeline")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--dry-run", action="store_true")
    r.add_argument("--patreon-url", default=os.environ.get("PATREON_URL_OVERRIDE") or None)
    li_p = sub.add_parser("linkedin")
    li_p.add_argument("--patreon-url", required=True)
    pt = sub.add_parser("patreon")
    pt.add_argument("--bundle", required=True, type=Path)
    a = p.parse_args(argv)
    try:
        if a.cmd == "run":
            return run(a.dry_run, a.patreon_url)
        if a.cmd == "linkedin":
            return resume_linkedin(a.patreon_url)
        return resume_patreon(a.bundle)
    except patreon.PatreonChallenge as exc:
        log.error("%s", exc)
        return 3
    except patreon.PatreonError as exc:
        log.error("%s", exc)
        return 2
    except RuntimeError as exc:
        log.error("%s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
