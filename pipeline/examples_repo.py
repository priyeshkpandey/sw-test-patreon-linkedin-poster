"""Stage 6 — commit the executed demo (and charts) to the examples repo."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from pipeline.config import EXAMPLES_BRANCH, EXAMPLES_REPO

_README = "# sw-testing-developing-tech-examples\n\nRunnable demos backing the AI-in-testing Patreon posts. Each folder under `examples/` has its own README.\n"


def _git(args: list[str], cwd: Path) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    if r.returncode != 0:
        # never echo args: the remote URL may embed the token
        raise RuntimeError(f"git {args[0]} failed: {r.stderr.replace(os.environ.get('EXAMPLES_REPO_TOKEN', '@@'), '***')[-400:]}")
    return r.stdout


def folder_name(date: str, slug: str) -> str:
    return f"examples/{date}-{slug}"


def public_urls(date: str, slug: str) -> tuple[str, str]:
    base = f"https://github.com/{EXAMPLES_REPO}"
    raw = f"https://raw.githubusercontent.com/{EXAMPLES_REPO}/{EXAMPLES_BRANCH}"
    return f"{base}/tree/{EXAMPLES_BRANCH}/{folder_name(date, slug)}", f"{raw}/{folder_name(date, slug)}"


def push(demo_dir: Path, extra_files: list[Path], date: str, slug: str, checkout: Path) -> None:
    token = os.environ["EXAMPLES_REPO_TOKEN"]
    url = f"https://x-access-token:{token}@github.com/{EXAMPLES_REPO}.git"
    if checkout.exists():
        shutil.rmtree(checkout)
    empty = subprocess.run(["git", "ls-remote", "--heads", url], capture_output=True, text=True).stdout.strip() == ""
    if empty:  # repo has no commits yet
        checkout.mkdir(parents=True)
        _git(["init", "-b", EXAMPLES_BRANCH], checkout)
        _git(["remote", "add", "origin", url], checkout)
        (checkout / "README.md").write_text(_README, encoding="utf-8")
    else:
        _git(["clone", "--depth", "1", url, str(checkout)], checkout.parent)
    dest = checkout / folder_name(date, slug)
    dest.mkdir(parents=True, exist_ok=True)
    for f in demo_dir.iterdir():
        if f.is_file() and f.suffix != ".pyc":
            shutil.copy(f, dest / f.name)
    for f in extra_files:
        shutil.copy(f, dest / f.name)
    _git(["config", "user.name", "content-bot"], checkout)
    _git(["config", "user.email", "content-bot@users.noreply.github.com"], checkout)
    _git(["add", "-A"], checkout)
    _git(["commit", "-m", f"Add example: {slug}"], checkout)
    _git(["push", "origin", EXAMPLES_BRANCH], checkout)
