"""Central configuration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

ROOT: Final[Path] = Path(__file__).resolve().parent.parent
STATE_FILE: Final[Path] = ROOT / "state" / "history.json"
PROMPTS_DIR: Final[Path] = Path(__file__).parent / "prompts"
WORK_DIR: Final[Path] = Path(os.environ.get("WORK_DIR", ROOT / "work"))
OUT_DIR: Final[Path] = Path(os.environ.get("OUT_DIR", ROOT / "out"))

SONNET_MODEL: Final[str] = "claude-sonnet-5-5"
HAIKU_MODEL: Final[str] = "claude-haiku-5-5"

EXAMPLES_REPO: Final[str] = os.environ.get(
    "EXAMPLES_REPO", "priyeshkpandey/sw-testing-developing-tech-examples"
)
EXAMPLES_BRANCH: Final[str] = "main"

SIGNAL_LOOKBACK_DAYS: Final[int] = 14
DEMO_MAX_ATTEMPTS: Final[int] = 3
DEMO_TIMEOUT_S: Final[int] = 120
LINKEDIN_MAX_CHARS: Final[int] = 1300

TONES: Final[tuple[str, ...]] = (
    "contrarian",
    "story",
    "data-first",
    "checklist",
    "question-led",
    "myth-busting",
    "behind-the-scenes",
    "prediction",
)
