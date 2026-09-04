"""Report orchestrator — the full deterministic-first feedback pipeline.

Ties the pieces together in the order docs/PLAN.md prescribes:

    transcript -> features.analyze (deterministic metrics)
              -> retrieval.triggers_from_metrics (metric-driven, query-free)
              -> retrieval.retrieve (tagged citations)
              -> generation.generate_report (phrases metrics + citations)
              -> validator.validate_report (rejects mismatched numbers)

`build_report` works from a transcript dict and needs no AWS, so it is fully
testable offline. `report_from_s3` adds the audio->transcript hop for the live
API path; its Whisper/S3 dependency is imported lazily so importing this module
never requires boto3, a model download, or the S3 bucket env var.
"""

from __future__ import annotations

from backend.pipeline import features, generation, validator
from backend.pipeline.generation import Phraser
from backend.pipeline.retrieval import (
    RetrievalChunk,
    load_seed_corpus,
    retrieve,
    triggers_from_metrics,
)


def build_report(
    transcript: dict,
    *,
    corpus: list[RetrievalChunk] | None = None,
    phraser: Phraser | None = None,
) -> dict:
    """Run the full metrics -> retrieval -> generation -> validation pipeline.

    transcript: a transcribe()-shaped dict ({text, language, words}).
    corpus: retrieval corpus; loads the seed corpus once when omitted.
    phraser: optional prose rewriter passed through to generation.

    Returns a dict with the computed `analysis`, the triggered `tags`, the grounded
    `report`, and the `validation` result. The report is always returned alongside
    its validation verdict rather than dropped on failure, so the API layer can
    decide how to surface an ungrounded report (this prototype refuses to serve one).
    """
    if corpus is None:
        corpus = load_seed_corpus()

    analysis = features.analyze(transcript)
    tags = triggers_from_metrics(analysis)
    retrieved = retrieve(tags, corpus)
    report = generation.generate_report(analysis, tags, retrieved, phraser=phraser)
    validation = validator.validate_report(report, analysis)

    return {
        "analysis": analysis,
        "tags": tags,
        "report": report,
        "validation": validation,
    }


def report_from_s3(
    s3_key: str,
    *,
    corpus: list[RetrievalChunk] | None = None,
    phraser: Phraser | None = None,
) -> dict:
    """Transcribe an uploaded recording by S3 key, then build its report.

    The transcribe import is deferred to here so the offline pipeline and its tests
    do not pull in boto3/Whisper or require the S3 bucket environment variable.
    """
    from backend.pipeline.transcribe import transcribe

    transcript = transcribe(s3_key)
    result = build_report(transcript, corpus=corpus, phraser=phraser)
    result["transcript"] = transcript
    return result
