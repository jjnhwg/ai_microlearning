"""Checks for retrieval search, generation, validation, and the full pipeline.

Run: python -m tests.test_generation
"""
from backend.pipeline.generation import generate_report
from backend.pipeline.report import build_report
from backend.pipeline.retrieval import (
    RetrievalChunk,
    load_seed_corpus,
    retrieve,
    triggers_from_metrics,
)
from backend.pipeline.validator import validate_report


def _analysis(rate_per_min=11.0, count=8, overall_wpm=185.0, pause_count=5, pause_total=6.4):
    return {
        "fillers": {"count": count, "rate_per_min": rate_per_min, "occurrences": []},
        "wpm": {"overall_wpm": overall_wpm, "windows": []},
        "pauses": {"count": pause_count, "total_duration": pause_total, "pauses": []},
    }


def test_retrieve_returns_chunks_for_tags():
    corpus = load_seed_corpus()
    chunks = retrieve(["fillers"], corpus)
    assert chunks and all(c.criterion == "fillers" for c in chunks)


def test_retrieve_respects_per_tag_and_order():
    corpus = load_seed_corpus()
    chunks = retrieve(["fillers", "pacing"], corpus, per_tag=1)
    assert [c.criterion for c in chunks] == ["fillers", "pacing"]


def test_retrieve_empty_tags():
    assert retrieve([], load_seed_corpus()) == []


def test_generate_uses_exact_numbers_and_cites():
    analysis = _analysis()
    tags = triggers_from_metrics(analysis)
    retrieved = retrieve(tags)
    report = generate_report(analysis, tags, retrieved)
    assert {i["criterion"] for i in report["insights"]} == {"fillers", "pacing"}
    for insight in report["insights"]:
        assert insight["citations"]
        assert "8" in insight["message"] or "185" in insight["message"]


def test_validator_passes_on_generated_report():
    analysis = _analysis()
    tags = triggers_from_metrics(analysis)
    report = generate_report(analysis, tags, retrieve(tags))
    result = validate_report(report, analysis)
    assert result["ok"], result["issues"]


def test_validator_catches_fabricated_number():
    analysis = _analysis()
    tags = triggers_from_metrics(analysis)
    report = generate_report(analysis, tags, retrieve(tags))
    # inject a number that is not a computed metric
    report["insights"][0]["message"] += " You improved by 42 percent."
    result = validate_report(report, analysis)
    assert not result["ok"]
    assert any("42" in issue for issue in result["issues"])


def test_validator_requires_citation():
    analysis = _analysis()
    tags = triggers_from_metrics(analysis)
    report = generate_report(analysis, tags, retrieve(tags))
    report["insights"][0]["citations"] = []
    result = validate_report(report, analysis)
    assert not result["ok"]
    assert any("citation" in issue for issue in result["issues"])


def test_phraser_hook_is_applied():
    analysis = _analysis()
    tags = triggers_from_metrics(analysis)
    report = generate_report(
        analysis, tags, retrieve(tags), phraser=lambda msg, nums: msg.upper()
    )
    assert report["insights"][0]["message"].isupper()


def _transcript():
    """A short transcript that triggers both fillers and fast pacing."""
    words = []
    t = 0.0
    tokens = (["um"] + ["word"] * 4) * 12  # many fast words + fillers
    for i, tok in enumerate(tokens):
        start = t
        end = t + 0.18
        words.append({"word": tok, "start": round(start, 3), "end": round(end, 3), "confidence": 0.9})
        t = end + 0.02
        if i in (10, 30, 50):  # a few long pauses
            t += 0.8
    return {"text": " ".join(tokens), "language": "en", "words": words}


def test_end_to_end_build_report_is_grounded():
    result = build_report(_transcript())
    assert result["tags"]
    assert result["report"]["insights"]
    assert result["validation"]["ok"], result["validation"]["issues"]


def test_clean_speech_yields_no_insights_but_valid():
    analysis = _analysis(rate_per_min=1.0, count=1, overall_wpm=130.0, pause_count=0, pause_total=0.0)
    tags = triggers_from_metrics(analysis)
    report = generate_report(analysis, tags, retrieve(tags))
    assert report["insights"] == []
    assert validate_report(report, analysis)["ok"]


def test_invalid_chunk_criterion_rejected():
    try:
        RetrievalChunk(chunk_id="x", text="t", criterion="tempo", source="s")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for invalid criterion")


if __name__ == "__main__":
    test_retrieve_returns_chunks_for_tags()
    test_retrieve_respects_per_tag_and_order()
    test_retrieve_empty_tags()
    test_generate_uses_exact_numbers_and_cites()
    test_validator_passes_on_generated_report()
    test_validator_catches_fabricated_number()
    test_validator_requires_citation()
    test_phraser_hook_is_applied()
    test_end_to_end_build_report_is_grounded()
    test_clean_speech_yields_no_insights_but_valid()
    test_invalid_chunk_criterion_rejected()
    print("all generation/validation/pipeline tests passed")
