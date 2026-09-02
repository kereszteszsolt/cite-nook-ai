# MRA-006: Persist conversations and messages

## Status

Implemented

## User story

As a user, I want chats to stay after I reload the page.

## Goal

Save chats and messages. Load them in a clear order.

## Dependencies

`MRA-002`.

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
