# MRA-004: Index documents with a separate worker

## Status

Implemented

## User story

As a user, I want document extraction and embedding to happen outside the API request so that uploads return quickly and processing state remains visible.

## Acceptance criteria

- [x] An upload creates a PostgreSQL-backed ingestion job.
- [x] A separate worker claims jobs with FOR UPDATE SKIP LOCKED.
- [x] PDF page numbers are retained; DOCX, TXT, and Markdown text is extracted.
- [x] Text is split into deterministic overlapping chunks.
- [x] Embeddings are produced in batches with the official Ollama Python client.
- [x] Chunks, model name, page number, and pgvector embedding are persisted.
- [x] Stale processing jobs are requeued after a bounded interval.

## Out of scope

Features outside the Release 0.1 boundary documented in the release README.

## Verification

Run the focused automated checks and the Docker smoke test described in `docs/testing.md`.

## Implementation evidence

- Queue and recovery: `apps/api/app/services/ingestion.py` claims PostgreSQL jobs atomically with `FOR UPDATE SKIP LOCKED` and returns processing jobs older than the configured threshold to the queue.
- Extraction and chunking: `apps/api/app/services/extraction.py` retains one-based PDF page numbers and reads DOCX, TXT, and Markdown; `apps/api/app/services/chunking.py` produces deterministic overlapping chunks.
- Embedding boundary: `apps/api/app/ollama_gateway.py` uses the official client's batch embedding API, while the ingestion service enforces a configurable batch size and consistent vector dimensions.
- Persistence and runtime: `DocumentChunk` stores the text, ordinal, page number, embedding model, and pgvector value; `apps/api/app/worker.py` runs the claim/process loop outside the API process.

## Focused tests

- `apps/api/tests/test_extraction.py` uses real TXT, Markdown, DOCX, and two-page PDF files and verifies one-based PDF page retention.
- `apps/api/tests/test_chunking.py` verifies deterministic content, overlap, stable ordinals, and page-number propagation.
- `apps/api/tests/test_ingestion.py` verifies SKIP LOCKED claim SQL, bounded batches, persisted chunk fields, and configured stale-job recovery.
- `apps/api/tests/test_ollama_gateway.py` verifies the official batch embedding call and provider failure handling.

## Verification evidence

Verified on 2026-08-22:

- Focused Ruff checks — passed.
- API test suite — 34 tests passed.
- `npm run lint` through Turborepo — 3/3 package tasks passed.
- `npm run test` through Turborepo — 4/4 tasks passed; 34 Python, 6 web, and 1 brand test passed.
- `npm run build` through Turborepo — 3/3 package tasks passed; the Vite production build completed.
- External-Ollama Docker smoke — the separate worker called `qwen3-embedding:0.6b`, completed all five valid queued jobs, and persisted matching counts of 1024-dimensional pgvector chunks, including 472 chunks for a larger text document.
- PostgreSQL concurrency check — while one session held the first queued job lock, a second service session claimed a different queued job; the generated claim uses `FOR UPDATE SKIP LOCKED`.
- Stale recovery check — a processing job timestamped 16 minutes earlier was returned to `queued` with its worker assignment cleared under the configured 15-minute limit.

## Known limitations

- Persistent status inspection, file opening, deletion, and user-facing failure details belong to MRA-005.
- Retrieval and grounded answers do not consume the stored chunks until MRA-007.
