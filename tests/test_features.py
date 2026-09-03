"""Quick check for count_fillers. Run: python -m tests.test_features"""
from backend.pipeline.features import count_fillers

# 6 words over a 3s span (0.0 -> 3.0); 2 fillers: "um", "like"
_WORDS = [
    {"word": "So", "start": 0.0, "end": 0.3, "confidence": 0.9},
    {"word": "um,", "start": 0.4, "end": 0.7, "confidence": 0.6},
    {"word": "I", "start": 0.9, "end": 1.0, "confidence": 0.99},
    {"word": "was", "start": 1.1, "end": 1.4, "confidence": 0.98},
    {"word": "like", "start": 1.6, "end": 1.9, "confidence": 0.7},
    {"word": "ready.", "start": 2.5, "end": 3.0, "confidence": 0.95},
]


def test_counts_and_rate():
    # "So" is in DEFAULT_FILLERS too -> 3 fillers over 3.0s span = 1 min * 60 rate
    result = count_fillers(_WORDS)
    assert result["count"] == 3
    assert [o["word"] for o in result["occurrences"]] == ["So", "um,", "like"]
    # 3 fillers / (3.0s / 60) = 60.0 per minute
    assert result["rate_per_min"] == 60.0


def test_empty_input():
    result = count_fillers([])
    assert result == {"count": 0, "rate_per_min": 0.0, "occurrences": []}


def test_custom_filler_set():
    result = count_fillers(_WORDS, fillers=frozenset({"like"}))
    assert result["count"] == 1
    assert result["occurrences"][0]["word"] == "like"


if __name__ == "__main__":
    test_counts_and_rate()
    test_empty_input()
    test_custom_filler_set()
    print("all filler tests passed")
