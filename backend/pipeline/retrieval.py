"""Feature-triggered retrieval — Step 1: chunk model + trigger rules.

See docs/PLAN.md "Retrieval design". Retrieval here is driven by the
deterministic metrics produced by features.analyze(), NOT by a user query.
This module only defines (1) the shape of a tagged corpus chunk, (2) the
deterministic mapping from computed metrics to the criterion tags we should
retrieve, and (3) a loader for the small hand-picked seed corpus. No embeddings,
no database, no tag->chunk search yet — those are later steps.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

# The four per-criterion tags every corpus chunk is labeled with. A chunk about
# um/uh disfluencies is tagged "fillers"; a Toastmasters pacing rubric line is
# tagged "pacing"; and so on. Kept as an ordered tuple so retrieval results and
# tests are stable.
CRITERIA: tuple[str, ...] = ("pacing", "fillers", "structure", "vocal_variety")


@dataclass(frozen=True)
class RetrievalChunk:
    """One tagged passage of source material the feedback can cite.

    A chunk is a small piece of a research abstract or a published rubric,
    labeled with the single speaking criterion it speaks to. Later steps embed
    `text`, store it, and retrieve it when the matching criterion is triggered.
    `source`/`source_url` carry the citation so generated feedback stays grounded.

    criterion: must be one of CRITERIA; rejected otherwise so a mistagged chunk
    can never silently enter the corpus.
    """

    chunk_id: str
    text: str
    criterion: str
    source: str
    source_url: str | None = None

    def __post_init__(self) -> None:
        if self.criterion not in CRITERIA:
            raise ValueError(
                f"criterion {self.criterion!r} is not one of {CRITERIA}"
            )


def triggers_from_metrics(
    analysis: dict,
    *,
    filler_rate_max: float = 6.0,
    slow_wpm: float = 110.0,
    fast_wpm: float = 160.0,
    min_pauses_for_pacing: int = 3,
) -> list[str]:
    """Map computed speech metrics to the criterion tags worth retrieving.

    analysis: the dict returned by features.analyze() -> {fillers, wpm, pauses}.
    Thresholds are tunable parameters, not truths (same philosophy as
    features.py): what counts as "too many" fillers or "too fast" is a knob, and
    the actual good/bad judgment is deferred to the cited feedback layer.

    Returns a de-duplicated, first-seen-ordered list of criterion tags. Only tags
    backed by a v1 metric can fire: "fillers" (from filler rate) and "pacing"
    (from words-per-minute band and/or pause count). "structure" and
    "vocal_variety" are in CRITERIA for the corpus but are not triggered yet —
    v1 computes no signal for them (vocal variety/pitch is a stretch goal).
    """
    tags: list[str] = []

    fillers = analysis.get("fillers", {})
    if fillers.get("rate_per_min", 0.0) > filler_rate_max:
        tags.append("fillers")

    wpm = analysis.get("wpm", {})
    overall = wpm.get("overall_wpm", 0.0)
    if overall and (overall < slow_wpm or overall > fast_wpm):
        tags.append("pacing")

    pauses = analysis.get("pauses", {})
    if pauses.get("count", 0) >= min_pauses_for_pacing:
        tags.append("pacing")

    seen: set[str] = set()
    ordered: list[str] = []
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            ordered.append(tag)
    return ordered


# Default location of the hand-picked seed corpus, next to this module.
_SEED_PATH = Path(__file__).with_name("seed_corpus.json")


def load_seed_corpus(path: Path = _SEED_PATH) -> list[RetrievalChunk]:
    """Load the seed corpus JSON into validated RetrievalChunk objects.

    path: JSON file holding a list of chunk records. Each RetrievalChunk is
    constructed here, so a record with an invalid `criterion` fails fast at load
    time rather than silently entering the corpus. Later steps swap this seed
    file for a larger ingested corpus without changing the loader.
    """
    with open(path, encoding="utf-8") as f:
        records = json.load(f)
    return [
        RetrievalChunk(
            chunk_id=record["chunk_id"],
            text=record["text"],
            criterion=record["criterion"],
            source=record["source"],
            source_url=record.get("source_url"),
        )
        for record in records
    ]


def retrieve(
    tags: list[str],
    corpus: list[RetrievalChunk] | None = None,
    *,
    per_tag: int = 2,
) -> list[RetrievalChunk]:
    """Return the corpus chunks that back the triggered criterion tags.

    tags: criterion tags from triggers_from_metrics() (e.g. ["fillers", "pacing"]).
    corpus: chunks to search; loads the seed corpus when omitted.
    per_tag: max chunks returned per tag, ordered as they appear in the corpus.

    This is the deterministic, query-free retrieval the plan calls for: selection
    is driven purely by which criteria the metrics triggered, never by user text.
    Full hybrid BM25+dense+reranker is a later step; here a stable tag filter over
    the small seed corpus keeps the vertical runnable and its output reproducible.
    Results preserve `tags` order so downstream feedback is deterministic.
    """
    if corpus is None:
        corpus = load_seed_corpus()

    selected: list[RetrievalChunk] = []
    for tag in tags:
        matches = [c for c in corpus if c.criterion == tag]
        selected.extend(matches[:per_tag])
    return selected
