# Release 0.5 verification

## Status

Release 0.5 is implemented. `MRA-018` through `MRA-026` are committed, and implemented `MRA-027` is awaiting commit approval.

## Evidence table

| Story | Implementation approval | Focused checks | Review result | Commit approval | Commit | Status |
| --- | --- | --- | --- | --- | --- | --- |
| MRA-018 | Approved 2026-08-30 | Passed | Passed | Approved 2026-08-30 | `98beb09` | Implemented |
| MRA-019 | Approved 2026-08-30 | Passed | Passed | Approved 2026-08-30 | `e32cbba` | Implemented |
| MRA-020 | Approved 2026-08-30 | Passed | Passed | Approved 2026-08-30 | `33d1f50` | Implemented |
| MRA-021 | Approved 2026-08-30 | Passed | Passed | Approved 2026-08-30 | `1b2ace3` | Implemented |
| MRA-022 | Approved 2026-08-30 | Passed | Passed | Approved 2026-08-30 | `4aa1003` | Implemented |
| MRA-023 | Approved 2026-08-30 | Passed | Passed | Approved 2026-08-30 | `e5e2ce1` | Implemented |
| MRA-024 | Approved 2026-08-31 | Passed | Passed | Approved 2026-08-31 | `f9987ef` | Implemented |
| MRA-025 | Approved 2026-08-31 | Passed | Passed | Approved 2026-08-31 | `e470532` | Implemented |
| MRA-026 | Approved 2026-08-31 | Passed | Passed | Approved 2026-08-31 | `163aa11` | Implemented |
| MRA-027 | Approved 2026-08-31 | Passed | Passed | Approved 2026-08-31 | This commit | Implemented |

## MRA-018 evidence

Implementation approval was given on 2026-08-30 when the user asked to start implementing `MRA-018`.

- `python3 .agents/skills/release-evidence/scripts/verify_repository.py` passed with 3 agents, 3 skills, and 27 stories under one strict rule set.
- The focused historical audit found 17 implemented stories with the exact section order and four to eight checked criteria each.
- The proof audit found `MRA-001` through `MRA-017` once and in order across the four historical release verification files.
- The heading audit found no issue or limitation section in any story.
- The historical release-link audit resolved 21 local Markdown targets across four release maps.
- `git diff --check` passed.
- Review found no application, runtime, dependency, Docker, or data-contract change.

Commit approval was given on 2026-08-30. Commit `98beb09` contains the implementation.

## MRA-019 evidence

Implementation approval was given on 2026-08-30 when the user asked to start `MRA-019`.

- The comment inventory reviewed 59 hand-written Python, TypeScript, TSX, JavaScript, shell, and SQL source files.
- The only retained prose notes are two one-sentence repository-script docstrings and one one-sentence TypeScript comment that explains a non-JSON error fallback.
- No comment repeats code, records old work, or stores plans, history, logs, or release proof.
- SPDX headers, `noqa`, `type: ignore`, lint, coverage, TypeScript, and Vitest directives remain excluded from prose limits.
- `python3 .agents/skills/release-evidence/scripts/test_comment_rules.py` passed all 7 focused tests, including grouped line comments, file-line errors, directives, and a mixed license/prose block.
- `python3 .agents/skills/release-evidence/scripts/verify_repository.py` passed with 3 agents, 3 skills, and 27 stories, including the source-comment audit.
- In the Node 26 container, `npm run lint` passed 3/3 tasks; `npm run test` passed 61 API, 48 web, and 1 brand test; `npm run build` passed 3/3 tasks.
- The host Node command remains unavailable under WSL1, so the documented isolated container path supplied the full gate result.
- `git diff --check` passed, and review found no application behavior, runtime, dependency, Docker, or data-contract change.

Commit approval was given on 2026-08-30. Commit `e32cbba` contains the implementation.

## MRA-020 evidence

Implementation approval was given on 2026-08-30 after the scope and checks were reviewed.

- Conversation state, API actions, dialogs, views, and tests now live under `apps/web/src/features/conversations`.
- Document state, polling, upload, active state, delete work, views, and tests now live under `apps/web/src/features/documents`.
- `App.tsx` is a 136-line shell that calls only the model catalog API and coordinates startup, workspace choice, shared errors, and layout.
- Static boundary checks found no conversation or document API call in `App.tsx`, no direct `fetch` outside `api.ts`, and no import from a removed component path.
- The focused startup, conversation, document, and message-format tests passed 36/36 tests across four files.
- The 24 conversation tests passed in three consecutive runs after async interaction assertions were made timing-safe.
- The full web suite passed 48/48 tests, TypeScript lint passed, and the production build transformed 32 modules successfully.
- In the isolated Node 26 container, full monorepo lint passed 3/3 tasks, tests passed 61 API, 48 web, and 1 brand test, and build passed 3/3 tasks.
- The pinned Playwright screenshot test passed, and a clean repeat matched all four checked desktop and mobile PNG hashes exactly.
- Package manifests, the lock file, shared HTTP types, the API client, and `styles.css` stayed unchanged.
- `git diff --check` passed, and review found no backend, HTTP contract, dependency, routing, global state, or UI framework change.

