# Release 0.1 verification

These records were moved from the implemented story files by `MRA-018`. They keep the original 2026-08-22 proof and the shipped Release 0.1 facts.

## MRA-001: Run the branded local monorepo

Implementation proof:

- `package.json`, `turbo.json`, `apps/web`, `apps/api`, and both Compose files provide the monorepo and local runtime.
- `packages/brand/brand.json` supplies the shared identity, and the named volumes retain PostgreSQL data, uploads, and optional container-managed Ollama models.
- The repository verifier enforces the source-header policy.

Focused and release proof:

- Brand, settings, shared brand contract, and web API-boundary tests passed.
- `python3 .agents/skills/release-evidence/scripts/verify_repository.py` passed with 3 agents, 3 skills, and 7 stories.
- `npm run lint`, `npm run test`, and `npm run build` passed with 3/3 lint tasks, 4/4 test tasks, 2 Python tests, 2 TypeScript tests, and 3/3 build tasks.
- Both Compose configurations passed; external mode started web, API, worker, and PostgreSQL, while container mode started all five services and served `/api/tags` on port 11435.
- `/api/health` returned `cite-nook-ai`, the branded page loaded, and all three named volumes remained after teardown.
- Commit: `4d844d0` (`feat(mra-001): establish branded local stack`).

The container smoke used an empty Ollama model list; model discovery and selection shipped in `MRA-002`.

## MRA-002: Select and remember Ollama models

Implementation proof:

- `apps/api/app/ollama_gateway.py`, `apps/api/app/services/model_catalog.py`, and `GET /api/models` compare configured names with installed Ollama models.
- The conversation model stores both names, and the React header restores and updates the active pair while blocking unavailable choices.

Focused and release proof:

- Ollama gateway, model catalog, conversation service, header, and app workflow tests passed.
- The repository verifier, both Compose configurations, all 3 lint tasks, all 3 build tasks, 10 Python tests, 4 web tests, and 1 brand test passed.
- External mode discovered installed models and persisted create, update, and list operations; an unconfigured model returned HTTP 422.
- Container mode kept configured models visible but unavailable and retained the conversation pair created in external mode.
- Commits: `275e8c5` (`feat(mra-002): select and remember Ollama models`) and `a39716a` (environment and Ollama setup proof).

## MRA-003: Upload and persist supported documents

Implementation proof:

- The document model stores metadata, embedding model, digest, final path, and a queued job.
- The upload service sanitizes names, streams bounded data, computes SHA-256, moves the file before commit, and stores bytes in `citenook_uploads_data`.
- `POST /api/documents` and the web upload control support the selected installed embedding model.

Focused and release proof:

- Upload, settings, multipart API, and app upload tests passed.
- The repository verifier, both Compose configurations, all 3 lint tasks, all 3 build tasks, 21 Python tests, 6 web tests, and 1 brand test passed.
- PDF, DOCX, TXT, and Markdown uploads returned HTTP 201; unsafe paths became `safe-name.md`, while unsupported, empty, and unconfigured-model requests returned 415, 422, and 422.
- Four rows with 64-character SHA-256 values and four queued jobs matched four UUID-scoped files, and all records, files, sizes, and hashes survived a Compose restart.
- Commit: `3bf8006` (`feat(mra-003): persist supported document uploads`).

## MRA-004: Index documents with a separate worker

Implementation proof:

- The ingestion service claims PostgreSQL jobs with `FOR UPDATE SKIP LOCKED` and requeues stale work.
- Extraction preserves PDF pages and reads DOCX, TXT, and Markdown; deterministic chunks are embedded in batches and stored with model, page, ordinal, and pgvector data.
- `apps/api/app/worker.py` owns the processing loop outside the API process.

Focused and release proof:

- Extraction, chunking, ingestion, and Ollama gateway tests passed.
- Focused Ruff, all 3 lint tasks, all 3 build tasks, 34 API tests, 6 web tests, and 1 brand test passed.
- The external-Ollama worker used `qwen3-embedding:0.6b`, completed five valid jobs, and persisted 1024-dimensional vectors, including 472 chunks for one large file.
- A second session skipped a locked job, and a job aged 16 minutes was requeued under the 15-minute stale limit.
- Commit: `4f49ef9` (`feat(mra-004): index documents in worker`).

## MRA-005: Inspect and manage document status

Implementation proof:

- The document API lists newest-first metadata, serves original files, and deletes records only after safe UUID-scoped file handling.
- The web app shows the four states, bounded failures, file links, delete controls, and polls only while work is queued or processing.

Focused and release proof:

- Document service, web API, and app state tests passed.
- Focused and full Ruff, all 3 lint tasks, all 3 build tasks, 39 API tests, 10 web tests, and 1 brand test passed.
- The live API and Chromium showed every required field and all four states; an original file returned HTTP 200 with the uploaded SHA-256.
- Deleting a ready test document removed one document, four chunks, one job, and its UUID directory after HTTP 204.
- Commit: `51f77b0` (`feat(mra-005): inspect and manage documents`).

## MRA-006: Persist conversations and messages

Implementation proof:

- `ConversationMessage` stores ordered roles, full content, assistant model provenance, citations, and a cascading conversation key.
- Turn storage is atomic, the first title is deterministic and bounded to 80 characters, full history reloads in order, and model context uses a bounded recent suffix.
- The API and web app reload and delete persisted conversations.

Focused and release proof:

- Message persistence, settings, app, and API-client tests passed.
- Five focused API tests, 13 web tests, all 3 lint tasks, all 3 builds, 44 API tests, and 1 brand test passed.
- PostgreSQL stored 14 ordered messages for seven turns with title, model, and citation snapshots; the recent-history limit returned the last 12 messages.
- All 14 messages reloaded after API and web restarts, and deleting the test conversation reduced its conversation and message counts to zero without removing four other chats.
- Commit: `1b163f4` (`feat(mra-006): persist conversations and messages`).

## MRA-007: Answer from documents with references

Implementation proof:

- `GroundedAnswerService` embeds the question, filters ready model-compatible chunks, applies stable cosine ordering and `RAG_TOP_K`, and labels sources as `S1`, `S2`, and so on.
- The prompt treats source text as untrusted data, requires exact markers, and returns an explicit insufficient-source answer when needed.
- Used markers become structured citations, and the web answer links each source to the original file.

Focused and release proof:

- Grounded-answer, Ollama chat, app, and API-client tests passed.
- Ruff, 23 focused API tests, all 15 web tests, all 3 lint tasks, all 3 builds, 52 API tests, and 1 brand test passed.
- The external-Ollama smoke searched 960 compatible 1024-dimensional chunks with `qwen3-embedding:0.6b`; `qwen3.5:9b` returned valid `[S1]` through `[S4]` markers.
- All four citations joined to exact ready, model-compatible chunk UUIDs; Chromium displayed the saved answer and references, and the first source file returned HTTP 200.
- The test conversation and its two messages were removed without changing any document.
- Commit: `2f4f9ce` (`feat(mra-007): answer from documents with references`).

Release 0.1 answers remain non-streaming. Authentication, OCR, reranking, hybrid retrieval, agents, and cloud features stayed outside the release boundary.
