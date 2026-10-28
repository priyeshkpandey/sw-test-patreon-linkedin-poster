"""Stage 3 — have the model write a demo, then actually run it. Metrics come only from the run."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from pathlib import Path

from pipeline import llm
from pipeline.config import DEMO_MAX_ATTEMPTS, DEMO_TIMEOUT_S, SONNET_MODEL

log = logging.getLogger(__name__)

SYSTEM = """You write small, honest, runnable Python demos for an SDET audience.
Rules:
- Python stdlib only, deterministic (seed any randomness), no network, no secrets, <60s runtime.
- Files: `demo.py` (run as `python demo.py`; writes `results.json` in the cwd), `test_demo.py`
  (unittest; asserts the demo's invariants), `README.md` (what/why/how to run).
- If the topic involves an LLM, simulate it with a clearly labelled deterministic stub and SAY so
  in the README — never pretend a stub is a real model.
- `results.json` schema (required):
  {"summary": {"<metric>": number, ...},
   "chart": {"title": str, "ylabel": str, "labels": [str], "series": {"<name>": [number]}},
   "table": {"columns": [str], "rows": [[...]]},
   "notes": [str]}   # include honest limitations
Reply with JSON only: {"files": {"demo.py": "...", "test_demo.py": "...", "README.md": "..."}}"""

REQUIRED_KEYS = ("summary", "chart", "table", "notes")


def validate_results(res: dict) -> None:
    missing = [k for k in REQUIRED_KEYS if k not in res]
    if missing:
        raise ValueError(f"results.json missing keys: {missing}")
    ch = res["chart"]
    n = len(ch["labels"])
    if not ch["series"] or any(len(v) != n for v in ch["series"].values()):
        raise ValueError("chart series lengths must match labels")


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    # Scrubbed environment: generated code must never see secrets.
    env = {"PATH": os.environ.get("PATH", ""), "PYTHONHASHSEED": "0", "HOME": str(cwd)}
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True,
                          timeout=DEMO_TIMEOUT_S, check=False)


def _write_files(files: dict[str, str], folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        target = (folder / name).resolve()
        if folder.resolve() not in target.parents:
            raise ValueError(f"unsafe file path from model: {name!r}")
        target.write_text(content, encoding="utf-8")


def build_and_run(topic: dict, folder: Path, *, client=None) -> dict:
    """Return results dict. Raises RuntimeError if no attempt produces a passing, valid run."""
    feedback = ""
    for attempt in range(1, DEMO_MAX_ATTEMPTS + 1):
        prompt = f"Topic: {json.dumps(topic)}\n{feedback}"
        reply = llm.complete(SYSTEM, prompt, model=SONNET_MODEL, max_tokens=8000, client=client)
        try:
            files = llm.extract_json(reply)["files"]
            _write_files(files, folder)
            (folder / "results.json").unlink(missing_ok=True)
            run = _run([sys.executable, "demo.py"], folder)
            if run.returncode != 0:
                raise RuntimeError(f"demo.py exit {run.returncode}:\n{run.stderr[-1500:]}")
            tests = _run([sys.executable, "-m", "unittest", "-q", "test_demo"], folder)
            if tests.returncode != 0:
                raise RuntimeError(f"tests failed:\n{tests.stderr[-1500:]}")
            res = json.loads((folder / "results.json").read_text(encoding="utf-8"))
            validate_results(res)
            res["_test_log"] = tests.stderr.strip()[-500:]
            return res
        except Exception as exc:  # noqa: BLE001 — feed any failure back for repair
            log.warning("demo: attempt %d failed: %s", attempt, exc)
            feedback = f"Your previous attempt failed. Fix it.\nError: {exc}"
    raise RuntimeError(f"demo: no working demo after {DEMO_MAX_ATTEMPTS} attempts — aborting run")
