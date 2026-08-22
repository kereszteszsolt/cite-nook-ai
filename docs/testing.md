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

MRA-007's API tests cover question embedding with the conversation model, ready and model-compatible cosine retrieval, deterministic source numbering, bounded top-k selection, source-only prompt rules, recent context, explicit insufficiency, invalid-marker rejection, official Ollama chat calls, and grounded-turn persistence. Its web tests cover question submission, structured references, page labels, similarity scores, and original-document links; the runtime browser smoke also checks the fixed composer layout.

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

For MRA-007, create a dedicated conversation whose models are installed, then submit a question through `POST /api/conversations/{id}/messages`. Verify that the assistant content contains only available `[S1]`, `[S2]`, and similar markers, and that every returned citation joins to a `ready` document and chunk whose embedding model matches the conversation. Open each returned document link and verify a 200 response. In the browser, inspect the source label, optional page, snippet, similarity score, and fixed question composer. Delete only the dedicated smoke conversation after recording the evidence.

These commands remove containers and networks only. Named volumes remain persistent.
