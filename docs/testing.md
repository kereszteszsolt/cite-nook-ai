# Testing

## Automated checks

```bash
python3 .agents/skills/release-evidence/scripts/verify_repository.py
npm run lint
npm run test
npm run build
docker compose config
docker compose -f docker-compose.yml -f docker-compose.ollama.yml config
```

The first Compose command must contain no `ollama` service and must resolve `OLLAMA_HOST` to an external endpoint. The override configuration must add the `ollama` service, its named volume, `http://ollama:11434` for the API and worker, and host port `11435` by default.

MRA-002's API tests cover model-name normalization, installed/unavailable catalog results, and configured-name validation. Its web tests cover separate selectors, disabled unavailable options, restoration of a stored model pair, and updating the active conversation.

MRA-003's API tests cover all supported suffixes, safe names, UUID directories, chunked writes, size enforcement, SHA-256, cleanup, and the file-before-commit ordering. Its web tests cover multipart requests and uploading with the selected embedding model.

MRA-004's API tests use real TXT, Markdown, DOCX, and two-page PDF fixtures to cover extraction and page retention. They also cover deterministic overlap, bounded embedding batches through the Ollama gateway, pgvector chunk construction, atomic `FOR UPDATE SKIP LOCKED` claiming, and stale-job recovery.

MRA-005's API tests cover newest-first listing, upload-root file boundaries, complete directory deletion, missing documents, and directory restoration after a failed database commit. Its web tests cover every displayed field, failed-job details, original-file links, confirmed deletion, and polling that stops when all documents are terminal.

MRA-006's API tests cover atomic ordered turn storage, deterministic bounded titles, assistant model and citation provenance, newest-activity ordering, complete reload history, bounded recent model history, and conversation deletion. Its web tests cover persisted-message reload and confirmed conversation deletion.

MRA-007's API tests cover question embedding with the conversation model, ready and model-compatible cosine retrieval, deterministic source numbering, bounded top-k selection, source-only prompt rules, recent context, explicit insufficiency, invalid-marker rejection, official Ollama chat calls, and grounded-turn persistence. Its web tests cover question submission, structured references, page labels, similarity scores, and original-document links; the runtime browser smoke also checks the persistent composer layout.

MRA-008's API tests cover the active default, persisted activation changes that leave bytes and indexing state intact, missing documents, and the active-document retrieval filter. Its web tests cover the Chat/Documents tab boundary, the global document list, activation and deactivation controls, retained open/delete actions, the PATCH contract, and update failures.

MRA-009's API tests cover partial conversation updates, title normalization and limits, model preservation, and protection of a manually edited title from first-question replacement. Its web tests cover edit/save/cancel/loading/error states, immediate header/sidebar synchronization, the title-only PATCH contract, Enter and Shift+Enter behavior, bounded composer growth, success reset, failed-question retention, accessible icon controls, and confirmed deletion.

MRA-010 reuses the existing per-conversation API contract. Its web tests cover the model-free application header, stored-pair display, default and fallback model selections, unavailable-model blocking, explicit create/edit cancellation, pair persistence, retryable failures, removal of misleading headings, and custom conversation-deletion cancel/loading/failure behavior without native browser confirmation.

MRA-011's web tests cover the custom document-deletion modal, selected-file and irreversible-data copy, safe initial focus, explicit and Escape cancellation, loading disablement, target-only success, retryable failure, absence of native confirmation, file-picker selection/success/reset/disabled behavior, every document-status badge, bounded failure feedback, and text-labelled Ollama connection states.

MRA-012's API tests cover deterministic server-side duration measurement, assistant-only persistence, non-negative validation, and unchanged grounded retrieval/citation rules. Its web tests cover wider action-ready messages, clipboard success/failure, retry request identity, busy and failed retry behavior, original-history retention, response-time formats, and explicit legacy timing fallback.

MRA-013's settings and web tests cover both loopback CORS defaults, relative same-origin API URLs, normalized fetch failures, checking/connected/Ollama-unavailable/API-unavailable header states, failed initial loading, and successful in-place retry of models, conversations, documents, and the active history.

