# MRA-010: Configure models and controls per conversation

## Status

Implemented

## User story

As a local CiteNook user, I want to choose and later change the chat and embedding models for each conversation so that every conversation remembers its own model pair without global configuration controls getting in the way.

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

## Verification

Run focused web tests, all repository lint/test/build gates, both Compose configuration checks, and the MRA-010 browser smoke described in `docs/testing.md`.

## Implementation evidence

- `Header` now renders only the shared brand identity and Ollama status; model controls exist only in conversation workflows.
- `App` opens a model dialog before creation, restores each active conversation's persisted pair, updates both model fields together, and keeps document uploads aligned with the active/default embedding model.
- `ConversationDialogs` provides custom create/edit and irreversible-delete flows with installed-model boundaries, available defaults, modal semantics, initial focus, Escape cancellation, busy states, and retryable errors.
- The compact conversation header keeps title editing, the stored model summary, model editing, and a restrained destructive action together. `ConversationMessages` now dedicates its bounded content area to history and the composer without a decorative saved-message heading.
- The existing FastAPI `ConversationCreate`/`ConversationUpdate`, `ConversationService`, and PostgreSQL `conversations.chat_model`/`embedding_model` fields remain the only model-pair persistence contract; no configuration entity or migration was added.

## Focused tests

- `apps/web/src/App.test.tsx` covers default/fallback selection, unavailable-model blocking, explicit creation, stored-pair display, edit/cancel/failure states, heading removal, and custom deletion cancel/loading/failure flows without `confirm()`.
- `apps/web/src/api.test.ts` verifies that conversation creation and model updates send both camel-case model fields through the centralized API boundary.
- `apps/web/src/components/Header.test.tsx` verifies the compact brand/status header contains no combobox or configuration label.
- `apps/api/tests/test_messages.py` verifies a conversation model-pair update does not rewrite existing assistant-message model provenance.

## Verification evidence

Verified on 2026-08-22:

- Automated gates — Ruff passed; all 59 API tests, 35 web tests, and 1 brand test passed. API compileall and web/brand production builds completed successfully.
- Repository and Compose — structural verification passed with 3 agents, 3 skills, and 10 stories; both the external-Ollama base Compose file and optional separate-Ollama override resolved successfully.
- API runtime — a dedicated conversation was created with `llama3.1:8b`/`qwen3-embedding:0.6b`, atomically changed to `qwen3.5:9b`/`qwen3-embedding:0.6b`, reloaded with that exact pair, and deleted after verification.
- Browser smoke — Chromium opened the create, edit, and delete dialogs without any native browser dialog. Creation preselected the installed defaults, edit restored the stored pair, the first model field received focus, Escape closed the idle create dialog, and Cancel received initial destructive-dialog focus.
- Desktop layout — at 1800 × 900 the global header rendered at 52 px, the conversation header at 110 px, the page height equalled the viewport, and the 1320 px message history ended 10 px above the equally wide composer. No global selector, `Model configuration`, `Saved messages`, or page scrollbar was present.
- Rejected-prototype cleanup — the local persistent volume retained 2 conversations, 4 messages, and 8 documents while the uncommitted prototype's configuration table and conversation FK column were removed; the final runtime smoke left no dedicated test conversation.

## Known limitations

- Documents continue to use the active conversation's embedding model for new uploads, or the configured available default when no conversation is active.
- Document deletion retains its existing confirmation flow; this story replaces the native confirmation only for conversation deletion.
