# MRA-008: Manage document availability in a dedicated workspace

## Status

Implemented

## User story

As a user, I want one focused place to manage every uploaded document and choose which sources may participate in answers without deleting them.

## Acceptance criteria

- [x] The web app provides accessible top-level Chat and Documents tabs.
- [x] Document upload and management appear only in the Documents workspace and do not occupy the Chat workspace.
- [x] The Documents workspace lists all uploaded documents independently of the selected conversation.
- [x] Every document has a PostgreSQL-backed active state that defaults to active and is returned by the API.
- [x] A document can be activated or deactivated without deleting it, changing its processing state, or re-running ingestion, and the choice survives reloads and container restarts.
- [x] An inactive document remains stored, openable, deletable, and available for later reactivation.
- [x] Retrieval uses only active documents that are also ready and embedding-model compatible.
- [x] The UI clearly communicates active, inactive, saving, and failed update states.

## Out of scope

Conversation-title editing, chat message widths, composer redesign, and conversation-delete styling belong to MRA-009. Authentication and per-conversation document collections remain outside this release.

## Verification

Run the focused automated checks, repository gates, Compose configuration checks, and the MRA-008 runtime smoke described in `docs/testing.md`.

## Implementation evidence

- Persistence and API: `Document.is_active` is non-null with a true default; startup initialization adds the column idempotently to existing database volumes. `PATCH /api/documents/{id}` changes only this field and returns the complete document contract.
- Retrieval boundary: `GroundedAnswerService.retrieve` requires active, ready, document-model-compatible, and chunk-model-compatible rows before ranking them by cosine distance.
- Focused workspace: `App.tsx` renders accessible Chat/Documents tabs. Upload and the global document table are mounted only in Documents, while conversation controls and the fixed composer remain in Chat.
- Document controls: each row exposes an accessible active switch with saving and inactive labels. Failed updates keep the previous state and use the shared error banner; open and delete actions remain available in either state.

## Focused tests

- `apps/api/tests/test_documents.py`, `test_uploads.py`, and `test_grounded_answers.py` verify the active default, isolated state updates, rollback, missing documents, retained files/indexing metadata, and the exact active retrieval predicate.
- `apps/web/src/App.test.tsx` and `api.test.ts` verify tab separation, global listing, PATCH serialization, activation/deactivation, retained management actions, and failed-update feedback.

## Verification evidence

Verified on 2026-08-22:

- Repository gates — structural verification passed with 3 agents, 3 skills, and 8 stories; full lint passed for all packages.
- Automated tests — 55 API, 19 web, and 1 brand test passed; all API, web, and brand production builds completed.
- Compose validation — both the external-Ollama base configuration and optional separate-Ollama override configuration passed.
- Existing-volume migration — the rebuilt API initialized the new non-null active column without removing the existing PostgreSQL or upload volumes; existing documents returned `isActive: true`.
- Runtime persistence — a dedicated ready document with 6 chunks was deactivated. All 6 chunks and the original file remained, 0 chunks matched the retrieval predicate, and `isActive: false` remained after an API-container restart.
- Runtime reactivation — the same document was enabled without re-ingestion; all 6 chunks immediately matched the retrieval predicate and the 5861-byte original returned HTTP 200.
- Browser smoke — headless Chromium confirmed the default Chat tab contains neither upload nor document list; Documents contains both, exposes all 8 stored-document switches, and contains neither conversation sidebar nor composer.
- Cleanup — the dedicated runtime document was deleted; its document, chunk, and job counts were all zero and its original-file endpoint returned 404.

## Known limitations

- Activation is global for the local installation, not per conversation. Deactivating queued or processing work does not cancel ingestion; it only prevents retrieval, and the completed chunks remain available for later reactivation.