MRA-014's brand tests cover the configured favicon asset path in both the typed frontend package and the backend-loaded brand document. The web production build copies the SVG into the static output and the browser entrypoint applies the configured path.

MRA-015's Playwright screenshot suite serves only the real Vite/React application shell and intercepts every `/api` request with static generic fixture responses. It does not connect to PostgreSQL, an upload volume, the running Compose application, or Ollama. The suite captures desktop chat, the new-conversation dialog, the stored-document panel, and mobile chat into `docs/screenshots`.

## Runtime smoke checks

External Ollama mode:

```bash
docker compose up --build --detach
curl --fail http://localhost:8000/api/health
curl --fail http://localhost:8000/api/models
curl --fail http://localhost:5173
docker compose down
```

Separate Ollama container mode:

```bash
docker compose -f docker-compose.yml -f docker-compose.ollama.yml up --build --detach
curl --fail http://localhost:8000/api/health
curl --fail http://localhost:8000/api/models
curl --fail http://localhost:11435/api/tags
curl --fail http://localhost:5173
docker compose -f docker-compose.yml -f docker-compose.ollama.yml down
```

For MRA-002, create a conversation through `POST /api/conversations`, update its model pair through `PATCH /api/conversations/{id}`, and confirm that `GET /api/conversations` returns the stored pair after switching between the two Compose modes.

For MRA-003, upload a supported file and its configured embedding model as multipart data:

```bash
curl --fail -X POST http://localhost:8000/api/documents \
  -F 'file=@README.md;filename=smoke.md;type=text/markdown' \
  -F 'embedding_model=qwen3-embedding:0.6b'
```

Restart the stack without `--volumes`, then verify that the document row, queued job, and `<UUID>/smoke.md` file remain present.

For MRA-004, start the worker with the selected embedding model installed in the configured Ollama instance. After the upload, inspect the worker log for the completed job and verify in PostgreSQL that the document is `ready`, `chunk_count` matches its rows in `document_chunks`, every row stores the selected model, and `vector_dims(embedding)` is nonzero. A real two-session database check should hold a row lock on the first queued job and confirm that another worker claim skips it.

For MRA-005, use `GET /api/documents` to inspect all metadata and processing errors, then open `GET /api/documents/{id}/file` and verify that its bytes match the original upload. Delete only a dedicated smoke record through `DELETE /api/documents/{id}`; the response must be 204, its document/chunk/job counts must all be zero, and its UUID upload directory must no longer exist.

For MRA-006, store more turns than `CHAT_HISTORY_MESSAGES` through `ConversationService.record_turn`, restart the API and web containers without removing volumes, and use `GET /api/conversations/{id}/messages` to verify that the complete ordered history, assistant model, and structured citations reload. Verify separately that `recent_history` returns only the configured suffix. Delete only this dedicated smoke conversation through `DELETE /api/conversations/{id}`; the response must be 204 and both its conversation and message counts must become zero.

For MRA-007, create a dedicated conversation whose models are installed, then submit a question through `POST /api/conversations/{id}/messages`. Verify that the assistant content contains only available `[S1]`, `[S2]`, and similar markers, and that every returned citation joins to a `ready` document and chunk whose embedding model matches the conversation. Open each returned document link and verify a 200 response. In the browser, inspect the source label, optional page, snippet, similarity score, and persistent question composer. Delete only the dedicated smoke conversation after recording the evidence.

For MRA-008, upload or select a dedicated ready document, set `isActive` to false through `PATCH /api/documents/{id}`, and confirm the original file and chunks remain while retrieval returns no chunks from that document. Restart the API without removing volumes and verify the false state through `GET /api/documents`; then set it to true and verify retrieval can use it again. In the browser, confirm document upload and management appear only under Documents, and that the active switch retains its value after a reload.

For MRA-009, create a dedicated conversation and update only its title through `PATCH /api/conversations/{id}`. Confirm whitespace normalization, unchanged model fields, 422 for an empty title, and persistence through an API-container restart. In desktop and mobile browser sizes, verify inline title editing, immediate sidebar synchronization, distinct wider user/assistant bubbles, the integrated send icon, panel-contained upward-growing composer with bounded internal scrolling, and the restrained destructive conversation control. On desktop, confirm the composer matches the message-history width, the history ends above it at both minimum and maximum input heights, the header remains compact, and the document has no default page scrollbar. Delete only the dedicated smoke conversation and verify both its conversation and message counts are zero.