Commit approval was given on 2026-08-30. Commit `33d1f50` contains the implementation.

## MRA-021 evidence

Implementation approval was given on 2026-08-30 after the scope and checks were reviewed.

- HTTP routers, schemas, and request dependencies now live under `app/api`, while use cases and extraction live under `app/application`.
- Settings and brand loading now live under `app/core`, and SQLAlchemy setup and ORM models live under `app/persistence`.
- The Ollama adapter now lives under `app/ai`, and native chunking lives under `app/rag/native` without adding later-story ports or backends.
- The application model catalog uses its own result data classes, so `app/application` has no dependency on `app/api`.
- Static package checks found no old import path, compatibility module, application-to-API import, empty forwarding layer, or early `bootstrap` or contract module.
- New contract tests preserve all 14 public method and route pairs, the model catalog JSON keys, and the five database table names.
- In the isolated Python 3.14 container, Ruff passed, all 64 API tests passed, the API build passed, and both `app.main` and `app.worker` imported successfully.
- Full monorepo lint passed 3/3 tasks; the sequential test run passed 64 API, 48 web, and 1 brand test; and build passed 3/3 tasks.
- The first parallel full test exposed one timing-sensitive web retry failure after 47/48 web tests, then its focused rerun and the complete sequential suite passed.
- Both current Compose configuration commands, repository verification, and `git diff --check` passed.

Commit approval was given on 2026-08-30. Commit `1b2ace3` contains the implementation.

## MRA-022 evidence

Implementation approval was given on 2026-08-30 after the scope and checks were reviewed.

- `ChatProvider`, `EmbeddingProvider`, and `ModelCatalogProvider` define the three small model boundaries, with one combined type for composition.
- `OllamaProvider` implements all model work, receives its host from composition, and `app/ai/ollama.py` is the only app module that imports the Ollama SDK.
- `build_application()` reads settings, creates one shared provider, and builds the conversation, answer, document, upload, model catalog, and ingestion services.
- FastAPI dependencies return services from the application container stored on `app.state`, so routers no longer construct services.
- Both `app.main` and `app.worker` call the same composition root, and the worker receives the composed ingestion service.
- Static boundary checks found no `get_settings()` call or concrete model provider reference under `app/application`, and no early MRA-023 RAG port or LlamaIndex import.
- Fake-provider tests cover composition without network access, while focused tests preserve model discovery, grounded answers, ingestion failure state, public 503 mapping, and worker retry delay.
- In the isolated Python 3.14 container, Ruff passed and all 70 API tests passed.
- Full monorepo lint passed 3/3 tasks, tests passed 70 API, 48 web, and 1 brand test, and build passed 3/3 tasks.
- Both current Compose configuration commands, repository verification, import compilation, and `git diff --check` passed.

Commit approval was given on 2026-08-30. Commit `4aa1003` contains the implementation.

## MRA-023 evidence

Implementation approval was given on 2026-08-30 after the scope and checks were reviewed.

- `DocumentIndexer` and `SourceRetriever` expose backend-neutral index documents, text sections, and retrieved sources while keeping SQLAlchemy rows inside adapters.
- `NativeDocumentIndexer` owns unchanged chunking, embedding batches, vector validation, replacement writes, and explicit index deletion without committing the application transaction.
- `NativeSourceRetriever` owns query embedding, ready and active filters, embedding-model matching, pgvector cosine order, stable source IDs, and the Release 0.4 score calculation.
- Ingestion now owns extraction and job state only, while grounded answers retain the common prompt, chat, citation, timing, and message flow.
- Document deletion calls the selected indexer before app-record and file cleanup, and rollback tests prove that an index failure preserves both app data and the stored file.
- Contract tests preserve the 14 public method and route pairs, five database table names, citation JSON fields, native `S1` ordering and scores, and the existing HTTP error mappings.
- An isolated `pgvector/pgvector:pg17` smoke test read an existing Release 0.4-style row as `S1` with score `1.0`, replaced its native chunks, and deleted them with no schema migration.
- Static boundary scans found no ORM, pgvector, or embedding implementation in the ingestion and answer services, and no LlamaIndex import in the native API build.
- In the isolated Python 3.14 container, Ruff passed, all 76 API tests passed, and the API build passed.
- In the isolated Node 26 container, TypeScript lint passed, 48 web and 1 brand test passed, and both production builds passed.
- Both current Compose configuration commands, repository verification, import compilation, and `git diff --check` passed.

Commit approval was given on 2026-08-30. Commit `e5e2ce1` contains the implementation.

