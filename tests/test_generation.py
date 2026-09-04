"""Quick checks for the generation-input assembler.
Run: /opt/homebrew/bin/python3.12 -m tests.test_generation
"""
import json

from backend.pipeline.generation import build_generation_input
from backend.pipeline.retrieval import RetrievalChunk


def _analysis():
    return {
        "fillers": {"count": 6, "rate_per_min": 156.5, "occurrences": []},
        "wpm": {"overall_wpm": 260.9, "windows": []},
        "pauses": {"count": 0, "total_duration": 0.0, "pauses": []},
    }


def _chunks():
    return [
        RetrievalChunk("fillers-01", "Fillers lower confidence.", "fillers", "src", None),
        RetrievalChunk("pacing-01", "120-150 wpm is comfortable.", "pacing", "src", "http://x"),
    ]


def test_has_three_top_level_keys():
    out = build_generation_input(_analysis(), ["fillers", "pacing"], _chunks())
    assert set(out) == {"tags", "metrics", "citations"}


def test_metrics_passed_through_unchanged():
    analysis = _analysis()
    out = build_generation_input(analysis, ["fillers"], _chunks())
    assert out["metrics"] == analysis


def test_citations_flattened_to_dicts():
    out = build_generation_input(_analysis(), ["fillers", "pacing"], _chunks())
    first = out["citations"][0]
    assert first["chunk_id"] == "fillers-01"
    assert first["criterion"] == "fillers"
    assert set(first) == {"chunk_id", "criterion", "text", "source", "source_url"}


def test_payload_is_json_serializable():
    out = build_generation_input(_analysis(), ["fillers", "pacing"], _chunks())
    json.dumps(out)  # raises if any value isn't serializable


def test_empty_chunks_gives_empty_citations():
    out = build_generation_input(_analysis(), [], [])
    assert out["citations"] == [] and out["tags"] == []


if __name__ == "__main__":
    test_has_three_top_level_keys()
    test_metrics_passed_through_unchanged()
    test_citations_flattened_to_dicts()
    test_payload_is_json_serializable()
    test_empty_chunks_gives_empty_citations()
    print("all generation tests passed")
