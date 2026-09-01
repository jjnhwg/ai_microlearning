# SpeakSharp — Project Plan

A communication-coaching tool. A user is shown a speaking prompt, records themselves
answering it (or uploads an existing practice-talk recording), and gets back a feedback
report where every quantitative claim is tied to a timestamp in their own transcript and
every qualitative claim is tied to a cited communication-research finding or published rubric.

## Primary user flow

Prompt shown → timer + audio record → stop → async pipeline
(transcribe → forced alignment → deterministic feature extraction →
feature-triggered retrieval → grounded generation) → cited feedback report →
optional: save attempt to track trends over time.

Secondary flow: user uploads their own audio file instead of using a prompt.

## Hard architectural rule (do not violate)

Split deterministic work from LLM work explicitly:

- Objective, computable values (words-per-minute over sliding windows, filler-word
  counts, pause count/duration) are computed by deterministic code. The LLM NEVER
  estimates a number.
- The LLM only synthesizes and phrases: connecting metrics into an insight, relating it
  to retrieved research, making it actionable.
- The generation step receives already-computed metrics and already-retrieved citations
  as structured input.
- A post-generation validator rejects any output whose numeric claims don't match the
  computed metrics row.

## Retrieval design

Retrieval is driven by deterministic analysis results, NOT a user query. E.g. high filler
rate detected → retrieve filler-word research; long monotone stretch → retrieve
vocal-variety rubric. Corpus: public communication-research abstracts (PubMed/PsyArXiv) +
published Toastmasters evaluation rubrics, chunked per-criterion (pacing, structure,
filler words, vocal variety), each chunk tagged with criterion type. Hybrid retrieval
(BM25 + dense) + a reranker.

## Tech stack (decided)

- Python + FastAPI backend.
- Postgres + pgvector for metadata and embeddings; separate structured table for computed
  speech metrics.
- Whisper for transcription, self-hosted on the Fargate task.
- Forced alignment for word-level timestamps.
- AWS Step Functions to orchestrate the long-running pipeline (per-step retry and
  partial-failure recovery). A transcription-confidence gate drops low-confidence segments
  before feature extraction.
- S3 for raw audio. Secrets Manager for keys. CloudWatch + X-Ray for tracing.
- AWS CDK for all infrastructure as code.
- GitHub Actions for CI.

No PyTorch in the core stack (Whisper uses it internally; no training/fine-tuning in v1).

## Evaluation strategy (three tiers, all run in CI)

1. Feature-extraction eval (fully objective, no LLM judge): hand-count filler words and
   words spoken across 100+ transcript segments; report precision/recall on filler
   detection and mean WPM error. Flagship metric — build and validate first.
2. Retrieval eval: 100+ (feature-trigger → correct rubric chunks) pairs; Recall@5, MRR.
3. Generation eval: groundedness, citation accuracy, custom "actionability" rubric;
   latency and cost per report.

CI blocks PRs on regressions; the deterministic tier is a non-LLM regression gate.

## Scope constraints for v1

- Single speaker, English, decent mic, 3–15 minute recordings. State this in README.
- Features in scope: filler words, words-per-minute, pause count/duration. Vocal variety /
  pitch analysis is a stretch goal, NOT v1.
- Prompt bank is a curated static table (~40 prompts tagged by type and target duration).
  LLM-generated prompt variations are a stretch goal.

## Non-goals

No diagnosis, no individualized health/medical claims, no multi-speaker/diarization, no
real-time streaming feedback, no mobile app. Feedback is generated only after the full
recording is processed.

## Build phases

- Week 1: audio → S3 → Whisper → word-level transcript with confidence scores.
- Week 2: forced alignment + deterministic feature extraction; validate against hand count
  on ~20 segments.
- Week 3: rubric/research corpus ingestion + feature-triggered retrieval.
- Week 4: generation + numeric-claim validator + 40-case eval set.
- Week 5: Step Functions orchestration, retries, confidence gating, CI evals.
- Week 6: full 100+ case eval across all tiers, CDK deploy, observability dashboard,
  README, demo recording.

## Working rules (collaboration)

1. Explain the plan in plain English and wait for explicit "go" before writing anything.
2. One step at a time — smallest useful change, then stop for review.
3. Show every change as a diff with a short note on why.
4. Never edit more than one file (or one function) without checking in.
5. Ask before installing packages, deleting code, or refactoring anything not asked for.
