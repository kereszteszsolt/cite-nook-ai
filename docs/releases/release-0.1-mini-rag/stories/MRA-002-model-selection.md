# MRA-002: Select and remember Ollama models

## Status

Implemented

## User story

As a user, I want to pick local models so each chat uses the right ones.

## Goal

Show which models can run. Save both model names with each chat.

## Dependencies

`MRA-001`.

## Acceptance criteria

- [x] The API lists configured chat and embedding models and marks whether they are installed in Ollama.
- [x] The header exposes separate chat-model and embedding-model selectors.
- [x] Unavailable models remain visible but cannot be selected through the normal UI.
- [x] A conversation persists both selected model names.
- [x] Opening an existing conversation restores its selected models.
- [x] Changing selectors updates the active conversation.

## Out of scope

Features outside the Release 0.1 boundary documented in the release README.