## MRA-024 evidence

Implementation approval was given on 2026-08-31 after the scope and checks were reviewed.

- The `llamaindex` extra pins `llama-index-core==0.14.24` and `llama-index-vector-stores-postgres==0.8.1`, and `uv.lock` resolves 99 packages.
- Dependency resolution passed for Python 3.13 and 3.14 with the current CiteNook pins, and both versions installed the optional set successfully.
- `CiteNookEmbedding` sends the selected model and bounded batches through the common `EmbeddingProvider` without adding a second Ollama adapter.
- The LlamaIndex indexer splits each extracted section separately, keeps page boundaries, and assigns deterministic UUIDs plus document, file, page, order, model, and node metadata.
- The official PostgreSQL store writes JSONB metadata into the dedicated `citenook_llamaindex` schema and separates collections by embedding model and vector dimension.
- Replacement clears every prior collection for the document and model, while repeated delete is safe and a failed write makes a best-effort cleanup before returning one short error.
- The common ingestion service still marks a document ready only after the indexer returns its stored count, and its existing failure path stores the bounded index error.
- Seven focused unit tests cover batching, metadata, stable IDs, collection names, replacement, repeated delete, and failed-write cleanup; four ingestion tests preserve job state behavior.
- An isolated `pgvector/pgvector:pg17` integration test stored 2 nodes, replaced them with 1 stable node, verified every required metadata field, and passed two delete calls with 0 nodes left.
- Python 3.13 and clean Python 3.14 runs passed Ruff and 83 API tests; without `TEST_DATABASE_URL`, the separately proven PostgreSQL test was the single expected skip.
- A clean native API image imported `app.main` and reported `llama_index=absent`; the run-owned image was removed after the check.
- Web lint, 48 web tests, 1 brand test, both web builds, both current Compose configurations, and `git diff --check` passed.
- Initial isolated attempts stopped before application tests because of copied local environment data or a missing brand mount; the corrected minimal runners produced the results above.
- Static scans found no LlamaIndex import outside its optional adapter and tests, and no retriever, query engine, backend switch, Docker target, or Compose override was added.

Commit approval was given on 2026-08-31. Commit `f9987ef` contains the implementation.

## MRA-025 evidence

Implementation approval was given on 2026-08-31 after the scope and checks were reviewed.

- The adapter first selects ready, active documents for the conversation embedding model and returns no source or model call when none are eligible.
- The common embedding bridge creates one query vector, and its dimension selects an existing model-specific PostgreSQL store without creating a table during read.
- `VectorStoreIndex.from_vector_store()` and its retriever apply eligible document IDs plus the embedding model as LlamaIndex metadata filters.
- Retrieved node text, document data, optional page, stable node UUID, and similarity map to the backend-neutral source record.
- PostgreSQL adds node order and UUID after vector distance, and the adapter repeats that stable tie order before assigning `S1`, `S2`, and later markers.
- The unchanged common answer service still builds the grounded prompt, calls chat, rejects bad markers, stores only cited sources, and uses the fixed insufficient answer with no citation for no result.
- Twenty-two focused tests passed across LlamaIndex indexing and retrieval, native retrieval, and grounded answers.
- An isolated `pgvector/pgvector:pg17` run passed 2 integration tests, excluding inactive, failed, missing, and model-mismatched data while preserving two equal-score nodes in stable order.
- The full Python 3.13 and clean Python 3.14 runs each passed 90 API tests with the 2 PostgreSQL tests skipped when `TEST_DATABASE_URL` was absent.
- Full API Ruff and import compilation passed, and static scans found LlamaIndex imports only in its optional adapter with no query engine, prompt, chat, message storage, backend switch, Docker, or Compose change.
- Initial isolated invocations stopped before application tests because of a capture temp file, an unsupported coverage flag, a root-relative brand path, or a read-only editable build; the corrected runs produced the results above.

Commit approval was given on 2026-08-31. Commit `e470532` contains the implementation.

## MRA-026 evidence

Implementation approval was given on 2026-08-31 after the scope and checks were reviewed.

