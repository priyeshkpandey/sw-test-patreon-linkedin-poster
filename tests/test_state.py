from pipeline import state
from pipeline.config import TONES


def test_first_tone_deterministic():
    assert state.pick_tone([], "a") == state.pick_tone([], "a")


def test_never_repeats_previous_and_cycles_all():
    history, seen = [], []
    for i in range(len(TONES)):
        t = state.pick_tone(history, f"s{i}")
        if history:
            assert t != history[-1]["tone"]
        history.append({"slug": f"s{i}", "tone": t})
        seen.append(t)
    assert set(seen) == set(TONES)  # LRU uses every tone before reusing one


def test_append_and_update(tmp_path):
    f = tmp_path / "h.json"
    state.update_last("x", {"tone": "story"}, f)
    state.update_last("x", {"patreon_url": "u"}, f)
    h = state.load(f)
    assert len(h) == 1 and h[0]["patreon_url"] == "u" and state.used_slugs(h) == {"x"}
