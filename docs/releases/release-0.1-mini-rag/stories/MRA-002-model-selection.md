# MRA-002: Select and remember Ollama models

## Status

Planned

## User story

As a user, I want to select the local chat and embedding models in the header so that each conversation uses an explicit model configuration.

## Acceptance criteria

- [ ] The API lists configured chat and embedding models and marks whether they are installed in Ollama.
- [ ] The header exposes separate chat-model and embedding-model selectors.
- [ ] Unavailable models remain visible but cannot be selected through the normal UI.
- [ ] A conversation persists both selected model names.
- [ ] Opening an existing conversation restores its selected models.
- [ ] Changing selectors updates the active conversation.

## Out of scope

Features outside the Release 0.1 boundary documented in the release README.

## Verification

Run the focused automated checks and the Docker smoke test described in `docs/testing.md`.
