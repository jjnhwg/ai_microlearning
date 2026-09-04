"""Tiny offline driver to watch the retrieval path run end to end.

No S3, no Whisper — feeds a hand-made transcript (same shape transcribe()
returns) through: analyze -> triggers_from_metrics -> select_chunks.

Run: python -m scripts.try_retrieval
"""

from backend.pipeline.features import analyze
from backend.pipeline.retrieval import (
    load_seed_corpus,
    select_chunks,
    triggers_from_metrics,
)

# A fake transcript: lots of "um"/"like" fillers, spoken fast (words packed
# close together) so both "fillers" and "pacing" should trigger. Tweak these to
# see different tags fire.
SAMPLE_WORDS = [
    {"word": "um", "start": 0.0, "end": 0.2, "confidence": 0.7},
    {"word": "so", "start": 0.2, "end": 0.4, "confidence": 0.9},
    {"word": "like", "start": 0.4, "end": 0.6, "confidence": 0.8},
    {"word": "the", "start": 0.6, "end": 0.7, "confidence": 0.9},
    {"word": "project", "start": 0.7, "end": 1.0, "confidence": 0.9},
    {"word": "um", "start": 1.0, "end": 1.2, "confidence": 0.7},
    {"word": "basically", "start": 1.2, "end": 1.6, "confidence": 0.9},
    {"word": "works", "start": 1.6, "end": 1.9, "confidence": 0.9},
    {"word": "like", "start": 1.9, "end": 2.1, "confidence": 0.8},
    {"word": "this", "start": 2.1, "end": 2.3, "confidence": 0.9},
]

TRANSCRIPT = {"text": "um so like the project...", "language": "en", "words": SAMPLE_WORDS}


def main() -> None:
    print("=== 1. analyze() — deterministic metrics ===")
    analysis = analyze(TRANSCRIPT)
    print(f"  fillers: {analysis['fillers']['count']} "
          f"({analysis['fillers']['rate_per_min']}/min)")
    print(f"  overall wpm: {analysis['wpm']['overall_wpm']}")
    print(f"  pauses: {analysis['pauses']['count']}")

    print("\n=== 2. triggers_from_metrics() — which criteria fired ===")
    tags = triggers_from_metrics(analysis)
    print(f"  tags: {tags}")

    print("\n=== 3. select_chunks() — sources for those criteria ===")
    corpus = load_seed_corpus()
    chunks = select_chunks(tags, corpus)
    if not chunks:
        print("  (no chunks — clean speech, nothing triggered)")
    for c in chunks:
        print(f"  [{c.criterion}] {c.chunk_id}: {c.text[:70]}...")


if __name__ == "__main__":
    main()