For MRA-010, open New conversation and verify its custom modal preselects an installed configured chat and embedding model but does not create a record before confirmation. Cancel, reopen, choose a pair, create the conversation, and confirm both names survive reload through `GET /api/conversations`. From the active conversation header, change the pair and confirm the PATCH sends both names while existing assistant-message `chat_model` values remain unchanged. Verify the global header contains no selectors; `Model configuration` and `Saved messages` are absent; the custom delete modal warns that deletion is permanent and supports Cancel without calling the API. At 1800 × 900 confirm the application header is 52 px, the document has no page scrollbar, the message history remains above the composer, and no native browser dialog is opened. Delete only the dedicated smoke conversation after evidence is recorded.

For MRA-011, open Documents at desktop and mobile widths. Verify Choose file uses the CiteNook control, reports the selected file name, and remains inside the viewport. Inspect queued, processing, ready, and failed records: only their status badges should use the restrained amber, blue, green, and red treatments, while a failed explanation should stay bounded and should not tint the complete table row. Open Delete on a dedicated document and confirm the custom dialog names the file and its stored/indexed data, initially focuses Cancel, closes with Cancel or Escape without a DELETE request, and never opens a browser-native dialog. Confirming a dedicated test record should disable both dialog actions until the API resolves and remove only that record after success; a forced API failure should leave the dialog available for retry. Verify both connected and unavailable Ollama states retain their text and use only their pastel status pills for color feedback. At 1440 × 900 the page should equal the viewport while Documents scrolls internally; at 390 px the picker and dialog should fit without page-level horizontal overflow.

For MRA-012, create a dedicated conversation with installed models and submit one grounded question. Confirm the POST response and a subsequent `GET /api/conversations/{id}/messages` return `responseDurationMs: null` for the user message and the same non-negative integer for the assistant message. Restart the API without removing volumes and verify the values again; inspect PostgreSQL to confirm the nullable integer column and non-negative check constraint. In the browser, verify assistant messages use the wider bounded layout, action rows follow content and references, copy writes the complete message, retry sends the exact preceding question, and the original turn remains while a successful new turn is appended. Force clipboard and retry failures and confirm the stored history remains unchanged. Verify millisecond, second, minute, and unavailable timing labels, disabled retry while answering, independent history/composer layout, no desktop page scrollbar, and no horizontal overflow at 390 px. Delete only the dedicated smoke conversation and confirm both its conversation and message counts are zero.

For MRA-013, keep an external Ollama instance on the configured endpoint and start the base Compose stack. Open both `http://localhost:5173` and `http://127.0.0.1:5173`; in each case confirm that `/api/models`, `/api/conversations`, and `/api/documents` stay on that page origin, return successfully through the Vite proxy, and produce `Ollama connected` without an error banner. Then stop only the API container while keeping the loaded web page open, reload the page, and confirm the neutral check resolves to `CiteNook API unavailable`, no raw `Failed to fetch` appears, and **Retry connection** is present. Start the API again, use that button without refreshing, and confirm the connected state and normal controls return with no duplicate database records.

These commands remove containers and networks only. Named volumes remain persistent.

## Product screenshots

With Node and a Playwright Chromium installation available, regenerate the checked screenshots with:

```bash
npm run screenshots
```

The repository's pinned browser image can run the same dev-only workflow from WSL without using the host Node installation:

```bash
docker run --rm --init --ipc=host \
  -v "$PWD":/workspace \
  -v citenook-node-modules:/workspace/node_modules \
  -w /workspace \
  mcr.microsoft.com/playwright:v1.62.0-noble \
  sh -lc 'npm ci && npm run screenshots'
```

The fixture contains only invented energy, garden, transit, and workshop examples. Keep personal uploads and live API responses out of this suite and review every regenerated PNG before committing it.
