# MRA-003: Upload and persist supported documents

## Status

Implemented

## User story

As a user, I want to upload a document that remains available after a restart so that it can be indexed and used later.

## Acceptance criteria

- [x] The API accepts PDF, DOCX, TXT, and Markdown multipart uploads.
- [x] The selected embedding model is stored with the document.
- [x] File names are reduced to a safe base name and each upload receives a UUID directory.
- [x] Uploads are streamed with a configurable size limit and SHA-256 digest.
- [x] The file is moved into its final persistent path before the ingestion job is committed.
- [x] Uploaded bytes use a named Docker volume.

## Out of scope

Features outside the Release 0.1 boundary documented in the release README.

## Verification

Run the focused automated checks and the Docker smoke test described in `docs/testing.md`.

## Implementation evidence

- Persistence model: `apps/api/app/models.py` stores document metadata, the selected embedding model, digest, final path, and queued ingestion job.
- Upload boundary: `apps/api/app/services/uploads.py` sanitizes the name, streams bounded chunks, calculates SHA-256, moves the final file, and only then commits the database transaction.
- HTTP and UI: `POST /api/documents` accepts multipart data; `apps/web/src/components/DocumentUpload.tsx` submits supported files with the selected installed embedding model.
- Runtime storage: `docker-compose.yml` mounts `citenook_uploads_data` at the configured `/data/uploads` path for both API and worker.

## Focused tests

- `apps/api/tests/test_uploads.py` covers every supported suffix, safe names, UUID directories, streaming, digest generation, the size limit, cleanup, and commit ordering.
- `apps/api/tests/test_settings.py` covers the upload directory and positive whole-megabyte limit.
- `apps/web/src/api.test.ts` verifies the multipart API request without an incorrect JSON content type.
- `apps/web/src/App.test.tsx` verifies upload with the selected embedding model and success feedback.

## Verification evidence

Verified on 2026-08-22:

- `python3 .agents/skills/release-evidence/scripts/verify_repository.py` — passed.
- `npm run lint` through Turborepo — 3/3 package tasks passed.
- `npm run test` through Turborepo — 4/4 tasks passed; 21 Python, 6 web, and 1 brand test passed.
- `npm run build` through Turborepo — 3/3 package tasks passed; the Vite production build completed.
- Both Compose configuration commands — passed.
- External-mode Docker smoke — PDF, DOCX, TXT, and Markdown multipart requests returned HTTP 201; a path-bearing name was stored as `safe-name.md`; unsupported, empty, and unconfigured-model uploads returned 415, 422, and 422.
- PostgreSQL and volume inspection — four document rows with 64-character SHA-256 values and four queued jobs matched four UUID-scoped files in `citenook_uploads_data`.
- Restart persistence — all four database records, jobs, files, sizes, and file hashes remained after `docker compose down` followed by `docker compose up` without volume deletion.

## Known limitations

- Queued jobs are intentionally not processed until MRA-004.
- Persistent document listing, status inspection, opening, and deletion belong to MRA-005; MRA-003 shows confirmation only for the upload completed in the current page session.
