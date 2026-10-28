import json

import pytest

from pipeline import demo

GOOD_DEMO = '''
import json
json.dump({"summary": {"x": 1}, "chart": {"title": "t", "ylabel": "y", "labels": ["a"],
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


def reply(demo_py):
    return json.dumps({"files": {"demo.py": demo_py, "test_demo.py": GOOD_TEST, "README.md": "r"}})


def test_runs_and_returns_measured_results(tmp_path):
    res = demo.build_and_run({"title": "t"}, tmp_path, client=FakeClient([reply(GOOD_DEMO)]))
    assert res["summary"] == {"x": 1}


def test_repairs_after_failure(tmp_path):
    c = FakeClient([reply("raise SystemExit(3)"), reply(GOOD_DEMO)])
    assert demo.build_and_run({"title": "t"}, tmp_path, client=c)["summary"]["x"] == 1


def test_aborts_when_never_works(tmp_path):
    c = FakeClient([reply("raise SystemExit(3)")] * 3)
    with pytest.raises(RuntimeError, match="no working demo"):
        demo.build_and_run({"title": "t"}, tmp_path, client=c)


def test_rejects_path_traversal(tmp_path):
    bad = json.dumps({"files": {"../evil.py": "x"}})
    with pytest.raises(RuntimeError):
        demo.build_and_run({"title": "t"}, tmp_path / "d", client=FakeClient([bad] * 3))


def test_secrets_not_visible_to_demo(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret")
    leak = GOOD_DEMO + "\nimport os\nassert 'ANTHROPIC_API_KEY' not in os.environ\n"
    assert demo.build_and_run({"title": "t"}, tmp_path, client=FakeClient([reply(leak)]))
