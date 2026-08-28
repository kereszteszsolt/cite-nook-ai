# MRA-018: Add an optional LlamaIndex comparison path

## Status

Planned

## User story

As a developer reviewing CiteNook, I want to query the application's already indexed local documents through a small LlamaIndex command so that I can compare a framework-based query engine with the existing direct Ollama and pgvector implementation without putting the stable product path at risk.

## Context

CiteNook already owns extraction, chunking, embeddings, PostgreSQL persistence, pgvector retrieval, prompt construction, citation validation, and conversation storage. Its `document_chunks` schema is an application contract rather than a LlamaIndex-managed vector-store schema. Release 0.5 therefore needs an adapter and comparison path, not a migration or a second ingestion pipeline.

## Scope

Add the minimum optional LlamaIndex packages and a developer-only command that reads existing compatible chunks, maps them to LlamaIndex nodes, performs a real local retrieval/query-engine flow with Ollama, and returns the answer together with the actual source nodes used. Keep it outside the React and public FastAPI contracts.

## Acceptance criteria

- [ ] Confirm current compatibility of `llama-index-core`, `llama-index-llms-ollama`, and `llama-index-embeddings-ollama` with the repository's Python 3.13–3.14 range, pin exact compatible versions, and update the lock file reproducibly.
- [ ] Place LlamaIndex packages in a named optional dependency extra used by framework/evaluation commands; the normal `pip install .` API/worker image must not install them.
- [ ] Do not add the aggregate `llama-index` meta-package, a cloud LLM integration, a LlamaIndex-managed PostgreSQL table, or another persistent vector store.
- [ ] Add one documented CLI/module entry point that accepts a question plus explicit chat and embedding model values, or a conversation identifier from which those values are read; invalid or unavailable configured models fail with an actionable message.
- [ ] Require an explicit document selection or enforce a documented maximum eligible-chunk limit so the comparison command never loads an unbounded corpus into memory.
- [ ] Read only chunks whose documents are `ready`, active, and use the selected embedding model. Empty or incompatible corpora return a clear no-data result rather than falling back to unrelated chunks or model prior knowledge.
- [ ] Map each selected `DocumentChunk` to a LlamaIndex node while preserving the CiteNook document ID, file name, page number, chunk ID, chunk ordinal, and embedding-model metadata.
- [ ] Reuse the already stored chunk embeddings when the pinned LlamaIndex API supports this safely, and use the same configured Ollama embedding model for the query. Do not re-ingest documents or write duplicate embeddings back to PostgreSQL.
- [ ] Use a substantive LlamaIndex retrieval/query primitive such as `VectorStoreIndex` with a retriever and `CitationQueryEngine`/`RetrieverQueryEngine`; a wrapper that only calls `Ollama.complete()` does not satisfy the story.
- [ ] Configure the LlamaIndex Ollama LLM and embedding clients from the existing `OLLAMA_HOST` and selected model names. Do not introduce API keys, external provider fallback, model pulling, or hidden network calls.
- [ ] Return a structured console or JSON result containing the question, answer, selected models, elapsed time, and the source-node metadata/scores actually returned by LlamaIndex. Do not persist a conversation turn or modify document state.
- [ ] Treat source text as untrusted data and configure the query prompt to answer only from retrieved nodes, state insufficiency when evidence is missing, and avoid claiming parity with CiteNook's exact `[S1]` citation contract unless that behavior is separately verified.
- [ ] Add focused tests for settings/model validation, chunk filtering, node mapping, source metadata, no-data behavior, and result serialization without requiring PostgreSQL or Ollama; isolate framework objects behind a narrow adapter so they can be faked.
- [ ] Complete one local smoke query against a real PostgreSQL/pgvector dataset and installed Ollama chat/embedding models, recording the command, model names, number of eligible chunks, and observed limitations without committing private document text.
- [ ] Preserve all existing API, worker, web, ingestion, retrieval, citation, and persistence tests and behavior. No public endpoint, frontend control, database migration, or Compose service is added by this story.

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
