# MRA-018: Add an optional LlamaIndex comparison path

## Status

Implemented

## User story

As a developer reviewing CiteNook, I want to query the application's already indexed local documents through a small LlamaIndex command so that I can compare a framework-based query engine with the existing direct Ollama and pgvector implementation without putting the stable product path at risk.

## Context

CiteNook already owns extraction, chunking, embeddings, PostgreSQL persistence, pgvector retrieval, prompt construction, citation validation, and conversation storage. Its `document_chunks` schema is an application contract rather than a LlamaIndex-managed vector-store schema. Release 0.5 therefore needs an adapter and comparison path, not a migration or a second ingestion pipeline.

## Scope

Add the minimum optional LlamaIndex packages and a developer-only command that reads existing compatible chunks, maps them to LlamaIndex nodes, performs a real local retrieval/query-engine flow with Ollama, and returns the answer together with the actual source nodes used. Keep it outside the React and public FastAPI contracts.

## Acceptance criteria

- [x] Confirm current compatibility of `llama-index-core`, `llama-index-llms-ollama`, and `llama-index-embeddings-ollama` with the repository's Python 3.13–3.14 range, pin exact compatible versions, and update the lock file reproducibly.
- [x] Place LlamaIndex packages in a named optional dependency extra used by framework/evaluation commands; the normal `pip install .` API/worker image must not install them.
- [x] Do not add the aggregate `llama-index` meta-package, a cloud LLM integration, a LlamaIndex-managed PostgreSQL table, or another persistent vector store.
- [x] Add one documented CLI/module entry point that accepts a question plus explicit chat and embedding model values, or a conversation identifier from which those values are read; invalid or unavailable configured models fail with an actionable message.
- [x] Require an explicit document selection or enforce a documented maximum eligible-chunk limit so the comparison command never loads an unbounded corpus into memory.
- [x] Read only chunks whose documents are `ready`, active, and use the selected embedding model. Empty or incompatible corpora return a clear no-data result rather than falling back to unrelated chunks or model prior knowledge.
- [x] Map each selected `DocumentChunk` to a LlamaIndex node while preserving the CiteNook document ID, file name, page number, chunk ID, chunk ordinal, and embedding-model metadata.
- [x] Reuse the already stored chunk embeddings when the pinned LlamaIndex API supports this safely, and use the same configured Ollama embedding model for the query. Do not re-ingest documents or write duplicate embeddings back to PostgreSQL.
- [x] Use a substantive LlamaIndex retrieval/query primitive such as `VectorStoreIndex` with a retriever and `CitationQueryEngine`/`RetrieverQueryEngine`; a wrapper that only calls `Ollama.complete()` does not satisfy the story.
- [x] Configure the LlamaIndex Ollama LLM and embedding clients from the existing `OLLAMA_HOST` and selected model names. Do not introduce API keys, external provider fallback, model pulling, or hidden network calls.
- [x] Return a structured console or JSON result containing the question, answer, selected models, elapsed time, and the source-node metadata/scores actually returned by LlamaIndex. Do not persist a conversation turn or modify document state.
- [x] Treat source text as untrusted data and configure the query prompt to answer only from retrieved nodes, state insufficiency when evidence is missing, and avoid claiming parity with CiteNook's exact `[S1]` citation contract unless that behavior is separately verified.
- [x] Add focused tests for settings/model validation, chunk filtering, node mapping, source metadata, no-data behavior, and result serialization without requiring PostgreSQL or Ollama; isolate framework objects behind a narrow adapter so they can be faked.
- [x] Complete one local smoke query against a real PostgreSQL/pgvector dataset and installed Ollama chat/embedding models, recording the command, model names, number of eligible chunks, and observed limitations without committing private document text.
- [x] Preserve all existing API, worker, web, ingestion, retrieval, citation, and persistence tests and behavior. No public endpoint, frontend control, database migration, or Compose service is added by this story.

## Verification plan

- Install the project once without the optional extra and confirm the API/worker build remains unchanged, then install with the optional extra and verify lock-file consistency.
- Run focused unit tests for the LlamaIndex adapter and command with fake nodes, embeddings, retriever results, and LLM output.
- Run the existing API lint, test, and build commands plus both Compose configuration checks.
- With a dedicated privacy-safe document already indexed, execute the comparison command once with compatible models and once with an incompatible embedding model; verify successful source output in the first case and an explicit no-data result in the second.
- Inspect the database before and after the command to confirm no rows, embeddings, document states, conversations, or messages changed.

## Out of scope

Replacing `GroundedAnswerService`, selecting LlamaIndex from the UI or public API, persisting LlamaIndex indices, LlamaIndex ingestion/readers, database-schema changes, chat memory, agents, tools, reranking, hybrid search, additional vector stores, streaming, and framework performance claims are excluded.

## Implementation notes

Prefer a small module under an evaluation or examples namespace and reuse the existing SQLAlchemy models/settings. The comparison path should make LlamaIndex visible and technically real while remaining removable without affecting the product. If precomputed embeddings cannot be consumed reliably by the pinned version, stop and document the compatibility gap rather than creating an unbounded re-indexing path.

## Comments

- Implemented in `apps/api/app/evaluation/llamaindex_compare.py` with the exact `framework-evaluation` extra in `apps/api/pyproject.toml`; the normal Compose API image was verified to contain no `llama_index` package.
- Focused evidence on 2026-08-28: Python 3.13.14 and 3.14.4 both installed the locked optional extra and passed 16 tests; the full API suite passed Ruff, 77 tests, and bytecode compilation. Clean Node 26 checks passed brand lint/build plus 1 test and web lint/build plus 48 tests. The repository audit and both Compose configuration checks passed.
- Real-stack evidence used one invented 206-byte TXT fixture, PostgreSQL/pgvector, `llama3.1:8b`, and `qwen3-embedding:0.6b`. One eligible chunk produced an `answered` result in 41,333 ms with source metadata and score `0.747135`; a missing explicit document selection produced `no_data` with zero sources in 28 ms.
- Database row counts and the fixture's status, content hash, and embedding hash were unchanged by the comparison command. The dedicated document, chunk, job, and uploaded file were removed after verification. The host npm command was unavailable under WSL1, so brand/web checks ran in an isolated Linux container; `embeddinggemma` was not installed, so the real no-data smoke used a missing explicit document ID while model-incompatibility filtering remained covered by focused tests.
