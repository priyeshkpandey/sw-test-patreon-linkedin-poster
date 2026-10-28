"""Stage 3 — have the model write an experiment, then actually run it. Metrics come only from the run.

The experiment's job is to learn what works and what doesn't. A technique that fails is a valid
result. Only *harness* errors (crash / invalid results.json) are retried; if the harness never
runs, a `harness_failed` result is returned (never an exception) so an honest post can still be made.
"""

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

SYSTEM = """You write small, honest, runnable Python experiments for an SDET audience. The goal is
to LEARN what works and what does not — not to make the technique look good. Include cases where
it is expected to struggle. Never tune thresholds/data until results look favourable; report
failures and weak spots as plainly as successes.
Rules:
- Python stdlib only, deterministic (seed any randomness), no network, no secrets, <60s runtime.
- Files: `demo.py` (run as `python demo.py`; writes `results.json` in the cwd), `test_demo.py`
  (unittest; asserts the HARNESS is sound — deterministic, schema valid — NOT that the technique succeeds), `README.md` (what/why/how to run).
- If the topic involves an LLM, simulate it with a clearly labelled deterministic stub and SAY so
  in the README — never pretend a stub is a real model.
- `results.json` schema (required):
  {"verdict": "one honest sentence: when it works and when it does not",
   "summary": {"<metric>": number, ...},
   "outcomes": [{"case": str, "verdict": "worked"|"partial"|"failed", "evidence": str}],  # >=3, include failures
   "chart": {"title": str, "ylabel": str, "labels": [str], "series": {"<name>": [number]}},
   "table": {"columns": [str], "rows": [[...]]},
   "notes": [str]}   # include honest limitations
Reply with JSON only: {"files": {"demo.py": "...", "test_demo.py": "...", "README.md": "..."}}"""

REQUIRED_KEYS = ("verdict", "summary", "outcomes", "chart", "table", "notes")
VERDICTS = ("worked", "partial", "failed")


def validate_results(res: dict) -> None:
    missing = [k for k in REQUIRED_KEYS if k not in res]
    if missing:
        raise ValueError(f"results.json missing keys: {missing}")
    for o in res["outcomes"]:
        if o.get("verdict") not in VERDICTS or not o.get("case") or not o.get("evidence"):
            raise ValueError(f"invalid outcome entry: {o!r}")
    if not res["outcomes"]:
        raise ValueError("outcomes must not be empty")
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


def harness_failed(topic: dict, attempts: list[str]) -> dict:
    """Honest result for a run whose harness never worked — still publishable as a 'what broke' post."""
    return {
        "status": "harness_failed",
        "verdict": "I could not get a working experiment for this topic; the attempt log shows where it broke.",
        "summary": {"attempts": len(attempts)},
        "outcomes": [{"case": f"attempt {i}", "verdict": "failed", "evidence": a[:300]}
                     for i, a in enumerate(attempts, 1)],
        "table": {"columns": ["attempt", "error"], "rows": [[i, a[:200]] for i, a in enumerate(attempts, 1)]},
        "notes": [f"Topic: {topic.get('title', '')}", "No measured technique results exist for this run."],
        "attempt_log": attempts,
    }


def build_and_run(topic: dict, folder: Path, *, client=None) -> dict:
    """Return a results dict (status "ok" or "harness_failed"). Never raises for experiment problems."""
    attempts: list[str] = []
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
            res["status"] = "ok"
            res["_test_log"] = tests.stderr.strip()[-500:]
            return res
        except Exception as exc:  # noqa: BLE001 — feed any failure back for repair
            log.warning("demo: attempt %d failed: %s", attempt, exc)
            attempts.append(str(exc))
            feedback = (f"Your previous attempt failed to RUN (harness error). Fix the harness only — "
                        f"do not change the experiment to make results look better.\nError: {exc}")
    log.warning("demo: harness never worked after %d attempts — publishing as harness_failed",
                DEMO_MAX_ATTEMPTS)
    folder.mkdir(parents=True, exist_ok=True)
    res = harness_failed(topic, attempts)
    (folder / "ATTEMPTS.md").write_text(
        "# Attempt log\n\n" + "\n\n".join(f"## Attempt {i}\n```\n{a}\n```" for i, a in enumerate(attempts, 1)),
        encoding="utf-8")
    (folder / "results.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    return res
