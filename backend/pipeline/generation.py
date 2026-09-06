"""Generation — Step A: assemble the structured input for the LLM.

This is still deterministic. It does NOT call an LLM. It packs the already-
computed metrics (features.analyze) and the already-retrieved citations
(retrieval.select_chunks) into a single JSON-serializable payload that the
generation prompt is built from. Keeping this separate means the LLM step
receives a fixed, testable contract — and the numeric-claim validator later has
one place to read the "true" numbers from.
"""

from backend.pipeline.retrieval import RetrievalChunk


#


# TODO (you): write the function signature ->
#   def build_generation_input(
#       analysis: dict,
#       tags: list[str],
#       chunks: list[RetrievalChunk],
#   ) -> dict:
    """Pack computed metrics + retrieved citations into one LLM-ready payload.

    analysis: the dict from features.analyze() -> {fillers, wpm, pauses}. These
        are the ground-truth numbers; the LLM may phrase them but never invent
        or alter them.
    tags: the criterion tags from triggers_from_metrics(), carried through so the
        prompt knows which issues fired and in what order.
    chunks: the RetrievalChunk list from select_chunks() — the sources the
        feedback must cite. Flattened to plain dicts here so the payload is
        JSON-serializable for the prompt.

    Returns a structured dict with three keys: `tags`, `metrics`, `citations`.
    Nothing is judged or phrased — that's the LLM's job in the next step.
    """
    citations = [
        {
            "chunk_id": c.chunk_id,
            "criterion": c.criterion,
            "text": c.text,
            "source": c.source,
            "source_url": c.source_url,
        }
        for c in chunks
    ]

    return {
        "tags": tags,
        "metrics": analysis,
        "citations": citations,
    }
