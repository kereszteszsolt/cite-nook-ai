# MRA-008: Manage document availability in a dedicated workspace

## Status

Implemented

## User story

As a user, I want one place to choose which files can support an answer.

## Goal

Keep file work out of chat. Let me turn each file on or off.

## Dependencies

`MRA-007`.

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
