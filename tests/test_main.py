import json

from pipeline import demo, main, visuals


def test_outcomes_chart_and_no_chart_for_harness_failure(tmp_path):
    res = demo.harness_failed({"title": "t"}, ["boom", "bang"])
    assert visuals.bar_chart(res, tmp_path / "c.png") is None
    assert visuals.outcomes_chart(res, tmp_path / "o.png").is_file()
    assert visuals.summary_card(res, "t", tmp_path / "s.png").is_file()


def test_run_produces_bundle_and_publishes_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "OUT_DIR", tmp_path / "out")
    monkeypatch.setattr(main, "WORK_DIR", tmp_path / "work")
    monkeypatch.setattr(main.state, "STATE_FILE", tmp_path / "h.json")
    monkeypatch.setattr(main.state, "load", lambda *a: [])
    saved = {}
    monkeypatch.setattr(main.state, "update_last", lambda slug, f: saved.update(f))
    monkeypatch.delenv("EXAMPLES_REPO_TOKEN", raising=False)
    tp = {"title": "T", "slug": "t"}
    res = demo.harness_failed(tp, ["boom"])
    monkeypatch.setattr(main.research, "gather", lambda: [{"title": "s", "url": "u", "score": 1, "source": "x"}])
    monkeypatch.setattr(main.topic, "choose", lambda s, u: tp)
    monkeypatch.setattr(main.demo, "build_and_run", lambda t, f: (f.mkdir(parents=True), (f / "demo.py").write_text("x"), res)[2])
    monkeypatch.setattr(main.content, "write_post", lambda *a, **k: "## What broke\n\n{{IMG_OUTCOMES}}\n")
    monkeypatch.setattr(main.linkedin_post, "write", lambda *a, **k: "post [PATREON_LINK]")
    assert main.run() == 0
    b = tmp_path / "out" / "bundle"
    names = {p.name for p in b.iterdir()}
    assert {"patreon_post.html", "patreon_post.md", "linkedin_post.txt", "UPLOAD_GUIDE.md",
            "outcomes.png", "card.png", "results.json", "demo"} <= names
    assert 'src="outcomes.png"' in (b / "patreon_post.html").read_text()
    assert "[PATREON_LINK]" in (b / "UPLOAD_GUIDE.md").read_text() and saved["examples_pushed"] is False
    assert json.loads((b / "results.json").read_text())["status"] == "harness_failed"
