# RAG pipeline

MRA-001 contains only the runtime foundation. The document-to-answer path is added incrementally:

1. MRA-002 selects and persists Ollama chat and embedding models.
2. MRA-003 persists supported uploads.
3. MRA-004 extracts, chunks, and embeds documents in the worker. Implemented.
4. MRA-005 exposes processing state and document management. Implemented.
5. MRA-006 persists conversations and messages. Implemented.
6. MRA-007 retrieves compatible chunks and returns grounded answers with citations. Implemented.
7. MRA-008 lets users keep documents stored while excluding inactive ones from retrieval. Implemented.
8. MRA-012 records grounded-answer duration and lets the UI submit a prior question through the same RAG path as a new auditable turn. Implemented.

Each story's acceptance criteria were checked only after its implementation and verification evidence were complete.

## Primary product data flow

The supported product flow remains linear:

1. FastAPI streams an uploaded PDF, DOCX, TXT, or Markdown file into the persistent upload volume and queues a PostgreSQL ingestion job.
2. The worker extracts text, creates deterministic overlapping chunks, calls the configured local Ollama embedding model in bounded batches, and stores model-tagged pgvector rows.
3. For a question, FastAPI embeds the normalized input with the conversation's embedding model and retrieves only active, `ready`, model-compatible chunks.
4. The direct CiteNook prompt treats those chunks as untrusted sources, requires exact source markers, and asks the configured local Ollama chat model for one non-streaming grounded answer.
5. The API validates source markers, persists the turn and cited-source snapshot, and returns the answer with document, page, chunk, snippet, score, model, and duration provenance.

Neither optional Release 0.5 command changes this data flow.

## Optional LlamaIndex comparison

`citenook-llamaindex` is a developer-only comparison over data CiteNook already owns. It accepts an explicit document selection and a bounded maximum chunk count, reads only active and `ready` chunks compatible with the chosen embedding model, and maps their existing text, vectors, and metadata into an in-memory LlamaIndex index. Only the comparison question is embedded; the command does not re-ingest files, persist another index, write duplicate vectors, create conversation history, or expose a public route.

The returned answer and source nodes show how the selected LlamaIndex retriever/query engine behaves with the same local models and stored corpus. They do not claim parity with CiteNook's prompt validation or exact `[S1]` citation contract, and one local query is not a performance or quality benchmark.

## Local Ragas evaluation

`citenook-ragas` uses the committed invented fixture and reviewable eight-case dataset. It validates stable IDs, questions, references, fixture evidence, fields, paths, and secret-like values before any model call. It then uses the public CiteNook upload, document polling, conversation, question, and deletion contracts, so answer collection covers the normal worker and direct product RAG path rather than a second evaluation-only backend.

For each case, the harness builds a Ragas `SingleTurnSample` from the user question, CiteNook response, human-written reference, and only the citation snippets returned by the public answer. Faithfulness evaluates the answer against those cited contexts; Factual Correctness compares it with the reference. A configurable local Ollama model performs both judgments through Ragas, with telemetry disabled and no hosted account, key, upload, or experiment service.

The result is non-production review evidence. Scores vary with answer and evaluator models, generation settings, and repeated runs. The eight invented cases are too small for statistical conclusions, no human-judge alignment study has been performed, and using the same model for answering and judging may correlate the results. CiteNook's public response exposes cited snippets rather than every raw top-k candidate, so the harness does not measure full retriever recall, ranking quality, or evidence that was retrieved but not cited.

Timestamped per-case JSON and CSV files remain ignored under `evals/experiments/`. A successful smoke run requires all cases, `0..1` metric values, matching artifact coverage, and cleanup of the run-owned document and conversations; it deliberately has no CI score threshold.

For a step-by-step English comparison over the committed Mosslight fixture, including WSL2 execution, output interpretation, no-data behavior, and cleanup, see [Optional LlamaIndex comparison](llamaindex-comparison.md).
