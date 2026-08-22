# MRA-002: Select and remember Ollama models

## Status

Implemented

## User story

As a user, I want to select the local chat and embedding models in the header so that each conversation uses an explicit model configuration.

## Acceptance criteria

- [x] The API lists configured chat and embedding models and marks whether they are installed in Ollama.
- [x] The header exposes separate chat-model and embedding-model selectors.
- [x] Unavailable models remain visible but cannot be selected through the normal UI.
- [x] A conversation persists both selected model names.
- [x] Opening an existing conversation restores its selected models.
- [x] Changing selectors updates the active conversation.

## Out of scope

Features outside the Release 0.1 boundary documented in the release README.

## Verification

Run the focused automated checks and the Docker smoke test described in `docs/testing.md`.

## Implementation evidence

- Model catalog: `apps/api/app/ollama_gateway.py`, `apps/api/app/services/model_catalog.py`, and `GET /api/models` use the official Ollama client to compare configured names with installed models.
- Persistence: `apps/api/app/models.py` stores both model names on each conversation; the conversation API lists, creates, and updates that pair.
- Web workflow: `apps/web/src/components/Header.tsx` renders separate selectors and disables unavailable options; `apps/web/src/App.tsx` restores and updates the active conversation.

## Focused tests

- `apps/api/tests/test_ollama_gateway.py` verifies Ollama response handling and model-name normalization.
- `apps/api/tests/test_model_catalog.py` verifies installed markers and the unavailable-provider fallback.
- `apps/api/tests/test_conversation_service.py` verifies configured-name validation.
- `apps/web/src/components/Header.test.tsx` verifies separate selectors and visible, disabled unavailable models.
- `apps/web/src/App.test.tsx` verifies restoring stored selections and persisting selector changes.

## Verification evidence

Verified on 2026-08-22:

- `python3 .agents/skills/release-evidence/scripts/verify_repository.py` — passed.
- `npm run lint` through Turborepo — 3/3 package tasks passed.
- `npm run test` through Turborepo — 4/4 tasks passed; 10 Python, 4 web, and 1 brand test passed.
- `npm run build` through Turborepo — 3/3 package tasks passed; the Vite production build completed.
- Both Compose configuration commands — passed.
- External-mode Docker smoke — Ollama discovery marked the installed chat and embedding models correctly; creating, updating, and listing a conversation preserved its model pair; an unconfigured model returned HTTP 422.
- Container-mode Docker smoke — all five services started, Ollama reported an empty installed-model list, configured models remained visible as unavailable, and the conversation created in external mode retained its updated model pair.

## Known limitations

- MRA-002 stores conversation model configuration only. Persistent messages, document ingestion, and grounded answers belong to later stories.
