"""Quick checks for retrieval triggers + seed corpus. Run: python -m tests.test_retrieval"""
from backend.pipeline.retrieval import (
    CRITERIA,
    RetrievalChunk,
    load_seed_corpus,
    triggers_from_metrics,
)


def _analysis(rate_per_min=0.0, overall_wpm=130.0, pause_count=0):
    """Build a minimal analyze()-shaped dict for the fields triggers reads."""
    return {
        "fillers": {"rate_per_min": rate_per_min},
        "wpm": {"overall_wpm": overall_wpm},
        "pauses": {"count": pause_count},
    }


def test_high_fillers_only():
    # 11/min > 6 default, pace fine, few pauses
    assert triggers_from_metrics(_analysis(rate_per_min=11.0)) == ["fillers"]


def test_fast_wpm_triggers_pacing():
    assert triggers_from_metrics(_analysis(overall_wpm=180.0)) == ["pacing"]


def test_slow_wpm_triggers_pacing():
    assert triggers_from_metrics(_analysis(overall_wpm=90.0)) == ["pacing"]


def test_many_pauses_triggers_pacing():
    assert triggers_from_metrics(_analysis(pause_count=5)) == ["pacing"]


def test_both_tags():
    result = triggers_from_metrics(
        _analysis(rate_per_min=11.0, overall_wpm=185.0, pause_count=5)
    )
    assert result == ["fillers", "pacing"]


def test_clean_speech_triggers_nothing():
    assert triggers_from_metrics(_analysis(rate_per_min=2.0)) == []


def test_pacing_not_duplicated():
    # both fast wpm AND many pauses fire pacing; should appear once
    assert triggers_from_metrics(_analysis(overall_wpm=185.0, pause_count=5)) == ["pacing"]


def test_seed_corpus_loads_and_is_valid():
    chunks = load_seed_corpus()
    assert len(chunks) >= 6
    assert all(isinstance(c, RetrievalChunk) for c in chunks)
    assert all(c.criterion in CRITERIA for c in chunks)
    tags = {c.criterion for c in chunks}
    assert "fillers" in tags and "pacing" in tags


def test_invalid_criterion_rejected():
    try:
        RetrievalChunk(chunk_id="x", text="t", criterion="speed", source="s")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for invalid criterion")


if __name__ == "__main__":
    test_high_fillers_only()
    test_fast_wpm_triggers_pacing()
    test_slow_wpm_triggers_pacing()
    test_many_pauses_triggers_pacing()
    test_both_tags()
    test_clean_speech_triggers_nothing()
    test_pacing_not_duplicated()
    test_seed_corpus_loads_and_is_valid()
    test_invalid_criterion_rejected()
    print("all retrieval tests passed")