- Settings tests prove that `native` is the default, `llamaindex` is accepted, and any other value stops composition with a clear error.
- The native and LlamaIndex composition tests each construct one indexer and retriever pair, with no fallback or second live backend.
- Locked Python 3.14 image builds installed 47 native packages and 94 LlamaIndex packages; import checks reported `llama_index=absent` for native and `llama_index=installed` for LlamaIndex.
- All four Compose configurations resolved successfully; the base targets `runtime-native`, the override targets `runtime-llamaindex`, and both API and worker receive the same backend.
- The supported project names resolve to separate `citenook_*` and `citenook-llamaindex_*` PostgreSQL and upload volumes.
- Backend-marker unit tests cover empty databases, Release 0.4 native adoption, same-backend reuse, and both mismatch directions.
- An isolated `pgvector/pgvector:pg17` run passed all 7 marker tests, including real marker storage, legacy native-chunk adoption, and mismatch rejection.
- `/api/health` returns `ragBackend`, while API and worker startup logs reported the selected backend on every isolated start.
- Four isolated end-to-end runs passed for native and LlamaIndex with both external and Compose-managed Ollama, using installed `qwen3:4b` and `qwen3-embedding:0.6b` models.
- Every runtime run produced one ready chunk, one grounded citation, two persisted messages after API, worker, and web restart, and successful deletion of only its dedicated document and conversation.
- Each smoke stack stopped without volume deletion; eight distinct run-owned PostgreSQL and upload volumes were verified before their later test cleanup.
- Full API Ruff and compile checks passed; 102 API tests passed and 3 separately proven PostgreSQL tests were skipped without `TEST_DATABASE_URL`.
- In an isolated Node 26 copy, web and brand lint, test, and build passed 6/6 tasks, including 48 web tests and 1 brand test.
- The first combined Node-only gate stopped at the API lint because that image does not provide `uv`; the API gate then passed separately in its Python environment.
- Repository verification passed with 3 agents, 3 skills, and 27 stories, and `git diff --check` passed.
- Static boundary scans found no LlamaIndex import in native or application packages, direct web fetch outside `api.ts`, UI backend switch, query engine, dual write, dual query, runtime hot switch, or silent fallback.

Commit approval was given on 2026-08-31. Commit `163aa11` contains the implementation.

## MRA-027 evidence

Implementation approval was given on 2026-08-31 after the release documentation scope and checks were reviewed.

- The root README and release map name `native` as the default and show the exact four commands for both backends with external or Compose-managed Ollama.
- Architecture, RAG, development, testing, technology, user, index, and roadmap guides now match the final package tree, shared answer path, deployment settings, image targets, data isolation, startup checks, and reindex rule.
- The active story workflow, repository rules, three Codex role files, and three repository skills use the same one-story, one-backend, Compose, runtime, evidence, and approval rules.
- Locked dependency checks confirm uv `0.11.29`, Node `26.3.0`, `llama-index-core==0.14.24`, and `llama-index-vector-stores-postgres==0.8.1`; the LlamaIndex packages remain optional.
- The roadmap keeps Ragas in Release 0.6 and compares the two real deployments one at a time.
- Repository verification passed with 3 agents, 3 skills, 27 stories, and 107 valid local Markdown links; the story audit found no issue or limitation heading.
- The comment-rule suite passed all 7 tests, the repository verifier passed Ruff, and `git diff --check` passed.
- Full API Ruff and compile checks passed; 102 API tests passed and 3 separately proven PostgreSQL tests were skipped without `TEST_DATABASE_URL`.
- In an isolated Node 26 copy, web and brand lint, test, and build passed 6/6 tasks, including 48 web tests, 1 brand test, and a 32-module web build.
- All four native or LlamaIndex Compose configurations with external or managed Ollama resolved successfully.
- Isolated native and LlamaIndex external-Ollama smoke runs used installed `llama3.1:8b` and `qwen3-embedding:0.6b` models; each reported its selected backend, one ready chunk, one grounded citation, and two persisted messages after API, worker, and web restart.
- Both smoke runs deleted only their dedicated document and conversation, stopped without volume deletion, verified their four named volumes, and then removed those run-owned test volumes.
- An initial native chat attempt with installed `qwen3:4b` returned a long answer without a valid source marker and was correctly rejected with HTTP 502; the clean proof used `llama3.1:8b` and passed both backends.
- Host Node was unavailable and the root Ruff cache was read-only, so the isolated Node copy and direct no-cache Ruff run supplied the complete checks.

Commit approval was given on 2026-08-31. The resulting hash is reported after the approved commit succeeds because a commit cannot contain its own hash.

## Required release checks

```bash
python3 .agents/skills/release-evidence/scripts/verify_repository.py
npm run lint
npm run test
npm run build
docker compose config
docker compose -f docker-compose.yml -f docker-compose.ollama.yml config
docker compose -f docker-compose.yml -f docker-compose.llamaindex.yml config
docker compose -f docker-compose.yml -f docker-compose.llamaindex.yml -f docker-compose.ollama.yml config
```

All four Compose configurations are supported Release 0.5 checks.

## Runtime proof

The final release proof records separate native and LlamaIndex smoke runs. Each run recorded the backend from `/api/health`, one completed document job, one grounded answer, valid source data, restart persistence, document cleanup, and container shutdown without deleting named volumes.

## Evidence rules

- Record exact commands and short results.
- Link large logs as files instead of pasting them into a story.
- Record the approved commit hash for each story.
- Do not mark a story implemented while a criterion is open.
- Do not add issue or limitation sections to story files.
