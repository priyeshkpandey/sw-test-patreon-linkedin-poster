
from pipeline import demo

GOOD_DEMO = '''
import json
json.dump({"verdict": "v", "summary": {"x": 1}, "outcomes": [{"case": "c", "verdict": "failed", "evidence": "e"}], "chart": {"title": "t", "ylabel": "y", "labels": ["a"],
 "series": {"s": [1]}}, "table": {"columns": ["c"], "rows": [[1]]}, "notes": ["n"]},
 open("results.json", "w"))
'''
GOOD_TEST = "import unittest\nclass T(unittest.TestCase):\n    def test_ok(self):\n        self.assertTrue(True)\n"


class FakeClient:
    def __init__(self, replies):
        self.replies = iter(replies)
        self.messages = self

    def create(self, **kw):
        class B:
            type = "text"
            text = next(self.replies)
        return type("R", (), {"content": [B()]})()

    def stream(self, **kw):  # used for large max_tokens
        resp = self.create(**kw)

        class Ctx:
            def __enter__(s): return s
            def __exit__(s, *a): return False
            def get_final_message(s): return resp
        return Ctx()


def reply(demo_py):
    return (f"=== FILE: demo.py ===\n{demo_py}\n=== FILE: test_demo.py ===\n```python\n{GOOD_TEST}```\n"
            "=== FILE: README.md ===\nr\n=== END ===")


def test_runs_and_returns_measured_results(tmp_path):
    res = demo.build_and_run({"title": "t"}, tmp_path, client=FakeClient([reply(GOOD_DEMO)]))
    assert res["summary"] == {"x": 1}


def test_repairs_after_failure(tmp_path):
    c = FakeClient([reply("raise SystemExit(3)"), reply(GOOD_DEMO)])
    assert demo.build_and_run({"title": "t"}, tmp_path, client=c)["summary"]["x"] == 1


def test_failing_technique_is_a_valid_result(tmp_path):
    # outcomes marked "failed" must NOT trigger repair/abort — they are the finding
    res = demo.build_and_run({"title": "t"}, tmp_path, client=FakeClient([reply(GOOD_DEMO)]))
    assert res["status"] == "ok" and res["outcomes"][0]["verdict"] == "failed"


def test_harness_never_works_yields_publishable_result(tmp_path):
    c = FakeClient([reply("raise SystemExit(3)")] * 3)
    res = demo.build_and_run({"title": "t"}, tmp_path, client=c)
    assert res["status"] == "harness_failed" and len(res["outcomes"]) == 3
    assert (tmp_path / "ATTEMPTS.md").is_file() and "chart" not in res
    demo.validate_results({**res, "chart": {"labels": ["a"], "series": {"s": [1]}}})


def test_invalid_outcome_verdict_is_a_harness_error(tmp_path):
    bad = GOOD_DEMO.replace('"failed"', '"great"')
    res = demo.build_and_run({"title": "t"}, tmp_path, client=FakeClient([reply(bad)] * 3))
    assert res["status"] == "harness_failed"


def test_rejects_path_traversal(tmp_path):
    bad = "=== FILE: ../evil.py ===\nx\n=== END ==="
    res = demo.build_and_run({"title": "t"}, tmp_path / "d", client=FakeClient([bad] * 3))
    assert res["status"] == "harness_failed" and not (tmp_path / "evil.py").exists()


def test_secrets_not_visible_to_demo(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret")
    leak = GOOD_DEMO + "\nimport os\nassert 'ANTHROPIC_API_KEY' not in os.environ\n"
    assert demo.build_and_run({"title": "t"}, tmp_path, client=FakeClient([reply(leak)]))


def test_code_and_run_output_are_saved(tmp_path):
    demo.build_and_run({"title": "t"}, tmp_path, client=FakeClient([reply(GOOD_DEMO)]))
    for name in ("demo.py", "test_demo.py", "README.md", "results.json", "run_output.txt", "test_output.txt"):
        assert (tmp_path / name).is_file(), name
    assert "test_ok" in (tmp_path / "test_output.txt").read_text()
    assert not list(tmp_path.glob("attempt_*_reply.txt"))


def test_failed_attempts_keep_raw_reply_and_code(tmp_path):
    res = demo.build_and_run({"title": "t"}, tmp_path,
                             client=FakeClient(["no files here"] + [reply("raise SystemExit(3)")] * 2))
    assert res["status"] == "harness_failed"
    assert (tmp_path / "attempt_1_reply.txt").read_text() == "no files here"
    assert "SystemExit" in (tmp_path / "demo.py").read_text()  # last attempt's code is kept


def test_extract_files_handles_fences_and_prose():
    out = demo.llm.extract_files("intro\n=== FILE: a.py ===\n```python\nx = 1\n```\n=== FILE: b.md ===\nhi\n=== END ===")
    assert out == {"a.py": "x = 1\n", "b.md": "hi\n"}


def test_prose_and_stray_fences_inside_a_file_are_rejected_with_clear_feedback():
    messy = "=== FILE: demo.py ===\n```python\nx = 1\n```\n\nCleanup note: delete above.\n\n```python\ny = 2\n```\n=== END ==="
    try:
        demo.llm.extract_files(messy)
    except ValueError as exc:
        assert "ONE clean file" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_readme_may_contain_fenced_examples():
    out = demo.llm.extract_files("=== FILE: README.md ===\n```markdown\n# T\n\n```bash\npython demo.py\n```\n```\n=== END ===")
    assert "python demo.py" in out["README.md"]


class StreamClient:
    """Mimics client.messages.stream(...) as a context manager; create() must NOT be used."""

    def __init__(self, text, stop="end_turn"):
        self.messages, self.text, self.stop = self, text, stop

    def create(self, **kw):
        raise AssertionError("large requests must stream")

    def stream(self, **kw):
        outer = self

        class Ctx:
            def __enter__(s): return s
            def __exit__(s, *a): return False
            def get_final_message(s):
                b = type("B", (), {"type": "text", "text": outer.text})()
                return type("R", (), {"content": [b], "stop_reason": outer.stop, "usage": None})()
        return Ctx()


def test_large_max_tokens_uses_streaming():
    assert demo.llm.complete("s", "u", model="m", max_tokens=32000, client=StreamClient("ok")) == "ok"


def test_truncated_reply_is_a_repairable_harness_error_and_partial_is_saved(tmp_path):
    res = demo.build_and_run({"title": "t"}, tmp_path, client=StreamClient("=== FILE: demo.py ===\nimport", "max_tokens"))
    assert res["status"] == "harness_failed"
    assert "CUT OFF" in res["attempt_log"][0]
    assert (tmp_path / "attempt_1_reply.txt").read_text().endswith("import")
