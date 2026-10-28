import pytest

from pipeline import research
from pipeline.publishers import patreon


class FakePage:
    def __init__(self, url="https://www.patreon.com/posts/123-abc?x=1", logged_in=True):
        self.url = "https://www.patreon.com/login" if not logged_in else url
        self._final = url
        self.clicked = []

    def goto(self, *a, **k): pass
    def wait_for_selector(self, *a, **k): pass
    def fill(self, *a, **k): pass
    def evaluate(self, *a, **k): pass
    def wait_for_url(self, *a, **k): self.url = self._final

    def locator(self, sel):
        page = self

        class L:
            first = property(lambda s: s)
            def count(s): return 1
            def click(s): page.clicked.append(sel)
        return L()


def test_patreon_draft_returns_clean_url():
    p = FakePage()
    assert patreon.publish("t", "<p>b</p>", mode="draft", page_factory=lambda: p) == \
        "https://www.patreon.com/posts/123-abc"
    assert any("Save" in c for c in p.clicked) and not any(c == patreon.SELECTORS["publish"] for c in p.clicked)


def test_patreon_publish_mode_clicks_publish():
    p = FakePage()
    patreon.publish("t", "b", mode="publish", page_factory=lambda: p)
    assert patreon.SELECTORS["publish"] in p.clicked


def test_patreon_login_redirect_errors():
    with pytest.raises(patreon.PatreonError, match="renew"):
        patreon.publish("t", "b", mode="draft", page_factory=lambda: FakePage(logged_in=False))


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
