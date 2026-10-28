import json

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


def reply(demo_py):
    return json.dumps({"files": {"demo.py": demo_py, "test_demo.py": GOOD_TEST, "README.md": "r"}})


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
    bad = json.dumps({"files": {"../evil.py": "x"}})
    res = demo.build_and_run({"title": "t"}, tmp_path / "d", client=FakeClient([bad] * 3))
    assert res["status"] == "harness_failed" and not (tmp_path / "evil.py").exists()


def test_secrets_not_visible_to_demo(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret")
    leak = GOOD_DEMO + "\nimport os\nassert 'ANTHROPIC_API_KEY' not in os.environ\n"
    assert demo.build_and_run({"title": "t"}, tmp_path, client=FakeClient([reply(leak)]))
