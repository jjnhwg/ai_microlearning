"""Grounded feedback generation — turns metrics + retrieved citations into a report.

Hard architectural rule from docs/PLAN.md: the generation step NEVER estimates a
number. It receives already-computed metrics (from features.analyze) and
already-retrieved citations (from retrieval.retrieve) as structured input, and
only *phrases* them into an actionable, cited insight. Every quantitative claim
in the output is a value copied verbatim from the metrics row, and every
qualitative claim carries a citation. A separate validator (validator.py) then
rejects any report whose numbers don't match the metrics.

This prototype phrases deterministically so it runs offline and is reproducible.
An LLM phraser can be injected later via `phraser=`; it may only rewrite the
prose around the pre-formatted numbers, never introduce or alter a number.
"""

from __future__ import annotations

from typing import Callable

from backend.pipeline.retrieval import RetrievalChunk

# A phraser takes the deterministic message + the exact numbers it is allowed to
# use, and returns polished prose. Default is identity (no LLM).
Phraser = Callable[[str, list[str]], str]


def _cite(chunks: list[RetrievalChunk]) -> list[dict]:
    """Shape retrieved chunks into citation records for the report."""
    return [
        {
            "chunk_id": c.chunk_id,
            "source": c.source,
            "source_url": c.source_url,
            "text": c.text,
        }
        for c in chunks
    ]


def _fmt(value: float | int) -> str:
    """Format a metric exactly as it will appear in the message text.

    Integers stay integers; floats keep their stored precision. The validator
    extracts numbers from the message and checks them against this same set, so
    formatting here and allowed-number formatting must agree.
    """
    if isinstance(value, bool):  # guard: bool is an int subclass
        return str(value)
    if isinstance(value, int):
        return str(value)
    if float(value).is_integer():
        return str(int(value))
    return str(round(float(value), 2))


def _fillers_insight(analysis: dict, chunks: list[RetrievalChunk]) -> dict:
    fillers = analysis.get("fillers", {})
    count = int(fillers.get("count", 0))
    rate = float(fillers.get("rate_per_min", 0.0))
    numbers = [_fmt(count), _fmt(rate)]
    message = (
        f"You used {_fmt(count)} filler words, about {_fmt(rate)} per minute. "
        "Research links frequent fillers to lower perceived confidence; try "
        "replacing them with a short silent pause at the transitions between points."
    )
    return {
        "criterion": "fillers",
        "metrics": {"count": count, "rate_per_min": rate},
        "numbers": numbers,
        "message": message,
        "citations": _cite(chunks),
    }


def _pacing_insight(analysis: dict, chunks: list[RetrievalChunk]) -> dict:
    wpm = analysis.get("wpm", {})
    pauses = analysis.get("pauses", {})
    overall = float(wpm.get("overall_wpm", 0.0))
    pause_count = int(pauses.get("count", 0))
    pause_total = float(pauses.get("total_duration", 0.0))
    numbers = [_fmt(overall), _fmt(pause_count), _fmt(pause_total)]
    message = (
        f"Your overall pace was {_fmt(overall)} words per minute, with "
        f"{_fmt(pause_count)} notable pauses totalling {_fmt(pause_total)} seconds. "
        "A conversational rate keeps listeners with you; use your pauses "
        "deliberately to let key points land rather than to search for words."
    )
    return {
        "criterion": "pacing",
        "metrics": {
            "overall_wpm": overall,
            "pause_count": pause_count,
            "pause_total_s": pause_total,
        },
        "numbers": numbers,
        "message": message,
        "citations": _cite(chunks),
    }


_BUILDERS = {
    "fillers": _fillers_insight,
    "pacing": _pacing_insight,
}


def generate_report(
    analysis: dict,
    tags: list[str],
    retrieved: list[RetrievalChunk],
    *,
    phraser: Phraser | None = None,
) -> dict:
    """Compose a grounded feedback report from metrics, tags, and citations.

    analysis: metrics dict from features.analyze().
    tags: triggered criterion tags from retrieval.triggers_from_metrics().
    retrieved: chunks from retrieval.retrieve(tags) — the citations to ground on.
    phraser: optional prose rewriter (e.g. an LLM). It receives the deterministic
        message and the list of allowed number strings, and must return text that
        introduces no new numbers. If omitted, the deterministic message is used.

    Returns a report dict: an ordered list of per-criterion insights (each with its
    exact metrics, the numbers it asserts, its message, and its citations) plus a
    plain-language summary. If a tag has no retrieved citation, it is skipped so no
    claim is ever made without a source to back it.
    """
    by_criterion: dict[str, list[RetrievalChunk]] = {}
    for chunk in retrieved:
        by_criterion.setdefault(chunk.criterion, []).append(chunk)

    insights: list[dict] = []
    for tag in tags:
        builder = _BUILDERS.get(tag)
        chunks = by_criterion.get(tag, [])
        if builder is None or not chunks:
            continue
        insight = builder(analysis, chunks)
        if phraser is not None:
            insight["message"] = phraser(insight["message"], insight["numbers"])
        insights.append(insight)

    if insights:
        criteria = ", ".join(i["criterion"] for i in insights)
        summary = f"Feedback focuses on: {criteria}. Every number below is measured from your recording."
    else:
        summary = "No coaching thresholds were triggered — your pacing and filler use look solid."

    return {"summary": summary, "insights": insights}
