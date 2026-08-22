# MRA-005: Inspect and manage document status

## Status

Implemented

## User story

As a user, I want to see document processing status and errors so that I know when a document is ready for questions.

## Acceptance criteria

- [x] The Documents section lists file name, size, embedding model, status, chunk count, and upload time.
- [x] Document status uses queued, processing, ready, or failed.
- [x] Failed processing stores and displays a bounded error message.
- [x] The web app polls only while queued or processing documents exist.
- [x] The original file can be opened from the document list.
- [x] Deleting a document removes its database rows, chunks, jobs, and stored file directory.

## Out of scope

Features outside the Release 0.1 boundary documented in the release README.

## Verification

Run the focused automated checks and the Docker smoke test described in `docs/testing.md`.

## Implementation evidence

- API contract: `GET /api/documents` returns newest-first metadata with one of four document statuses and an optional bounded error; `GET /api/documents/{id}/file` serves the original inline; `DELETE /api/documents/{id}` returns 204 after successful cleanup.
- Safe persistence cleanup: `apps/api/app/services/documents.py` limits file access to `<UPLOAD_DIR>/<document UUID>/...`, quarantines that UUID directory, commits the database cascade, restores bytes on commit failure, and removes the directory after success.
- Web behavior: `apps/web/src/components/DocumentList.tsx` renders every required field, terminal failures, original-file links, and confirmed delete controls. `apps/web/src/App.tsx` polls at two-second intervals only while queued or processing documents exist.
- Existing ingestion boundary: `apps/api/app/services/ingestion.py` bounds stored worker errors to 2000 characters and transitions documents only through queued, processing, ready, or failed.

## Focused tests

- `apps/api/tests/test_documents.py` verifies newest-first selection, safe original-file resolution, successful database/file deletion, unknown documents, and directory restoration after a failed commit.
- `apps/web/src/api.test.ts` verifies list, inline-file URL, DELETE, and empty 204 response handling.
- `apps/web/src/App.test.tsx` verifies required metadata, failed errors, original-file links, confirmed deletion, and polling that stops when every document becomes terminal.

## Verification evidence

Verified on 2026-08-22:

- Focused and full Ruff checks — passed.
- API test suite — 39 tests passed.
- Frontend TypeScript and focused Vitest checks — passed; 10 web tests passed.
- `npm run lint` through Turborepo — 3/3 package tasks passed.
- `npm run test` through Turborepo — 4/4 tasks passed; 39 Python, 10 web, and 1 brand test passed.
- `npm run build` through Turborepo — 3/3 package tasks passed; the Vite production build completed.
- External-Ollama Docker smoke — the live API listed every required field and all four statuses, including bounded failure details; a headless Chromium render showed the document table, status badges, and actions.
- Original-file smoke — the inline response returned HTTP 200 with the original name and an SHA-256 hash identical to the uploaded file.
- Deletion smoke — a dedicated ready document began with one document, four chunks, one job, and its stored UUID directory; DELETE returned 204 and all three database counts plus the directory became absent.

## Known limitations

- Document questions, persistent messages, retrieval, and citations remain in MRA-006 and MRA-007.
