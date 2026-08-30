# MRA-010: Configure models and controls per conversation

## Status

Implemented

## User story

As a user, I want each chat to keep its own model pair.

## Goal

Choose models when a chat starts. Let the pair change later.

## Dependencies

`MRA-009`.

## Acceptance criteria

- [x] The main CiteNook header is compact and contains branding and Ollama status but no model or model-configuration editor.
- [x] New conversation opens a CiteNook-styled modal before creating anything, lists the configured chat and embedding models, disables unavailable choices, and preselects the configured default or first installed model in each list.
- [x] A conversation is created only after confirming an installed chat and embedding model, stores both selections on that conversation, and restores them when the conversation is opened again.
- [x] The compact conversation header shows the editable conversation title and both stored models, and its model editor persists the selected pair together for future questions while existing assistant-message provenance remains unchanged.
- [x] The misleading `Model configuration` and `Saved messages` headings are absent, and the freed space belongs to the bounded message history above the composer.
- [x] Conversation deletion uses a restrained header action and a custom CiteNook confirmation modal with explicit Cancel and Delete conversation actions, irreversible-deletion copy, loading/error handling, and no native browser confirmation.
- [x] Model and deletion dialogs provide labelled controls, modal semantics, initial focus, Escape cancellation when idle, disabled busy states, cancellation without persistence, and retryable failure states.
- [x] At the default desktop viewport the application header is thinner, the page has no scrollbar, and the independently scrolling message history remains above the full-width composer without overlap.

## Out of scope

Named or reusable saved model configurations, a global Configurations tab, per-user defaults, authentication, cloud synchronization, streaming, and changes to document ingestion or grounded-answer contracts are out of scope.
