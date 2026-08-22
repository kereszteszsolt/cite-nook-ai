# MRA-006: Persist conversations and messages

## Status

Planned

## User story

As a user, I want conversations and messages to remain after a reload so that I can continue previous document questions.

## Acceptance criteria

- [ ] Conversations and messages are stored in PostgreSQL.
- [ ] The conversation list is ordered by most recent activity.
- [ ] The first question creates a bounded deterministic title without a second model request.
- [ ] Each assistant message stores the chat model and structured citations used for that answer.
- [ ] Full history is persisted, while model requests use a bounded recent-history window.
- [ ] The application reloads an existing conversation and its messages.
- [ ] Deleting a conversation cascades to its messages.

## Out of scope

Features outside the Release 0.1 boundary documented in the release README.

## Verification

Run the focused automated checks and the Docker smoke test described in `docs/testing.md`.
