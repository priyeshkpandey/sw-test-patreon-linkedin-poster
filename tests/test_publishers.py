import pytest

from pipeline import research
from pipeline.publishers import patreon


class FakePage:
    def __init__(self, url="https://www.patreon.com/posts/123-abc?x=1", logged_in=True):
        self.url = "https://www.patreon.com/login" if not logged_in else url
        self._final = url
        self.clicked = []

    challenge = False
    broken = False

    def goto(self, *a, **k): pass
    def wait_for_selector(self, *a, **k):
        if self.broken and a and a[0] == patreon.SELECTORS["title"]:
            raise TimeoutError("selector not found")
    def wait_for_load_state(self, *a, **k): pass
    def wait_for_timeout(self, *a, **k): pass
    def screenshot(self, **k): self.shot = True
    def content(self): return "<html/>"
    def fill(self, *a, **k): pass
    def evaluate(self, *a, **k): pass
    def wait_for_url(self, *a, **k): self.url = self._final

    def locator(self, sel):
        page = self

        class L:
            first = property(lambda s: s)
            def count(s):
                if sel == patreon.SELECTORS["challenge"]:
                    return 1 if page.challenge else 0
                if sel == patreon.SELECTORS["password"]:
                    return 1
                return 1
            def click(s): page.clicked.append(sel)
        return L()


@pytest.fixture(autouse=True)
def _debug_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(patreon, "DEBUG_DIR", tmp_path / "dbg")


def test_patreon_draft_returns_clean_url():
    p = FakePage()
    assert patreon.publish("t", "<p>b</p>", mode="draft", page_factory=lambda: p) == \
        "https://www.patreon.com/posts/123-abc"
    assert any("Save" in c for c in p.clicked) and not any(c == patreon.SELECTORS["publish"] for c in p.clicked)


def test_patreon_publish_mode_clicks_publish():
    p = FakePage()
    patreon.publish("t", "b", mode="publish", page_factory=lambda: p)
    assert patreon.SELECTORS["publish"] in p.clicked


def test_login_redirect_is_challenge_not_repairable():
    with pytest.raises(patreon.PatreonChallenge):
        patreon.publish("t", "b", mode="draft", page_factory=lambda: FakePage(logged_in=False))


def test_captcha_is_challenge():
    p = FakePage()
    p.challenge = True
    with pytest.raises(patreon.PatreonChallenge, match="captcha"):
        patreon.publish("t", "b", mode="draft", page_factory=lambda: p)


def test_selector_breakage_is_repairable_and_saves_debug(tmp_path):
    p = FakePage()
    p.broken = True
    with pytest.raises(patreon.PatreonError) as ei:
        patreon.publish("t", "b", mode="draft", page_factory=lambda: p)
    assert not isinstance(ei.value, patreon.PatreonChallenge)
    assert "create-post" in (tmp_path / "dbg" / "step.txt").read_text()


def test_missing_credentials_is_challenge(monkeypatch):
    monkeypatch.delenv("PATREON_EMAIL", raising=False)
    with pytest.raises(patreon.PatreonChallenge):
        patreon.publish("t", "b", mode="draft")


def test_main_exit_codes(monkeypatch):
    from pipeline import main as m
    for exc, code in ((patreon.PatreonChallenge("x"), 3), (patreon.PatreonError("x"), 2),
                      (RuntimeError("x"), 1)):
        monkeypatch.setattr(m, "run", lambda *a, e=exc: (_ for _ in ()).throw(e))
        assert m.main(["run", "--dry-run"]) == code


def test_patreon_bad_mode():
    with pytest.raises(patreon.PatreonError):
        patreon.publish("t", "b", mode="nope", page_factory=lambda: FakePage())


def test_research_survives_one_failing_source():
    def bad(): raise ConnectionError("x")
    def good(): return [{"source": "s", "title": "t", "url": "u", "score": 1}]
    assert research.gather(fetchers=(bad, good))[0]["url"] == "u"


def test_research_all_fail():
    def bad(): raise ConnectionError("x")
    with pytest.raises(RuntimeError):
        research.gather(fetchers=(bad,))


def test_outcomes_chart_and_no_chart_for_harness_failure(tmp_path):
    from pipeline import demo, visuals
    res = demo.harness_failed({"title": "t"}, ["boom", "bang"])
    assert visuals.bar_chart(res, tmp_path / "c.png") is None
    assert visuals.outcomes_chart(res, tmp_path / "o.png").is_file()
    assert visuals.summary_card(res, "t", tmp_path / "s.png").is_file()
