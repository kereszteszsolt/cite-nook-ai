# Release 0.5 verification

## Status

Release 0.5 is in progress. `MRA-018` through `MRA-022` are committed, and `MRA-023` is implemented and awaits commit approval; later stories remain planned.

## Evidence table

| Story | Implementation approval | Focused checks | Review result | Commit approval | Commit | Status |
| --- | --- | --- | --- | --- | --- | --- |
| MRA-018 | Approved 2026-08-30 | Passed | Passed | Approved 2026-08-30 | `98beb09` | Implemented |
| MRA-019 | Approved 2026-08-30 | Passed | Passed | Approved 2026-08-30 | `e32cbba` | Implemented |
| MRA-020 | Approved 2026-08-30 | Passed | Passed | Approved 2026-08-30 | `33d1f50` | Implemented |
| MRA-021 | Approved 2026-08-30 | Passed | Passed | Approved 2026-08-30 | `1b2ace3` | Implemented |
| MRA-022 | Approved 2026-08-30 | Passed | Passed | Approved 2026-08-30 | `4aa1003` | Implemented |
| MRA-023 | Approved 2026-08-30 | Passed | Passed | Pending | This commit | Implemented |
| MRA-024 | Pending | Pending | Pending | Pending | — | Planned |
| MRA-025 | Pending | Pending | Pending | Pending | — | Planned |
| MRA-026 | Pending | Pending | Pending | Pending | — | Planned |
| MRA-027 | Pending | Pending | Pending | Pending | — | Planned |

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

Commit approval was given on 2026-08-30. The resulting hash is reported after the commit succeeds because a commit cannot contain its own hash.

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

Commit approval is pending. The resulting hash is reported after the approved commit succeeds because a commit cannot contain its own hash.

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

The two LlamaIndex Compose commands become runnable after `MRA-026`. Before that story, they remain planned checks.

## Runtime proof

The final release proof must record separate native and LlamaIndex smoke runs. Each run records the backend from `/api/health`, one completed document job, one grounded answer, valid source data, restart persistence, document cleanup, and container shutdown without deleting named volumes.

## Evidence rules

- Record exact commands and short results.
- Link large logs as files instead of pasting them into a story.
- Record the approved commit hash for each story.
- Do not mark a story implemented while a criterion is open.
- Do not add issue or limitation sections to story files.
