# MRA-006: Persist conversations and messages

## Status

Implemented

## User story

As a user, I want conversations and messages to remain after a reload so that I can continue previous document questions.

## Acceptance criteria

- [x] Conversations and messages are stored in PostgreSQL.
- [x] The conversation list is ordered by most recent activity.
- [x] The first question creates a bounded deterministic title without a second model request.
- [x] Each assistant message stores the chat model and structured citations used for that answer.
- [x] Full history is persisted, while model requests use a bounded recent-history window.
- [x] The application reloads an existing conversation and its messages.
- [x] Deleting a conversation cascades to its messages.

## Out of scope

Features outside the Release 0.1 boundary documented in the release README.

## Verification

Run the focused automated checks and the Docker smoke test described in `docs/testing.md`.

## Implementation evidence

- Persistence contract: `ConversationMessage` stores stable ordinals, roles, complete content, assistant chat-model provenance, structured JSONB citations, and a cascading PostgreSQL conversation foreign key.
- Turn storage: `ConversationService.record_turn` locks the conversation row, writes the user and assistant records in one transaction, and derives the first title deterministically from normalized question text with an 80-character limit and no model call.
- History boundaries: `list_messages` returns every message in ascending order for reload, while `recent_history` returns only the configurable `CHAT_HISTORY_MESSAGES` suffix in chronological order.
- API and web behavior: `GET /api/conversations/{id}/messages` reloads stored history, the sidebar is ordered by latest activity, and confirmed `DELETE /api/conversations/{id}` removes the conversation and its messages.

## Focused tests

- `apps/api/tests/test_messages.py` verifies atomic ordered turns, the row lock, title determinism and stability, assistant provenance, complete versus bounded history, recent-activity ordering, and delete cascade configuration.
- `apps/api/tests/test_settings.py` verifies the configurable recent-history limit.
- `apps/web/src/App.test.tsx` verifies persisted history reload and confirmed conversation deletion; `apps/web/src/api.test.ts` verifies the messages and DELETE contracts.

## Verification evidence

Verified on 2026-08-22:

- Focused API tests — 5 message-persistence tests passed.
- Frontend TypeScript and Vitest checks — passed; 13 web tests passed.
- Full repository gates — lint passed for all three packages; 44 API, 13 web, and 1 brand test passed; all three production builds completed.
- External-Ollama Docker smoke — PostgreSQL stored 14 ordered messages for seven turns, an 80-character deterministic title, the assistant model, and structured document/chunk citation snapshots; the recent-history boundary returned only the configured final 12 messages.
- Reload smoke — after restarting the API and web containers, the API returned all 14 messages from ordinal 1 through 14 and a headless Chromium render displayed the persisted conversation and saved messages.
- Deletion smoke — the dedicated conversation began with 14 messages; DELETE returned 204 and both its conversation and message counts became zero, while four pre-existing conversations remained.

## Known limitations

- MRA-006 exposes the persistence and reload contract but does not accept arbitrary assistant content from the browser. MRA-007 owns question submission, compatible-chunk retrieval, the official Ollama chat request, grounded-answer generation, and detailed source rendering.
