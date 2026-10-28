import pytest

from pipeline import content, linkedin_post, llm

RES = {"summary": {"flaky_rate_before": 0.37, "after": 0.05}, "chart": {}, "table": {}, "notes": []}


def test_extract_json_fenced():
    assert llm.extract_json('x\n```json\n{"a": 1}\n```') == {"a": 1}


def test_check_numbers_flags_invented():
    assert content.check_numbers("We saw 0.37 and 0.05.", RES) == []
    assert content.check_numbers("We saw 99.9% gains.", RES) == ["99.9"]


def test_to_html_substitutes_images():
    html = content.to_html("# T\n\n{{IMG_CHART}}", {"IMG_CHART": "http://x/c.png"})
    assert "http://x/c.png" in html


URL = linkedin_post.PLACEHOLDER


def test_linkedin_validate():
    good = f"Hook\n\nSee {URL}\n\nQ?\n\n#a #b #c"
    assert linkedin_post.validate(good) == []
    assert linkedin_post.validate("no link #a #b #c")
    assert linkedin_post.validate(good + "x" * 1300)


class FakeClient:
    def __init__(self, replies):
        self.replies = iter(replies)
        self.messages = self

    def create(self, **kw):
        class B:
            type = "text"
            text = next(self.replies)
        return type("R", (), {"content": [B()]})()


def test_linkedin_retries_then_succeeds():
    good = f"Hook\n\n{URL}\n\nQ?\n\n#a #b #c"
    out = linkedin_post.write({"title": "t"}, RES, "story", client=FakeClient(["bad", good]))
    assert out == good


def test_linkedin_falls_back():
    out = linkedin_post.write({"title": "t"}, RES, "story", client=FakeClient(["bad", "bad"]))
    assert URL in out and linkedin_post.validate(out) == []


def test_harness_failed_post_must_say_so():
    res = {**RES, "status": "harness_failed"}
    with pytest.raises(RuntimeError, match="harness_failed"):
        content.write_post({"title": "t"}, res, __import__("pathlib").Path("."), "u", [],
                           client=FakeClient(["# Great success, it all works"]))
    ok = content.write_post({"title": "t"}, res, __import__("pathlib").Path("."), "u", [],
                            client=FakeClient(["## What I tried and where it broke"]))
    assert "broke" in ok


def test_missing_image_placeholder_removed():
    assert "IMG_CHART" not in content.to_html("a\n\n{{IMG_CHART}}\n\nb", {})


def test_post_numbers_retry_then_raise():
    c = FakeClient(["costs 99.9", "still 88.8"])
    with pytest.raises(RuntimeError):
        content.write_post({"title": "t"}, RES, __import__("pathlib").Path("."), "u", [], client=c)
