# Release 0.2 verification

These records were moved from the implemented story files by `MRA-018`. They keep the original 2026-08-22 proof and the shipped Release 0.2 facts.

## MRA-008: Manage document availability in a dedicated workspace

Implementation proof:

- `Document.is_active` defaults to true, is added to old volumes idempotently, and is changed alone by `PATCH /api/documents/{id}`.
- Retrieval requires active, ready, document-model-compatible, and chunk-model-compatible data.
- Accessible Chat and Documents tabs separate chat from global upload and file management, and each row exposes safe active-state feedback.

Focused and release proof:

- Document, upload, grounded-answer, app, and API-client tests covered state, rollback, persistence, retained files, and the exact retrieval predicate.
- The repository verifier, all package lint and builds, both Compose configurations, 55 API tests, 19 web tests, and 1 brand test passed.
- An old volume gained the non-null column without losing data; a six-chunk file stayed stored while inactive, survived an API restart, and returned all six chunks to retrieval after activation without re-ingestion.
- Chromium showed the expected workspace split and all eight stored-document switches, and cleanup removed the test document, chunks, job, and file endpoint.
- Commit: `c94e4ea` (`feat(mra-008): manage document availability`).

Activation is global to the local install, not per conversation. Turning off a queued or processing file does not cancel ingestion; it only blocks retrieval and keeps completed chunks for later use.

## MRA-009: Refine chat interaction and conversation controls

Implementation proof:

- The title PATCH normalizes a custom one-line title, enforces the 120-character limit, preserves the model pair, and protects a manual title from first-question replacement.
- The title editor provides focus, save, cancel, Escape, busy, and retry states, while the response updates both heading and sidebar.
- Wider bubbles, an integrated keyboard-aware composer, bounded growth, separate history scrolling, and a restrained delete action fit inside the viewport.

Focused and release proof:

- Message service, app, and API-client tests covered title rules, immediate UI updates, composer keys and sizes, success and failure states, icons, and deletion.
- The repository verifier, all package lint and builds, both Compose configurations, 58 API tests, 27 web tests, and 1 brand test passed.
- Runtime PATCH normalized whitespace, retained `qwen3.5:9b` and `qwen3-embedding:0.6b`, rejected blank input with HTTP 422, and preserved a custom title across an API restart.
- Chromium verified a 48 px to 160 px composer, no page scrollbar at 1800×900 or 1366×768, no overlap at the cap, and a contained 308 px mobile composer at 390 px width.
- The two tracked test conversations were deleted; a pre-existing read-only conversation remained.
- Commit: `fb6bcfa` (`feat(mra-009): refine chat experience`).

Title edits use the shared error banner and have no undo history. The composer remains non-streaming and keeps the 4000-character question limit.
