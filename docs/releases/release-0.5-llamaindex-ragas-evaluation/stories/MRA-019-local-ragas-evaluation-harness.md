# MRA-019: Add a local Ragas evaluation harness

## Status

Implemented

## User story

As a developer improving CiteNook's RAG behavior, I want a small repeatable local evaluation command so that I can inspect groundedness and factual correctness instead of relying only on manual impressions of generated answers.

## Context

CiteNook already returns persistent grounded answers and structured citation snippets. Ragas is evaluation tooling, not a runtime requirement for answering questions and not a dependency of LlamaIndex. The harness should exercise the existing direct CiteNook path, use a dedicated generic fixture, and keep evaluator output local.

## Scope

Add a privacy-safe evaluation fixture, a small question/reference dataset, and a command that prepares dedicated temporary CiteNook resources, collects answers and cited contexts, evaluates them with Ragas using a local Ollama judge, writes local result artifacts, and cleans up the temporary resources.

## Acceptance criteria

- [x] Add the pinned Ragas package and only the smallest client/adapter dependencies required for local Ollama evaluation to the same named optional dependency extra introduced by MRA-018; the normal product install and Docker images remain unchanged.
- [x] Add one committed, invented text/Markdown fixture containing enough explicit facts for 8–10 single-turn questions. The fixture and references must contain no personal, proprietary, production, or copied customer content.
- [x] Store the evaluation cases in a reviewable JSON, JSONL, or CSV dataset with stable case IDs, user questions, reference answers or grading notes, and any expected evidence hints needed for deterministic setup validation.
- [x] Validate the dataset before any model call: reject duplicate IDs, empty questions/references, missing fixture evidence, unsupported fields, and accidental absolute paths or secrets.
- [x] Provide one documented command that targets a running local CiteNook API, creates a dedicated conversation with explicit chat/embedding models, uploads the fixture, waits for successful ingestion with a bounded timeout, executes every question, and captures the generated response plus returned citation snippets.
- [x] Name or tag temporary resources so the command deletes only the conversation/document it created. Cleanup runs on success, evaluation failure, timeout, and keyboard interruption; an explicit diagnostic option may retain them for troubleshooting.
- [x] Build Ragas single-turn samples from `user_input`, `response`, `reference`, and the cited source snippets used as `retrieved_contexts`. Document that CiteNook's public response exposes cited contexts rather than every raw top-k candidate, so Release 0.5 does not claim full retriever-ranking evaluation.
- [x] Run at least two Ragas metrics that match the available data. The default set should include faithfulness/groundedness against cited contexts and factual correctness against the human-written reference; add another metric only if it remains local and materially useful.
- [x] Use an explicitly configured local Ollama evaluator model through a supported Ragas adapter. Do not require an OpenAI, Anthropic, Google, LangSmith, Ragas Cloud, or other hosted account, key, upload, or telemetry endpoint.
- [x] Keep the answer-generating model and evaluator model configurable and record both in every result. Warn when the same model is used for both roles and state that the scores are model-assisted signals rather than human ground truth.
- [x] Print a concise aggregate summary and save timestamped per-case CSV plus machine-readable JSON metadata under an ignored `evals/experiments/` location. Record case ID, models, answer, cited context identifiers/snippets, metric scores, duration, run status, and errors without storing hidden prompts or unrelated database content.
- [x] Do not impose a hard quality threshold in the normal CI pipeline. The local smoke gate requires successful completion, valid score ranges, complete case coverage, and cleanup; score interpretation remains documented and reviewable.
- [x] Add focused tests for dataset validation, API orchestration, polling timeout, evaluator input mapping, score/result serialization, and cleanup behavior using fake HTTP/model boundaries. Unit tests must not require a running Ollama server or Docker stack.
- [x] Complete one real local evaluation run with the committed fixture and record the reproducible command, installed models, case count, aggregate scores, failed cases, and limitations. Do not present a single small run as a benchmark or proof that one RAG implementation is superior.

## Verification plan

- Run dataset-validation and evaluation-runner tests with all external calls replaced by fakes.
- Start the supported Compose stack with installed chat, embedding, and evaluator models, then execute the documented evaluation command from a clean environment.
- Verify the fixture becomes `ready`, all cases produce either a scored result or a structured error, CSV/JSON artifacts agree, and temporary CiteNook resources are removed afterward.
- Force one ingestion timeout, one answer failure, and one evaluator failure and confirm cleanup plus actionable diagnostics.
- Inspect outbound configuration and logs to confirm evaluation traffic remains on the configured local CiteNook/Ollama endpoints and no secret or hosted telemetry is required.

## Out of scope

A web dashboard, production monitoring, automatic synthetic test generation, human-annotation tooling, CI quality thresholds, large benchmark datasets, multi-turn evaluation, retrieval recall over unretrieved ground-truth chunks, LlamaIndex-vs-direct leaderboard claims, cloud experiment tracking, and frontend score presentation are excluded.

## Implementation notes

Keep the harness outside request-time application behavior. Prefer the existing public API for setup and answer collection so the evaluation reflects the shipped vertical slice. A small custom orchestration layer is acceptable, but metric computation must genuinely use Ragas rather than only printing hand-written scores.

## Comments

- Implemented in `apps/api/app/evaluation/ragas_dataset.py` and `ragas_evaluate.py`, with the invented Markdown fixture and eight stable JSON cases under `evals/fixtures/`. Ragas 0.4.3 and its local OpenAI-compatible Ollama adapter dependencies are exact pins in the existing `framework-evaluation` extra. The normal Python 3.14 API/worker Compose image build remained successful and did not install the optional packages; the evaluation environment uses Python 3.13 because the locked Ragas dependency tree currently lacks a prebuilt Python 3.14 `scikit-network` wheel.
- Focused evidence on 2026-08-28: strict validation and fake-boundary orchestration, local-endpoint enforcement, timeout, failure, mapping, persistent-event-loop, serialization, retention, and cleanup coverage passed 27 tests without Docker or Ollama. The full API suite passed Ruff and 104 tests. Forced keyboard interruption and failed diagnostic runs left zero tagged MRA-019 documents and conversations.
- The successful local run used `RAGAS_DO_NOT_TRACK=true uv run --directory apps/api --python 3.13 --extra framework-evaluation citenook-ragas --api-url http://localhost:8000/api --ollama-url http://localhost:11434 --answer-model llama3.1:8b --embedding-model qwen3-embedding:0.6b --evaluator-model llama3.1:8b --ingestion-timeout-seconds 180 --request-timeout-seconds 600`. Run `mra019-20260828T144238Z` completed all 8 cases with 0 failed cases, aggregate Faithfulness `0.8`, and aggregate Factual Correctness `0.82375`; all 16 per-case scores were within `0..1`, JSON and CSV case coverage agreed, cleanup errors were empty, and zero tagged resources remained.
- The timestamped artifacts remain local and ignored under `evals/experiments/`. This single invented-fixture run is not a benchmark: the answer and evaluator roles used the same locally available model, scores can therefore be correlated, and only public citation snippets—not unretrieved raw top-k candidates—were evaluated.
